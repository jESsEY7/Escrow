"""
Signals for the Users app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.users.models import User


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """Handle user creation and updates."""
    if created:
        # Log user creation in audit
        from apps.audit.services.audit_service import AuditService
        AuditService.log_action(
            entity_type='User',
            entity_id=str(instance.id),
            action='create',
            actor=instance,
            new_state={
                'email': instance.email,
                'role': instance.role,
                'status': instance.status
            }
        )
