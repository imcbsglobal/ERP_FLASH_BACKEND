from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import TravelTrip
from .serializers import (
    TravelTripListSerializer,
    StartTripSerializer,
    EndTripSerializer,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_auth_user(request):
    """
    Decode the JWT from the Authorization header, then look up the user
    record in login.User to get their CURRENT role and status.

    Returns {'username': str, 'role': str, 'status': str} or None.
    """
    # ── Step 1: decode the token ──────────────────────────────────────────
    decoded = getattr(request, "auth", None)   # set by JWTAuthentication

    if decoded is None:
        # Manual decode from the Authorization: Bearer <token> header
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None
        raw = auth_header.split(" ", 1)[1].strip()
        if not raw:
            return None
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            decoded = AccessToken(raw)
        except Exception:
            return None   # expired / invalid token

    # ── Step 2: get user_id from the token ───────────────────────────────
    user_id = decoded.get("user_id") or decoded.get("id")
    if not user_id:
        return None

    # ── Step 3: fetch CURRENT role directly from the database ────────────
    # Never trust the role claim in the token — it is stamped at login and
    # can be stale if the user's role was changed after they logged in.
    # A broad except was previously silently swallowing DB/import errors and
    # falling back to role="User", which made every admin look like a User.
    from login.models import User as LoginUser
    try:
        db_user = LoginUser.objects.get(pk=user_id)
    except LoginUser.DoesNotExist:
        return None   # token references a deleted user — treat as unauthenticated

    return {
        "username": db_user.username,
        "role":     db_user.role,     # "Admin" / "Manager" / "User" — always fresh
        "status":   db_user.status,   # "Active" / "Inactive"
    }


def _require_auth(request):
    """
    Return a 401 Response if no valid JWT is present or user is inactive.
    Returns None if the request is authenticated and the user is active.
    """
    auth = _get_auth_user(request)
    if auth is None:
        return Response(
            {"detail": "Authentication credentials were not provided or are invalid."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if auth.get("status", "Active") == "Inactive":
        return Response(
            {"detail": "Your account is inactive."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


def _role_filtered_qs(request, base_qs):
    """
    Apply role-based visibility rules to *base_qs*:
      • Admin / Manager  → see ALL trips
      • User             → see ONLY their own trips (traveled_by = username)

    Role comparison is case-insensitive so "admin", "Admin", "ADMIN" all work.
    If the token is missing/invalid the queryset is empty — callers should have
    already called _require_auth() and returned 401 before reaching here.
    """
    auth = _get_auth_user(request)
    if auth is None:
        return base_qs.none()

    uid  = auth.get("username", "")
    role = auth.get("role", "User").strip().lower()   # normalise for comparison

    # Admin and Manager see everything
    if role in ("admin", "manager"):
        return base_qs

    # Regular user — guard against empty uid leaking all rows
    if not uid:
        return base_qs.none()

    return base_qs.filter(traveled_by__iexact=uid)


# ── 1. List all trips + Create a new trip (Start Trip) ───────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class TravelTripListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/travel/trips/   → paginated trip list (Travel_Trip.jsx table)
    POST /api/travel/trips/   → start a new trip   (StartTrip.jsx)

    Visibility rules:
      • Admin / Manager → all trips
      • User (driver)   → only trips where traveled_by matches their JWT username
      • No token        → 401
    """

    authentication_classes = []
    permission_classes     = [AllowAny]
    parser_classes         = [MultiPartParser, FormParser, JSONParser]
    filter_backends        = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields       = ['status', 'date']
    search_fields          = ['vehicle_name', 'registration_number', 'traveled_by', 'purpose_of_trip']
    ordering_fields        = ['date', 'start_time', 'distance_covered', 'fuel_cost']
    ordering               = ['-date', '-start_time']

    def get_queryset(self):
        return _role_filtered_qs(request=self.request, base_qs=TravelTrip.objects.all())

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StartTripSerializer
        return TravelTripListSerializer

    def list(self, request, *args, **kwargs):
        # Reject unauthenticated requests before touching the DB
        err = _require_auth(request)
        if err:
            return err
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        err = _require_auth(request)
        if err:
            return err
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Stamp traveled_by from the JWT so it always matches the filter key.
        We have already verified the token is present in create(), so
        _get_auth_user() will not return None here.
        """
        auth = _get_auth_user(self.request)
        uid  = auth.get("username", "") if auth else ""
        if uid:
            serializer.save(traveled_by=uid)
        else:
            serializer.save()


# ── 2. Retrieve / Update / Delete a single trip ───────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class TravelTripDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/travel/trips/<id>/   → trip detail
    PATCH  /api/travel/trips/<id>/   → generic field update (Edit button)
    DELETE /api/travel/trips/<id>/   → delete

    Users can only access their own trips; Admin/Manager can access all.
    No token → 401.
    """

    authentication_classes = []
    permission_classes     = [AllowAny]
    parser_classes         = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return _role_filtered_qs(request=self.request, base_qs=TravelTrip.objects.all())

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return StartTripSerializer
        return TravelTripListSerializer

    def _check_auth(self, request):
        return _require_auth(request)

    def retrieve(self, request, *args, **kwargs):
        err = self._check_auth(request)
        if err:
            return err
        return super().retrieve(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        err = self._check_auth(request)
        if err:
            return err
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        err = self._check_auth(request)
        if err:
            return err
        return super().destroy(request, *args, **kwargs)


# ── 3. End Trip ───────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class EndTripView(generics.UpdateAPIView):
    """
    PATCH /api/travel/trips/<id>/end/

    • No token           → 401
    • Non-admin trying to end someone else's trip → 403
    • Trip already completed → 400
    """

    authentication_classes = []
    permission_classes     = [AllowAny]
    serializer_class       = EndTripSerializer
    parser_classes         = [MultiPartParser, FormParser, JSONParser]
    http_method_names      = ['patch']

    def get_queryset(self):
        # Use the full queryset for pk lookup — ownership enforced in patch()
        return TravelTrip.objects.all()

    def patch(self, request, *args, **kwargs):
        # 1. Must be authenticated
        err = _require_auth(request)
        if err:
            return err

        instance = self.get_object()

        # 2. Non-admin users can only end their OWN trips
        auth = _get_auth_user(request)
        role = auth.get("role", "User")
        if role not in ("Admin", "Manager"):
            if instance.traveled_by.lower() != auth["username"].lower():
                return Response(
                    {'detail': 'You do not have permission to end this trip.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # 3. Cannot end an already-completed trip
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

@method_decorator(csrf_exempt, name='dispatch')
class OngoingTripsView(generics.ListAPIView):
    """
    GET /api/travel/trips/ongoing/

    Returns only ongoing trips, scoped to the caller's role.
    No token → 401.
    """

    authentication_classes = []
    permission_classes     = [AllowAny]
    serializer_class       = TravelTripListSerializer

    def get_queryset(self):
        base = TravelTrip.objects.filter(status='ongoing').order_by('-date', '-start_time')
        return _role_filtered_qs(request=self.request, base_qs=base)

    def list(self, request, *args, **kwargs):
        err = _require_auth(request)
        if err:
            return err
        return super().list(request, *args, **kwargs)