from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Claim
from .serializers import (
    ClaimSerializer,
    ClaimListSerializer,
    ClaimStatusUpdateSerializer,
)


class ClaimListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/claims/          → paginated list of all claims
    POST /api/claims/          → create a new claim (multipart for file upload)
    """

    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # ?search=  searches these fields (mirrors frontend search behaviour)
    search_fields  = ["client_name", "claimed_by__first_name", "claimed_by__last_name",
                      "department", "expense_type"]
    filterset_fields = ["status", "department", "expense_type"]
    ordering_fields  = ["created_at", "amount"]
    ordering         = ["-created_at"]

    def get_queryset(self):
        return Claim.objects.select_related("claimed_by").all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ClaimListSerializer
        return ClaimSerializer

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            print(f"Error creating claim: {str(e)}")
            return Response(
                {"detail": f"Error creating claim: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


class ClaimRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/claims/{id}/   → full claim detail
    PUT    /api/claims/{id}/   → full update
    PATCH  /api/claims/{id}/   → partial update
    DELETE /api/claims/{id}/   → delete
    """

    queryset           = Claim.objects.select_related("claimed_by").all()
    serializer_class   = ClaimSerializer
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Remove the receipt file from storage before deleting the record
        if instance.receipt:
            instance.receipt.delete(save=False)
        self.perform_destroy(instance)
        return Response(
            {"detail": "Claim deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )


class ClaimStatusUpdateView(APIView):
    """
    PATCH /api/claims/{id}/status/
    Body: { "status": "Approved" | "Pending" | "Rejected" }
    Updates only the status field (mirrors the inline dropdown in the list table).
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            claim = Claim.objects.get(pk=pk)
        except Claim.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ClaimStatusUpdateSerializer(claim, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClaimDraftCreateView(generics.CreateAPIView):
    """
    POST /api/claims/draft/
    Creates a claim with status="Draft".
    Only expense_type and department are required (mirrors frontend draft validation).
    """

    serializer_class   = ClaimSerializer
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        serializer.save(status="Draft", claimed_by=self.request.user)