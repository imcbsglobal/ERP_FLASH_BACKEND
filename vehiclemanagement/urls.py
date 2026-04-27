from django.urls import path
from .views import (
    TravelTripListCreateView,
    TravelTripDetailView,
    EndTripView,
    OngoingTripsView,
)

app_name = 'travel'

urlpatterns = [
    # ── Trip collection ───────────────────────────────────────────────────────
    # GET  → trip list  (Travel_Trip.jsx)
    # POST → start trip (StartTrip.jsx)
    # Full URL: /api/travel/trips/
    path(
        'trips/',
        TravelTripListCreateView.as_view(),
        name='trip-list-create',
    ),

    # ── Ongoing trips ─────────────────────────────────────────────────────────
    # MUST be BEFORE trips/<int:pk>/ — Django matches top-to-bottom.
    # Without this ordering, "ongoing" is cast to int → 404.
    # Full URL: /api/travel/trips/ongoing/
    path(
        'trips/ongoing/',
        OngoingTripsView.as_view(),
        name='trip-ongoing',
    ),

    # ── Single trip ───────────────────────────────────────────────────────────
    # GET    → detail
    # PATCH  → edit
    # DELETE → delete
    # Full URL: /api/travel/trips/<id>/
    path(
        'trips/<int:pk>/',
        TravelTripDetailView.as_view(),
        name='trip-detail',
    ),

    # ── End trip ──────────────────────────────────────────────────────────────
    # PATCH → end an ongoing trip (EndTrip.jsx)
    # Full URL: /api/travel/trips/<id>/end/
    path(
        'trips/<int:pk>/end/',
        EndTripView.as_view(),
        name='trip-end',
    ),
]