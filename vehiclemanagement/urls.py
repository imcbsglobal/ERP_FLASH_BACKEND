from django.urls import path
from .views import (
    TravelTripListCreateView,
    TravelTripDetailView,
    EndTripView,
    OngoingTripsView,
)

app_name = 'travel'

urlpatterns = [
    # ── Trip collection ──────────────────────────────────────────
    # GET  → trip table (Travel_Trip.jsx)
    # POST → start a new trip (StartTrip.jsx)
    path(
        'trips/',
        TravelTripListCreateView.as_view(),
        name='trip-list-create',
    ),

    # ── Single trip ───────────────────────────────────────────────
    # GET    → trip detail
    # PATCH  → edit trip fields (Edit button)
    # DELETE → delete trip (Delete button)
    path(
        'trips/<int:pk>/',
        TravelTripDetailView.as_view(),
        name='trip-detail',
    ),

    # ── End trip ──────────────────────────────────────────────────
    # PATCH → end an ongoing trip (EndTrip.jsx)
    path(
        'trips/<int:pk>/end/',
        EndTripView.as_view(),
        name='trip-end',
    ),

    # ── Ongoing trips shortcut ────────────────────────────────────
    # GET → list only ongoing trips
    path(
        'trips/ongoing/',
        OngoingTripsView.as_view(),
        name='trip-ongoing',
    ),
]


