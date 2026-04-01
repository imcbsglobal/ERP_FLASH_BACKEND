# login/urls.py
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    ChangePasswordView,
    UserListView,
    UserDetailView,
    UserToggleStatusView,
)

urlpatterns = [
    # Auth endpoints
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="auth-change-password"),

    # User management endpoints - note: no /api/ prefix here
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("users/<int:pk>/toggle-status/", UserToggleStatusView.as_view(), name="user-toggle-status"),
]