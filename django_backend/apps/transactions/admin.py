"""
Django Admin configuration for Transactions app.
"""
from django.contrib import admin
from apps.transactions.models import Wallet, Transaction, PaymentIntent, FeeSchedule


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['escrow', 'balance', 'held_balance', 'released_amount', 'currency']
    search_fields = ['escrow__reference_code']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'escrow', 'type', 'amount', 'currency',
        'status', 'payment_method', 'created_at'
    ]
    list_filter = ['type', 'status', 'payment_method', 'currency']
    search_fields = ['escrow__reference_code', 'external_reference', 'idempotency_key']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'failed_at']

    fieldsets = (
        (None, {'fields': ('escrow', 'wallet', 'milestone')}),
        ('Transaction Details', {'fields': ('type', 'amount', 'currency', 'status')}),
        ('Payment', {'fields': ('payment_method', 'payment_provider', 'external_reference')}),
        ('Parties', {'fields': ('initiated_by', 'recipient')}),
        ('Fees', {'fields': ('fee_amount', 'fee_type')}),
        ('Metadata', {'fields': ('description', 'metadata', 'idempotency_key')}),
        ('Error Handling', {'fields': ('error_message', 'retry_count')}),
        ('Timestamps', {'fields': ('completed_at', 'failed_at', 'created_at', 'updated_at')}),
    )


@admin.register(PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = ['escrow', 'provider', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['provider', 'status']
    search_fields = ['provider_intent_id', 'escrow__reference_code']


@admin.register(FeeSchedule)
class FeeScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'percentage', 'fixed_fee', 'is_active']
    list_filter = ['is_active', 'escrow_type']
