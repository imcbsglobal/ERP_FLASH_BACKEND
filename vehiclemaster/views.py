from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import VehicleMaster
from .serializers import VehicleMasterSerializer


class VehicleMasterViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleMasterSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'vehicle_type', 'ownership', 'fuel_type']
    search_fields   = ['vehicle_name', 'registration_number', 'owner_name', 'company_brand']
    ordering_fields = ['vehicle_name', 'created_at', 'current_odometer']
    ordering        = ['-created_at']

    def get_queryset(self):
        qs = VehicleMaster.objects.all()
        # exclude_ongoing=true → hide vehicles that have an ongoing trip
        if self.request.query_params.get('exclude_ongoing') == 'true':
            try:
                from vehiclemanagement.models import TravelTrip
                busy_regs = TravelTrip.objects.filter(
                    status='ongoing'
                ).values_list('registration_number', flat=True)
                qs = qs.exclude(registration_number__in=busy_regs)
            except Exception:
                pass
        return qs