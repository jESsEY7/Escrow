"""
Audit Service for logging all platform activities.
"""
import threading
from django.db import transaction
from apps.audit.models import AuditLog, SystemEvent


class AuditService:
    """
    Service for creating audit log entries.
    Designed to be non-blocking and failure-tolerant.
    """

    # Thread-local storage for request context
    _local = threading.local()

    @classmethod
    def set_request_context(cls, request):
        """Store request context for audit logging."""
        cls._local.ip_address = cls._get_client_ip(request)
        cls._local.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        cls._local.request_id = request.META.get('HTTP_X_REQUEST_ID', '')

    @classmethod
    def clear_request_context(cls):
        """Clear request context."""
        cls._local.ip_address = None
        cls._local.user_agent = None
        cls._local.request_id = None

    @classmethod
    def _get_client_ip(cls, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    @classmethod
    def log_action(
        cls,
        entity_type: str,
        entity_id: str,
        action: str,
        actor=None,
        previous_state: dict = None,
        new_state: dict = None,
        metadata: dict = None,
    ):
        """
        Log an action to the audit log.

        Args:
            entity_type: Type of entity (e.g., 'EscrowAccount', 'User')
            entity_id: ID of the entity
            action: Action performed
            actor: User who performed the action
            previous_state: State before the action
            new_state: State after the action
            metadata: Additional context
        """
        try:
            # Get the last checksum for chaining
            last_log = AuditLog.objects.filter(
                entity_type=entity_type,
                entity_id=entity_id
            ).order_by('-created_at').first()
            
            previous_checksum = last_log.checksum if last_log else None

            # Compute changes
            changes = None
            if previous_state and new_state:
                changes = cls._compute_changes(previous_state, new_state)

            # Create audit log entry
            log = AuditLog(
                entity_type=entity_type,
                entity_id=str(entity_id),
                action=action,
                actor=actor,
                previous_state=previous_state,
                new_state=new_state,
                changes=changes,
                metadata=metadata,
                previous_checksum=previous_checksum,
                ip_address=getattr(cls._local, 'ip_address', None),
                user_agent=getattr(cls._local, 'user_agent', ''),
                request_id=getattr(cls._local, 'request_id', ''),
            )
            log.save()
            
            return log

        except Exception as e:
            # Log to system events if audit logging fails
            cls.log_system_event(
                event_type='audit_log_failure',
                severity='error',
                title='Failed to create audit log',
                message=str(e),
                source='AuditService',
                metadata={
                    'entity_type': entity_type,
                    'entity_id': str(entity_id),
                    'action': action,
                }
            )
            return None

    @classmethod
    def _compute_changes(cls, previous_state: dict, new_state: dict) -> dict:
        """Compute the diff between two states."""
        changes = {}
        
        all_keys = set(previous_state.keys()) | set(new_state.keys())
        
        for key in all_keys:
            old_val = previous_state.get(key)
            new_val = new_state.get(key)
            
            if old_val != new_val:
                changes[key] = {
                    'old': old_val,
                    'new': new_val
                }
        
        return changes if changes else None

    @classmethod
    def log_system_event(
        cls,
        event_type: str,
        severity: str,
        title: str,
        message: str,
        source: str,
        stack_trace: str = '',
        related_entity_type: str = None,
        related_entity_id: str = None,
        metadata: dict = None,
    ):
        """Log a system event."""
        try:
            event = SystemEvent.objects.create(
                event_type=event_type,
                severity=severity,
                title=title,
                message=message,
                source=source,
                stack_trace=stack_trace,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                metadata=metadata,
            )
            return event
        except Exception:
            # If even system event logging fails, we can't do much
            # In production, this would go to an external monitoring service
            pass

    @classmethod
    def get_entity_history(cls, entity_type: str, entity_id: str, limit: int = 50):
        """Get audit history for an entity."""
        return AuditLog.objects.filter(
            entity_type=entity_type,
            entity_id=str(entity_id)
        ).order_by('-created_at')[:limit]

    @classmethod
    def get_user_actions(cls, user, limit: int = 50):
        """Get all actions performed by a user."""
        return AuditLog.objects.filter(
            actor=user
        ).order_by('-created_at')[:limit]

    @classmethod
    def verify_entity_audit_chain(cls, entity_type: str, entity_id: str) -> tuple:
        """
        Verify the integrity of an entity's audit chain.
        
        Returns:
            (is_valid, broken_at_index, total_logs)
        """
        is_valid, broken_at = AuditLog.get_chain_integrity(
            entity_type=entity_type,
            entity_id=entity_id
        )
        total = AuditLog.objects.filter(
            entity_type=entity_type,
            entity_id=entity_id
        ).count()
        
        return is_valid, broken_at, total
