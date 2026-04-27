from rest_framework import serializers
from django.utils import timezone
from .models import Customer, CaptureLink, OtpRecord, ImageCapture


# ══════════════════════════════════════════════════════════════════
# Customer
# ══════════════════════════════════════════════════════════════════

class CustomerSerializer(serializers.ModelSerializer):
    """
    Used by Image_link.jsx to populate the branch/customer dropdowns.
    GET /api/customers/?branch=&search=
    """
    class Meta:
        model  = Customer
        fields = ["id", "name", "phone", "branch", "email", "created"]
        read_only_fields = ["id", "created"]


# ══════════════════════════════════════════════════════════════════
# CaptureLink
# ══════════════════════════════════════════════════════════════════

class CaptureLinkCreateSerializer(serializers.ModelSerializer):
    """
    POST /api/generate-link/
    Matches Image_link.jsx handleGenerate() — accepts either a
    customer FK (customer_id) or a free-text customer_name.
    """
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source="customer",
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model  = CaptureLink
        fields = [
            "id", "uuid", "customer_id", "customer_name", "phone",
            "status", "created_at", "expires_at", "link_path",
        ]
        read_only_fields = ["id", "uuid", "status", "created_at", "link_path"]

    def validate(self, data):
        if not data.get("customer") and not data.get("customer_name", "").strip():
            raise serializers.ValidationError(
                {"customer_name": "Provide either customer_id or customer_name."}
            )
        return data


class CaptureLinkDetailSerializer(serializers.ModelSerializer):
    """
    GET /api/capture-link/<uuid>/
    Returns everything the capture page (ImageCaptureFlow) needs on load:
    customer name, phone, expiry flag.
    """
    customer_name_resolved = serializers.SerializerMethodField()
    is_expired             = serializers.SerializerMethodField()
    link_path              = serializers.SerializerMethodField()

    class Meta:
        model  = CaptureLink
        fields = [
            "id", "uuid",
            "customer", "customer_name", "customer_name_resolved",
            "phone", "status",
            "created_at", "expires_at",
            "link_path", "is_expired",
        ]

    def get_customer_name_resolved(self, obj):
        return obj.effective_name

    def get_is_expired(self, obj):
        return bool(obj.expires_at and obj.expires_at < timezone.now())

    def get_link_path(self, obj):
        return obj.link_path


class CaptureLinkListSerializer(serializers.ModelSerializer):
    """
    GET /api/capture-links/
    Lightweight list used in admin / imgcapture_list.jsx link overview.
    """
    customer_name_resolved = serializers.SerializerMethodField()

    class Meta:
        model  = CaptureLink
        fields = [
            "id", "uuid", "customer_name_resolved",
            "phone", "status", "created_at", "expires_at", "link_path",
        ]

    def get_customer_name_resolved(self, obj):
        return obj.effective_name


# ══════════════════════════════════════════════════════════════════
# OTP
# ══════════════════════════════════════════════════════════════════

class OtpSendSerializer(serializers.Serializer):
    """
    POST /api/send-otp/
    phoneverify.jsx → handleSend()
    """
    phone = serializers.CharField(max_length=20)
    uuid  = serializers.UUIDField(required=False, allow_null=True)

    def validate_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        return value


class OtpVerifySerializer(serializers.Serializer):
    """
    POST /api/verify-otp/
    Otp_verification.jsx → verifyOtpWithCode()
    Frontend sends a 4-digit code (CORRECT_OTP = "1234" in demo mode).
    """
    phone    = serializers.CharField(max_length=20)
    otp_code = serializers.CharField(max_length=10, min_length=4)
    uuid     = serializers.UUIDField(required=False, allow_null=True)


class OtpRecordReadSerializer(serializers.ModelSerializer):
    """Read-only — returned in list/detail admin views."""
    class Meta:
        model  = OtpRecord
        fields = ["id", "phone", "status", "attempts", "created_at", "verified_at"]
        read_only_fields = fields


# ══════════════════════════════════════════════════════════════════
# ImageCapture
# ══════════════════════════════════════════════════════════════════

