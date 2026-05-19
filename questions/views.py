from typing import Any

from django.shortcuts import get_object_or_404, redirect
from django.core.paginator import EmptyPage, Paginator, PageNotAnInteger
from django.views.generic import TemplateView, FormView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum

from core.forms import QuestionForm, AnswerForm
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

def set_questions_votes(request, page):
    if not request.user.is_authenticated:
        for q in page.object_list:
            q.user_vote = 0
        return
    obj_ids = [q.id for q in page.object_list]
    votes = dict(
        QuestionLike.objects.filter(user=request.user, question_id__in=obj_ids)
        .values_list('question_id', 'value')
    )
    for q in page.object_list:
        q.user_vote = votes.get(q.id, 0)
        
def set_answers_votes(request, page):
    if not request.user.is_authenticated:
        for a in page.object_list:
            a.user_vote = 0
        return
    ans_ids = [a.id for a in page.object_list]
    ans_votes = dict(
        AnswerLike.objects.filter(user=request.user, answer_id__in=ans_ids)
        .values_list('answer_id', 'value')
    )
    for a in page.object_list:
        a.user_vote = ans_votes.get(a.id, 0)

class IndexPageView(TemplateView):
    template_name = 'questions/index.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)     
        page = paginate(Question.objects.new(), self.request)
        set_questions_votes(request=self.request, page=page)
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
        set_questions_votes(request=self.request, page=page)
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
        set_questions_votes(request=self.request, page=page)
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
        answers_qs = question.answers.select_related("author").order_by("-created_at")
        page = paginate(answers_qs, self.request, per_page=10)
        
        if self.request.user.is_authenticated:
            q_vote = QuestionLike.objects.filter(user=self.request.user, question=question).values_list('value', flat=True).first()
            question.user_vote = q_vote or 0
        else:
            question.user_vote = 0
            
        set_answers_votes(request=self.request, page=page)
        
        context["question"] = question
        context["answers"] = page
        context["page"] = page
        context.update(get_sidebar_context())
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

@login_required
@require_POST
def like_question(request):
    q_id = request.POST.get('question_id')
    action = request.POST.get('action')
    if action not in ('like', 'dislike'):
        return JsonResponse({'error': 'invalid_action'}, status=400)
    question = get_object_or_404(Question, pk=q_id)
    reaction_value = 1 if action == 'like' else -1
    like_obj = QuestionLike.objects.filter(user=request.user, question=question).first()
    if like_obj:
        if like_obj.value == reaction_value:
            like_obj.delete()
        else:
            like_obj.value = reaction_value
            like_obj.save()
    else:
        QuestionLike.objects.create(user=request.user, question=question, value=reaction_value)
    rating = question.question_likes.aggregate(total=Sum('value'))['total'] or 0
    current_like = QuestionLike.objects.filter(user=request.user, question=question).first()
    user_vote = current_like.value if current_like else 0
    return JsonResponse({'rating': rating, 'user_vote': user_vote, 'status': 'ok'})

@login_required
@require_POST
def like_answer(request):
    a_id = request.POST.get('answer_id')
    action = request.POST.get('action')
    if action not in ('like', 'dislike'):
        return JsonResponse({'error': 'invalid_action'}, status=400)
    answer = get_object_or_404(Answer, pk=a_id)
    reaction_value = 1 if action == 'like' else -1
    like_obj = AnswerLike.objects.filter(user=request.user, answer=answer).first()
    if like_obj:
        if like_obj.value == reaction_value:
            like_obj.delete()
        else:
            like_obj.value = reaction_value
            like_obj.save()
    else:
        AnswerLike.objects.create(user=request.user, answer=answer, value=reaction_value)
    rating = answer.answer_likes.aggregate(total=Sum('value'))['total'] or 0
    current_like = AnswerLike.objects.filter(user=request.user, answer=answer).first()
    user_vote = current_like.value if current_like else 0
    return JsonResponse({'rating': rating, 'user_vote': user_vote, 'status': 'ok'})

@login_required
@require_POST
def mark_correct_answer(request):
    q_id = request.POST.get('question_id')
    a_id = request.POST.get('answer_id')
    question = get_object_or_404(Question, pk=q_id)
    answer = get_object_or_404(Answer, pk=a_id, question=question)
    if question.author != request.user:
        return JsonResponse({'error': 'permission_denied'}, status=403)
    answer.is_approved = not answer.is_approved
    answer.save()
    return JsonResponse({'is_approved': answer.is_approved, 'status': 'ok'}) 