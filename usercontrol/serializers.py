from rest_framework import serializers
import logging

from .models import MenuPermission
from login.models import User as LoginUser

logger = logging.getLogger(__name__)


# ── Menu Permission Serializer ───────────────────────────────────────────
class MenuPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuPermission
        fields = [
            "dashboard",
            "col_reports",
            "um_users",
            "um_roles",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def validate_dashboard(self, value):
        if value is not None and not isinstance(value, bool):
            raise serializers.ValidationError("dashboard must be a boolean")
        return value if value is not None else False

    def validate_col_reports(self, value):
        if value is not None and not isinstance(value, bool):
            raise serializers.ValidationError("col_reports must be a boolean")
        return value if value is not None else False

    def validate_um_users(self, value):
        if value is not None and not isinstance(value, bool):
            raise serializers.ValidationError("um_users must be a boolean")
        return value if value is not None else False

    def validate_um_roles(self, value):
        if value is not None and not isinstance(value, bool):
            raise serializers.ValidationError("um_roles must be a boolean")
        return value if value is not None else False


# ── Login User with Permissions ──────────────────────────────────────────
class LoginUserWithPermissionsSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    menu_permissions = serializers.SerializerMethodField()

    class Meta:
        model = LoginUser
        fields = [
            "id",
            "username",
            "full_name",
            "email",
            "role",
            "status",
            "menu_permissions",
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        first = (obj.first_name or "").strip()
        last = (obj.last_name or "").strip()
        full = f"{first} {last}".strip()
        return full if full else (obj.username or "")

    def get_menu_permissions(self, obj):
        try:
            # Use the related_name to access permissions
            return MenuPermissionSerializer(obj.menu_permissions).data
        except MenuPermission.DoesNotExist:
            logger.debug(f"No permissions found for user {obj.pk}, returning defaults")
            return {
                "dashboard": False,
                "col_reports": False,
                "um_users": False,
                "um_roles": False,
            }
        except Exception as e:
            logger.error(f"Error fetching permissions for user {obj.pk}: {str(e)}")
            return {
                "dashboard": False,
                "col_reports": False,
                "um_users": False,
                "um_roles": False,
            }