class ImageCaptureUploadSerializer(serializers.ModelSerializer):
    """
    POST /api/upload-image/   (multipart/form-data)
    Mirrors Image_add.jsx handleUpload() FormData fields:
        image, uuid, latitude, longitude, address,
        customer_name (optional), phone (optional)
    """
    uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model  = ImageCapture
        fields = [
            "id", "uuid",
            "customer_name", "phone",
            "image",
            "latitude", "longitude", "address",
            "verification_status", "verified_at",
        ]
        read_only_fields = ["id", "verification_status", "verified_at"]

    def create(self, validated_data):
        raw_uuid = validated_data.pop("uuid", None)
        link = None

        if raw_uuid:
            try:
                link = CaptureLink.objects.get(uuid=raw_uuid)
                link.status = CaptureLink.STATUS_USED
                link.save(update_fields=["status"])
                # Back-fill name / phone from the link if not submitted
                if not validated_data.get("customer_name"):
                    validated_data["customer_name"] = link.effective_name
                if not validated_data.get("phone"):
                    validated_data["phone"] = link.phone
            except CaptureLink.DoesNotExist:
                pass

        return ImageCapture.objects.create(capture_link=link, **validated_data)


class ImageCaptureListSerializer(serializers.ModelSerializer):
    """
    GET /api/captures/
    Matches the column shape expected by imgcapture_list.jsx:
        clientDetails { name, contact, phone }
        image, location, coordinate,
        verificationTime, status, manualStatus
    """
    client_details        = serializers.SerializerMethodField()
    location              = serializers.CharField(source="address")
    coordinate            = serializers.SerializerMethodField()
    verification_time     = serializers.DateTimeField(
        source="verified_at", format="%Y-%m-%d %H:%M:%S"
    )
    status                = serializers.CharField(source="verification_status")
    manual_status_display = serializers.CharField(source="get_manual_status_display", read_only=True)

    class Meta:
        model  = ImageCapture
        fields = [
            "id",
            "client_details",
            "image",
            "location",
            "coordinate",
            "verification_time",
            "status",
            "manual_status",
            "manual_status_display",
        ]

    def get_client_details(self, obj):
        email = ""
        if obj.capture_link and obj.capture_link.customer:
            email = obj.capture_link.customer.email
        return {
            "name":    obj.customer_name,
            "phone":   obj.phone,
            "contact": email,
        }

    def get_coordinate(self, obj):
        if obj.latitude and obj.longitude:
            return f"{obj.latitude}° N, {obj.longitude}° E"
        return ""


class ImageCaptureDetailSerializer(serializers.ModelSerializer):
    """
    GET /api/captures/<pk>/
    Full record — mirrors verify_success.jsx state shape:
        customerName, phone, preview (image URL),
        address, lat, lng, verifiedAt
    """
    lat         = serializers.DecimalField(
        source="latitude", max_digits=10, decimal_places=7, allow_null=True
    )
    lng         = serializers.DecimalField(
        source="longitude", max_digits=10, decimal_places=7, allow_null=True
    )
    verified_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S")

    class Meta:
        model  = ImageCapture
        fields = [
            "id",
            "customer_name",
            "phone",
            "image",          # URL string after DRF request context
            "address",
            "lat", "lng",
            "verification_status",
            "manual_status",
            "verified_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add absolute image URL if request is in context
        request = self.context.get("request")
        if request and instance.image:
            data["image"] = request.build_absolute_uri(instance.image.url)
        return data


class ManualStatusUpdateSerializer(serializers.ModelSerializer):
    """
    PATCH /api/captures/<pk>/manual-status/
    Staff approves / rejects from imgcapture_list.jsx action menu.
    Body: { "manual_status": "approved" | "under_review" | "rejected" | "pending" }
    """
    class Meta:
        model  = ImageCapture
        fields = ["manual_status"]

    def validate_manual_status(self, value):
        valid = [c[0] for c in ImageCapture.MANUAL_STATUS_CHOICES]
        if value not in valid:
            raise serializers.ValidationError(
                f"Invalid status. Choose from: {', '.join(valid)}"
            )
        return value