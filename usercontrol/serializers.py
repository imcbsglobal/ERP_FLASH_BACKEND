from rest_framework import serializers
import logging

from .models import MenuPermission
from login.models import User as LoginUser

logger = logging.getLogger(__name__)


class MenuPermissionSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField(read_only=True)
    allowed_menus = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = MenuPermission
        fields = [
            "username",
            "dashboard",
            "col_reports",
            "col_reports_view",
            "vm_trips",
            "vm_service",
            "cl_list",
            "image_capture",
            "um_users",
            "um_roles",
            "mm_vehicle",
            "allowed_menus",
            "updated_at",
        ]
        read_only_fields = ["username", "allowed_menus", "updated_at"]

    def get_username(self, obj):
        return obj.login_user.username if obj.login_user else None

    def get_allowed_menus(self, obj):
        try:
            return obj.allowed_menus()
        except Exception:
            return []

    def _bool(self, value):
        if value is None:
            return False
        if not isinstance(value, bool):
            raise serializers.ValidationError("Must be a boolean.")
        return value

    def validate_dashboard(self,        v): return self._bool(v)
    def validate_col_reports(self,      v): return self._bool(v)
    def validate_col_reports_view(self, v): return self._bool(v)
    def validate_vm_trips(self,         v): return self._bool(v)
    def validate_vm_service(self,       v): return self._bool(v)
    def validate_cl_list(self,          v): return self._bool(v)
    def validate_image_capture(self,    v): return self._bool(v)
    def validate_um_users(self,         v): return self._bool(v)
    def validate_um_roles(self,         v): return self._bool(v)
    def validate_mm_vehicle(self,       v): return self._bool(v)


class LoginUserWithPermissionsSerializer(serializers.ModelSerializer):
    full_name        = serializers.SerializerMethodField()
    photo_url        = serializers.SerializerMethodField()
    menu_permissions = serializers.SerializerMethodField()
    allowed_menus    = serializers.SerializerMethodField()

    class Meta:
        model  = LoginUser
        fields = ["id", "username", "full_name", "email",
                  "role", "status", "photo_url", "menu_permissions", "allowed_menus"]
        read_only_fields = fields

    def get_full_name(self, obj):
        first = (getattr(obj, "first_name", "") or "").strip()
        last  = (getattr(obj, "last_name",  "") or "").strip()
        full  = f"{first} {last}".strip()
        return full or (obj.username or "")

    def get_menu_permissions(self, obj):
        _empty = {
            "username": obj.username,
            "dashboard": False, "col_reports": False, "col_reports_view": False,
            "vm_trips": False,  "vm_service": False,
            "cl_list": False,   "image_capture": False,
            "um_users": False,  "um_roles": False,
            "mm_vehicle": False, "allowed_menus": [],
        }
        try:
            return MenuPermissionSerializer(obj.menu_permissions).data
        except MenuPermission.DoesNotExist:
            return _empty
        except Exception as e:
            logger.error(f"Error fetching permissions for user {obj.pk}: {e}")
            return _empty

    def get_photo_url(self, obj):
        photo = getattr(obj, "photo", None)
        if not photo:
            return None
        request = self.context.get("request")
        if hasattr(photo, "name") and photo.name:
            try:
                if request:
                    return request.build_absolute_uri(photo.url)
                return photo.url
            except Exception:
                return None
        if isinstance(photo, str) and photo:
            if request:
                from django.conf import settings
                return request.build_absolute_uri(f"{settings.MEDIA_URL}{photo}")
            return photo
        return None

    def get_allowed_menus(self, obj):
        try:
            perm = obj.menu_permissions
            return perm.allowed_menus() if perm else []
        except MenuPermission.DoesNotExist:
            return []
        except Exception as e:
            logger.error(f"Error fetching allowed_menus for user {obj.pk}: {e}")
            return []