from rest_framework import serializers
from .models import Claim


class ClaimSerializer(serializers.ModelSerializer):
    """
    Full serializer used for create / update / retrieve.
    `claimed_by` is read-only and is set automatically from request.user.
    `claimed_by_name` is a display-only helper field shown in list views.
    """

    claimed_by_name = serializers.SerializerMethodField(read_only=True)

    # Human-readable label for expense_type choice field
    expense_type_display = serializers.CharField(
        source="get_expense_type_display", read_only=True
    )

    class Meta:
        model = Claim
        fields = [
            "id",
            "claimed_by",
            "claimed_by_name",
            "expense_type",
            "expense_type_display",
            "department",
            "client_name",
            "purpose",
            "amount",
            "notes",
            "receipt",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "claimed_by", "created_at", "updated_at"]

    def get_claimed_by_name(self, obj):
        if obj.claimed_by:
            if hasattr(obj.claimed_by, 'get_full_name') and callable(obj.claimed_by.get_full_name):
                full_name = obj.claimed_by.get_full_name()
                if full_name:
                    return full_name
            if hasattr(obj.claimed_by, 'username'):
                return obj.claimed_by.username
            if hasattr(obj.claimed_by, 'email'):
                return obj.claimed_by.email
            return f"User {obj.claimed_by.id}"
        return None

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["claimed_by"] = request.user
        else:
            raise serializers.ValidationError("User must be authenticated")
        return super().create(validated_data)


class ClaimListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer used only for list responses.
    """

    claimed_by_name = serializers.SerializerMethodField(read_only=True)
    expense_type_display = serializers.CharField(
        source="get_expense_type_display", read_only=True
    )
    receipt = serializers.FileField(read_only=True)
    has_receipt = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Claim
        fields = [
            "id",
            "claimed_by_name",
            "expense_type",
            "expense_type_display",
            "department",
            "client_name",
            "amount",
            "receipt",
            "has_receipt",
            "status",
            "created_at",
        ]

    def get_claimed_by_name(self, obj):
        if obj.claimed_by:
            if hasattr(obj.claimed_by, 'get_full_name') and callable(obj.claimed_by.get_full_name):
                full_name = obj.claimed_by.get_full_name()
                if full_name:
                    return full_name
            if hasattr(obj.claimed_by, 'username'):
                return obj.claimed_by.username
            if hasattr(obj.claimed_by, 'email'):
                return obj.claimed_by.email
            return f"User {obj.claimed_by.id}"
        return None

    def get_has_receipt(self, obj):
        return bool(obj.receipt)


class ClaimStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for PATCH /claims/{id}/status/ endpoint.
    """

    class Meta:
        model = Claim
        fields = ["status"]