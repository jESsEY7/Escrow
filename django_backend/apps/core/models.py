"""
Webhook event model for tracking incoming webhooks.
"""
import uuid
from django.db import models


class WebhookEventStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    IGNORED = 'ignored', 'Ignored'


class WebhookEvent(models.Model):
    """
    Tracks incoming webhook events for audit and replay.
    Ensures idempotent processing of payment callbacks.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Source identification
    provider = models.CharField(max_length=50, db_index=True)  # mpesa, stripe, etc.
    event_type = models.CharField(max_length=100, db_index=True)
    
    # Payload
    payload = models.JSONField()
    headers = models.JSONField(default=dict)
    signature = models.CharField(max_length=255, blank=True)
    
    # Processing status
    status = models.CharField(
        max_length=20,
        choices=WebhookEventStatus.choices,
        default=WebhookEventStatus.PENDING,
        db_index=True
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    
    # Idempotency
    idempotency_key = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Related entity (after processing)
    related_entity_type = models.CharField(max_length=50, blank=True)
    related_entity_id = models.UUIDField(null=True, blank=True)
    
    # Request metadata
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
    # Timestamps
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'webhook_events'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['provider', 'event_type']),
            models.Index(fields=['status', 'retry_count']),
        ]

    def __str__(self):
        return f'{self.provider}:{self.event_type} - {self.status}'

    def mark_processing(self):
        """Mark webhook as being processed."""
        from django.utils import timezone
        self.status = WebhookEventStatus.PROCESSING
        self.save(update_fields=['status', 'updated_at'])

    def mark_completed(self, entity_type: str = '', entity_id: str = None):
        """Mark webhook as successfully processed."""
        from django.utils import timezone
        self.status = WebhookEventStatus.COMPLETED
        self.processed_at = timezone.now()
        self.related_entity_type = entity_type
        self.related_entity_id = entity_id
        self.save(update_fields=[
            'status', 'processed_at', 'related_entity_type', 
            'related_entity_id', 'updated_at'
        ])

    def mark_failed(self, error_message: str):
        """Mark webhook as failed."""
        self.status = WebhookEventStatus.FAILED
        self.error_message = error_message
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'retry_count', 'updated_at'])

    def can_retry(self) -> bool:
        """Check if webhook can be retried."""
        return (
            self.status == WebhookEventStatus.FAILED and
            self.retry_count < self.max_retries
        )

    @classmethod
    def create_from_request(cls, provider: str, request, event_type: str = ''):
        """Create webhook event from Django request."""
        import json
        import hashlib
        
        # Parse payload
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            payload = {'raw': request.body.decode('utf-8', errors='replace')}
        
        # Generate idempotency key
        body_hash = hashlib.sha256(request.body).hexdigest()[:32]
        idempotency_key = f"{provider}:{body_hash}"
        
        # Check for duplicate
        existing = cls.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing, False  # Already exists
        
        # Extract headers
        headers = {
            key: value for key, value in request.META.items()
            if key.startswith('HTTP_')
        }
        
        # Get IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            source_ip = x_forwarded_for.split(',')[0].strip()
        else:
            source_ip = request.META.get('REMOTE_ADDR')
        
        webhook = cls.objects.create(
            provider=provider,
            event_type=event_type,
            payload=payload,
            headers=headers,
            idempotency_key=idempotency_key,
            source_ip=source_ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )
        
        return webhook, True  # Newly created


class ContactRequest(models.Model):
    """
    Model for storing contact form submissions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    transaction_type = models.CharField(max_length=50)
    transaction_value = models.CharField(max_length=100)
    message = models.TextField()
    
    is_resolved = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contact_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.first_name} {self.last_name} - {self.transaction_type}'
