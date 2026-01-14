"""
Escrow State Machine.
Deterministic state transitions for escrow lifecycle management.
"""
from django.utils import timezone
from apps.core.enums import EscrowStatus
from apps.core.exceptions import InvalidStateTransitionError


class EscrowStateMachine:
    """
    State machine for escrow status transitions.
    Enforces valid transitions and handles side effects.
    """

    # Valid state transitions: {current_state: [allowed_next_states]}
    TRANSITIONS = {
        EscrowStatus.CREATED: [
            EscrowStatus.FUNDED,
            EscrowStatus.CANCELLED,
        ],
        EscrowStatus.FUNDED: [
            EscrowStatus.IN_VERIFICATION,
            EscrowStatus.MILESTONE_PENDING,  # If no verification needed
            EscrowStatus.CANCELLED,
            EscrowStatus.REFUNDED,
        ],
        EscrowStatus.IN_VERIFICATION: [
            EscrowStatus.MILESTONE_PENDING,
            EscrowStatus.DISPUTED,
            EscrowStatus.REFUNDED,
        ],
        EscrowStatus.MILESTONE_PENDING: [
            EscrowStatus.PARTIALLY_RELEASED,
            EscrowStatus.FULLY_RELEASED,
            EscrowStatus.DISPUTED,
        ],
        EscrowStatus.PARTIALLY_RELEASED: [
            EscrowStatus.MILESTONE_PENDING,  # Next milestone
            EscrowStatus.FULLY_RELEASED,
            EscrowStatus.DISPUTED,
        ],
        EscrowStatus.DISPUTED: [
            EscrowStatus.RESOLVED,
            EscrowStatus.MILESTONE_PENDING,  # If dispute withdrawn
        ],
        EscrowStatus.RESOLVED: [
            EscrowStatus.FULLY_RELEASED,
            EscrowStatus.REFUNDED,
            EscrowStatus.PARTIALLY_RELEASED,  # Split decision
        ],
        EscrowStatus.FULLY_RELEASED: [
            EscrowStatus.CLOSED,
        ],
        EscrowStatus.REFUNDED: [
            EscrowStatus.CLOSED,
        ],
        EscrowStatus.CANCELLED: [
            EscrowStatus.CLOSED,
        ],
        EscrowStatus.CLOSED: [],  # Terminal state
    }

    # States that prevent further modifications
    TERMINAL_STATES = [
        EscrowStatus.CLOSED,
    ]

    # States that require special handling
    DISPUTED_STATES = [
        EscrowStatus.DISPUTED,
        EscrowStatus.RESOLVED,
    ]

    @classmethod
    def can_transition(cls, current_status, new_status):
        """
        Check if a transition is valid.

        Args:
            current_status: Current escrow status
            new_status: Desired new status

        Returns:
            bool: True if transition is valid
        """
        if current_status == new_status:
            return True  # No-op transition is always valid

        allowed = cls.TRANSITIONS.get(current_status, [])
        return new_status in allowed

    @classmethod
    def get_allowed_transitions(cls, current_status):
        """
        Get list of allowed transitions from current status.

        Args:
            current_status: Current escrow status

        Returns:
            list: List of allowed status values
        """
        return cls.TRANSITIONS.get(current_status, [])

    @classmethod
    def transition(cls, escrow, new_status, actor=None, reason=None):
        """
        Perform a state transition with validation and side effects.

        Args:
            escrow: EscrowAccount instance
            new_status: New status to transition to
            actor: User performing the transition (optional)
            reason: Reason for transition (optional)

        Returns:
            EscrowAccount: Updated escrow instance

        Raises:
            InvalidStateTransitionError: If transition is not valid
        """
        current_status = escrow.status

        if not cls.can_transition(current_status, new_status):
            raise InvalidStateTransitionError(
                f'Cannot transition from {current_status} to {new_status}. '
                f'Allowed transitions: {cls.get_allowed_transitions(current_status)}'
            )

        # Store previous status
        escrow.previous_status = current_status
        escrow.status = new_status

        # Handle side effects based on new status
        cls._handle_transition_effects(escrow, current_status, new_status)

        escrow.save()

        # Log the transition
        cls._log_transition(escrow, current_status, new_status, actor, reason)

        return escrow

    @classmethod
    def _handle_transition_effects(cls, escrow, old_status, new_status):
        """Handle side effects of state transitions."""
        now = timezone.now()

        if new_status == EscrowStatus.FUNDED:
            escrow.funded_at = now

        elif new_status == EscrowStatus.FULLY_RELEASED:
            escrow.completed_at = now

        elif new_status == EscrowStatus.CANCELLED:
            escrow.cancelled_at = now

        elif new_status == EscrowStatus.REFUNDED:
            escrow.completed_at = now

        elif new_status == EscrowStatus.CLOSED:
            if not escrow.completed_at:
                escrow.completed_at = now

    @classmethod
    def _log_transition(cls, escrow, old_status, new_status, actor, reason):
        """Log the state transition to audit logs."""
        try:
            from apps.audit.services import AuditService
            AuditService.log_action(
                entity_type='EscrowAccount',
                entity_id=str(escrow.id),
                action='status_change',
                actor=actor,
                previous_state={'status': old_status},
                new_state={'status': new_status},
                metadata={
                    'reason': reason,
                    'reference_code': escrow.reference_code,
                }
            )
        except Exception:
            # Don't fail transition if audit logging fails
            pass

    @classmethod
    def auto_expire_check(cls, escrow):
        """
        Check if escrow should be auto-expired.
        Called by background task.

        Returns:
            bool: True if escrow was expired
        """
        if escrow.status != EscrowStatus.CREATED:
            return False

        if timezone.now() > escrow.expires_at:
            cls.transition(
                escrow,
                EscrowStatus.CANCELLED,
                reason='Auto-expired: funding deadline passed'
            )
            return True

        return False

    @classmethod
    def can_fund(cls, escrow):
        """Check if escrow can be funded."""
        return escrow.status == EscrowStatus.CREATED and not escrow.is_expired

    @classmethod
    def can_release(cls, escrow):
        """Check if escrow can release funds."""
        return escrow.status in [
            EscrowStatus.MILESTONE_PENDING,
            EscrowStatus.PARTIALLY_RELEASED,
            EscrowStatus.RESOLVED,
        ]

    @classmethod
    def can_refund(cls, escrow):
        """Check if escrow can be refunded."""
        return escrow.status in [
            EscrowStatus.FUNDED,
            EscrowStatus.IN_VERIFICATION,
            EscrowStatus.RESOLVED,
        ]

    @classmethod
    def can_dispute(cls, escrow):
        """Check if a dispute can be raised on this escrow."""
        return escrow.status in [
            EscrowStatus.IN_VERIFICATION,
            EscrowStatus.MILESTONE_PENDING,
            EscrowStatus.PARTIALLY_RELEASED,
        ]

    @classmethod
    def is_terminal(cls, escrow):
        """Check if escrow is in a terminal state."""
        return escrow.status in cls.TERMINAL_STATES

    @classmethod
    def is_disputed(cls, escrow):
        """Check if escrow is in a disputed state."""
        return escrow.status in cls.DISPUTED_STATES
