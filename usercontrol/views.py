from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
import logging

from .models import MenuPermission
from .serializers import (
    MenuPermissionSerializer,
    LoginUserWithPermissionsSerializer,
)
from login.models import User as LoginUser

logger = logging.getLogger(__name__)

ALLOWED_MENU_KEYS = ["dashboard", "col_reports", "col_reports_view", "vm_trips", "vm_service", "um_users", "um_roles", "cl_list", "mm_vehicle"]

def normalize_permission_payload(data):
    """Convert allowed_menus list into explicit booleans for serializer input."""
    if not isinstance(data, dict):
        return data

    data = data.copy()
    if "allowed_menus" in data:
        selected = set(data.get("allowed_menus") or [])
        for key in ALLOWED_MENU_KEYS:
            data[key] = key in selected

    return data


# ── List all login.User rows with permissions attached ────────────────────
class LoginUserListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        qs = LoginUser.objects.all().order_by("-date_joined")

        role = request.query_params.get("role")
        search = request.query_params.get("search")

        if role:
            qs = qs.filter(role=role)
        if search:
            qs = qs.filter(username__icontains=search)

        qs = qs.prefetch_related('menu_permissions')

        serializer = LoginUserWithPermissionsSerializer(
            qs, many=True, context={"request": request}
        )
        return Response({"count": qs.count(), "results": serializer.data})


# ── Per-user permissions GET / PATCH ──────────────────────────────────────
class UserPermissionsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            user = get_object_or_404(LoginUser, pk=pk)
            menu_perm, created = MenuPermission.objects.get_or_create(login_user=user)
            if created:
                logger.info(f"Created new MenuPermission for user {user.username} (ID: {pk})")
            return Response(MenuPermissionSerializer(menu_perm).data)
        except LoginUser.DoesNotExist:
            return Response(
                {"error": f"User with id {pk} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error in GET permissions for user {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk):
        try:
            logger.info(f"Received PATCH for user {pk} with data: {request.data}")

            user = get_object_or_404(LoginUser, pk=pk)
            menu_perm, created = MenuPermission.objects.get_or_create(login_user=user)
            if created:
                logger.info(f"Created new MenuPermission for user {user.username} (ID: {pk}) before update")

            payload = normalize_permission_payload(request.data)
            serializer = MenuPermissionSerializer(menu_perm, data=payload, partial=True)
            if not serializer.is_valid():
                logger.error(f"Validation errors for user {pk}: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            saved_perm = serializer.save()
            logger.info(
                f"Saved permissions for user {user.username} (ID: {pk}): "
                f"dashboard={saved_perm.dashboard}, col_reports={saved_perm.col_reports}, "
                f"col_reports_view={saved_perm.col_reports_view}, "
                f"vm_trips={saved_perm.vm_trips}, vm_service={saved_perm.vm_service}, "
                f"um_users={saved_perm.um_users}, um_roles={saved_perm.um_roles}, "
                f"cl_list={saved_perm.cl_list}, mm_vehicle={saved_perm.mm_vehicle}"
            )
            return Response(serializer.data)
        except LoginUser.DoesNotExist:
            return Response(
                {"error": f"User with id {pk} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error saving permissions for user {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── Bulk permissions PATCH ────────────────────────────────────────────────
class BulkMenuPermissionView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def patch(self, request, *args, **kwargs):
        items = request.data.get("permissions", [])
        logger.info(f"Received bulk PATCH with {len(items)} items")

        if not isinstance(items, list):
            return Response(
                {"detail": "Expected a list under 'permissions'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated = []
        errors = []

        for item in items:
            user_id = item.get("user_id")
            try:
                user = LoginUser.objects.get(pk=user_id)
                menu_perm, _ = MenuPermission.objects.get_or_create(login_user=user)

                item_data = normalize_permission_payload(item)
                serializer_data = {k: item_data[k] for k in ALLOWED_MENU_KEYS if k in item_data}

                serializer = MenuPermissionSerializer(menu_perm, data=serializer_data, partial=True)

                if serializer.is_valid():
                    serializer.save()
                    updated.append({"user_id": user_id, **serializer.data})
                else:
                    errors.append({"user_id": user_id, "error": serializer.errors})
            except LoginUser.DoesNotExist:
                errors.append({"user_id": user_id, "error": "User not found."})
            except Exception as e:
                errors.append({"user_id": user_id, "error": str(e)})

        logger.info(f"Bulk update complete: {len(updated)} updated, {len(errors)} errors")
        return Response({"updated": updated, "errors": errors})