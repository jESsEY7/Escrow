"""
Payment Service for the Escrow Platform.
Handles all payment-related operations.
"""
import uuid
from decimal import Decimal
from django.db import transaction as db_transaction
from django.utils import timezone
from apps.transactions.models import Transaction, Wallet, PaymentIntent
from apps.core.enums import TransactionType, TransactionStatus, PaymentMethod
from apps.core.exceptions import PaymentProcessingError, InsufficientFundsError
from apps.audit.services.audit_service import AuditService


class PaymentService:
    """
    Service for processing payments.
    """

    @classmethod
    @db_transaction.atomic
    def process_deposit(
        cls,
        escrow,
        amount: Decimal,
        payment_method: str,
        initiated_by,
        payment_details: dict = None,
    ):
        """
        Process a deposit into an escrow wallet.

        Args:
            escrow: EscrowAccount instance
            amount: Amount to deposit
            payment_method: Payment method used
            initiated_by: User initiating the payment
            payment_details: Additional payment details

        Returns:
            Transaction instance
        """
        wallet = escrow.wallet

        # Generate idempotency key
        idempotency_key = f"deposit_{escrow.id}_{uuid.uuid4()}"

        # Create transaction record
        transaction = Transaction.objects.create(
            escrow=escrow,
            wallet=wallet,
            type=TransactionType.DEPOSIT,
            amount=amount,
            currency=escrow.currency,
            status=TransactionStatus.PENDING,
            payment_method=payment_method,
            initiated_by=initiated_by,
            idempotency_key=idempotency_key,
            payment_details=payment_details,
            description=f"Deposit for escrow {escrow.reference_code}",
        )

        try:
            # In production, integrate with actual payment provider
            # For now, simulate successful payment
            cls._simulate_payment_processing(transaction, payment_method, payment_details)

            # Update wallet balance
            wallet.deposit(amount)

            # Mark transaction as complete
            transaction.complete()

            # Log to audit
            AuditService.log_action(
                entity_type='Transaction',
                entity_id=str(transaction.id),
                action='deposit',
                actor=initiated_by,
                new_state={
                    'amount': str(amount),
                    'status': TransactionStatus.COMPLETED,
                    'escrow_reference': escrow.reference_code,
                },
            )

            return transaction

        except Exception as e:
            transaction.fail(str(e))
            raise PaymentProcessingError(str(e))

    @classmethod
    @db_transaction.atomic
    def release_milestone(cls, escrow, milestone, released_by):
        """
        Release funds for a completed milestone.

        Args:
            escrow: EscrowAccount instance
            milestone: Milestone instance
            released_by: User triggering the release

        Returns:
            Transaction instance
        """
        wallet = escrow.wallet

        if wallet.balance < milestone.amount:
            raise InsufficientFundsError(
                f"Insufficient balance: {wallet.balance}, required: {milestone.amount}"
            )

        # Calculate platform fee for this milestone
        fee_percent = escrow.platform_fee_percent
        fee_amount = (milestone.amount * fee_percent / 100).quantize(Decimal('0.01'))
        net_amount = milestone.amount - fee_amount

        idempotency_key = f"release_{milestone.id}_{uuid.uuid4()}"

        # Create release transaction
        transaction = Transaction.objects.create(
            escrow=escrow,
            wallet=wallet,
            milestone=milestone,
            type=TransactionType.RELEASE,
            amount=net_amount,
            currency=escrow.currency,
            status=TransactionStatus.PENDING,
            initiated_by=released_by,
            recipient=escrow.seller,
            fee_amount=fee_amount,
            fee_type='platform_fee',
            idempotency_key=idempotency_key,
            description=f"Release for milestone: {milestone.title}",
        )

        try:
            # Process release (in production, trigger actual transfer)
            wallet.release(milestone.amount)

            # Mark transaction complete
            transaction.complete()

            # Create fee transaction if applicable
            if fee_amount > 0:
                Transaction.objects.create(
                    escrow=escrow,
                    wallet=wallet,
                    type=TransactionType.FEE,
                    amount=fee_amount,
                    currency=escrow.currency,
                    status=TransactionStatus.COMPLETED,
                    initiated_by=released_by,
                    description=f"Platform fee for milestone: {milestone.title}",
                    completed_at=timezone.now(),
                )

            AuditService.log_action(
                entity_type='Transaction',
                entity_id=str(transaction.id),
                action='release',
                actor=released_by,
                new_state={
                    'milestone': str(milestone.id),
                    'amount': str(net_amount),
                    'fee': str(fee_amount),
                    'recipient': escrow.seller.email,
                },
            )

            return transaction

        except Exception as e:
            transaction.fail(str(e))
            raise PaymentProcessingError(str(e))

    @classmethod
    @db_transaction.atomic
    def process_refund(cls, escrow, amount, refund_to, initiated_by, reason=''):
        """
        Process a refund from escrow.

        Args:
            escrow: EscrowAccount instance
            amount: Amount to refund
            refund_to: User to receive refund
            initiated_by: User initiating refund
            reason: Reason for refund

        Returns:
            Transaction instance
        """
        wallet = escrow.wallet

        if wallet.balance < amount:
            raise InsufficientFundsError(
                f"Insufficient balance for refund: {wallet.balance}, requested: {amount}"
            )

        idempotency_key = f"refund_{escrow.id}_{uuid.uuid4()}"

        transaction = Transaction.objects.create(
            escrow=escrow,
            wallet=wallet,
            type=TransactionType.REFUND,
            amount=amount,
            currency=escrow.currency,
            status=TransactionStatus.PENDING,
            initiated_by=initiated_by,
            recipient=refund_to,
            idempotency_key=idempotency_key,
            description=reason or f"Refund for escrow {escrow.reference_code}",
        )

        try:
            wallet.refund(amount)
            transaction.complete()

            AuditService.log_action(
                entity_type='Transaction',
                entity_id=str(transaction.id),
                action='refund',
                actor=initiated_by,
                new_state={
                    'amount': str(amount),
                    'recipient': refund_to.email,
                    'reason': reason,
                },
            )

            return transaction

        except Exception as e:
            transaction.fail(str(e))
            raise PaymentProcessingError(str(e))

    @classmethod
    def _simulate_payment_processing(cls, transaction, payment_method, payment_details):
        """
        Simulate payment processing.
        In production, this would integrate with actual payment providers.
        """
        # Generate fake external reference
        transaction.external_reference = f"sim_{uuid.uuid4().hex[:16]}"
        transaction.payment_provider = 'simulator'
        transaction.save()

        # Simulate processing delay (in real implementation, this would be async)
        import time
        time.sleep(0.1)

    @classmethod
    def get_transaction_history(cls, escrow, limit=50):
        """Get transaction history for an escrow."""
        return Transaction.objects.filter(
            escrow=escrow
        ).order_by('-created_at')[:limit]

    @classmethod
    def get_user_transactions(cls, user, limit=50):
        """Get all transactions for a user."""
        from django.db.models import Q
        return Transaction.objects.filter(
            Q(initiated_by=user) | Q(recipient=user)
        ).order_by('-created_at')[:limit]
