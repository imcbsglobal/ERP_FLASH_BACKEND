# login/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


# ── Custom JWT payload ────────────────────────────────────────
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "username"

    def validate(self, attrs):
        username = attrs.get("username", "").strip()
        try:
            user = User.objects.get(username=username)
            if user.status == "Inactive":
                raise serializers.ValidationError(
                    "Your account is inactive. Contact an administrator."
                )
        except User.DoesNotExist:
            pass  # let super().validate() raise the wrong-credentials error

        data = super().validate(attrs)

        data['user'] = {
            'id':        self.user.id,
            'username':  self.user.username,
            'email':     self.user.email,
            'full_name': self.user.full_name,
            'role':      self.user.role,
            'status':    self.user.status,
            'is_staff':  self.user.is_staff,
        }
        return data


# ── User profile serializer ───────────────────────────────────
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model  = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'address', 'phone', 'branch_id', 'status',
            'is_active', 'is_staff', 'date_joined', 'last_login',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


# ── Registration / Create-user serializer ─────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    """
    Accepts the payload from user_list.jsx:
      { username, password, address, phone, branch_id, role, status }

    `branch_id`  — accepted and discarded (login.User has no branch FK).
    `status`     — mapped to `is_active` so Django auth respects it immediately.
    `password`   — write-only; hashed via set_password() inside create().
    """
    password  = serializers.CharField(write_only=True, min_length=6)
    branch_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model  = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'role', 'address', 'phone', 'status',
            'branch_id',
        ]

    def create(self, validated_data):
        # Extract password before passing to create_user
        # (create_user expects it as a positional arg, NOT in **extra_fields)
        password = validated_data.pop('password')

        # Sync is_active with status so login works immediately
        user_status = validated_data.get('status', 'Active')
        validated_data['is_active'] = (user_status == 'Active')

        # create_user hashes the password via set_password()
        user = User.objects.create_user(password=password, **validated_data)
        return user

    def update(self, instance, validated_data):
        """Allow superuser to update a user's details including password."""
        password = validated_data.pop('password', None)

        # Sync is_active if status is changing
        if 'status' in validated_data:
            validated_data['is_active'] = (validated_data['status'] == 'Active')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)  # hashes correctly

        instance.save()
        return instance


# ── Change password serializer ────────────────────────────────
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value