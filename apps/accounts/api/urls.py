from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.api.views import (
    CurrentUserAPIView,
    LoginAPIView,
    UserRegistrationAPIView,
)

urlpatterns = [
    path("register/", UserRegistrationAPIView.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("me/", CurrentUserAPIView.as_view(), name="current-user"),
]
