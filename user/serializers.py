from rest_framework import serializers
from django.contrib.auth.hashers import make_password

from .models import Branch


# ── Branch ───────────────────────────────────────────────────────────────────

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Branch
        fields = ["id", "name", "created_at"]
        read_only_fields = ["id", "created_at"]


# ── User (read) ───────────────────────────────────────────────────────────────

class UserReadSerializer(serializers.Serializer):
    """
    Read-only. Works with login.User instances that have been passed through
    _enrich() / _enrich_many() in views.py, which sets ._branch_name.
    login.User stores branch as a plain integer column (branch_id), NOT a FK,
    so we never call .branch.name — we use the pre-fetched _branch_name instead.
    """
    id          = serializers.IntegerField(read_only=True)
    username    = serializers.CharField(read_only=True)
    address     = serializers.CharField(read_only=True)
    phone       = serializers.CharField(read_only=True)
    role        = serializers.CharField(read_only=True)
    status      = serializers.CharField(read_only=True)
    branch_id   = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    branch      = serializers.SerializerMethodField()
    created_at  = serializers.SerializerMethodField()
    updated_at  = serializers.SerializerMethodField()

    def get_branch_id(self, obj):
        return getattr(obj, "branch_id", None)

    def get_branch_name(self, obj):
        return getattr(obj, "_branch_name", None)

    def get_branch(self, obj):
        return getattr(obj, "branch_id", None)

    def get_created_at(self, obj):
        val = getattr(obj, "date_joined", None) or getattr(obj, "created_at", None)
        return val.isoformat() if val else None

    def get_updated_at(self, obj):
        val = getattr(obj, "updated_at", None) or getattr(obj, "last_login", None)
        return val.isoformat() if val else None


# ── User (write) ──────────────────────────────────────────────────────────────

class UserWriteSerializer(serializers.Serializer):
    """
    Write serializer for create / update against login.User.
    branch_id is stored as a plain integer on login.User — no FK object needed.
    The UserModel is injected via context["UserModel"] from the view.
    """
    username  = serializers.CharField(max_length=150)
    address   = serializers.CharField(allow_blank=True, default="")
    phone     = serializers.CharField(max_length=20, allow_blank=True, default="")
    password  = serializers.CharField(write_only=True, min_length=8, required=False)
    branch_id = serializers.IntegerField(required=False, allow_null=True)
    role      = serializers.CharField(max_length=20)
    status    = serializers.CharField(max_length=10, default="Active")

    ROLE_CHOICES   = ["Admin", "Manager", "Operator", "Viewer", "Support", "Auditor"]
    STATUS_CHOICES = ["Active", "Inactive"]

    def _model(self):
        from django.apps import apps
        return self.context.get("UserModel") or apps.get_model("login", "User")

    def validate_username(self, value):
        User = self._model()
        qs = User.objects.filter(username=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_phone(self, value):
        import re
        if value and not re.match(r"^\+?[\d\s\-()\u0020]{7,15}$", value):
            raise serializers.ValidationError("Enter a valid phone number.")
        return value

    def validate_role(self, value):
        if value not in self.ROLE_CHOICES:
            raise serializers.ValidationError(
                f"Role must be one of: {', '.join(self.ROLE_CHOICES)}")
        return value

    def validate_status(self, value):
        if value not in self.STATUS_CHOICES:
            raise serializers.ValidationError(
                f"Status must be one of: {', '.join(self.STATUS_CHOICES)}")
        return value

    def validate_branch_id(self, value):
        """Confirm the branch exists; return the integer ID (not a Branch object)."""
        if value is None:
            return None
        if not Branch.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f"Branch with ID {value} does not exist.")
        return value   # ← integer, not a Branch instance

    def create(self, validated_data):
        User    = self._model()
        raw_pwd = validated_data.pop("password", None)
        user    = User(**validated_data)
        user.password    = make_password(raw_pwd) if raw_pwd else ""
        user.is_active   = True
        user.is_staff    = False
        user.is_superuser = False
        user.save()
        return user

    def update(self, instance, validated_data):
        if "password" in validated_data:
            instance.password = make_password(validated_data.pop("password"))
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance