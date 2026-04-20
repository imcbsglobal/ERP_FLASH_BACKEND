from django.urls import path
from .views import (
    ClaimListCreateView,
    ClaimRetrieveUpdateDestroyView,
    ClaimStatusUpdateView,
    ClaimDraftCreateView,
)

app_name = "claims"

urlpatterns = [
    # List all claims / Create new claim
    path("", ClaimListCreateView.as_view(), name="claim-list-create"),

    # Save as draft (only expense_type + department required)
    path("draft/", ClaimDraftCreateView.as_view(), name="claim-draft"),

    # Retrieve / Update / Delete a single claim
    path("<int:pk>/", ClaimRetrieveUpdateDestroyView.as_view(), name="claim-detail"),

    # Update only the status field (used by the inline status dropdown)
    path("<int:pk>/status/", ClaimStatusUpdateView.as_view(), name="claim-status"),
]