"""
User serializers for the Escrow Platform.
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from apps.users.models import User
from apps.core.enums import UserRole, UserStatus, KYCStatus


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )
    role = serializers.ChoiceField(
        choices=[('buyer', 'Buyer'), ('seller', 'Seller')],
        default='buyer'
    )

    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm', 
            'first_name', 'last_name', 'phone_number', 'role'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with additional claims."""

    def validate(self, attrs):
        # Check if user is locked out
        try:
            user = User.objects.get(email=attrs['email'])
            if user.is_locked_out():
                raise serializers.ValidationError({
                    'email': 'Account is temporarily locked. Please try again later.'
                })
        except User.DoesNotExist:
            pass

        try:
            data = super().validate(attrs)
        except Exception as e:
            # Record failed login attempt
            try:
                user = User.objects.get(email=attrs['email'])
                user.record_login_attempt(success=False)
            except User.DoesNotExist:
                pass
            raise

        # Record successful login
        self.user.record_login_attempt(success=True)

        # Add custom claims
        data['user'] = UserSerializer(self.user).data
        
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['role'] = user.role
        token['status'] = user.status
        
        return token


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile."""
    full_name = serializers.CharField(read_only=True)
    can_transact = serializers.BooleanField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'profile_image', 'role', 'status',
            'kyc_status', 'email_verified', 'two_factor_enabled',
            'can_transact', 'is_verified', 'created_at', 'last_login_at'
        ]
        read_only_fields = [
            'id', 'email', 'role', 'status', 'kyc_status',
            'email_verified', 'created_at', 'last_login_at'
        ]

    effecitve_plan = serializers.SerializerMethodField()

    def get_effecitve_plan(self, obj):
        """
        Get the effective plan details (fees, SLA) considering overrides.
        """
        from apps.plans.services import FeeEngine, SLAEngine
        
        plan_name = obj.plan.name if obj.plan else 'Default'
        
        return {
            'name': plan_name,
            'fee_percent': FeeEngine.get_fee_percent(obj),
            'sla_hours': SLAEngine.get_sla_hours(obj),
            'features': {
                'api_access': obj.plan.has_api_access if obj.plan else False,
                'dedicated_support': obj.plan.has_dedicated_support if obj.plan else False,
                'white_labeling': obj.plan.has_white_labeling if obj.plan else False,
            }
        }


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number', 'profile_image', 'address'
        ]


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True, 
        write_only=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'New passwords do not match.'
            })
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Passwords do not match.'
            })
        return attrs


class KYCSubmissionSerializer(serializers.Serializer):
    """Serializer for KYC document submission."""
    document_type = serializers.ChoiceField(
        choices=[
            ('passport', 'Passport'),
            ('national_id', 'National ID'),
            ('drivers_license', 'Driver\'s License'),
        ]
    )
    document_number = serializers.CharField(max_length=50)
    document_front_url = serializers.URLField()
    document_back_url = serializers.URLField(required=False)
    selfie_url = serializers.URLField()
    date_of_birth = serializers.DateField()
    nationality = serializers.CharField(max_length=50)
    address = serializers.JSONField()


class TwoFactorEnableSerializer(serializers.Serializer):
    """Serializer for enabling 2FA."""
    verification_code = serializers.CharField(
        max_length=6,
        min_length=6,
        required=True
    )


class TwoFactorVerifySerializer(serializers.Serializer):
    """Serializer for verifying 2FA code."""
    code = serializers.CharField(max_length=6, min_length=6, required=True)
