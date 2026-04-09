from typing import Any

from django.shortcuts import render
from django.views.generic import TemplateView

best_members = [
    {
       'user_id' : i,
       'username': f'user_{i}',
       'user_avatar': None
    } for i in range(1, 6)
]

popular_tags = [
    {
        'name': f'tag_{i}', 
        'color': '#4a6fa5'
    } for i in range(1, 6)
]

class LoginPageView(TemplateView):
    template_name = 'core/login.html'
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["best_members"] = best_members
        context["popular_tags"] = popular_tags
        return context
        
class SignUpPageView(TemplateView):
    template_name = 'core/signup.html'
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["best_members"] = best_members
        context["popular_tags"] = popular_tags
        return context
        
class ProfilePageView(TemplateView):
    template_name = 'core/profile.html'
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["best_members"] = best_members
        context["popular_tags"] = popular_tags
        return context
