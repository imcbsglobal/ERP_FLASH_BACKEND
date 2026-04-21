from django.db.models              import Sum, Count, Q
from rest_framework                 import status
from rest_framework.generics        import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers         import MultiPartParser, FormParser, JSONParser
from rest_framework.response        import Response
from rest_framework.views           import APIView
from django_filters.rest_framework  import DjangoFilterBackend
from rest_framework.filters         import SearchFilter, OrderingFilter
import requests

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
        # Automatically record which user created this payment
        serializer.save(created_by=request.user if request.user.is_authenticated else None)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        qs = super().get_queryset()
        # ?my_payments=true  →  return only the authenticated user's payments
        if self.request.query_params.get('my_payments') == 'true':
            if self.request.user.is_authenticated:
                qs = qs.filter(created_by=self.request.user)
        return qs


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
            completed_count = Count('id', filter=Q(status='Completed')),
            pending_count   = Count('id', filter=Q(status='Pending')),
            failed_count    = Count('id', filter=Q(status='Failed')),
        )
        data['total_amount'] = data['total_amount'] or 0
        return Response(data)


class FlashERPDebtorsProxyView(APIView):
    """
    GET /api/payments/flasherp/debtors/
    Proxies the FlashERP debtor list server-side so the browser
    never hits flasherp.imcbs.com directly (avoids CORS).

    Pagination: pass ?next=<url> to fetch subsequent pages.
    The frontend can also pass ?page=N if FlashERP supports it.
    """

    FLASHERP_DEBTORS_URL = 'https://flasherp.imcbs.com/api/debtors/'

    def get(self, request):
        # Allow the frontend to request a specific page URL (for pagination)
        target_url = request.query_params.get('next') or self.FLASHERP_DEBTORS_URL

        # Forward all other query params (e.g. ?page=2) except 'next'
        params = {k: v for k, v in request.query_params.items() if k != 'next'}

        # Use the FlashERP token forwarded from the frontend,
        # or fall back to a server-side env setting if available.
        flasherp_token = request.headers.get('X-Flasherp-Token')
        headers = {'Accept': 'application/json'}
        if flasherp_token:
            headers['Authorization'] = f'Token {flasherp_token}'

        try:
            resp = requests.get(target_url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            return Response(resp.json(), status=resp.status_code)

        except requests.exceptions.ConnectionError:
            return Response(
                {'detail': 'Cannot reach FlashERP server. Check your internet connection.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except requests.exceptions.Timeout:
            return Response(
                {'detail': 'FlashERP server timed out. Please try again.'},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except requests.exceptions.HTTPError:
            return Response(
                {'detail': f'FlashERP returned an error: {resp.status_code}'},
                status=resp.status_code,
            )


class FlashERPDepartmentsProxyView(APIView):
    """
    GET /api/payments/flasherp/departments/
    Proxies the FlashERP departments list server-side.
    """

    FLASHERP_DEPARTMENTS_URL = 'https://flasherp.imcbs.com/api/departments/'

    def get(self, request):
        target_url = self.FLASHERP_DEPARTMENTS_URL
        
        flasherp_token = request.headers.get('X-Flasherp-Token')
        headers = {'Accept': 'application/json'}
        if flasherp_token:
            headers['Authorization'] = f'Token {flasherp_token}'

        try:
            resp = requests.get(target_url, headers=headers, timeout=15)
            resp.raise_for_status()
            return Response(resp.json(), status=resp.status_code)
            
        except requests.exceptions.ConnectionError:
            return Response(
                {'detail': 'Cannot reach FlashERP server. Check your internet connection.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except requests.exceptions.Timeout:
            return Response(
                {'detail': 'FlashERP server timed out. Please try again.'},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except requests.exceptions.HTTPError:
            return Response(
                {'detail': f'FlashERP returned an error: {resp.status_code}'},
                status=resp.status_code,
            )