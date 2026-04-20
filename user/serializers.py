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
    Read-only. Works with LocalUser instances that have been passed through
    _enrich() / _enrich_many() in views.py, which sets ._branch_name.
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
    photo_url   = serializers.SerializerMethodField()

    def get_branch_id(self, obj):
        # LocalUser has branch as FK — branch_id is the raw integer column
        return getattr(obj, "branch_id", None)

    def get_branch_name(self, obj):
        return getattr(obj, "_branch_name", None)

    def get_branch(self, obj):
        return getattr(obj, "branch_id", None)

    def get_created_at(self, obj):
        val = getattr(obj, "created_at", None) or getattr(obj, "date_joined", None)
        return val.isoformat() if val else None

    def get_updated_at(self, obj):
        val = getattr(obj, "updated_at", None) or getattr(obj, "last_login", None)
        return val.isoformat() if val else None

    def get_photo_url(self, obj):
        """
        Return the absolute URL of the user's photo, or None if not set.
        LocalUser.photo is an ImageField — use .name and .url directly.
        """
        request = self.context.get("request")
        photo = getattr(obj, "photo", None)
        if not photo:
            return None
        # ImageField / FieldFile — check .name to confirm a file is stored
        if hasattr(photo, "name") and photo.name:
            try:
                if request:
                    return request.build_absolute_uri(photo.url)
                return photo.url
            except Exception:
                return None
        # Plain string path (fallback for legacy rows)
        if isinstance(photo, str) and photo:
            if request:
                from django.conf import settings
                return request.build_absolute_uri(f"{settings.MEDIA_URL}{photo}")
            return photo
        return None


# ── User (write) ──────────────────────────────────────────────────────────────

class UserWriteSerializer(serializers.Serializer):
    """
    Write serializer for create / update against LocalUser (models.py User).
    LocalUser.branch is a real FK to Branch, so we accept branch_id (int)
    and set it directly as the integer FK column.

    Photo is handled as a separate multipart field; the view passes the
    InMemoryUploadedFile (or None) via context["photo_file"].
    """
    username  = serializers.CharField(max_length=150)
    address   = serializers.CharField(allow_blank=True, default="")
    phone     = serializers.CharField(max_length=20, allow_blank=True, default="")
    password  = serializers.CharField(write_only=True, min_length=8, required=False)
    branch_id = serializers.IntegerField(required=False, allow_null=True)
    role      = serializers.CharField(max_length=20)
    status    = serializers.CharField(max_length=10, default="Active")

    ROLE_CHOICES   = ["Admin", "Manager", "User"]
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
        """Confirm the branch exists; return the integer ID."""
        if value is None:
            return None
        if not Branch.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f"Branch with ID {value} does not exist.")
        return value

    # ── internal helper ───────────────────────────────────────────────────────
    def _save_photo(self, user):
        """
        Persist the uploaded photo file onto the user instance (if provided).
        LocalUser.photo is an ImageField — we write the file to disk and assign
        the relative path so Django's storage layer tracks it correctly.
        Skips silently if the user model has no photo field.
        """
        photo_file = self.context.get("photo_file")
        if photo_file is None:
            return  # no upload — keep existing photo

        if not hasattr(user, "photo"):
            return  # model has no photo column — skip

        import os, uuid
        from django.conf import settings

        ext       = os.path.splitext(photo_file.name)[1].lower() or ".jpg"
        safe_name = (user.username or "user").replace(" ", "_")
        filename  = f"{safe_name}_{uuid.uuid4().hex[:8]}{ext}"
        rel_path  = f"user_photos/{safe_name}/{filename}"
        abs_path  = os.path.join(settings.MEDIA_ROOT, rel_path)

        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        with open(abs_path, "wb") as fh:
            for chunk in photo_file.chunks():
                fh.write(chunk)

        # Assign relative path — works for both ImageField and CharField
        user.photo = rel_path
        try:
            user.save(update_fields=["photo"])
        except Exception:
            user.save()

    def create(self, validated_data):
        User      = self._model()
        raw_pwd   = validated_data.pop("password", None)
        branch_id = validated_data.pop("branch_id", None)

        user = User(**validated_data)
        user.password = make_password(raw_pwd) if raw_pwd else ""

        # LocalUser.branch is a FK — assign the integer directly to branch_id
        if branch_id is not None:
            user.branch_id = branch_id

        user.save()
        self._save_photo(user)
        return user

    def update(self, instance, validated_data):
        if "password" in validated_data:
            instance.password = make_password(validated_data.pop("password"))

        branch_id = validated_data.pop("branch_id", None)
        if branch_id is not None:
            instance.branch_id = branch_id

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        self._save_photo(instance)
        return instance