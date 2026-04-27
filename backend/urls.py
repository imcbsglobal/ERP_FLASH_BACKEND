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
    path('api/',          include('user.urls')),
    path('api/',          include('usercontrol.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/',          include('vehiclemaster.urls')),

    # ── Vehicle Management / Travel Trips ──────────────────────────────────────
    # Mounted at api/travel/ so trips resolve to:
    #   GET/POST  /api/travel/trips/
    #   GET/PATCH /api/travel/trips/<id>/
    #   PATCH     /api/travel/trips/<id>/end/
    #   GET       /api/travel/trips/ongoing/
    path('api/travel/',   include('vehiclemanagement.urls')),

    path('api/challan/',  include('challan.urls')),
    path('api/claims/',   include('claims.urls')),
    path('image_capture/', include('imagecapture.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)