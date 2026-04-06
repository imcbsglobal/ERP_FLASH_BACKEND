# vehiclemaster/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VehicleMasterViewSet

router = DefaultRouter()
router.register(r'vehicles', VehicleMasterViewSet, basename='vehicle')

urlpatterns = [
    path('', include(router.urls)),
]