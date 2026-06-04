from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from django.db.models.signals import pre_save
from django.contrib.postgres.search import SearchVector

from questions.models import Question, Answer, QuestionLike, AnswerLike

@receiver([post_save, post_delete], sender=Answer)
def update_question_answers_count(sender, instance, **kwargs):
    question = instance.question
    question.answers_cnt = question.answers.count()
    question.save(update_fields=['answers_cnt'])
    
@receiver([post_save, post_delete], sender=QuestionLike)
def update_question_likes_count(sender, instance, **kwargs):
    question = instance.question
    result = question.question_likes.aggregate(total=Sum('value'))
    question.likes_cnt = result['total'] or 0
    question.save(update_fields=['likes_cnt'])
    
@receiver([post_save, post_delete], sender=AnswerLike)
def update_answer_likes_count(sender, instance, **kwargs):
    answer = instance.answer
    result = answer.answer_likes.aggregate(total=Sum('value'))
    answer.likes_cnt = result['total'] or 0
    answer.save(update_fields=['likes_cnt'])
    
@receiver(post_save, sender=Question)
def update_search_vector(sender, instance, created, **kwargs):
    Question.objects.filter(id=instance.id).update(
        search_vector=(
            SearchVector('title', weight='A', config='russian') +
            SearchVector('text', weight='B', config='russian')
        )
    )