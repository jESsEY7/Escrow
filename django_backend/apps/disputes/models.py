"""
Dispute and Arbitration models for the Escrow Platform.
Handles dispute lifecycle and resolution.
"""
import uuid
import hashlib
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.core.enums import DisputeStatus, DisputeReason, RulingType


class Dispute(models.Model):
    """
    Dispute model for handling escrow conflicts.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escrow = models.ForeignKey(
        'escrow.EscrowAccount',
        on_delete=models.PROTECT,
        related_name='disputes'
    )
    
    # Dispute Details
    reason = models.CharField(
        max_length=30,
        choices=DisputeReason.choices
    )
    description = models.TextField()
    
    # Parties
    raised_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='disputes_raised'
    )
    against = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='disputes_against'
    )
    
    # Status
    status = models.CharField(
        max_length=30,
        choices=DisputeStatus.choices,
        default=DisputeStatus.OPEN,
        db_index=True
    )
    
    # Arbitration
    priority_score = models.IntegerField(default=0, help_text="Standard=0, Pro=10, Enterprise=100")
    evidence_folder_url = models.URLField(null=True, blank=True)

    assigned_arbitrator = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='arbitrated_disputes'
    )
    assigned_at = models.DateTimeField(null=True, blank=True)
    
    # Timeline
    response_deadline = models.DateTimeField()
    resolution_deadline = models.DateTimeField()
    escalation_deadline = models.DateTimeField(null=True, blank=True)
    
    # Resolution
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_summary = models.TextField(blank=True)
    
    # Amount in dispute
    disputed_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Metadata
    metadata = models.JSONField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'disputes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['escrow', 'status']),
            models.Index(fields=['assigned_arbitrator', 'status']),
            models.Index(fields=['status', 'resolution_deadline']),
        ]

    def __str__(self):
        return f'Dispute #{self.id} - {self.reason}'

    @property
    def is_open(self):
        return self.status in [DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW, DisputeStatus.AWAITING_EVIDENCE]

    @property
    def is_resolved(self):
        return self.status in [DisputeStatus.RESOLVED, DisputeStatus.CLOSED]

    @property
    def is_overdue(self):
        return timezone.now() > self.resolution_deadline and not self.is_resolved

    @property
    def days_until_deadline(self):
        if self.is_resolved:
            return 0
        delta = self.resolution_deadline - timezone.now()
        return max(0, delta.days)

    def assign_arbitrator(self, arbitrator):
        """Assign an arbitrator to this dispute."""
        self.assigned_arbitrator = arbitrator
        self.assigned_at = timezone.now()
        self.status = DisputeStatus.ARBITRATION
        self.save()

    def escalate(self, reason=None):
        """Escalate dispute to admin."""
        self.status = DisputeStatus.ESCALATED
        if reason:
            self.metadata = self.metadata or {}
            self.metadata['escalation_reason'] = reason
        self.save()

    def resolve(self, summary):
        """Mark dispute as resolved."""
        self.status = DisputeStatus.RESOLVED
        self.resolved_at = timezone.now()
        self.resolution_summary = summary
        self.save()

    def close(self):
        """Close the dispute."""
        self.status = DisputeStatus.CLOSED
        if not self.resolved_at:
            self.resolved_at = timezone.now()
        self.save()


class DisputeResponse(models.Model):
    """
    Response to a dispute from the other party.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispute = models.ForeignKey(
        Dispute,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    
    # Responder
    responder = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='dispute_responses'
    )
    
    # Response content
    content = models.TextField()
    accepts_claim = models.BooleanField(null=True)  # True = accepts, False = rejects, None = partial
    counter_offer = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'dispute_responses'
        ordering = ['created_at']

    def __str__(self):
        return f'Response by {self.responder.email}'


class Evidence(models.Model):
    """
    Evidence submitted for a dispute.
    Files are hashed for integrity verification.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispute = models.ForeignKey(
        Dispute,
        on_delete=models.CASCADE,
        related_name='evidence'
    )
    
    # Submitter
    submitted_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='submitted_evidence'
    )
    
    # Evidence details
    title = models.CharField(max_length=255)
    description = models.TextField()
    evidence_type = models.CharField(max_length=50)  # 'document', 'image', 'video', 'text', 'link'
    
    # File (if applicable)
    file_url = models.URLField(null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    file_hash = models.CharField(max_length=64, null=True, blank=True)  # SHA-256
    
    # Text evidence
    text_content = models.TextField(blank=True)
    
    # Link evidence
    external_url = models.URLField(null=True, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_evidence'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'evidence'
        ordering = ['created_at']
        verbose_name_plural = 'Evidence'

    def __str__(self):
        return f'{self.title} - {self.evidence_type}'

    def compute_hash(self, file_content):
        """Compute SHA-256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()

    def verify_integrity(self, file_content):
        """Verify file integrity against stored hash."""
        if not self.file_hash:
            return None
        computed_hash = self.compute_hash(file_content)
        return computed_hash == self.file_hash


class ArbitrationDecision(models.Model):
    """
    Final arbitration decision for a dispute.
    Binding ruling that determines fund distribution.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispute = models.OneToOneField(
        Dispute,
        on_delete=models.PROTECT,
        related_name='decision'
    )
    
    # Arbitrator
    arbitrator = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='arbitration_decisions'
    )
    
    # Decision
    ruling = models.CharField(
        max_length=30,
        choices=RulingType.choices
    )
    reasoning = models.TextField()
    
    # Fund distribution
    buyer_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    seller_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Fees
    arbitration_fee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00')
    )
    fee_paid_by = models.CharField(
        max_length=20,
        choices=[('buyer', 'Buyer'), ('seller', 'Seller'), ('split', 'Split'), ('platform', 'Platform')],
        default='split'
    )
    
    # Status
    is_final = models.BooleanField(default=False)
    is_executed = models.BooleanField(default=False)
    executed_at = models.DateTimeField(null=True, blank=True)
    
    # Appeal
    can_appeal = models.BooleanField(default=True)
    appeal_deadline = models.DateTimeField(null=True, blank=True)
    
    # Supporting documents
    supporting_documents = models.JSONField(default=list)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'arbitration_decisions'

    def __str__(self):
        return f'Decision for Dispute #{self.dispute.id} - {self.ruling}'

    @property
    def total_amount(self):
        return self.buyer_amount + self.seller_amount

    def finalize(self):
        """Mark decision as final (no more appeals)."""
        self.is_final = True
        self.can_appeal = False
        self.save()

    def execute(self):
        """Execute the decision (trigger fund transfers)."""
        if not self.is_final:
            raise ValueError('Decision must be finalized before execution')
        if self.is_executed:
            raise ValueError('Decision has already been executed')
        
        self.is_executed = True
        self.executed_at = timezone.now()
        self.save()
        
        # Trigger fund distribution
        from apps.disputes.services import ArbitrationService
        ArbitrationService.execute_decision(self)


class DisputeTimeline(models.Model):
    """
    Timeline entries for dispute history.
    Tracks all actions and status changes.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispute = models.ForeignKey(
        Dispute,
        on_delete=models.CASCADE,
        related_name='timeline'
    )
    
    # Event details
    event_type = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Actor
    actor = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Metadata
    metadata = models.JSONField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'dispute_timeline'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.event_type} - {self.title}'
