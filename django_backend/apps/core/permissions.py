"""
Custom permissions for the Escrow Platform.
Role-based access control with fine-grained permissions.
"""
from rest_framework import permissions
from apps.core.enums import UserRole, UserStatus, KYCStatus


class IsAuthenticated(permissions.BasePermission):
    """Verify user is authenticated and active."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.status == UserStatus.ACTIVE
        )


class IsAdmin(permissions.BasePermission):
    """Only allow admin users."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.ADMIN
        )


class IsArbitrator(permissions.BasePermission):
    """Only allow arbitrator users."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.ARBITRATOR
        )


class IsAdminOrArbitrator(permissions.BasePermission):
    """Allow admin or arbitrator users."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in [UserRole.ADMIN, UserRole.ARBITRATOR]
        )


class IsAuditor(permissions.BasePermission):
    """Allow auditor users (read-only access)."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.role == UserRole.AUDITOR:
            # Auditors have read-only access
            return request.method in permissions.SAFE_METHODS
        
        return request.user.role == UserRole.ADMIN


class IsBuyer(permissions.BasePermission):
    """Only allow buyer role."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.BUYER
        )


class IsSeller(permissions.BasePermission):
    """Only allow seller role."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.SELLER
        )


class IsBuyerOrSeller(permissions.BasePermission):
    """Allow buyer or seller roles."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in [UserRole.BUYER, UserRole.SELLER]
        )


class IsKYCVerified(permissions.BasePermission):
    """Require KYC verification for sensitive operations."""
    message = 'KYC verification is required to perform this action.'

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Admins and arbitrators bypass KYC check
        if request.user.role in [UserRole.ADMIN, UserRole.ARBITRATOR]:
            return True
        
        return request.user.kyc_status == KYCStatus.APPROVED


class IsEscrowParticipant(permissions.BasePermission):
    """Only allow users who are part of the escrow (buyer, seller, arbitrator)."""
    message = 'You are not a participant in this escrow.'

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Admin can access all
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Auditor has read-only access to all
        if request.user.role == UserRole.AUDITOR:
            return request.method in permissions.SAFE_METHODS
        
        # Check if user is participant
        user = request.user
        return (
            obj.buyer_id == user.id or
            obj.seller_id == user.id or
            (obj.arbitrator_id and obj.arbitrator_id == user.id)
        )


class IsEscrowBuyer(permissions.BasePermission):
    """Only allow the buyer of the escrow."""
    message = 'Only the buyer can perform this action.'

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.role == UserRole.ADMIN:
            return True
        
        return obj.buyer_id == request.user.id


class IsEscrowSeller(permissions.BasePermission):
    """Only allow the seller of the escrow."""
    message = 'Only the seller can perform this action.'

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.role == UserRole.ADMIN:
            return True
        
        return obj.seller_id == request.user.id


class IsDisputeParticipant(permissions.BasePermission):
    """Only allow dispute participants or assigned arbitrator."""
    message = 'You are not authorized to access this dispute.'

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.role == UserRole.ADMIN:
            return True
        
        if request.user.role == UserRole.AUDITOR:
            return request.method in permissions.SAFE_METHODS
        
        # Check escrow participants
        escrow = obj.escrow
        user = request.user
        
        return (
            escrow.buyer_id == user.id or
            escrow.seller_id == user.id or
            (escrow.arbitrator_id and escrow.arbitrator_id == user.id)
        )


class CanModifyEscrow(permissions.BasePermission):
    """Check if escrow can be modified based on its state."""
    message = 'This escrow cannot be modified in its current state.'

    def has_object_permission(self, request, view, obj):
        from apps.core.enums import EscrowStatus
        
        # Read-only operations always allowed
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Cannot modify closed, cancelled, or fully released escrows
        immutable_states = [
            EscrowStatus.CLOSED,
            EscrowStatus.CANCELLED,
            EscrowStatus.FULLY_RELEASED,
            EscrowStatus.REFUNDED,
        ]
        
        return obj.status not in immutable_states
