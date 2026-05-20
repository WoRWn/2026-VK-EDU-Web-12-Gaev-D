from typing import Any

from django.db.models import Count
from django.views.generic import TemplateView

from questions.models import Tag, User


def get_sidebar_context() -> dict[str, Any]:
    popular_tags = Tag.objects.annotate(q_count=Count("questions")).order_by("-q_count")[:5]
    best_members = User.objects.annotate(q_count=Count("questions")).select_related("profile").order_by("-q_count")[:5]
    return { 'best_members': best_members, 'popular_tags': popular_tags }


class LoginPageView(TemplateView):
    template_name = 'core/login.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(get_sidebar_context())
        return context
        
class SignUpPageView(TemplateView):
    template_name = 'core/signup.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(get_sidebar_context())
        return context

class ProfilePageView(TemplateView):
    template_name = 'core/profile.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(get_sidebar_context())
        return context
