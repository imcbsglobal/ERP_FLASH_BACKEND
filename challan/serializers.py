from rest_framework import serializers
from .models import Challan


class ChallanSerializer(serializers.ModelSerializer):
    # Read-only display fields
    vehicle_display     = serializers.SerializerMethodField(read_only=True)
    challan_doc_url     = serializers.SerializerMethodField(read_only=True)
    payment_receipt_url = serializers.SerializerMethodField(read_only=True)
    # Expose creator's username so the frontend can filter per-user
    created_by_username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = Challan
        fields = [
            "id",
            "vehicle",
            "vehicle_display",
            "created_by",
            "created_by_username",
            "date",
            "challan_no",
            "challan_date",
            "offence_type",
            "location",
            "fine_amount",
            "payment_status",
            "challan_doc",
            "challan_doc_url",
            "payment_receipt",
            "payment_receipt_url",
            "remark",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]
        extra_kwargs = {
            "challan_doc":     {"required": False, "allow_null": True},
            "payment_receipt": {"required": False, "allow_null": True},
        }

    # ── helpers ──────────────────────────────────────────────────────────────

    def get_vehicle_display(self, obj):
        v = obj.vehicle
        if not v:
            return ""
        vehicle_name = getattr(v, 'vehicle_name', '') or getattr(v, 'model', '') or ''
        return f"{v.registration_number} - {vehicle_name}".strip("- ")

    def get_created_by_username(self, obj):
        if not obj.created_by:
            return None
        # Support both Django auth User (username) and custom login.User (username)
        return getattr(obj.created_by, "username", None)

    def _file_url(self, obj, field_name):
        file_field = getattr(obj, field_name)
        if not file_field:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(file_field.url) if request else file_field.url

    def get_challan_doc_url(self, obj):
        return self._file_url(obj, "challan_doc")

    def get_payment_receipt_url(self, obj):
        return self._file_url(obj, "payment_receipt")

    # ── validation ────────────────────────────────────────────────────────────

    def validate_fine_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Fine amount must be greater than zero.")
        return value

    def validate_challan_no(self, value):
        if not value.strip():
            raise serializers.ValidationError("Challan number cannot be blank.")
        return value.strip()