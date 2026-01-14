"""
Notification service for the Escrow Platform.
Handles sending notifications across multiple channels.
"""
import logging
from typing import List, Optional, Dict, Any
from django.conf import settings
from django.db import transaction

from apps.notifications.models import (
    Notification, NotificationType, NotificationPreference,
    NotificationTemplate, NotificationChannel, NotificationPriority
)

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Core notification service.
    Orchestrates notification creation and delivery across channels.
    """

    @classmethod
    def send(
        cls,
        user,
        notification_type: str,
        context: Dict[str, Any],
        entity_type: str = '',
        entity_id: str = None,
        priority: str = NotificationPriority.NORMAL,
        channels: List[str] = None,
    ) -> Optional[Notification]:
        """
        Send a notification to a user.
        
        Args:
            user: User to notify
            notification_type: Type of notification (from NotificationType)
            context: Context dict for template rendering
            entity_type: Related entity type (e.g., 'EscrowAccount')
            entity_id: Related entity ID
            priority: Notification priority
            channels: Override channels (if None, uses user preferences)
        
        Returns:
            Created Notification instance or None if failed
        """
        try:
            # Get template
            template = cls._get_template(notification_type)
            if not template:
                logger.warning(f"No template for notification type: {notification_type}")
                # Use fallback content
                title = context.get('title', notification_type.replace('_', ' ').title())
                message = context.get('message', '')
            else:
                # Render in-app content
                rendered = template.render('in_app', context)
                title = rendered.get('title', notification_type)
                message = rendered.get('body', '')

            # Determine channels
            if channels is None:
                channels = cls._get_user_channels(user, notification_type)

            # Create notification record
            notification = Notification.objects.create(
                user=user,
                type=notification_type,
                title=title,
                message=message,
                action_url=context.get('action_url', ''),
                priority=priority,
                entity_type=entity_type,
                entity_id=entity_id,
                channels=channels,
                metadata=context,
            )

            # Dispatch to channels asynchronously
            cls._dispatch_to_channels(notification, template, context)

            return notification

        except Exception as e:
            logger.exception(f"Failed to send notification: {e}")
            return None

    @classmethod
    def send_bulk(
        cls,
        users: list,
        notification_type: str,
        context: Dict[str, Any],
        **kwargs
    ) -> List[Notification]:
        """Send same notification to multiple users."""
        notifications = []
        for user in users:
            notification = cls.send(user, notification_type, context, **kwargs)
            if notification:
                notifications.append(notification)
        return notifications

    @classmethod
    def mark_as_read(cls, notification_ids: List[str], user) -> int:
        """Mark multiple notifications as read for a user."""
        from django.utils import timezone
        
        return Notification.objects.filter(
            id__in=notification_ids,
            user=user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())

    @classmethod
    def mark_all_as_read(cls, user) -> int:
        """Mark all notifications as read for a user."""
        from django.utils import timezone
        
        return Notification.objects.filter(
            user=user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())

    @classmethod
    def get_unread_count(cls, user) -> int:
        """Get count of unread notifications for a user."""
        return Notification.objects.filter(user=user, is_read=False).count()

    @classmethod
    def _get_template(cls, notification_type: str) -> Optional[NotificationTemplate]:
        """Get active template for notification type."""
        try:
            return NotificationTemplate.objects.get(
                type=notification_type,
                is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            return None

    @classmethod
    def _get_user_channels(cls, user, notification_type: str) -> List[str]:
        """Get channels based on user preferences."""
        try:
            prefs = user.notification_preferences
            return prefs.get_channels_for_type(notification_type)
        except NotificationPreference.DoesNotExist:
            # Default channels
            return ['email', 'in_app']

    @classmethod
    def _dispatch_to_channels(
        cls,
        notification: Notification,
        template: Optional[NotificationTemplate],
        context: Dict[str, Any]
    ):
        """Dispatch notification to all channels."""
        from apps.notifications.tasks import (
            send_email_notification,
            send_sms_notification,
            send_push_notification,
        )

        for channel in notification.channels:
            try:
                if channel == 'email':
                    # Queue email task
                    send_email_notification.delay(str(notification.id))
                    
                elif channel == 'sms':
                    # Queue SMS task
                    send_sms_notification.delay(str(notification.id))
                    
                elif channel == 'push':
                    # Queue push notification task
                    send_push_notification.delay(str(notification.id))
                    
                elif channel == 'in_app':
                    # In-app is already saved, just mark as pending
                    notification.update_delivery_status('in_app', 'delivered')
                    
            except Exception as e:
                logger.exception(f"Failed to dispatch to {channel}: {e}")
                notification.update_delivery_status(channel, 'failed', str(e))


# Convenience functions for common notifications
def notify_escrow_created(escrow):
    """Notify parties about new escrow."""
    context = {
        'escrow_reference': escrow.reference_code,
        'escrow_title': escrow.title,
        'amount': str(escrow.total_amount),
        'currency': escrow.currency,
        'action_url': f'/escrows/{escrow.id}',
    }
    
    # Notify buyer
    NotificationService.send(
        user=escrow.buyer,
        notification_type=NotificationType.ESCROW_CREATED,
        context={**context, 'role': 'buyer'},
        entity_type='EscrowAccount',
        entity_id=escrow.id,
    )
    
    # Notify seller
    NotificationService.send(
        user=escrow.seller,
        notification_type=NotificationType.ESCROW_CREATED,
        context={**context, 'role': 'seller'},
        entity_type='EscrowAccount',
        entity_id=escrow.id,
    )


def notify_escrow_funded(escrow):
    """Notify parties that escrow has been funded."""
    context = {
        'escrow_reference': escrow.reference_code,
        'escrow_title': escrow.title,
        'amount': str(escrow.total_amount),
        'currency': escrow.currency,
        'action_url': f'/escrows/{escrow.id}',
    }
    
    NotificationService.send(
        user=escrow.seller,
        notification_type=NotificationType.ESCROW_FUNDED,
        context=context,
        entity_type='EscrowAccount',
        entity_id=escrow.id,
        priority=NotificationPriority.HIGH,
    )


def notify_milestone_submitted(milestone):
    """Notify buyer about milestone submission."""
    escrow = milestone.escrow
    context = {
        'escrow_reference': escrow.reference_code,
        'milestone_title': milestone.title,
        'milestone_amount': str(milestone.amount),
        'action_url': f'/escrows/{escrow.id}',
    }
    
    NotificationService.send(
        user=escrow.buyer,
        notification_type=NotificationType.MILESTONE_SUBMITTED,
        context=context,
        entity_type='Milestone',
        entity_id=milestone.id,
    )


def notify_dispute_raised(dispute):
    """Notify relevant parties about a dispute."""
    escrow = dispute.escrow
    context = {
        'escrow_reference': escrow.reference_code,
        'dispute_reason': dispute.get_reason_display(),
        'action_url': f'/disputes/{dispute.id}',
    }
    
    # Notify non-raising party
    other_party = escrow.seller if dispute.raised_by == escrow.buyer else escrow.buyer
    NotificationService.send(
        user=other_party,
        notification_type=NotificationType.DISPUTE_RAISED,
        context=context,
        entity_type='Dispute',
        entity_id=dispute.id,
        priority=NotificationPriority.URGENT,
    )
    
    # Notify arbitrator if assigned
    if dispute.assigned_arbitrator:
        NotificationService.send(
            user=dispute.assigned_arbitrator,
            notification_type=NotificationType.DISPUTE_RAISED,
            context=context,
            entity_type='Dispute',
            entity_id=dispute.id,
            priority=NotificationPriority.URGENT,
        )
