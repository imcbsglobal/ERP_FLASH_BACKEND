from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):

    payment_proof_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = Payment
        fields = [
            'id',
            'client_name',
            'branch',
            'collection_type',
            'amount',
            'paid_for',
            'notes',
            'payment_proof',
            'payment_proof_url',
            'status',
            'date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'date', 'created_at', 'updated_at', 'payment_proof_url']

    # ── Validation ────────────────────────────────────────────────

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value

    def validate(self, data):
        collection_type = data.get('collection_type') or (
            self.instance.collection_type if self.instance else None
        )
        payment_proof = data.get('payment_proof') or (
            self.instance.payment_proof if self.instance else None
        )

        # Proof is required for all non-Cash payment types
        if collection_type and collection_type != 'Cash' and not payment_proof:
            raise serializers.ValidationError(
                {"payment_proof": "Payment proof is required for non-Cash payment types."}
            )
        return data

    # ── Helpers ───────────────────────────────────────────────────

    def get_payment_proof_url(self, obj):
        request = self.context.get('request')
        if obj.payment_proof and request:
            return request.build_absolute_uri(obj.payment_proof.url)
        return None


class PaymentStatusUpdateSerializer(serializers.ModelSerializer):
    """Lightweight serializer used only for PATCH status updates."""

    class Meta:
        model  = Payment
        fields = ['status']