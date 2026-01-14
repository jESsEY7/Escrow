"""
Transaction and Wallet models for the Escrow Platform.
Handles payments, wallets, and ledger entries.
"""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from apps.core.enums import (
    TransactionType, TransactionStatus, PaymentMethod, Currency
)


class Wallet(models.Model):
    """
    Segregated escrow wallet.
    Each escrow has its own wallet for fund isolation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escrow = models.OneToOneField(
        'escrow.EscrowAccount',
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    
    # Balances
    balance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    held_balance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    released_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallets'

    def __str__(self):
        return f'Wallet for {self.escrow.reference_code}'

    @property
    def available_balance(self):
        """Balance available for release."""
        return self.balance - self.held_balance

    @property
    def is_fully_funded(self):
        """Check if wallet is fully funded for escrow amount."""
        return self.balance >= self.escrow.total_amount

    def deposit(self, amount, transaction=None):
        """Add funds to wallet."""
        if amount <= 0:
            raise ValueError('Deposit amount must be positive')
        self.balance += Decimal(str(amount))
        self.save(update_fields=['balance', 'updated_at'])

    def hold(self, amount):
        """Hold funds (prevent release until cleared)."""
        if amount > self.available_balance:
            raise ValueError('Insufficient available balance')
        self.held_balance += Decimal(str(amount))
        self.save(update_fields=['held_balance', 'updated_at'])

    def release(self, amount):
        """Release funds from held balance."""
        amount = Decimal(str(amount))
        if amount > self.balance:
            raise ValueError('Insufficient balance')
        self.balance -= amount
        self.released_amount += amount
        if self.held_balance >= amount:
            self.held_balance -= amount
        self.save(update_fields=['balance', 'held_balance', 'released_amount', 'updated_at'])

    def refund(self, amount):
        """Refund funds from wallet."""
        amount = Decimal(str(amount))
        if amount > self.balance:
            raise ValueError('Insufficient balance for refund')
        self.balance -= amount
        self.save(update_fields=['balance', 'updated_at'])


class Transaction(models.Model):
    """
    Transaction ledger entry.
    Immutable record of all financial movements.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    escrow = models.ForeignKey(
        'escrow.EscrowAccount',
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    milestone = models.ForeignKey(
        'escrow.Milestone',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    
    # Transaction Details
    type = models.CharField(
        max_length=30,
        choices=TransactionType.choices,
        db_index=True
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        db_index=True
    )
    
    # Payment Details
    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
        null=True,
        blank=True
    )
    external_reference = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True
    )
    payment_provider = models.CharField(max_length=50, null=True, blank=True)
    payment_details = models.JSONField(null=True, blank=True)
    
    # Recipient (for releases/refunds)
    recipient = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='received_transactions'
    )
    recipient_account = models.JSONField(null=True, blank=True)  # Bank details, etc.
    
    # Initiator
    initiated_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='initiated_transactions'
    )
    
    # Fees
    fee_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00')
    )
    fee_type = models.CharField(max_length=50, null=True, blank=True)
    
    # Idempotency
    idempotency_key = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )
    
    # Metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(null=True, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['escrow', 'type']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['external_reference']),
            models.Index(fields=['idempotency_key']),
        ]

    def __str__(self):
        return f'{self.type} - {self.amount} {self.currency}'

    @property
    def is_completed(self):
        return self.status == TransactionStatus.COMPLETED

    @property
    def is_pending(self):
        return self.status == TransactionStatus.PENDING

    @property
    def can_retry(self):
        return (
            self.status == TransactionStatus.FAILED and
            self.retry_count < 3
        )

    def complete(self):
        """Mark transaction as completed."""
        self.status = TransactionStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

    def fail(self, error_message=None):
        """Mark transaction as failed."""
        self.status = TransactionStatus.FAILED
        self.failed_at = timezone.now()
        if error_message:
            self.error_message = error_message
        self.save(update_fields=['status', 'failed_at', 'error_message', 'updated_at'])

    def reverse(self):
        """Reverse a completed transaction."""
        if self.status != TransactionStatus.COMPLETED:
            raise ValueError('Only completed transactions can be reversed')
        self.status = TransactionStatus.REVERSED
        self.save(update_fields=['status', 'updated_at'])


class PaymentIntent(models.Model):
    """
    Payment intent for tracking pending payments.
    Used for webhook reconciliation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escrow = models.ForeignKey(
        'escrow.EscrowAccount',
        on_delete=models.CASCADE,
        related_name='payment_intents'
    )
    
    # External provider reference
    provider = models.CharField(max_length=50)  # 'stripe', 'mpesa', etc.
    provider_intent_id = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Payment details
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=3)
    payment_method = models.CharField(max_length=30, choices=PaymentMethod.choices)
    
    # Status
    status = models.CharField(max_length=30, default='pending')
    
    # Webhook data
    webhook_received = models.BooleanField(default=False)
    webhook_data = models.JSONField(null=True, blank=True)
    
    # Linked transaction
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_intent'
    )
    
    # Timestamps
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_intents'
        indexes = [
            models.Index(fields=['provider_intent_id']),
            models.Index(fields=['escrow', 'status']),
        ]

    def __str__(self):
        return f'{self.provider} - {self.amount} {self.currency}'


class FeeSchedule(models.Model):
    """
    Platform fee schedule.
    Can be customized per escrow type or amount tier.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Fee structure
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    fixed_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    minimum_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    maximum_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Applicability
    escrow_type = models.CharField(
        max_length=30,
        null=True,
        blank=True
    )
    min_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True
    )
    max_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True
    )
    currency = models.CharField(max_length=3, default='USD')
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fee_schedules'
        ordering = ['percentage']

    def __str__(self):
        return f'{self.name} - {self.percentage}%'

    def calculate_fee(self, amount):
        """Calculate fee for given amount."""
        amount = Decimal(str(amount))
        fee = (amount * self.percentage / 100) + self.fixed_fee
        
        if self.minimum_fee:
            fee = max(fee, self.minimum_fee)
        if self.maximum_fee:
            fee = min(fee, self.maximum_fee)
        
        return fee.quantize(Decimal('0.01'))


class LedgerEntry(models.Model):
    """
    Double-entry accounting ledger.
    Tracks every financial movement immutably.
    """
    id = models.BigAutoField(primary_key=True)
    escrow = models.ForeignKey(
        'escrow.EscrowAccount', 
        on_delete=models.PROTECT,
        related_name='ledger_entries'
    )
    account = models.ForeignKey(
        'users.User', 
        on_delete=models.PROTECT,
        related_name='ledger_entries'
    )
    
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="Positive for Credit, Negative for Debit"
    )
    entry_type = models.CharField(
        max_length=50, 
        choices=[
            ('funding', 'Funding'),
            ('payout', 'Payout'),
            ('fee_collection', 'Fee Collection'),
            ('refund', 'Refund')
        ]
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'ledger_entries'
        indexes = [
            models.Index(fields=['escrow', 'entry_type']),
            models.Index(fields=['account', 'created_at']),
        ]

    def __str__(self):
        return f"{self.entry_type}: {self.amount} for {self.escrow.reference_code}"
