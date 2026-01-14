"""
M-Pesa provider implementation.
Wrapper around existing mpesa_service using the provider abstraction.
"""
import logging
from decimal import Decimal
from typing import Dict, Any

from apps.transactions.services.payment_provider import (
    PaymentProvider, PaymentResult, WebhookResult, PayoutResult, PaymentStatus
)
from apps.transactions.services.mpesa_service import MpesaService

logger = logging.getLogger(__name__)


class MpesaProvider(PaymentProvider):
    """
    M-Pesa payment provider implementation.
    Uses the existing MpesaService for actual API calls.
    """
    
    def __init__(self):
        self._service = MpesaService()

    @property
    def provider_name(self) -> str:
        return 'mpesa'

    @property
    def supported_currencies(self) -> list:
        return ['KES']

    def initiate_payment(
        self,
        amount: Decimal,
        currency: str,
        customer_identifier: str,
        reference: str,
        description: str = 'Escrow Payment',
        metadata: Dict[str, Any] = None,
        escrow=None,  # Additional param for M-Pesa service
    ) -> PaymentResult:
        """
        Initiate M-Pesa STK Push.
        customer_identifier should be a phone number.
        """
        if currency not in self.supported_currencies:
            return PaymentResult(
                success=False,
                message=f"Currency {currency} not supported. Use: {self.supported_currencies}"
            )

        if escrow is None:
            return PaymentResult(
                success=False,
                message="Escrow instance required for M-Pesa payments"
            )

        success, response = self._service.initiate_stk_push(
            escrow=escrow,
            phone_number=customer_identifier,
            amount=amount,
            account_reference=reference,
            transaction_desc=description,
        )

        if success:
            return PaymentResult(
                success=True,
                transaction_id=response.get('payment_intent_id'),
                provider_reference=response.get('checkout_request_id'),
                status=PaymentStatus.PENDING,
                message=response.get('response_description', 'STK push sent'),
                metadata=response,
            )
        else:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message=str(response),
            )

    def process_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> WebhookResult:
        """Process M-Pesa callback."""
        success, message = self._service.process_callback(payload)
        
        # Extract data from callback
        body = payload.get('Body', {}).get('stkCallback', {})
        result_code = body.get('ResultCode')
        
        # Parse metadata if successful
        amount = None
        if result_code == 0:
            callback_metadata = body.get('CallbackMetadata', {}).get('Item', [])
            for item in callback_metadata:
                if item.get('Name') == 'Amount':
                    amount = Decimal(str(item.get('Value', 0)))
                    break

        return WebhookResult(
            success=success,
            transaction_id=body.get('CheckoutRequestID'),
            status=PaymentStatus.COMPLETED if success else PaymentStatus.FAILED,
            amount=amount,
            message=message,
            raw_data=payload,
        )

    def query_status(
        self,
        transaction_id: str,
    ) -> PaymentResult:
        """Query M-Pesa transaction status."""
        success, response = self._service.query_transaction_status(transaction_id)
        
        if success:
            result_code = response.get('ResultCode')
            status = PaymentStatus.COMPLETED if result_code == '0' else PaymentStatus.PENDING
            
            return PaymentResult(
                success=True,
                provider_reference=transaction_id,
                status=status,
                message=response.get('ResultDesc', ''),
                metadata=response,
            )
        else:
            return PaymentResult(
                success=False,
                message=str(response),
            )

    def initiate_payout(
        self,
        amount: Decimal,
        currency: str,
        recipient_identifier: str,
        reference: str,
        description: str = 'Escrow Payout',
    ) -> PayoutResult:
        """
        Initiate M-Pesa B2C payout.
        TODO: Implement B2C API integration.
        """
        logger.warning("M-Pesa B2C payout not yet implemented")
        return PayoutResult(
            success=False,
            message="M-Pesa B2C payout not yet implemented. Manual payout required.",
        )
