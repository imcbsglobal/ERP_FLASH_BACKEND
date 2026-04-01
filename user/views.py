import traceback
import logging

from rest_framework import status as drf_status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import check_password, make_password

from .models import Branch
from .serializers import BranchSerializer, UserReadSerializer, UserWriteSerializer

from login.models import User as LoginUser

# Auto-create MenuPermission row for every new user
try:
    from usercontrol.models import MenuPermission as _MenuPermission
    def _ensure_menu_permission(user_id):
        _MenuPermission.objects.get_or_create(login_user_id=user_id)
except Exception:
    def _ensure_menu_permission(user_id):
        pass

logger = logging.getLogger(__name__)


# ── helpers ───────────────────────────────────────────────────────────────────

def _user_qs():
    """
    Base queryset for login.User.
    login.User has NO ForeignKey to Branch — branch_id is a plain integer column.
    So we must NOT call select_related('branch') — that's what caused the 500.
    """
    qs = LoginUser.objects.all()
    if hasattr(LoginUser, "is_superuser"):
        qs = qs.filter(is_superuser=False)
    return qs


def _enrich(user):
    """
    Attach branch_name to a LoginUser instance by doing a direct Branch lookup
    on the raw branch_id integer, since there is no FK join available.
    """
    bid = getattr(user, "branch_id", None)
    if bid:
        try:
            user._branch_name = Branch.objects.get(pk=bid).name
        except Branch.DoesNotExist:
            user._branch_name = None
    else:
        user._branch_name = None
    return user


def _enrich_many(users):
    """Batch-load branch names for a queryset to avoid N+1 queries."""
    users = list(users)
    ids   = {getattr(u, "branch_id", None) for u in users if getattr(u, "branch_id", None)}
    names = {b.id: b.name for b in Branch.objects.filter(pk__in=ids)} if ids else {}
    for u in users:
        u._branch_name = names.get(getattr(u, "branch_id", None))
    return users


# ── Branch views ──────────────────────────────────────────────────────────────

class BranchListCreateView(APIView):
    authentication_classes = []
    permission_classes     = [AllowAny]

    def get(self, request):
        return Response(BranchSerializer(Branch.objects.all(), many=True).data)

    def post(self, request):
        s = BranchSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=drf_status.HTTP_201_CREATED)
        return Response(s.errors, status=drf_status.HTTP_400_BAD_REQUEST)


