from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import VehicleMaster
from .serializers import VehicleMasterSerializer


class VehicleMasterViewSet(viewsets.ModelViewSet):
    queryset = VehicleMaster.objects.all()
    serializer_class = VehicleMasterSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'vehicle_type', 'ownership', 'fuel_type']
    search_fields   = ['vehicle_name', 'registration_number', 'owner_name', 'company_brand']
    ordering_fields = ['vehicle_name', 'created_at', 'current_odometer']
    ordering        = ['-created_at']