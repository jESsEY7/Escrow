"""
User models for the Escrow Platform.
Custom user model with role-based access and KYC support.
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from apps.core.enums import UserRole, UserStatus, KYCStatus


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        extra_fields.setdefault('role', UserRole.BUYER)
        extra_fields.setdefault('status', UserStatus.PENDING_VERIFICATION)
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.ADMIN)
        extra_fields.setdefault('status', UserStatus.ACTIVE)
        extra_fields.setdefault('kyc_status', KYCStatus.APPROVED)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with email authentication and role-based access."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    
    # Profile Information
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_image = models.URLField(blank=True, null=True)
    
    # Role and Status
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.BUYER
    )
    status = models.CharField(
        max_length=30,
        choices=UserStatus.choices,
        default=UserStatus.PENDING_VERIFICATION
    )
    
    # Plan & Subscriptions
    plan = models.ForeignKey(
        'plans.Plan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="The pricing/feature plan assigned to this user."
    )
    
    # KYC Information
    kyc_status = models.CharField(
        max_length=20,
        choices=KYCStatus.choices,
        default=KYCStatus.NOT_STARTED
    )
    kyc_data = models.JSONField(null=True, blank=True)  # Encrypted in production
    kyc_submitted_at = models.DateTimeField(null=True, blank=True)
    kyc_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Contact Information
    address = models.JSONField(null=True, blank=True)  # Structured address data
    
    # Two-Factor Authentication
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=64, null=True, blank=True)  # Encrypted
    
    # Security
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, null=True, blank=True)
    password_reset_token = models.CharField(max_length=100, null=True, blank=True)
    password_reset_expires = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    lockout_until = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    last_login_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Django admin fields
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role', 'status']),
            models.Index(fields=['kyc_status']),
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return user's full name."""
        return f'{self.first_name} {self.last_name}'.strip() or self.email

    @property
    def is_verified(self):
        """Check if user is verified (email + KYC)."""
        return self.email_verified and self.kyc_status == KYCStatus.APPROVED

    @property
    def can_transact(self):
        """Check if user can participate in escrow transactions."""
        return (
            self.status == UserStatus.ACTIVE and
            self.email_verified and
            self.kyc_status == KYCStatus.APPROVED
        )

    def is_locked_out(self):
        """Check if user is currently locked out."""
        if self.lockout_until:
            return timezone.now() < self.lockout_until
        return False

    def record_login_attempt(self, success):
        """Record login attempt and handle lockout logic."""
        if success:
            self.failed_login_attempts = 0
            self.lockout_until = None
            self.last_login_at = timezone.now()
        else:
            self.failed_login_attempts += 1
            if self.failed_login_attempts >= 5:
                # Lock out for 30 minutes after 5 failed attempts
                self.lockout_until = timezone.now() + timezone.timedelta(minutes=30)
        self.save(update_fields=['failed_login_attempts', 'lockout_until', 'last_login_at'])


class UserSession(models.Model):
    """Track user sessions for security and audit."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    refresh_token_jti = models.CharField(max_length=255, unique=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.CharField(max_length=500, blank=True)
    device_info = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'user_sessions'
        ordering = ['-last_used_at']

    def __str__(self):
        return f'{self.user.email} - {self.ip_address}'

    def is_valid(self):
        """Check if session is still valid."""
        return self.is_active and timezone.now() < self.expires_at

    def revoke(self):
        """Revoke this session."""
        self.is_active = False
        self.save(update_fields=['is_active'])
