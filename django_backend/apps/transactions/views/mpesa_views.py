"""
M-Pesa views for the Escrow Platform.
"""
import json
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

from apps.escrow.models import EscrowAccount
from apps.transactions.services.mpesa_service import mpesa_service
from apps.transactions.models import PaymentIntent
from apps.core.enums import EscrowStatus


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_mpesa_payment(request):
    """
    Initiate M-Pesa STK Push payment.
    
    Request body:
    {
        "escrow_id": "uuid",
        "phone_number": "254XXXXXXXXX",
        "amount": 1000
    }
    """
    escrow_id = request.data.get('escrow_id')
    phone_number = request.data.get('phone_number')
    amount = request.data.get('amount')
    
    if not all([escrow_id, phone_number, amount]):
        return Response(
            {'error': 'escrow_id, phone_number, and amount are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get escrow
    escrow = get_object_or_404(EscrowAccount, pk=escrow_id)
    
    # Verify user is the buyer
    if escrow.buyer != request.user:
        return Response(
            {'error': 'Only the buyer can fund this escrow'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Verify escrow is in correct state
    if escrow.status != EscrowStatus.CREATED:
        return Response(
            {'error': 'Escrow cannot be funded in its current state'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Initiate STK Push
    success, result = mpesa_service.initiate_stk_push(
        escrow=escrow,
        phone_number=phone_number,
        amount=amount,
        account_reference=escrow.reference_code,
        transaction_desc=f"Escrow: {escrow.title[:20]}"
    )
    
    if success:
        return Response({
            'message': 'STK push sent. Please check your phone.',
            'data': result
        })
    else:
        return Response(
            {'error': result},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([AllowAny])  # Webhook - no auth required
@csrf_exempt
def mpesa_callback(request):
    """
    M-Pesa callback endpoint.
    Receives payment confirmation from Safaricom.
    """
    try:
        callback_data = request.data
        
        # Log the callback for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"M-Pesa callback received: {json.dumps(callback_data)}")
        
        success, message = mpesa_service.process_callback(callback_data)
        
        # M-Pesa expects a simple response
        return Response({'ResultCode': 0, 'ResultDesc': 'Success'})
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception(f"M-Pesa callback error: {e}")
        return Response({'ResultCode': 1, 'ResultDesc': str(e)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_payment_status(request, checkout_request_id):
    """
    Check the status of an M-Pesa payment.
    """
    # First check our database
    try:
        payment_intent = PaymentIntent.objects.get(
            provider='mpesa',
            provider_intent_id=checkout_request_id
        )
        
        # Verify user has access
        if payment_intent.escrow.buyer != request.user:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response({
            'status': payment_intent.status,
            'amount': str(payment_intent.amount),
            'currency': payment_intent.currency,
            'created_at': payment_intent.created_at,
            'transaction_id': str(payment_intent.transaction_id) if payment_intent.transaction else None,
        })
        
    except PaymentIntent.DoesNotExist:
        return Response(
            {'error': 'Payment not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def query_mpesa_status(request):
    """
    Query M-Pesa for the status of a transaction.
    Used when callback wasn't received.
    """
    checkout_request_id = request.data.get('checkout_request_id')
    
    if not checkout_request_id:
        return Response(
            {'error': 'checkout_request_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    success, result = mpesa_service.query_transaction_status(checkout_request_id)
    
    if success:
        return Response(result)
    else:
        return Response(
            {'error': result},
            status=status.HTTP_400_BAD_REQUEST
        )
