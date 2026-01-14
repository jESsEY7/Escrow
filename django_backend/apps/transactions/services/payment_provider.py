"""
Payment provider abstraction for the Escrow Platform.
Unified interface for multiple payment providers.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Dict, Any
from enum import Enum


class PaymentStatus(Enum):
    """Payment status enum."""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'


@dataclass
class PaymentResult:
    """Result of a payment initiation."""
    success: bool
    transaction_id: Optional[str] = None
    provider_reference: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    message: str = ''
    redirect_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class WebhookResult:
    """Result of webhook processing."""
    success: bool
    transaction_id: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    amount: Optional[Decimal] = None
    message: str = ''
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class PayoutResult:
    """Result of a payout/disbursement."""
    success: bool
    payout_id: Optional[str] = None
    provider_reference: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    message: str = ''


class PaymentProvider(ABC):
    """
    Abstract base class for payment providers.
    All payment integrations must implement this interface.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        pass

    @property
    @abstractmethod
    def supported_currencies(self) -> list:
        """Return list of supported currency codes."""
        pass

    @abstractmethod
    def initiate_payment(
        self,
        amount: Decimal,
        currency: str,
        customer_identifier: str,
        reference: str,
        description: str = '',
        metadata: Dict[str, Any] = None,
    ) -> PaymentResult:
        """
        Initiate a payment collection.
        
        Args:
            amount: Payment amount
            currency: Currency code (e.g., 'KES', 'USD')
            customer_identifier: Customer phone/email/account
            reference: Unique payment reference
            description: Payment description
            metadata: Additional data to store
        
        Returns:
            PaymentResult with status and provider reference
        """
        pass

    @abstractmethod
    def process_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> WebhookResult:
        """
        Process incoming webhook from payment provider.
        
        Args:
            payload: Webhook payload body
            headers: HTTP headers for signature verification
        
        Returns:
            WebhookResult with parsed transaction details
        """
        pass

    @abstractmethod
    def query_status(
        self,
        transaction_id: str,
    ) -> PaymentResult:
        """
        Query the status of a payment.
        
        Args:
            transaction_id: Provider transaction ID
        
        Returns:
            PaymentResult with current status
        """
        pass

    @abstractmethod
    def initiate_payout(
        self,
        amount: Decimal,
        currency: str,
        recipient_identifier: str,
        reference: str,
        description: str = '',
    ) -> PayoutResult:
        """
        Initiate a payout/disbursement to a recipient.
        
        Args:
            amount: Payout amount
            currency: Currency code
            recipient_identifier: Recipient phone/email/account
            reference: Unique payout reference
            description: Payout description
        
        Returns:
            PayoutResult with status
        """
        pass

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str,
    ) -> bool:
        """
        Verify webhook signature (optional override).
        Default implementation returns True.
        """
        return True
