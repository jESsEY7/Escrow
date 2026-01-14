"""
Celery Beat schedule configuration.
Defines periodic tasks for escrow automation.
"""
from celery.schedules import crontab

# Celery Beat Schedule
# Add this to your celery.py or settings.py
CELERY_BEAT_SCHEDULE = {
    # Escrow automation tasks
    'check-escrow-expirations': {
        'task': 'apps.escrow.tasks.check_escrow_expirations',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'check-auto-releases': {
        'task': 'apps.escrow.tasks.check_auto_releases',
        'schedule': crontab(minute=0),  # Every hour
    },
    'check-escrow-auto-releases-worker': {
        'task': 'apps.escrow.tasks.check_escrow_auto_releases',
        'schedule': crontab(minute='*'),  # Every minute (High frequency)
    },
    'send-escrow-reminders': {
        'task': 'apps.escrow.tasks.send_escrow_reminders',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    'escalate-overdue-disputes': {
        'task': 'apps.escrow.tasks.escalate_overdue_disputes',
        'schedule': crontab(hour=10, minute=0),  # Daily at 10 AM
    },
    'close-completed-escrows': {
        'task': 'apps.escrow.tasks.close_completed_escrows',
        'schedule': crontab(minute=30),  # Every hour at :30
    },
    'reconcile-pending-payments': {
        'task': 'apps.escrow.tasks.reconcile_pending_payments',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    
    # Notification tasks
    'cleanup-old-notifications': {
        'task': 'apps.notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    'send-daily-digest': {
        'task': 'apps.notifications.tasks.send_daily_digest',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
    },
}
