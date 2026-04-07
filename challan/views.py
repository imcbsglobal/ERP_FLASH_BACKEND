from django.db.models import Sum, Count, Q
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
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

    queryset         = Challan.objects.select_related("vehicle").all()
    serializer_class = ChallanSerializer
    parser_classes   = [MultiPartParser, FormParser, JSONParser]

    # ── filtering / search / ordering ────────────────────────────────────────
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["payment_status", "offence_type", "vehicle"]
    search_fields    = ["challan_no", "location", "offence_type", "vehicle__registration_number"]
    ordering_fields  = ["challan_date", "fine_amount", "created_at", "payment_status"]
    ordering         = ["-created_at"]

    # ── extra action ──────────────────────────────────────────────────────────

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Returns aggregate summary used by the list page's stat cards.
        Supports the same ?payment_status= / ?vehicle= filters.
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