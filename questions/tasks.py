from celery import shared_task
from django.core.cache import cache
from django.db.models import Count, Sum, F, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.conf import settings
import requests
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from questions.models import Tag, Answer, Question


User = get_user_model()
CACHE_TTL = 60 * 15

@shared_task
def update_popular_tags():
    threshold = timezone.now() - timedelta(days=90)
    
    tags_qs = Tag.objects.filter(
        questions__created_at__gte=threshold
    ).annotate(
        questions_count=Count('questions', distinct=True)
    ).order_by('-questions_count')[:10]

    data = [
        {'name': tag.name, 'count': tag.questions_count, 'color': tag.color}
        for tag in tags_qs
    ]
    
    cache.set('popular_tags', data, timeout=CACHE_TTL)
    return data


@shared_task
def update_best_members():
    threshold = timezone.now() - timedelta(days=365)
    
    users_qs = User.objects.annotate(
        week_q_likes=Sum('questions__question_likes__value', filter=Q(questions__created_at__gte=threshold)),
        week_a_likes=Sum('answers__answer_likes__value', filter=Q(answers__created_at__gte=threshold))
    ).annotate(
        total_popularity=F('week_q_likes') + F('week_a_likes')
    ).filter(total_popularity__gt=0).order_by('-total_popularity')[:10]

    data = [
        {
            'nickname': user.profile.get_display_name(),
            'score': user.total_popularity or 0
        }
        for user in users_qs
    ]
    
    cache.set('best_members', data, timeout=CACHE_TTL)
    return data

@shared_task
def notify_new_answer(answer_id):
    try:
        answer = Answer.objects.select_related('author', 'question__author').get(id=answer_id)
    except Answer.DoesNotExist:
        return

    channel = f"question_{answer.question_id}"
    
    nickname = answer.author.profile.get_display_name()
    
    payload = {
        "answer_id": answer.id,
        "text": answer.text,
        "author_username": answer.author.username,
        "author_nickname": nickname,
        "created_at": answer.created_at.isoformat(),
        "is_approved": answer.is_approved,
        "question_author_id": answer.question.author_id
    }

    url = f"{settings.CENTRIFUGO_URL.rstrip('/')}/api"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": settings.CENTRIFUGO_SECRET
    }
    data = {
        "method": "publish",
        "params": {
            "channel": channel,
            "data": payload
        }
    }
    
    requests.post(url, json=data, headers=headers, timeout=5)
        
@shared_task
def send_new_answer_notification(question_id, answer_id, recipient_email):
    question = Question.objects.get(id=question_id)
    answer = Answer.objects.select_related('author').get(id=answer_id)
    
    subject = f'Новый ответ на вопрос: {question.title}'
    
    context = {
        'question_title': question.title,
        'question_text': question.text,
        'answer_author': answer.author.username,
        'answer_text': answer.text,
        'question_url': f'http://localhost:8000/question/{question_id}/',
    }
    
    html_content = render_to_string('emails/new_answer.html', context)
    
    email = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
    )
    email.content_subtype = "html" 
    email.send(fail_silently=False)