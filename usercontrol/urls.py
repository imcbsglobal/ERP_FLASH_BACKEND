from django.urls import path
from .views import (
    BulkMenuPermissionView,
    UserPermissionsView,
    LoginUserListView,
)

urlpatterns = [
    # GET  /api/users/login-users/       → all login.User rows + permissions
    path("users/login-users/",          LoginUserListView.as_view(),      name="login-user-list"),

    # PATCH /api/users/permissions/bulk/ → save many users' permissions at once
    path("users/permissions/bulk/",     BulkMenuPermissionView.as_view(), name="bulk-menu-permissions"),

    # GET / PATCH /api/users/<pk>/permissions/ → single user permissions
    path("users/<int:pk>/permissions/", UserPermissionsView.as_view(),    name="user-permissions"),
]