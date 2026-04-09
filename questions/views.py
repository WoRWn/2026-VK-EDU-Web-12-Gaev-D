from typing import Any


from django.shortcuts import render
from django.core.paginator import EmptyPage, Paginator, PageNotAnInteger
from django.views.generic import TemplateView

answers = [
    {
        'user_id': i,
        'username': f'user_{i}',
        'user_avatar': None,
        'text': f'text_{i}',
        'votes': i,
        'approved': False,
        'post_time': f'{i} минут {i} секунд'
    } for i in range(1, 21)
]

questions = [
    {
        'id': i,
        'title': f'title_{i}',
        'text': f'text_{i}',
        'user_id': i,
        'username': f'user{i}',
        'user_avatar': None,
        'tags': [ { 'name': f'tag_{i}', 'color': f'#{i}a6fa5' } for i in range(1, 7) ],
        'votes': i,
        'answers': answers,
        'answers_cnt': len(answers),
        'post_time': f'{i} минут {i} секунд'
    } for i in range(0, 20)
]

best_members = [
    {
       'id' : i,
       'username': f'user_{i}',
       'avatar_url': None
    } for i in range(1, 6)
]

popular_tags = [
    {
        'name': f'tag_{i}', 
        'color': f'#{i}a6fa5'
    } for i in range(1, 6)
]

def paginate(objects_list, request, per_page=15):
    page_num = request.GET.get('page', 1)
    paginator = Paginator(objects_list, per_page)
    try:
        page = paginator.get_page(page_num)
    except PageNotAnInteger or EmptyPage:
        page = paginator.get_page(1)
    return page

class IndexPageView(TemplateView):
    template_name = 'questions/index.html'
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        page = paginate(questions, self.request)
        context["page"] = page
        context["questions"] = page.object_list
        context["best_members"] = best_members
        context["popular_tags"] = popular_tags
        return context

class TagPageView(TemplateView):
    template_name = 'questions/tag.html'
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        tag_name = self.kwargs.get('tag_name', '') 
        filtered_questions = [
            q for q in questions if any(t['name'] == tag_name for t in q.get('tags', []))
        ]
        
        page = paginate(filtered_questions, self.request)
        context["page"] = page
        context["questions"] = filtered_questions
        context["tag_name"] = tag_name
        
        context["best_members"] = best_members
        context["popular_tags"] = popular_tags
        return context

class HotPageView(TemplateView):
    template_name = 'questions/hot.html'
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        page = paginate(questions, self.request)
        context["page"] = page
        context["questions"] = page.object_list
        context["best_members"] = best_members
        context["popular_tags"] = popular_tags
        return context
    
class QuestionPageView(TemplateView):
    template_name = 'questions/question.html'
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        question_id = kwargs["question_id"]
        try:
            question_id = int(question_id)
        except ValueError:
            question_id = 1
        context["question"] = questions[question_id]
        context["best_members"] = best_members
        context["popular_tags"] = popular_tags
        return context

class AskPageView(TemplateView):
    template_name = 'questions/ask.html'
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["best_members"] = best_members
        context["popular_tags"] = popular_tags
        return context
