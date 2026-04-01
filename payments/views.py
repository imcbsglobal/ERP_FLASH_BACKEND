from django.db.models              import Sum, Count, Q   # ← fixed: Q imported here
from rest_framework                 import status
from rest_framework.generics        import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers         import MultiPartParser, FormParser, JSONParser
from rest_framework.response        import Response
from rest_framework.views           import APIView
from django_filters.rest_framework  import DjangoFilterBackend
from rest_framework.filters         import SearchFilter, OrderingFilter

from .models       import Payment
from .serializers  import PaymentSerializer, PaymentStatusUpdateSerializer


class PaymentListCreateView(ListCreateAPIView):
    """
    GET  /api/payments/         → list all payments (with search & filter)
    POST /api/payments/         → create a new payment (supports file upload)
    """

    queryset         = Payment.objects.all()
    serializer_class = PaymentSerializer
    parser_classes   = [MultiPartParser, FormParser, JSONParser]

    # ── Filtering / search / ordering ─────────────────────────────
    filter_backends  = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['collection_type', 'status', 'branch', 'date']
    search_fields    = ['client_name', 'branch', 'paid_for']
    ordering_fields  = ['date', 'amount', 'created_at']
    ordering         = ['-created_at']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PaymentDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET    /api/payments/<id>/  → retrieve single payment
    PUT    /api/payments/<id>/  → full update
    PATCH  /api/payments/<id>/  → partial update (e.g. status only)
    DELETE /api/payments/<id>/  → delete payment
    """

    queryset         = Payment.objects.all()
    serializer_class = PaymentSerializer
    parser_classes   = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_context(self):
        return {'request': self.request}

    def update(self, request, *args, **kwargs):
        partial    = kwargs.pop('partial', False)
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.payment_proof:
            instance.payment_proof.delete(save=False)
        instance.delete()
        return Response(
            {"detail": "Payment deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )


class PaymentStatusUpdateView(APIView):
    """
    PATCH /api/payments/<id>/status/  → update only the status field
    Body: { "status": "Completed" | "Pending" | "Failed" }
    """

    def patch(self, request, pk):
        try:
            payment = Payment.objects.get(pk=pk)
        except Payment.DoesNotExist:
            return Response({"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PaymentStatusUpdateSerializer(payment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            PaymentSerializer(payment, context={'request': request}).data
        )


class PaymentSummaryView(APIView):
    """
    GET /api/payments/summary/
    Returns aggregate stats shown in the frontend summary bar.
    """

    def get(self, request):
        qs   = Payment.objects.all()
        data = qs.aggregate(
            total_amount    = Sum('amount'),
            total_count     = Count('id'),
            completed_count = Count('id', filter=Q(status='Completed')),   # ← was models.Q (wrong)
            pending_count   = Count('id', filter=Q(status='Pending')),
            failed_count    = Count('id', filter=Q(status='Failed')),
        )
        data['total_amount'] = data['total_amount'] or 0
        return Response(data)