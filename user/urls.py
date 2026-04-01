from django.urls import path
from .views import (
    BranchListCreateView,
    BranchDetailView,
    UserListCreateView,
    UserDetailView,
    UserToggleStatusView,
    LoginView,
)

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────
    path("auth/login/", LoginView.as_view(), name="auth-login"),

    # ── Branches ──────────────────────────────────────────────
    path("branches/",        BranchListCreateView.as_view(), name="branch-list-create"),
    path("branches/<int:pk>/", BranchDetailView.as_view(),  name="branch-detail"),

    # ── Users ─────────────────────────────────────────────────
    path("users/",           UserListCreateView.as_view(),  name="user-list-create"),
    path("users/<int:pk>/",  UserDetailView.as_view(),      name="user-detail"),
    path("users/<int:pk>/toggle-status/", UserToggleStatusView.as_view(), name="user-toggle-status"),
]