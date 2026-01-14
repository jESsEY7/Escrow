"""
Celery Beat scheduled tasks for escrow automation.
Handles time-based escrow transitions and reminders.
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task
def check_escrow_expirations():
    """
    Check for escrows that have expired and need to be cancelled.
    Runs every 15 minutes.
    """
    from apps.escrow.models import EscrowAccount
    from apps.escrow.state_machine import EscrowStateMachine
    from apps.core.enums import EscrowStatus
    
    now = timezone.now()
    
    # Find unfunded escrows past expiration
    expired_escrows = EscrowAccount.objects.filter(
        status=EscrowStatus.CREATED,
        expires_at__lt=now
    )
    
    cancelled_count = 0
    for escrow in expired_escrows:
        try:
            EscrowStateMachine.transition(
                escrow,
                EscrowStatus.CANCELLED,
                reason='Auto-cancelled: funding deadline expired'
            )
            cancelled_count += 1
            logger.info(f"Auto-cancelled escrow {escrow.reference_code}")
        except Exception as e:
            logger.exception(f"Failed to cancel escrow {escrow.reference_code}: {e}")
    
    logger.info(f"Escrow expiration check: cancelled {cancelled_count} escrows")
    return cancelled_count


@shared_task
def check_auto_releases():
    """
    Check for milestones eligible for auto-release.
    Auto-releases funds if buyer hasn't disputed within inspection period.
    Runs every hour.
    """
    from apps.escrow.models import EscrowAccount, Milestone
    from apps.escrow.state_machine import EscrowStateMachine
    from apps.core.enums import EscrowStatus, MilestoneStatus
    
    now = timezone.now()
    
    # Find approved milestones past auto-release date
    eligible_milestones = Milestone.objects.filter(
        status=MilestoneStatus.APPROVED,
        approved_at__isnull=False,
    ).select_related('escrow')
    
    released_count = 0
    for milestone in eligible_milestones:
        escrow = milestone.escrow
        
        # Check if auto-release period has passed
        auto_release_date = milestone.approved_at + timedelta(days=escrow.auto_release_days)
        
        if now >= auto_release_date:
            try:
                # Release the milestone
                milestone.release()
                
                # Create payout transaction
                from apps.transactions.services.escrow_service import EscrowTransactionService
                EscrowTransactionService.release_milestone(milestone)
                
                released_count += 1
                logger.info(f"Auto-released milestone {milestone.id} for escrow {escrow.reference_code}")
                
                # Check if all milestones are released
                pending_milestones = escrow.milestones.exclude(
                    status=MilestoneStatus.RELEASED
                ).count()
                
                if pending_milestones == 0:
                    EscrowStateMachine.transition(
                        escrow,
                        EscrowStatus.FULLY_RELEASED,
                        reason='All milestones auto-released'
                    )
                    
            except Exception as e:
                logger.exception(f"Failed to auto-release milestone {milestone.id}: {e}")
    
    logger.info(f"Auto-release check: released {released_count} milestones")
    return released_count


@shared_task
def check_escrow_auto_releases():
    """
    Check for escrows that are funded and past their auto-release time.
    Triggers FULL release of funds to the seller.
    Runs every minute.
    """
    from apps.escrow.models import EscrowAccount
    from apps.escrow.services import EscrowService
    from apps.core.enums import EscrowStatus
    
    now = timezone.now()
    
    # Find funded escrows ready for auto-release
    ready_escrows = EscrowAccount.objects.filter(
        status=EscrowStatus.FUNDED,
        auto_release_at__lte=now
    )
    
    released_count = 0
    for escrow in ready_escrows:
        try:
            logger.info(f"Auto-releasing escrow {escrow.reference_code} (Due: {escrow.auto_release_at})")
            
            # Logic: Release all funds and close
            # Using the Service we just wrote
            EscrowService.release_funds(
                escrow_id=escrow.id,
                actor=None  # System action
            )
            
            released_count += 1
            
        except Exception as e:
            logger.exception(f"Failed to auto-release escrow {escrow.reference_code}: {e}")
    
    if released_count > 0:
        logger.info(f"Escrow Auto-Release: Processed {released_count} escrows")
    
    return released_count


@shared_task
def send_escrow_reminders():
    """
    Send reminder notifications for pending actions.
    Runs daily.
    """
    from apps.escrow.models import EscrowAccount, Milestone
    from apps.core.enums import EscrowStatus, MilestoneStatus
    from apps.notifications.services import NotificationService, NotificationType, NotificationPriority
    
    now = timezone.now()
    reminders_sent = 0
    
    # Remind buyers about unfunded escrows (24h before expiry)
    expiring_soon = EscrowAccount.objects.filter(
        status=EscrowStatus.CREATED,
        expires_at__gt=now,
        expires_at__lt=now + timedelta(hours=24)
    )
    
    for escrow in expiring_soon:
        NotificationService.send(
            user=escrow.buyer,
            notification_type=NotificationType.REMINDER,
            context={
                'title': 'Escrow Funding Reminder',
                'message': f'Your escrow {escrow.reference_code} will expire in 24 hours. Please fund it to proceed.',
                'action_url': f'/escrows/{escrow.id}',
            },
            entity_type='EscrowAccount',
            entity_id=escrow.id,
            priority=NotificationPriority.HIGH,
        )
        reminders_sent += 1
    
    # Remind sellers about pending milestones (5 days overdue)
    overdue_milestones = Milestone.objects.filter(
        status=MilestoneStatus.PENDING,
        due_date__lt=now - timedelta(days=5)
    ).select_related('escrow')
    
    for milestone in overdue_milestones:
        NotificationService.send(
            user=milestone.escrow.seller,
            notification_type=NotificationType.REMINDER,
            context={
                'title': 'Milestone Overdue',
                'message': f'Milestone "{milestone.title}" is overdue. Please submit your deliverables.',
                'action_url': f'/escrows/{milestone.escrow.id}',
            },
            entity_type='Milestone',
            entity_id=milestone.id,
            priority=NotificationPriority.HIGH,
        )
        reminders_sent += 1
    
    # Remind buyers about pending approvals (3 days pending)
    pending_approvals = Milestone.objects.filter(
        status=MilestoneStatus.SUBMITTED,
        submitted_at__lt=now - timedelta(days=3)
    ).select_related('escrow')
    
    for milestone in pending_approvals:
        NotificationService.send(
            user=milestone.escrow.buyer,
            notification_type=NotificationType.REMINDER,
            context={
                'title': 'Approval Pending',
                'message': f'Milestone "{milestone.title}" is awaiting your review.',
                'action_url': f'/escrows/{milestone.escrow.id}',
            },
            entity_type='Milestone',
            entity_id=milestone.id,
        )
        reminders_sent += 1
    
    logger.info(f"Sent {reminders_sent} reminder notifications")
    return reminders_sent


@shared_task
def escalate_overdue_disputes():
    """
    Escalate disputes that have been unresolved too long.
    Runs daily.
    """
    from apps.disputes.models import Dispute
    from apps.core.enums import DisputeStatus
    from apps.notifications.services import NotificationService, NotificationType, NotificationPriority
    from apps.users.models import User
    from apps.core.enums import UserRole
    
    now = timezone.now()
    
    # Find disputes past deadline
    overdue_disputes = Dispute.objects.filter(
        status__in=[DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW],
        resolution_deadline__lt=now
    )
    
    escalated_count = 0
    for dispute in overdue_disputes:
        try:
            dispute.escalate(reason='Resolution deadline exceeded')
            escalated_count += 1
            
            # Notify admins
            admins = User.objects.filter(role=UserRole.ADMIN, status='active')
            for admin in admins:
                NotificationService.send(
                    user=admin,
                    notification_type=NotificationType.DISPUTE_RAISED,
                    context={
                        'title': 'Dispute Escalated',
                        'message': f'Dispute for {dispute.escrow.reference_code} has been escalated.',
                        'action_url': f'/admin/disputes/{dispute.id}',
                    },
                    entity_type='Dispute',
                    entity_id=dispute.id,
                    priority=NotificationPriority.URGENT,
                )
                
        except Exception as e:
            logger.exception(f"Failed to escalate dispute {dispute.id}: {e}")
    
    logger.info(f"Escalated {escalated_count} overdue disputes")
    return escalated_count


@shared_task
def close_completed_escrows():
    """
    Close escrows that are in terminal states and finalized.
    Runs hourly.
    """
    from apps.escrow.models import EscrowAccount
    from apps.escrow.state_machine import EscrowStateMachine
    from apps.core.enums import EscrowStatus
    
    now = timezone.now()
    one_day_ago = now - timedelta(days=1)
    
    # Find escrows ready to close
    ready_to_close = EscrowAccount.objects.filter(
        status__in=[
            EscrowStatus.FULLY_RELEASED,
            EscrowStatus.REFUNDED,
            EscrowStatus.CANCELLED
        ],
        completed_at__lt=one_day_ago
    ).exclude(status=EscrowStatus.CLOSED)
    
    closed_count = 0
    for escrow in ready_to_close:
        try:
            EscrowStateMachine.transition(
                escrow,
                EscrowStatus.CLOSED,
                reason='Auto-closed after completion period'
            )
            closed_count += 1
        except Exception as e:
            logger.exception(f"Failed to close escrow {escrow.reference_code}: {e}")
    
    logger.info(f"Closed {closed_count} completed escrows")
    return closed_count


@shared_task
def reconcile_pending_payments():
    """
    Reconcile payments that are stuck in pending state.
    Queries payment providers for status updates.
    Runs every 30 minutes.
    """
    from apps.transactions.models import PaymentIntent
    
    now = timezone.now()
    stale_threshold = now - timedelta(minutes=30)
    
    # Find stale pending payments
    stale_payments = PaymentIntent.objects.filter(
        status='pending',
        created_at__lt=stale_threshold,
        webhook_received=False
    )
    
    updated_count = 0
    for payment in stale_payments:
        try:
            from apps.transactions.services.provider_registry import get_provider
            
            provider = get_provider(payment.provider)
            if provider:
                result = provider.query_status(payment.provider_intent_id)
                
                if result.success and result.status.value != 'pending':
                    payment.status = result.status.value
                    payment.save()
                    updated_count += 1
                    logger.info(f"Reconciled payment {payment.id}: {result.status}")
                    
        except Exception as e:
            logger.exception(f"Failed to reconcile payment {payment.id}: {e}")
    
    logger.info(f"Reconciled {updated_count} stale payments")
    return updated_count
