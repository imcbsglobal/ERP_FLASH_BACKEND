from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import TravelTrip
from .serializers import (
    TravelTripListSerializer,
    StartTripSerializer,
    EndTripSerializer,
)


# ── 1. List all trips + Create a new trip (Start Trip) ───────────────────────

class TravelTripListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/travel/trips/          → paginated trip list (Travel_Trip.jsx table)
    POST /api/travel/trips/          → start a new trip (StartTrip.jsx)

    Query params for filtering / searching:
      ?status=ongoing|completed
      ?search=<vehicle name / traveler / purpose>
      ?date=YYYY-MM-DD
      ?ordering=-date,-start_time
    """

    queryset = TravelTrip.objects.all()
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'date']
    search_fields   = ['vehicle_name', 'registration_number', 'traveled_by', 'purpose_of_trip']
    ordering_fields = ['date', 'start_time', 'distance_covered', 'fuel_cost']
    ordering        = ['-date', '-start_time']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StartTripSerializer
        return TravelTripListSerializer


# ── 2. Retrieve / Update / Delete a single trip ───────────────────────────────

class TravelTripDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/travel/trips/<id>/   → full trip detail
    PATCH  /api/travel/trips/<id>/   → generic field update (Edit button)
    DELETE /api/travel/trips/<id>/   → delete (Delete button)
    """

    queryset = TravelTrip.objects.all()
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return StartTripSerializer       # reuse start serializer for generic edits
        return TravelTripListSerializer

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


# ── 3. End Trip ───────────────────────────────────────────────────────────────

class EndTripView(generics.UpdateAPIView):
    """
    PATCH /api/travel/trips/<id>/end/

    Accepts EndTrip.jsx payload:
      end_time, odometer_end, fuel_cost, odometer_image (multipart file)

    Automatically computes distance_covered and sets status='completed'.
    """

    queryset = TravelTrip.objects.all()
    serializer_class = EndTripSerializer
    parser_classes   = [MultiPartParser, FormParser, JSONParser]
    http_method_names = ['patch']

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.status == 'completed':
            return Response(
                {'detail': 'This trip is already completed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


# ── 4. Ongoing trips shortcut ─────────────────────────────────────────────────

class OngoingTripsView(generics.ListAPIView):
    """
    GET /api/travel/trips/ongoing/

    Returns only trips that have not yet been ended.
    Useful for populating the 'End Trip' action in the table.
    """

    serializer_class = TravelTripListSerializer

    def get_queryset(self):
        return TravelTrip.objects.filter(status='ongoing').order_by('-date', '-start_time')