from django.urls import path
from core.views import LoginPageView, SignUpPageView, ProfilePageView

urlpatterns = [
    path('login/', LoginPageView.as_view(), name='login'),
    path('signup/', SignUpPageView.as_view(), name='signup'),
    path('profile/', ProfilePageView.as_view(), name='profile')
]