class BranchDetailView(APIView):
    authentication_classes = []
    permission_classes     = [AllowAny]

    def get_object(self, pk):
        return get_object_or_404(Branch, pk=pk)

    def get(self, request, pk):
        return Response(BranchSerializer(self.get_object(pk)).data)

    def put(self, request, pk):
        s = BranchSerializer(self.get_object(pk), data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=drf_status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        self.get_object(pk).delete()
        return Response({"detail": "Branch deleted."}, status=drf_status.HTTP_204_NO_CONTENT)


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginView(APIView):
    authentication_classes = []
    permission_classes     = [AllowAny]

    def post(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")

        if not username or not password:
            return Response({"detail": "Username and password are required."},
                            status=drf_status.HTTP_400_BAD_REQUEST)
        try:
            user = LoginUser.objects.get(username=username)
        except LoginUser.DoesNotExist:
            return Response({"detail": "Invalid username or password."},
                            status=drf_status.HTTP_401_UNAUTHORIZED)

        if not check_password(password, user.password):
            return Response({"detail": "Invalid username or password."},
                            status=drf_status.HTTP_401_UNAUTHORIZED)

        if getattr(user, "status", "Active") == "Inactive":
            return Response({"detail": "Your account is inactive."},
                            status=drf_status.HTTP_403_FORBIDDEN)

        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken()
        refresh["user_id"]  = user.id
        refresh["username"] = user.username
        refresh["role"]     = getattr(user, "role", "")

        branch_name = None
        bid = getattr(user, "branch_id", None)
        if bid:
            try:
                branch_name = Branch.objects.get(pk=bid).name
            except Branch.DoesNotExist:
                pass

        return Response({
            "access": str(refresh.access_token), "refresh": str(refresh),
            "user": {
                "id":       user.id,
                "username": user.username,
                "role":     getattr(user, "role", ""),
                "status":   getattr(user, "status", "Active"),
                "branch":   branch_name,
            },
        })


# ── User views ────────────────────────────────────────────────────────────────

class UserListCreateView(APIView):
    authentication_classes = []
    permission_classes     = [AllowAny]

    def get(self, request):
        try:
            qs = _user_qs()
            role    = request.query_params.get("role")
            status_ = request.query_params.get("status")
            branch  = request.query_params.get("branch")
            search  = request.query_params.get("search")
            if role:    qs = qs.filter(role=role)
            if status_: qs = qs.filter(status=status_)
            if branch:  qs = qs.filter(branch_id=branch)
            if search:  qs = qs.filter(username__icontains=search)
            users = _enrich_many(qs)
            # Backfill MenuPermission rows for any users that don't have one yet
            for u in users:
                _ensure_menu_permission(u.id)
            return Response({"count": len(users),
                             "results": UserReadSerializer(users, many=True).data})
        except Exception as e:
            logger.error(f"UserList.get: {e}\n{traceback.format_exc()}")
            return Response({"detail": str(e)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            s = UserWriteSerializer(data=request.data, context={"UserModel": LoginUser})
            if s.is_valid():
                user = _enrich(s.save())
                _ensure_menu_permission(user.id)
                return Response(UserReadSerializer(user).data,
                                status=drf_status.HTTP_201_CREATED)
            return Response(s.errors, status=drf_status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"UserList.post: {e}\n{traceback.format_exc()}")
            return Response({"detail": str(e)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDetailView(APIView):
    authentication_classes = []
    permission_classes     = [AllowAny]

    def _get(self, pk):
        return get_object_or_404(_user_qs(), pk=pk)

    def get(self, request, pk):
        try:
            return Response(UserReadSerializer(_enrich(self._get(pk))).data)
        except Exception as e:
            logger.error(f"UserDetail.get({pk}): {e}\n{traceback.format_exc()}")
            return Response({"detail": str(e)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        try:
            obj = self._get(pk)
            s = UserWriteSerializer(obj, data=request.data, context={"UserModel": LoginUser})
            if s.is_valid():
                return Response(UserReadSerializer(_enrich(s.save())).data)
            return Response(s.errors, status=drf_status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"UserDetail.put({pk}): {e}\n{traceback.format_exc()}")
            return Response({"detail": str(e)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk):
        try:
            obj = self._get(pk)
            s = UserWriteSerializer(obj, data=request.data, partial=True,
                                    context={"UserModel": LoginUser})
            if s.is_valid():
                return Response(UserReadSerializer(_enrich(s.save())).data)
            return Response(s.errors, status=drf_status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"UserDetail.patch({pk}): {e}\n{traceback.format_exc()}")
            return Response({"detail": str(e)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            self._get(pk).delete()
            return Response({"detail": "User deleted."}, status=drf_status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"UserDetail.delete({pk}): {e}\n{traceback.format_exc()}")
            return Response({"detail": str(e)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── Toggle status ─────────────────────────────────────────────────────────────

class UserToggleStatusView(APIView):
    authentication_classes = []
    permission_classes     = [AllowAny]

    def patch(self, request, pk):
        try:
            user = get_object_or_404(_user_qs(), pk=pk)
            user.status = "Inactive" if user.status == "Active" else "Active"
            user.save(update_fields=["status"])
            return Response({"id": user.id, "status": user.status})
        except Exception as e:
            logger.error(f"ToggleStatus.patch({pk}): {e}\n{traceback.format_exc()}")
            return Response({"detail": str(e)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)