from django.db.models import Sum, Count, Q
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Challan
from .serializers import ChallanSerializer


class ChallanViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints for Traffic Challans.

    list    : GET    /api/challan/challans/
    create  : POST   /api/challan/challans/   (multipart/form-data for file uploads)
    retrieve: GET    /api/challan/challans/<id>/
    update  : PUT    /api/challan/challans/<id>/
    partial : PATCH  /api/challan/challans/<id>/
    destroy : DELETE /api/challan/challans/<id>/

    Extra:
    summary : GET    /api/challan/challans/summary/  → counts + totals
    """

    serializer_class = ChallanSerializer
    parser_classes   = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [IsAuthenticated]

    # ── filtering / search / ordering ────────────────────────────────────────
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["payment_status", "offence_type", "vehicle"]
    search_fields    = ["challan_no", "location", "offence_type", "vehicle__registration_number"]
    ordering_fields  = ["challan_date", "fine_amount", "created_at", "payment_status"]
    ordering         = ["-created_at"]

    def get_queryset(self):
        """
        Admins see all challans.
        Non-admin users (Manager / User) see only their own challans.
        Role is read from the custom login.User model stored in the JWT.
        """
        user = self.request.user
        qs = Challan.objects.select_related("vehicle", "created_by").all()

        # Determine role — custom login.User stores role as a plain CharField
        role = getattr(user, "role", None)

        if role == "Admin":
            return qs  # Admins see everything

        # Non-admins: only their own challans
        return qs.filter(created_by=user)

    def perform_create(self, serializer):
        """Auto-assign created_by to the logged-in user on create."""
        serializer.save(created_by=self.request.user)

    # ── extra action ──────────────────────────────────────────────────────────

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Returns aggregate summary used by the list page's stat cards.
        Respects the same queryset scoping (admin vs user).
        """
        qs = self.filter_queryset(self.get_queryset())

        agg = qs.aggregate(
            total_challans=Count("id"),
            total_fine=Sum("fine_amount"),
            paid_count=Count("id", filter=Q(payment_status="Paid")),
            pending_count=Count("id", filter=Q(payment_status="Pending")),
            waived_count=Count("id", filter=Q(payment_status="Waived")),
        )
        return Response(agg, status=status.HTTP_200_OK)