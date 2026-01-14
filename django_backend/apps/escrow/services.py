from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from decimal import Decimal
from apps.escrow.models import EscrowAccount
from apps.core.enums import EscrowStatus, TransactionType
from apps.audit.services.audit_service import AuditService
from apps.transactions.models import Transaction
from apps.plans.services import SLAEngine, FeeEngine
from apps.notifications.services import NotificationService, notify_escrow_funded, NotificationType
import logging

logger = logging.getLogger(__name__)

class EscrowService:
    """
    Service for handling Escrow state transitions concurrently and safely.
    Acts as the "Brain" of the operation.
    """

    ALLOWED_TRANSITIONS = {
        EscrowStatus.CREATED: [EscrowStatus.FUNDED, EscrowStatus.CANCELLED],
        EscrowStatus.FUNDED: [EscrowStatus.IN_VERIFICATION, EscrowStatus.MILESTONE_PENDING, EscrowStatus.PARTIALLY_RELEASED, EscrowStatus.DISPUTED, EscrowStatus.CANCELLED],
        EscrowStatus.MILESTONE_PENDING: [EscrowStatus.PARTIALLY_RELEASED, EscrowStatus.DISPUTED, EscrowStatus.FULLY_RELEASED],
        EscrowStatus.PARTIALLY_RELEASED: [EscrowStatus.FULLY_RELEASED, EscrowStatus.DISPUTED],
        EscrowStatus.DISPUTED: [EscrowStatus.RESOLVED, EscrowStatus.FULLY_RELEASED, EscrowStatus.REFUNDED],
        EscrowStatus.RESOLVED: [EscrowStatus.FULLY_RELEASED, EscrowStatus.REFUNDED, EscrowStatus.CLOSED],
        EscrowStatus.FULLY_RELEASED: [EscrowStatus.CLOSED],
        EscrowStatus.REFUNDED: [EscrowStatus.CLOSED],
        EscrowStatus.CLOSED: [],
        EscrowStatus.CANCELLED: [],
    }

    @staticmethod
    def transition_status(escrow_id, next_status, actor=None, reason=None):
        """
        Transition escrow to a new status atomically.
        """
        with transaction.atomic():
            # 1. Fetch Request with Lock
            escrow = EscrowAccount.objects.select_for_update().get(id=escrow_id)
            old_status = escrow.status
            
            # 2. Guard: Validate Transition
            if next_status not in EscrowService.ALLOWED_TRANSITIONS.get(old_status, []):
                raise ValueError(f"Invalid transition from {old_status} to {next_status}")

            # 3. Apply Plan-Based Logic
            if next_status == EscrowStatus.FUNDED:
                # Calculate SLA and Auto-Release
                sla_hours = SLAEngine.get_sla_hours(escrow.buyer)
                escrow.auto_release_at = timezone.now() + timezone.timedelta(hours=sla_hours)
                escrow.funded_at = timezone.now()
                
                # Lock Fee (if not already applied)
                if not escrow.fee_applied:
                    fee_percent = FeeEngine.get_fee_percent(escrow.seller)
                    escrow.platform_fee_percent = fee_percent
                    escrow.fee_applied = (escrow.total_amount * fee_percent / 100).quantize(Decimal('0.01'))
                
                # Notify Parties
                notify_escrow_funded(escrow)
            
            elif next_status == EscrowStatus.CLOSED:
                escrow.closed_at = timezone.now()

            # 4. Update Database
            escrow.status = next_status
            escrow.save()

            # 5. Immutable Audit Log
            AuditService.log_action(
                entity_type='escrow',
                entity_id=escrow.id,
                action='STATUS_CHANGE',
                actor=actor,
                previous_state={'status': old_status},
                new_state={'status': next_status},
                metadata={'reason': reason}
            )
            
            logger.info(f"Escrow {escrow.reference_code} moved from {old_status} to {next_status}")
            return escrow

    @staticmethod
    def release_funds(escrow_id, amount=None, actor=None):
        """
        Release funds from escrow wallet to seller.
        """
        with transaction.atomic():
            escrow = EscrowAccount.objects.select_for_update().get(id=escrow_id)
            wallet = escrow.wallet
            
            release_amount = amount if amount else wallet.available_balance
            
            if release_amount > wallet.available_balance:
                raise ValueError("Insufficient available balance for release")

            # Update Wallet
            wallet.release(release_amount)
            
            # Create Transaction Record
            Transaction.objects.create(
                escrow=escrow,
                wallet=wallet,
                type=TransactionType.RELEASE,
                amount=release_amount,
                currency=escrow.currency,
                recipient=escrow.seller,
                initiated_by=actor if actor else escrow.buyer,
                status='completed',
                completed_at=timezone.now()
            )
            
            # Update Status if fully released
            if wallet.balance == 0:
                EscrowService.transition_status(escrow.id, EscrowStatus.FULLY_RELEASED, actor=actor, reason="Funds Fully Released")

            AuditService.log_action(
                entity_type='escrow',
                entity_id=escrow.id,
                action='FUNDS_RELEASE',
                actor=actor,
                new_value={'amount': str(release_amount), 'currency': escrow.currency},
                metadata={'initiated_by': str(actor) if actor else 'system'}
            )
            
            # Notify Seller
            NotificationService.send(
                user=escrow.seller,
                notification_type='funds_released',
                context={
                    'amount': str(release_amount),
                    'currency': escrow.currency,
                    'escrow_title': escrow.title,
                },
                entity_type='EscrowAccount',
                entity_id=escrow.id
            )
            
            return True
