"""
Notification models for the Escrow Platform.
Multi-channel notification system with delivery tracking.
"""
import uuid
from django.db import models
from django.utils import timezone


class NotificationType(models.TextChoices):
    """Types of notifications in the system."""
    # Escrow lifecycle
    ESCROW_CREATED = 'escrow_created', 'Escrow Created'
    ESCROW_FUNDED = 'escrow_funded', 'Escrow Funded'
    ESCROW_CANCELLED = 'escrow_cancelled', 'Escrow Cancelled'
    
    # Milestone events
    MILESTONE_SUBMITTED = 'milestone_submitted', 'Milestone Submitted'
    MILESTONE_APPROVED = 'milestone_approved', 'Milestone Approved'
    MILESTONE_REJECTED = 'milestone_rejected', 'Milestone Rejected'
    MILESTONE_RELEASED = 'milestone_released', 'Funds Released'
    
    # Dispute events
    DISPUTE_RAISED = 'dispute_raised', 'Dispute Raised'
    DISPUTE_RESPONSE = 'dispute_response', 'Dispute Response'
    DISPUTE_RESOLVED = 'dispute_resolved', 'Dispute Resolved'
    
    # Payment events
    PAYMENT_RECEIVED = 'payment_received', 'Payment Received'
    PAYMENT_FAILED = 'payment_failed', 'Payment Failed'
    PAYOUT_INITIATED = 'payout_initiated', 'Payout Initiated'
    PAYOUT_COMPLETED = 'payout_completed', 'Payout Completed'
    
    # System events
    KYC_APPROVED = 'kyc_approved', 'KYC Approved'
    KYC_REJECTED = 'kyc_rejected', 'KYC Rejected'
    REMINDER = 'reminder', 'Reminder'
    SECURITY_ALERT = 'security_alert', 'Security Alert'


class NotificationChannel(models.TextChoices):
    """Delivery channels for notifications."""
    EMAIL = 'email', 'Email'
    SMS = 'sms', 'SMS'
    PUSH = 'push', 'Push Notification'
    IN_APP = 'in_app', 'In-App'
    WEBHOOK = 'webhook', 'Webhook'


class NotificationPriority(models.TextChoices):
    """Priority levels for notifications."""
    LOW = 'low', 'Low'
    NORMAL = 'normal', 'Normal'
    HIGH = 'high', 'High'
    URGENT = 'urgent', 'Urgent'


class Notification(models.Model):
    """
    Core notification model.
    Tracks all notifications sent to users with delivery status.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    # Content
    type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        db_index=True
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    action_url = models.URLField(blank=True)
    
    # Priority
    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL
    )
    
    # Related entity (for deep linking)
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.UUIDField(null=True, blank=True)
    
    # Delivery tracking
    channels = models.JSONField(default=list)  # ['email', 'sms', 'in_app']
    delivery_status = models.JSONField(default=dict)  # {'email': 'sent', 'sms': 'failed'}
    
    # Read status
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['user', 'type']),
            models.Index(fields=['entity_type', 'entity_id']),
        ]

    def __str__(self):
        return f'{self.type} for {self.user.email}'

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])

    def update_delivery_status(self, channel: str, status: str, error: str = None):
        """Update delivery status for a specific channel."""
        self.delivery_status[channel] = {
            'status': status,
            'timestamp': timezone.now().isoformat(),
            'error': error,
        }
        self.save(update_fields=['delivery_status', 'updated_at'])


class NotificationPreference(models.Model):
    """
    User notification preferences.
    Controls which notifications users receive on which channels.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Channel toggles
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    
    # Per-type preferences (notification_type: [channels])
    type_preferences = models.JSONField(default=dict)
    
    # Quiet hours (no non-urgent notifications)
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')
    
    # Digest preferences
    email_digest = models.BooleanField(default=False)
    digest_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ],
        default='daily'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_preferences'

    def __str__(self):
        return f'Preferences for {self.user.email}'

    def get_channels_for_type(self, notification_type: str) -> list:
        """Get enabled channels for a notification type."""
        channels = []
        
        # Check type-specific preferences first
        if notification_type in self.type_preferences:
            return self.type_preferences[notification_type]
        
        # Fall back to global preferences
        if self.email_enabled:
            channels.append('email')
        if self.sms_enabled:
            channels.append('sms')
        if self.push_enabled:
            channels.append('push')
        
        # Always include in-app
        channels.append('in_app')
        
        return channels


class NotificationTemplate(models.Model):
    """
    Notification templates for consistent messaging.
    Supports variable interpolation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Identification
    type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        unique=True
    )
    name = models.CharField(max_length=100)
    
    # Templates per channel
    email_subject = models.CharField(max_length=255)
    email_body_html = models.TextField()
    email_body_text = models.TextField()
    
    sms_body = models.CharField(max_length=160)  # SMS character limit
    
    push_title = models.CharField(max_length=100)
    push_body = models.CharField(max_length=255)
    
    in_app_title = models.CharField(max_length=255)
    in_app_body = models.TextField()
    
    # Template variables (for documentation)
    available_variables = models.JSONField(default=list)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_templates'

    def __str__(self):
        return f'{self.name} ({self.type})'

    def render(self, channel: str, context: dict) -> dict:
        """Render template for a specific channel with context."""
        from string import Template
        
        if channel == 'email':
            subject = Template(self.email_subject).safe_substitute(context)
            body_html = Template(self.email_body_html).safe_substitute(context)
            body_text = Template(self.email_body_text).safe_substitute(context)
            return {'subject': subject, 'body_html': body_html, 'body_text': body_text}
        
        elif channel == 'sms':
            body = Template(self.sms_body).safe_substitute(context)
            return {'body': body}
        
        elif channel == 'push':
            title = Template(self.push_title).safe_substitute(context)
            body = Template(self.push_body).safe_substitute(context)
            return {'title': title, 'body': body}
        
        elif channel == 'in_app':
            title = Template(self.in_app_title).safe_substitute(context)
            body = Template(self.in_app_body).safe_substitute(context)
            return {'title': title, 'body': body}
        
        return {}
