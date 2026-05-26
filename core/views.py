from typing import Any

from django.http import HttpResponse
from django.views.generic import FormView
from django.contrib.auth.views import LogoutView
from django.contrib.auth import login
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.cache import cache
from django.db.models import Count, Sum, F, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from django.db.models import Count
from questions.models import Tag

from .forms import LoginForm, SignUpForm, ProfileForm

User = get_user_model()

def get_sidebar_context() -> dict[str, Any]:
    popular_tags = get_cached_popular_tags()
    best_members = get_cached_best_members()
    return { 'best_members': best_members, 'popular_tags': popular_tags }

def get_cached_popular_tags():
    data = cache.get('popular_tags')
    if data is not None:
        return data
    
    threshold = timezone.now() - timedelta(days=90)
    tags = Tag.objects.filter(
        questions__created_at__gte=threshold
    ).annotate(
        count=Count('questions', distinct=True)
    ).order_by('-count')[:10]
    
    data = [{'name': t.name, 'count': t.count, 'color': t.color} for t in tags]
    cache.set('popular_tags', data, timeout=900)
    return data

def get_cached_best_members():
    data = cache.get('best_members')
    if data is not None:
        return data
        
    threshold = timezone.now() - timedelta(days=7)
    users = User.objects.annotate(
        q_likes=Sum('questions__question_likes__value', filter=Q(questions__created_at__gte=threshold)),
        a_likes=Sum('answers__answer_likes__value', filter=Q(answers__created_at__gte=threshold))
    ).annotate(
        total=F('q_likes') + F('a_likes')
    ).filter(total__gt=0).order_by('-total')[:10]
    
    data = [
        {'username': u.username, 'nickname': getattr(u.profile, 'nickname', u.username), 'score': u.total or 0}
        for u in users
    ]
    cache.set('best_members', data, timeout=900)
    return data

class AnonymousRequiredMixin(UserPassesTestMixin):
    redirect_url = 'index'

    def test_func(self):
        return not self.request.user.is_authenticated

    def handle_no_permission(self):
        return redirect(self.redirect_url)

class LoginPageView(AnonymousRequiredMixin, FormView):
    template_name = 'core/login.html'
    form_class = LoginForm
    success_url = reverse_lazy("index")
    redirect_url = 'index'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(get_sidebar_context())
        return context
    
    def form_valid(self, form: Any) -> HttpResponse:
        login(self.request, form.cleaned_data["user"])
        
        next_url = self.request.GET.get("next", "/")
        if url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={self.request.get_host()}):
            return redirect(next_url)
        return super().form_valid(form)
        
class SignUpPageView(AnonymousRequiredMixin, FormView):
    template_name = 'core/signup.html'
    form_class = SignUpForm
    success_url = reverse_lazy("index")
    redirect_url = 'index'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(get_sidebar_context())
        return context
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)
    

class ProfilePageView(FormView):
    template_name = 'core/profile.html'
    form_class = ProfileForm
    success_url = reverse_lazy("index")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(get_sidebar_context())
        return context
    
    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    
class LogoutPageView(LogoutView):    
    next_page = reverse_lazy('index')
    