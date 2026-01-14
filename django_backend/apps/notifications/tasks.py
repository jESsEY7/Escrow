"""
Celery tasks for notification delivery.
Handles async sending of emails, SMS, and push notifications.
"""
import logging
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_notification(self, notification_id: str):
    """Send email notification."""
    from apps.notifications.models import Notification, NotificationTemplate
    from apps.core.services.email_service import EmailService
    
    try:
        notification = Notification.objects.select_related('user').get(id=notification_id)
        user = notification.user
        
        # Get template
        try:
            template = NotificationTemplate.objects.get(
                type=notification.type,
                is_active=True
            )
            rendered = template.render('email', notification.metadata or {})
            subject = rendered['subject']
            body_html = rendered['body_html']
            body_text = rendered['body_text']
        except NotificationTemplate.DoesNotExist:
            # Fallback to basic email
            subject = notification.title
            body_html = f"<p>{notification.message}</p>"
            body_text = notification.message
        
        # Send email
        EmailService.send_email(
            to_email=user.email,
            subject=subject,
            html_content=body_html,
            text_content=body_text,
        )
        
        notification.update_delivery_status('email', 'delivered')
        logger.info(f"Email sent for notification {notification_id}")
        
    except Notification.DoesNotExist:
        logger.error(f"Notification not found: {notification_id}")
    except Exception as e:
        logger.exception(f"Email send failed: {e}")
        notification.update_delivery_status('email', 'failed', str(e))
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_sms_notification(self, notification_id: str):
    """Send SMS notification."""
    from apps.notifications.models import Notification, NotificationTemplate
    
    try:
        notification = Notification.objects.select_related('user').get(id=notification_id)
        user = notification.user
        
        if not user.phone_number:
            notification.update_delivery_status('sms', 'skipped', 'No phone number')
            return
        
        # Get template
        try:
            template = NotificationTemplate.objects.get(
                type=notification.type,
                is_active=True
            )
            rendered = template.render('sms', notification.metadata or {})
            message = rendered['body']
        except NotificationTemplate.DoesNotExist:
            # Fallback - truncate message to 160 chars
            message = notification.message[:157] + '...' if len(notification.message) > 160 else notification.message
        
        # Send SMS via configured provider
        # TODO: Implement Twilio/Africa's Talking integration
        logger.info(f"SMS would be sent to {user.phone_number}: {message}")
        
        notification.update_delivery_status('sms', 'delivered')
        
    except Notification.DoesNotExist:
        logger.error(f"Notification not found: {notification_id}")
    except Exception as e:
        logger.exception(f"SMS send failed: {e}")
        notification.update_delivery_status('sms', 'failed', str(e))
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_push_notification(self, notification_id: str):
    """Send push notification."""
    from apps.notifications.models import Notification, NotificationTemplate
    
    try:
        notification = Notification.objects.select_related('user').get(id=notification_id)
        
        # Get template
        try:
            template = NotificationTemplate.objects.get(
                type=notification.type,
                is_active=True
            )
            rendered = template.render('push', notification.metadata or {})
            title = rendered['title']
            body = rendered['body']
        except NotificationTemplate.DoesNotExist:
            title = notification.title
            body = notification.message[:255]
        
        # Send push via configured provider
        # TODO: Implement Firebase Cloud Messaging
        logger.info(f"Push would be sent: {title} - {body}")
        
        notification.update_delivery_status('push', 'delivered')
        
    except Notification.DoesNotExist:
        logger.error(f"Notification not found: {notification_id}")
    except Exception as e:
        logger.exception(f"Push send failed: {e}")
        notification.update_delivery_status('push', 'failed', str(e))
        raise self.retry(exc=e)


@shared_task
def cleanup_old_notifications():
    """Clean up read notifications older than 90 days."""
    from django.utils import timezone
    from datetime import timedelta
    from apps.notifications.models import Notification
    
    cutoff = timezone.now() - timedelta(days=90)
    deleted_count, _ = Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old notifications")
    return deleted_count


@shared_task
def send_daily_digest():
    """Send daily notification digest to users who opted in."""
    from django.utils import timezone
    from datetime import timedelta
    from apps.notifications.models import Notification, NotificationPreference
    from apps.core.services.email_service import EmailService
    
    # Get users with daily digest enabled
    prefs = NotificationPreference.objects.filter(
        email_digest=True,
        digest_frequency='daily'
    ).select_related('user')
    
    yesterday = timezone.now() - timedelta(days=1)
    
    for pref in prefs:
        notifications = Notification.objects.filter(
            user=pref.user,
            created_at__gte=yesterday
        ).order_by('-created_at')[:20]
        
        if notifications:
            # Generate digest email
            # TODO: Use proper template
            subject = f"Your Daily Escrow Summary - {timezone.now().strftime('%B %d')}"
            body = f"You have {len(notifications)} new notifications..."
            
            EmailService.send_email(
                to_email=pref.user.email,
                subject=subject,
                html_content=f"<p>{body}</p>",
                text_content=body,
            )
            
    logger.info(f"Sent daily digest to {prefs.count()} users")
