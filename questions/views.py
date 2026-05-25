from typing import Any

from django.shortcuts import get_object_or_404, redirect
from django.core.paginator import EmptyPage, Paginator, PageNotAnInteger
from django.views.generic import TemplateView, FormView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from questions.forms import QuestionForm, AnswerForm
from core.views import get_sidebar_context
from questions.models import Question, Tag, QuestionLike, AnswerLike, Answer

def paginate(queryset, request, per_page=15):
    page_num = request.GET.get('page', 1)
    paginator = Paginator(queryset, per_page)
    try:
        page = paginator.get_page(page_num)
    except (PageNotAnInteger, EmptyPage):
        page = paginator.get_page(1)
    return page
        
def get_question_votes_context(user_id, question_ids):
    if not user_id or not question_ids:
        return {}
    
    question_likes_qs = QuestionLike.objects.filter(
        user_id=user_id, 
        question_id__in=question_ids
    )
    return {like.question_id: like.value for like in question_likes_qs}


def get_answer_votes_context(user_id, answer_ids):
    if not user_id or not answer_ids:
        return {}
    
    answer_likes_qs = AnswerLike.objects.filter(
        user_id=user_id, 
        answer_id__in=answer_ids
    )
    return {answer.answer_id: answer.value for answer in answer_likes_qs}

class IndexPageView(TemplateView):
    template_name = 'questions/index.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)     
        page = paginate(Question.objects.new(), self.request)
        
        if self.request.user.is_authenticated:
            question_ids = [q.id for q in page.object_list]
            votes_map = get_question_votes_context(self.request.user.pk, question_ids)
            
            for question in page.object_list:
                question.user_vote = votes_map.get(question.id, 0)
        else:
            for question in page.object_list:
                question.user_vote = 0
                
        context['questions'] = page
        context['page'] = page
        context.update(get_sidebar_context())
        return context

class TagPageView(TemplateView):
    template_name = 'questions/tag.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        tag_name = self.kwargs['tag_name']
        tag = get_object_or_404(Tag, name=tag_name)
        page = paginate(Question.objects.by_tag(tag_name), self.request)
        
        if self.request.user.is_authenticated:
            question_ids = [q.id for q in page.object_list]
            votes_map = get_question_votes_context(self.request.user.pk, question_ids)
            
            for question in page.object_list:
                question.user_vote = votes_map.get(question.id, 0)
        else:
            for question in page.object_list:
                question.user_vote = 0
        
        context["questions"] = page
        context["page"] = page
        context["tag"] = tag
        context.update(get_sidebar_context())
        return context

class HotPageView(TemplateView):
    template_name = 'questions/hot.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        page = paginate(Question.objects.hot(), self.request)
        
        if self.request.user.is_authenticated:
            question_ids = [q.id for q in page.object_list]
            votes_map = get_question_votes_context(self.request.user.pk, question_ids)
            
            for question in page.object_list:
                question.user_vote = votes_map.get(question.id, 0)
        else:
            for question in page.object_list:
                question.user_vote = 0
        
        context['questions'] = page
        context['page'] = page 
        context.update(get_sidebar_context())
        return context  
    
class QuestionPageView(TemplateView):
    template_name = 'questions/question.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        question_id = kwargs["question_id"]
        question = get_object_or_404(Question, pk=question_id)
        answers_qs = Answer.objects.filter(question=question).select_related("author", "author__profile").order_by("-created_at")
        
        page = paginate(answers_qs, self.request, per_page=10)
        
        if self.request.user.is_authenticated:
            votes_map = get_question_votes_context(self.request.user.pk, [question.id])
            question.user_vote = votes_map.get(question.id, 0)
        else:
            question.user_vote = 0
            
        if self.request.user.is_authenticated:
            answer_ids = [a.id for a in page.object_list]
            votes_map = get_answer_votes_context(self.request.user.pk, answer_ids)
            
            for answer in page.object_list:
                answer.user_vote = votes_map.get(answer.id, 0)
        else:
            for answer in page.object_list:
                answer.user_vote = 0
                    
        context["question"] = question
        context["answers"] = page
        context["page"] = page
        context.update(get_sidebar_context())
        context["answer_form"] = AnswerForm()
        return context
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        question_id = kwargs["question_id"]
        question = get_object_or_404(Question, pk=question_id)
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(question=question, author=request.user)
            return redirect(f"/question/{question_id}/#answer-{answer.id}")
        context = self.get_context_data(**kwargs)
        context["answer_form"] = form
        return self.render_to_response(context)
        
@method_decorator(login_required, name='dispatch')
class AskPageView(FormView):
    template_name = 'questions/ask.html'
    form_class = QuestionForm
    success_url = "/"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(get_sidebar_context())
        return context
    
    def form_valid(self, form):
        question = form.save(author=self.request.user)
        return redirect("question", question_id = question.id)
    
class LikeQuestionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, question_id):
        target_vote = int(request.POST.get("vote", 0))
        if target_vote not in (-1, 0, 1):
            return Response({'error': 'invalid_vote'}, status=status.HTTP_400_BAD_REQUEST)
        
        question = get_object_or_404(Question, pk=question_id)
        question.set_user_vote(request.user, target_vote)
        
        question.refresh_from_db()
        
        return Response({
            'rating': question.net_rating, 
            'user_vote': target_vote, 
            'status': 'ok'
        })
        
class LikeAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, question_id, answer_id):
        target_vote = int(request.data.get("vote", 0))
        
        if target_vote not in (-1, 0, 1):
            return Response({'error': 'invalid_vote'}, status=status.HTTP_400_BAD_REQUEST)
        
        answer = get_object_or_404(Answer, pk=answer_id, question_id=question_id)
        answer.set_user_vote(request.user, target_vote)
        
        answer.refresh_from_db()
        
        return Response({
            'rating': answer.net_rating, 
            'user_vote': target_vote, 
            'status': 'ok'
        })
        
class MarkCorrectAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, question_id, answer_id):
        is_approved = request.data.get("is_approved", "false").lower() == "true"
        
        question = get_object_or_404(Question, pk=question_id)
        answer = get_object_or_404(Answer, pk=answer_id, question_id=question_id)
        
        if question.author != request.user:
            return Response({'error': 'permission_denied'}, status=status.HTTP_403_FORBIDDEN)

        answer.set_is_approved(is_approved)
        
        return Response({
            'is_approved': answer.is_approved, 
            'status': 'ok'
        })