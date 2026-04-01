# login/views.py
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    RegisterSerializer,
    ChangePasswordSerializer,
)

# ── Auto-create MenuPermission for every new user ─────────────────────────────
from usercontrol.models import MenuPermission

User = get_user_model()


def _ensure_menu_permission(user):
    """
    Create a MenuPermission row (all False) for a newly created user.
    Safe to call even if it already exists (get_or_create).
    """
    MenuPermission.objects.get_or_create(login_user_id=user.pk)


# ── POST /api/auth/login/ ─────────────────────────────────────
class LoginView(TokenObtainPairView):
    """
    Accepts: { username, password }
    Returns: { access, refresh, user: { id, username, full_name, role, status } }
    """
    permission_classes = [AllowAny]
    serializer_class   = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except DRFValidationError as e:
            detail = e.detail
            if isinstance(detail, list):
                msg = str(detail[0])
            elif isinstance(detail, dict):
                msg = str(next(iter(detail.values()))[0]) if detail else "Validation error."
            else:
                msg = str(detail)
            return Response({'detail': msg}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            return Response(
                {'detail': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


# ── POST /api/auth/logout/ ────────────────────────────────────
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_205_RESET_CONTENT)


# ── GET / PATCH /api/auth/me/ ─────────────────────────────────
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ── POST /api/auth/register/ ─────────────────────────────────
class RegisterView(generics.CreateAPIView):
    """
    Only an authenticated (logged-in) user can create new users.
    Accepts: { username, password, role, address, phone, status, branch_id }
    Auto-creates a MenuPermission row (all False) for the new user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # ── Auto-create permission record so admin can set it immediately ──────
        _ensure_menu_permission(user)

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


# ── POST /api/auth/change-password/ ──────────────────────────
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'Password changed successfully.'})


# ── GET  /api/users/       → list all users ──────────────────
# ── POST /api/users/       → create a user  ──────────────────
class UserListView(APIView):
    """
    GET  /api/users/  – list all users in login.User (AUTH_USER_MODEL)
    POST /api/users/  – create a user (same as /api/auth/register/)
    Auto-creates a MenuPermission row (all False) for every new user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = User.objects.all()

        role    = request.query_params.get("role")
        status_ = request.query_params.get("status")
        search  = request.query_params.get("search")

        if role:
            qs = qs.filter(role=role)
        if status_:
            qs = qs.filter(status=status_)
        if search:
            qs = qs.filter(username__icontains=search)

        serializer = UserSerializer(qs, many=True)
        return Response({"count": qs.count(), "results": serializer.data})

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # ── Auto-create permission record so admin can set it immediately ──────
        _ensure_menu_permission(user)

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


# ── GET / PATCH / DELETE  /api/users/<id>/ ───────────────────
class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(User, pk=pk)

    def get(self, request, pk):
        return Response(UserSerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        user = self.get_object(pk)
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request, pk):
        user = self.get_object(pk)
        serializer = UserSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        # Also delete the permission record when user is deleted
        MenuPermission.objects.filter(login_user_id=pk).delete()
        self.get_object(pk).delete()
        return Response({"detail": "User deleted."}, status=status.HTTP_204_NO_CONTENT)


# ── PATCH /api/users/<id>/toggle-status/ ─────────────────────
class UserToggleStatusView(APIView):
    """
    Toggles status between Active ↔ Inactive on login.User.
    Also syncs is_active so the user can / cannot log in immediately.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.status    = "Inactive" if user.status == "Active" else "Active"
        user.is_active = (user.status == "Active")
        user.save(update_fields=["status", "is_active"])
        return Response({"id": user.id, "status": user.status}, status=status.HTTP_200_OK)