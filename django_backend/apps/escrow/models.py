"""
Escrow models for the Escrow Platform.
Core escrow account and milestone management.
"""
import uuid
import secrets
import string
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.core.enums import (
    EscrowStatus, EscrowType, MilestoneStatus, Currency
)


def generate_reference_code():
    """Generate a unique 12-character reference code."""
    chars = string.ascii_uppercase + string.digits
    return 'ESC-' + ''.join(secrets.choice(chars) for _ in range(8))


class EscrowAccount(models.Model):
    """
    Core escrow account model.
    Represents a single escrow transaction between buyer and seller.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_code = models.CharField(
        max_length=20, 
        unique=True, 
        db_index=True,
        default=generate_reference_code
    )
    
    # Participants
    buyer = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='escrows_as_buyer'
    )
    seller = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='escrows_as_seller'
    )
    arbitrator = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escrows_as_arbitrator'
    )
    
    # Status
    status = models.CharField(
        max_length=30,
        choices=EscrowStatus.choices,
        default=EscrowStatus.CREATED,
        db_index=True
    )
    previous_status = models.CharField(
        max_length=30,
        choices=EscrowStatus.choices,
        null=True,
        blank=True
    )
    
    # Transaction Details
    title = models.CharField(max_length=255)
    description = models.TextField()
    escrow_type = models.CharField(
        max_length=30,
        choices=EscrowType.choices,
        default=EscrowType.GENERAL
    )
    
    # Financial
    total_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD
    )
    platform_fee_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('2.50')  # Default if not overridden by Plan/FeeEngine
    )
    fee_applied = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Actual fee amount calculated at creation."
    )
    
    # Terms and Conditions
    terms = models.JSONField(default=dict)
    inspection_period_days = models.PositiveIntegerField(default=3)
    auto_release_days = models.PositiveIntegerField(default=14)
    auto_release_at = models.DateTimeField(null=True, blank=True, help_text="When funds unlock automatically.")
    
    # Automation
    conditions = models.JSONField(default=dict)  # Release conditions
    automation_enabled = models.BooleanField(default=True)
    
    # Timeline
    expires_at = models.DateTimeField()
    funded_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'escrow_accounts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference_code']),
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f'{self.reference_code} - {self.title}'

    @property
    def platform_fee(self):
        """Calculate platform fee amount."""
        return (self.total_amount * self.platform_fee_percent / 100).quantize(Decimal('0.01'))

    @property
    def net_amount(self):
        """Amount after platform fee deduction."""
        return self.total_amount - self.platform_fee

    @property
    def is_active(self):
        """Check if escrow is in an active state."""
        return self.status in [
            EscrowStatus.CREATED,
            EscrowStatus.FUNDED,
            EscrowStatus.IN_VERIFICATION,
            EscrowStatus.MILESTONE_PENDING,
            EscrowStatus.PARTIALLY_RELEASED,
            EscrowStatus.DISPUTED,
        ]

    @property
    def is_funded(self):
        """Check if escrow has been funded."""
        return self.funded_at is not None

    @property
    def is_expired(self):
        """Check if escrow has expired."""
        return timezone.now() > self.expires_at and self.status == EscrowStatus.CREATED

    @property
    def release_pending_milestones(self):
        """Get milestones pending release."""
        return self.milestones.filter(status=MilestoneStatus.APPROVED)

    @property
    def progress_percentage(self):
        """Calculate completion progress based on milestones."""
        total = self.milestones.count()
        if total == 0:
            return 0
        completed = self.milestones.filter(status=MilestoneStatus.RELEASED).count()
        return int((completed / total) * 100)

    def can_transition_to(self, new_status):
        """Check if transition to new status is valid."""
        from apps.escrow.state_machine import EscrowStateMachine
        return EscrowStateMachine.can_transition(self.status, new_status)

    def transition_to(self, new_status, actor=None):
        """Transition to a new status."""
        from apps.escrow.state_machine import EscrowStateMachine
        return EscrowStateMachine.transition(self, new_status, actor)


class Milestone(models.Model):
    """
    Milestone model for tracking escrow progress.
    Each milestone represents a deliverable or checkpoint.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escrow = models.ForeignKey(
        EscrowAccount,
        on_delete=models.CASCADE,
        related_name='milestones'
    )
    
    # Details
    title = models.CharField(max_length=255)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)
    
    # Financial
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=MilestoneStatus.choices,
        default=MilestoneStatus.PENDING
    )
    
    # Automation conditions
    conditions = models.JSONField(default=dict)
    due_date = models.DateTimeField(null=True, blank=True)
    
    # Completion tracking
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_notes = models.TextField(blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_milestones'
    )
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    
    # Deliverables
    deliverables = models.JSONField(default=list)  # List of deliverable items
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'milestones'
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['escrow', 'status']),
            models.Index(fields=['escrow', 'order']),
        ]

    def __str__(self):
        return f'{self.escrow.reference_code} - {self.title}'

    @property
    def is_complete(self):
        """Check if milestone is complete."""
        return self.status == MilestoneStatus.RELEASED

    @property
    def is_overdue(self):
        """Check if milestone is overdue."""
        if not self.due_date:
            return False
        return (
            timezone.now() > self.due_date and
            self.status not in [MilestoneStatus.RELEASED, MilestoneStatus.APPROVED]
        )

    def submit(self, notes=''):
        """Mark milestone as submitted for review."""
        self.status = MilestoneStatus.SUBMITTED
        self.submitted_at = timezone.now()
        self.submitted_notes = notes
        self.save()

    def approve(self, approved_by):
        """Approve milestone."""
        self.status = MilestoneStatus.APPROVED
        self.approved_at = timezone.now()
        self.approved_by = approved_by
        self.save()

    def reject(self, reason):
        """Reject milestone."""
        self.status = MilestoneStatus.REJECTED
        self.rejected_at = timezone.now()
        self.rejection_reason = reason
        self.save()

    def release(self):
        """Mark milestone as released (funds transferred)."""
        self.status = MilestoneStatus.RELEASED
        self.released_at = timezone.now()
        self.save()


class EscrowDocument(models.Model):
    """Documents attached to escrow (contracts, receipts, etc.)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escrow = models.ForeignKey(
        EscrowAccount,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    uploaded_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True
    )
    
    # File details
    name = models.CharField(max_length=255)
    file_url = models.URLField()
    file_type = models.CharField(max_length=50)
    file_size = models.PositiveIntegerField()  # in bytes
    file_hash = models.CharField(max_length=64)  # SHA-256 for integrity
    
    # Metadata
    description = models.TextField(blank=True)
    is_contract = models.BooleanField(default=False)
    is_signed = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'escrow_documents'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.escrow.reference_code} - {self.name}'


class EscrowInvitation(models.Model):
    """Invitations for users to join an escrow."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escrow = models.ForeignKey(
        EscrowAccount,
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    
    # Invitation details
    email = models.EmailField()
    role = models.CharField(max_length=20)  # 'seller' or 'buyer'
    token = models.CharField(max_length=100, unique=True)
    
    # Status
    is_accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_invitations'
    )
    
    # Expiry
    expires_at = models.DateTimeField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'escrow_invitations'

    def __str__(self):
        return f'Invitation to {self.email} for {self.escrow.reference_code}'

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_accepted and not self.is_expired
