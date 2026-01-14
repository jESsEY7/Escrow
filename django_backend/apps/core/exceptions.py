"""
Custom exceptions for the Escrow Platform.
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class EscrowException(APIException):
    """Base exception for escrow-related errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'An error occurred with the escrow operation.'
    default_code = 'escrow_error'


class InsufficientFundsError(EscrowException):
    """Raised when wallet has insufficient funds."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Insufficient funds for this operation.'
    default_code = 'insufficient_funds'


class InvalidStateTransitionError(EscrowException):
    """Raised when an invalid state transition is attempted."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid state transition for this escrow.'
    default_code = 'invalid_state_transition'


class EscrowNotFoundError(EscrowException):
    """Raised when escrow account is not found."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Escrow account not found.'
    default_code = 'escrow_not_found'


class UnauthorizedEscrowAccessError(EscrowException):
    """Raised when user tries to access escrow they're not party to."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You are not authorized to access this escrow.'
    default_code = 'unauthorized_escrow_access'


class DisputeException(APIException):
    """Base exception for dispute-related errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'An error occurred with the dispute operation.'
    default_code = 'dispute_error'


class DisputeAlreadyExistsError(DisputeException):
    """Raised when trying to create duplicate dispute."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'An active dispute already exists for this escrow.'
    default_code = 'dispute_exists'


class ArbitrationError(DisputeException):
    """Raised when arbitration operation fails."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Arbitration operation failed.'
    default_code = 'arbitration_error'


class PaymentException(APIException):
    """Base exception for payment-related errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Payment operation failed.'
    default_code = 'payment_error'


class PaymentProcessingError(PaymentException):
    """Raised when payment processing fails."""
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = 'Payment processing failed. Please try again.'
    default_code = 'payment_processing_error'


class PaymentVerificationError(PaymentException):
    """Raised when payment verification fails."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Payment verification failed.'
    default_code = 'payment_verification_error'


class KYCException(APIException):
    """Base exception for KYC-related errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'KYC operation failed.'
    default_code = 'kyc_error'


class KYCRequiredError(KYCException):
    """Raised when KYC is required but not completed."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'KYC verification is required to perform this action.'
    default_code = 'kyc_required'


class KYCPendingError(KYCException):
    """Raised when KYC is pending review."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Your KYC verification is still pending review.'
    default_code = 'kyc_pending'


class RateLimitExceededError(APIException):
    """Raised when rate limit is exceeded."""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Rate limit exceeded. Please try again later.'
    default_code = 'rate_limit_exceeded'


class ValidationError(APIException):
    """Custom validation error with field details."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Validation failed.'
    default_code = 'validation_error'

    def __init__(self, detail=None, field_errors=None):
        if field_errors:
            detail = {'message': detail or self.default_detail, 'errors': field_errors}
        super().__init__(detail)
