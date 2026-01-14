"""
User views for the Escrow Platform.
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from apps.users.models import User, UserSession
from apps.users.serializers import (
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    KYCSubmissionSerializer,
    TwoFactorEnableSerializer,
)
from apps.audit.services.audit_service import AuditService
from apps.core.enums import UserStatus, KYCStatus


class RegisterView(generics.CreateAPIView):
    """User registration endpoint."""
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Registration successful',
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """Custom login endpoint with extended response."""
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Log successful login
            try:
                user = User.objects.get(email=request.data.get('email'))
                AuditService.log_action(
                    entity_type='User',
                    entity_id=str(user.id),
                    action='login',
                    actor=user,
                    metadata={'ip': request.META.get('REMOTE_ADDR')}
                )
            except User.DoesNotExist:
                pass

        return response


class LogoutView(APIView):
    """Logout endpoint - blacklist refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            AuditService.log_action(
                entity_type='User',
                entity_id=str(request.user.id),
                action='logout',
                actor=request.user,
            )

            return Response({'message': 'Successfully logged out'})
        except Exception as e:
            return Response(
                {'error': 'Failed to logout'},
                status=status.HTTP_400_BAD_REQUEST
            )


class MeView(generics.RetrieveUpdateAPIView):
    """Get/update current user profile."""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Store previous state for audit
        previous_state = UserSerializer(instance).data
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Log update
        AuditService.log_action(
            entity_type='User',
            entity_id=str(instance.id),
            action='update',
            actor=request.user,
            previous_state=previous_state,
            new_state=UserSerializer(instance).data,
        )

        return Response(UserSerializer(instance).data)


class PasswordChangeView(APIView):
    """Change password endpoint."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        AuditService.log_action(
            entity_type='User',
            entity_id=str(request.user.id),
            action='password_change',
            actor=request.user,
        )

        return Response({'message': 'Password changed successfully'})


class PasswordResetRequestView(APIView):
    """Request password reset."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            # Generate reset token and send email
            # In production, implement actual email sending
            import secrets
            user.password_reset_token = secrets.token_urlsafe(32)
            user.password_reset_expires = timezone.now() + timezone.timedelta(hours=1)
            user.save()
            
            # TODO: Send email with reset link
            
        except User.DoesNotExist:
            pass  # Don't reveal if email exists

        return Response({
            'message': 'If an account exists with this email, you will receive a password reset link.'
        })


class PasswordResetConfirmView(APIView):
    """Confirm password reset."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        
        try:
            user = User.objects.get(
                password_reset_token=token,
                password_reset_expires__gt=timezone.now()
            )
            user.set_password(serializer.validated_data['new_password'])
            user.password_reset_token = None
            user.password_reset_expires = None
            user.save()

            AuditService.log_action(
                entity_type='User',
                entity_id=str(user.id),
                action='password_reset',
                actor=user,
            )

            return Response({'message': 'Password reset successful'})
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired reset token'},
                status=status.HTTP_400_BAD_REQUEST
            )


class KYCSubmitView(APIView):
    """Submit KYC documents."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = KYCSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.kyc_data = serializer.validated_data
        user.kyc_status = KYCStatus.PENDING
        user.kyc_submitted_at = timezone.now()
        user.save()

        AuditService.log_action(
            entity_type='User',
            entity_id=str(user.id),
            action='kyc_submitted',
            actor=user,
            new_state={'kyc_status': KYCStatus.PENDING},
        )

        return Response({
            'message': 'KYC documents submitted successfully',
            'status': KYCStatus.PENDING,
        })


class KYCStatusView(APIView):
    """Get KYC verification status."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'status': user.kyc_status,
            'submitted_at': user.kyc_submitted_at,
            'verified_at': user.kyc_verified_at,
            'can_transact': user.can_transact,
        })


class TwoFactorEnableView(APIView):
    """Enable two-factor authentication."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get 2FA setup QR code."""
        import pyotp
        import secrets
        
        user = request.user
        
        if user.two_factor_enabled:
            return Response(
                {'error': 'Two-factor authentication is already enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate new secret
        secret = pyotp.random_base32()
        user.two_factor_secret = secret
        user.save()
        
        # Generate provisioning URI for QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name='Escrow Platform'
        )
        
        return Response({
            'secret': secret,
            'provisioning_uri': provisioning_uri,
        })

    def post(self, request):
        """Verify and enable 2FA."""
        serializer = TwoFactorEnableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        code = serializer.validated_data['verification_code']
        
        import pyotp
        totp = pyotp.TOTP(user.two_factor_secret)
        
        if totp.verify(code):
            user.two_factor_enabled = True
            user.save()
            
            AuditService.log_action(
                entity_type='User',
                entity_id=str(user.id),
                action='2fa_enabled',
                actor=user,
            )
            
            return Response({'message': 'Two-factor authentication enabled'})
        else:
            return Response(
                {'error': 'Invalid verification code'},
                status=status.HTTP_400_BAD_REQUEST
            )


class TwoFactorDisableView(APIView):
    """Disable two-factor authentication."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        if not user.two_factor_enabled:
            return Response(
                {'error': 'Two-factor authentication is not enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify current 2FA code before disabling
        code = request.data.get('code')
        if not code:
            return Response(
                {'error': 'Verification code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        import pyotp
        totp = pyotp.TOTP(user.two_factor_secret)
        
        if totp.verify(code):
            user.two_factor_enabled = False
            user.two_factor_secret = None
            user.save()
            
            AuditService.log_action(
                entity_type='User',
                entity_id=str(user.id),
                action='2fa_disabled',
                actor=user,
            )
            
            return Response({'message': 'Two-factor authentication disabled'})
        else:
            return Response(
                {'error': 'Invalid verification code'},
                status=status.HTTP_400_BAD_REQUEST
            )
