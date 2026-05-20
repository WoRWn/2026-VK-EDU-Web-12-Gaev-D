from typing import Any

from django.shortcuts import get_object_or_404, redirect
from django.core.paginator import EmptyPage, Paginator, PageNotAnInteger
from django.views.generic import TemplateView, FormView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import Question
from questions.forms import QuestionForm, AnswerForm

from core.views import get_sidebar_context
from questions.models import Question, Tag

def paginate(queryset, request, per_page=15):
    page_num = request.GET.get('page', 1)
    paginator = Paginator(queryset, per_page)
    
    try:
        page = paginator.get_page(page_num)
    except (PageNotAnInteger, EmptyPage):
        page = paginator.get_page(1)
    return page

class IndexPageView(TemplateView):
    template_name = 'questions/index.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)     
        page = paginate(Question.objects.new(), self.request)
        context['questions'] = page
        context['page'] = page
        context.update(get_sidebar_context())
        return context

class TagPageView(TemplateView):
    template_name = 'questions/tag.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        tag_name = self.kwargs['tag_name']

        get_object_or_404(Tag, name=tag_name)
        
        page = paginate(Question.objects.by_tag(tag_name), self.request)
        context["questions"] = page
        context["page"] = page
        context["tag_name"] = tag_name
        context.update(get_sidebar_context())
        return context

class HotPageView(TemplateView):
    template_name = 'questions/hot.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        page = paginate(Question.objects.hot(), self.request)
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
        answers_qs = question.answers.select_related("author", "author__profile").order_by("-created_at")
        
        page = paginate(answers_qs, self.request, per_page=10)
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

    
