from typing import Any

from django.shortcuts import get_object_or_404
from django.core.paginator import EmptyPage, Paginator, PageNotAnInteger
from django.views.generic import TemplateView

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
        answers_qs = question.answers.select_related("author").order_by("-created_at")
        
        page = paginate(answers_qs, self.request, per_page=10)
        context["question"] = question
        context["answers"] = page
        context["page"] = page
        context.update(get_sidebar_context())
        return context

class AskPageView(TemplateView):
    template_name = 'questions/ask.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(get_sidebar_context())
        return context
