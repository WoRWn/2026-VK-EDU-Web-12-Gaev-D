from typing import Any

from django.http import HttpResponse
from django.views.generic import FormView
from django.contrib.auth.views import LogoutView
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth.mixins import UserPassesTestMixin

from django.db.models import Count
from questions.models import Tag, User

from .forms import LoginForm, SignUpForm, ProfileForm

def get_sidebar_context() -> dict[str, Any]:
    popular_tags = Tag.objects.annotate(q_count=Count("questions")).order_by("-q_count")[:5]
    best_members = User.objects.annotate(q_count=Count("questions")).select_related("profile").order_by("-q_count")[:5]
    return { 'best_members': best_members, 'popular_tags': popular_tags }

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
    