"""
M-Pesa Service for the Escrow Platform.
Handles STK Push and callback processing.
"""
import base64
import json
import logging
import uuid
from datetime import datetime
from decimal import Decimal

import pytz
import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
from django.db import transaction as db_transaction

from apps.transactions.models import Transaction, PaymentIntent
from apps.core.enums import TransactionType, TransactionStatus, PaymentMethod
from apps.audit.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class MpesaService:
    """
    Service for M-Pesa payment processing.
    Uses Safaricom's Daraja API.
    """

    # Sandbox URLs (change to production when ready)
    OAUTH_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    STK_PUSH_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    QUERY_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"

    def __init__(self):
        self.config = getattr(settings, 'PAYMENT_PROVIDERS', {}).get('mpesa', {})
        self.consumer_key = self.config.get('consumer_key', 'Rl3fp6w9WlJeB5GRPgtQQDvpmEEh76F3')
        self.consumer_secret = self.config.get('consumer_secret', 'pSWl8ceFxKWhZkAA')
        self.shortcode = self.config.get('shortcode', '174379')
        self.passkey = self.config.get('passkey', 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')
        self.callback_url = self.config.get('callback_url', 'https://jessy.softspin.co.ke/api/payments/mpesa/callback/')
        self.test_mode = self.config.get('test_mode', True)

    def _generate_access_token(self):
        """Generate OAuth access token from Safaricom."""
        try:
            response = requests.get(
                self.OAUTH_URL,
                auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret),
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"M-Pesa OAuth error: {response.text}")
                return None

            token_data = response.json()
            return token_data.get('access_token')

        except Exception as e:
            logger.exception(f"M-Pesa OAuth failed: {e}")
            return None

    def _get_timestamp(self):
        """Get current timestamp in Nairobi timezone."""
        timezone = pytz.timezone('Africa/Nairobi')
        now = datetime.now(timezone)
        return now.strftime('%Y%m%d%H%M%S')

    def _generate_password(self, timestamp):
        """Generate the password for STK push."""
        data_to_encode = self.shortcode + self.passkey + timestamp
        encoded = base64.b64encode(data_to_encode.encode())
        return encoded.decode('utf-8')

    def _format_phone_number(self, phone_number: str):
        """Format phone number to 254 format."""
        phone_number = phone_number.strip()

        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        if phone_number.startswith('7') or phone_number.startswith('1'):
            phone_number = '254' + phone_number

        return phone_number

    def initiate_stk_push(
        self,
        escrow,
        phone_number: str,
        amount: Decimal,
        account_reference: str = "",
        transaction_desc: str = "Escrow Deposit"
    ):
        """
        Initiate M-Pesa STK Push.

        Args:
            escrow: EscrowAccount instance
            phone_number: Customer's phone number
            amount: Amount to charge (in KES)
            account_reference: Reference for the transaction
            transaction_desc: Description of the transaction

        Returns:
            tuple: (success, response_data or error_message)
        """
        try:
            phone_number = self._format_phone_number(phone_number)

            access_token = self._generate_access_token()
            if not access_token:
                return False, "Failed to generate access token"

            timestamp = self._get_timestamp()
            password = self._generate_password(timestamp)

            # Generate unique reference if not provided
            if not account_reference:
                account_reference = escrow.reference_code

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            request_body = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': int(amount),  # M-Pesa requires integer
                'PartyA': phone_number,
                'PartyB': self.shortcode,
                'PhoneNumber': phone_number,
                'CallBackURL': self.callback_url,
                'AccountReference': account_reference,
                'TransactionDesc': transaction_desc
            }

            response = requests.post(
                self.STK_PUSH_URL,
                json=request_body,
                headers=headers,
                timeout=30
            )

            response_data = response.json()

            if response.status_code == 200 and response_data.get('ResponseCode') == '0':
                logger.info(f"STK push initiated: {response_data}")

                # Create payment intent to track this request
                payment_intent = PaymentIntent.objects.create(
                    escrow=escrow,
                    provider='mpesa',
                    provider_intent_id=response_data.get('CheckoutRequestID'),
                    amount=amount,
                    currency='KES',
                    payment_method=PaymentMethod.MPESA,
                    status='pending',
                    expires_at=datetime.now(pytz.UTC) + pytz.timedelta(minutes=5),
                )

                return True, {
                    'checkout_request_id': response_data.get('CheckoutRequestID'),
                    'merchant_request_id': response_data.get('MerchantRequestID'),
                    'response_description': response_data.get('ResponseDescription'),
                    'payment_intent_id': str(payment_intent.id),
                }
            else:
                logger.error(f"STK push failed: {response_data}")
                return False, response_data.get('errorMessage', 'Failed to initiate payment')

        except Exception as e:
            logger.exception(f"STK push error: {e}")
            return False, str(e)

    @db_transaction.atomic
    def process_callback(self, callback_data: dict):
        """
        Process M-Pesa callback/webhook.

        Args:
            callback_data: The callback data from M-Pesa

        Returns:
            tuple: (success, message)
        """
        try:
            body = callback_data.get('Body', {}).get('stkCallback', {})
            checkout_request_id = body.get('CheckoutRequestID')
            result_code = body.get('ResultCode')
            result_desc = body.get('ResultDesc')

            logger.info(f"M-Pesa callback: {checkout_request_id} - {result_code} - {result_desc}")

            # Find the payment intent
            try:
                payment_intent = PaymentIntent.objects.get(
                    provider='mpesa',
                    provider_intent_id=checkout_request_id
                )
            except PaymentIntent.DoesNotExist:
                logger.error(f"Payment intent not found: {checkout_request_id}")
                return False, "Payment intent not found"

            payment_intent.webhook_received = True
            payment_intent.webhook_data = callback_data

            if result_code == 0:
                # Payment successful
                payment_intent.status = 'completed'
                payment_intent.save()

                # Extract transaction details from metadata
                callback_metadata = body.get('CallbackMetadata', {}).get('Item', [])
                metadata_dict = {}
                for item in callback_metadata:
                    metadata_dict[item.get('Name')] = item.get('Value')

                # Credit the escrow wallet
                escrow = payment_intent.escrow
                wallet = escrow.wallet

                # Create transaction record
                transaction = Transaction.objects.create(
                    escrow=escrow,
                    wallet=wallet,
                    type=TransactionType.DEPOSIT,
                    amount=payment_intent.amount,
                    currency='KES',
                    status=TransactionStatus.COMPLETED,
                    payment_method=PaymentMethod.MPESA,
                    external_reference=metadata_dict.get('MpesaReceiptNumber'),
                    payment_provider='mpesa',
                    payment_details=metadata_dict,
                    initiated_by=escrow.buyer,
                    description=f"M-Pesa deposit for {escrow.reference_code}",
                    idempotency_key=f"mpesa_{checkout_request_id}",
                )
                transaction.complete()

                # Update wallet balance
                wallet.deposit(payment_intent.amount)

                # Link transaction to payment intent
                payment_intent.transaction = transaction
                payment_intent.save()

                # Log to audit
                AuditService.log_action(
                    entity_type='Transaction',
                    entity_id=str(transaction.id),
                    action='mpesa_deposit',
                    actor=escrow.buyer,
                    new_state={
                        'amount': str(payment_intent.amount),
                        'receipt': metadata_dict.get('MpesaReceiptNumber'),
                        'phone': metadata_dict.get('PhoneNumber'),
                    },
                )

                # Transition escrow to funded if fully funded
                if wallet.is_fully_funded:
                    from apps.escrow.state_machine import EscrowStateMachine
                    from apps.core.enums import EscrowStatus

                    EscrowStateMachine.transition(
                        escrow,
                        EscrowStatus.FUNDED,
                        reason='M-Pesa payment received'
                    )
                    EscrowStateMachine.transition(
                        escrow,
                        EscrowStatus.MILESTONE_PENDING,
                        reason='Escrow funded - awaiting milestone'
                    )

                return True, "Payment processed successfully"

            else:
                # Payment failed
                payment_intent.status = 'failed'
                payment_intent.save()

                logger.warning(f"M-Pesa payment failed: {result_desc}")
                return False, result_desc

        except Exception as e:
            logger.exception(f"Callback processing error: {e}")
            return False, str(e)

    def query_transaction_status(self, checkout_request_id: str):
        """
        Query the status of an STK push transaction.

        Args:
            checkout_request_id: The CheckoutRequestID from the STK push response

        Returns:
            tuple: (success, status_data or error_message)
        """
        try:
            access_token = self._generate_access_token()
            if not access_token:
                return False, "Failed to generate access token"

            timestamp = self._get_timestamp()
            password = self._generate_password(timestamp)

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            request_body = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'CheckoutRequestID': checkout_request_id
            }

            response = requests.post(
                self.QUERY_URL,
                json=request_body,
                headers=headers,
                timeout=30
            )

            response_data = response.json()
            return True, response_data

        except Exception as e:
            logger.exception(f"Query status error: {e}")
            return False, str(e)


# Singleton instance
mpesa_service = MpesaService()
