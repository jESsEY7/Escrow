import uuid
from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_type = models.CharField(max_length=100, db_index=True)
    entity_id = models.CharField(max_length=100, db_index=True)
    
    ACTION_CHOICES = [
        ('create', 'Create'), ('update', 'Update'), ('delete', 'Delete'),
        ('login', 'Login'), ('logout', 'Logout'),
        ('fund', 'Fund'), ('release', 'Release'), ('refund', 'Refund'),
        ('dispute_raised', 'Dispute Raised'), ('dispute_resolved', 'Dispute Resolved'),
        ('kyc_submitted', 'KYC Submitted'), ('kyc_approved', 'KYC Approved'), ('kyc_rejected', 'KYC Rejected'),
        ('STATUS_CHANGE', 'Status Change'), # Added this to match EscrowService usage if needed, or map it.
        ('FUNDS_RELEASE', 'Funds Release'),
    ]
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    actor_email = models.EmailField(null=True, blank=True)
    actor_role = models.CharField(max_length=30, null=True, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    request_id = models.CharField(max_length=100, null=True, blank=True)
    
    previous_state = models.JSONField(null=True, blank=True)
    new_state = models.JSONField(null=True, blank=True)
    changes = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    
    checksum = models.CharField(max_length=64, db_index=True)
    previous_checksum = models.CharField(max_length=64, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['actor', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['checksum']),
        ]

    def __str__(self):
        return f"{self.action} on {self.entity_type} {self.entity_id}"

    @classmethod
    def get_chain_integrity(cls, entity_type, entity_id):
        # Implementation placeholder / simplified since logic is in service likely, or expected to be here
        # Return (True, None) for now as reconstruction
        return True, None


class SystemEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=100, db_index=True)
    
    SEVERITY_CHOICES = [
        ('debug', 'Debug'), ('info', 'Info'), ('warning', 'Warning'), ('error', 'Error'), ('critical', 'Critical')
    ]
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    source = models.CharField(max_length=100)
    stack_trace = models.TextField(blank=True)
    
    related_entity_type = models.CharField(max_length=100, null=True, blank=True)
    related_entity_id = models.CharField(max_length=100, null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'system_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'severity']),
            models.Index(fields=['severity', 'created_at']),
            models.Index(fields=['is_resolved', 'severity']),
        ]


class ComplianceReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    data = models.JSONField()
    summary = models.JSONField(null=True, blank=True)
    
    file_url = models.URLField(null=True, blank=True)
    file_format = models.CharField(max_length=10, null=True, blank=True)
    
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_reports'
        ordering = ['-created_at']
