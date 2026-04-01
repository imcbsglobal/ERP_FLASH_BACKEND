from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView

from login.views import (
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    ChangePasswordView,
    # UserListView removed — /api/users/ is now fully handled by user.urls
    # via UserViewSet (which queries the same AUTH_USER_MODEL: usercontrol.CustomUser)
)

auth_urlpatterns = [
    path('login/',           LoginView.as_view(),          name='auth-login'),
    path('logout/',          LogoutView.as_view(),          name='auth-logout'),
    path('token/refresh/',   TokenRefreshView.as_view(),    name='token-refresh'),
    path('me/',              MeView.as_view(),              name='auth-me'),
    path('register/',        RegisterView.as_view(),        name='auth-register'),
    path('change-password/', ChangePasswordView.as_view(),  name='auth-change-password'),
]

urlpatterns = [
    path('admin/',        admin.site.urls),
    path('api/auth/',     include(auth_urlpatterns)),

    # ── Users, Branches, Permissions ──────────────────────────────────────────
    # user.urls registers (in this order, so bulk isn't swallowed by the router):
    #   PATCH  /api/users/permissions/bulk/     ← BulkMenuPermissionView
    #   GET    /api/users/                      ← UserViewSet.list
    #   POST   /api/users/                      ← UserViewSet.create
    #   GET    /api/users/me/                   ← UserViewSet.me  (logged-in user)
    #   GET    /api/users/{id}/                 ← UserViewSet.retrieve
    #   PATCH  /api/users/{id}/                 ← UserViewSet.partial_update
    #   DELETE /api/users/{id}/                 ← UserViewSet.destroy
    #   GET    /api/users/{id}/permissions/     ← UserViewSet.permissions_action
    #   PATCH  /api/users/{id}/permissions/     ← UserViewSet.permissions_action
    #   *      /api/branches/                   ← BranchViewSet (full CRUD)
    path('api/',          include('user.urls')),
    path('api/',          include('usercontrol.urls')),
    path('api/payments/', include('payments.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)