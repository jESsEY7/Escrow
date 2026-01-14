"""
Transaction serializers for the Escrow Platform.
"""
from rest_framework import serializers
from apps.transactions.models import Transaction, Wallet, PaymentIntent


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for wallet details."""
    available_balance = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)
    is_fully_funded = serializers.BooleanField(read_only=True)

    class Meta:
        model = Wallet
        fields = [
            'id', 'balance', 'held_balance', 'available_balance',
            'released_amount', 'currency', 'is_fully_funded',
            'created_at', 'updated_at'
        ]


class TransactionListSerializer(serializers.ModelSerializer):
    """Serializer for transaction list view."""
    escrow_reference = serializers.CharField(source='escrow.reference_code', read_only=True)
    initiated_by_email = serializers.CharField(source='initiated_by.email', read_only=True)
    recipient_email = serializers.CharField(source='recipient.email', read_only=True, allow_null=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'escrow_reference', 'type', 'amount', 'currency',
            'status', 'payment_method', 'initiated_by_email', 'recipient_email',
            'fee_amount', 'completed_at', 'created_at'
        ]


class TransactionDetailSerializer(serializers.ModelSerializer):
    """Serializer for transaction detail view."""
    escrow_reference = serializers.CharField(source='escrow.reference_code', read_only=True)
    initiated_by_email = serializers.CharField(source='initiated_by.email', read_only=True)
    recipient_email = serializers.CharField(source='recipient.email', read_only=True, allow_null=True)
    milestone_title = serializers.CharField(source='milestone.title', read_only=True, allow_null=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'escrow', 'escrow_reference', 'milestone', 'milestone_title',
            'type', 'amount', 'currency', 'status',
            'payment_method', 'payment_provider', 'external_reference',
            'initiated_by_email', 'recipient_email',
            'fee_amount', 'fee_type', 'description',
            'error_message', 'retry_count',
            'completed_at', 'failed_at', 'created_at', 'updated_at'
        ]


class PaymentIntentSerializer(serializers.ModelSerializer):
    """Serializer for payment intents."""

    class Meta:
        model = PaymentIntent
        fields = [
            'id', 'provider', 'provider_intent_id', 'amount', 'currency',
            'payment_method', 'status', 'expires_at', 'created_at'
        ]
