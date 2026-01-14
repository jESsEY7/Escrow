"""
Django Admin configuration for Escrow app.
"""
from django.contrib import admin
from apps.escrow.models import EscrowAccount, Milestone, EscrowDocument, EscrowInvitation


class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 0
    readonly_fields = ['status', 'submitted_at', 'approved_at', 'released_at']


class EscrowDocumentInline(admin.TabularInline):
    model = EscrowDocument
    extra = 0
    readonly_fields = ['file_hash', 'created_at']


@admin.register(EscrowAccount)
class EscrowAccountAdmin(admin.ModelAdmin):
    list_display = [
        'reference_code', 'title', 'status', 'escrow_type',
        'total_amount', 'currency', 'buyer', 'seller', 'created_at'
    ]
    list_filter = ['status', 'escrow_type', 'currency', 'automation_enabled']
    search_fields = ['reference_code', 'title', 'buyer__email', 'seller__email']
    readonly_fields = ['reference_code', 'created_at', 'updated_at', 'funded_at', 'completed_at']
    inlines = [MilestoneInline, EscrowDocumentInline]

    fieldsets = (
        (None, {'fields': ('reference_code', 'title', 'description', 'escrow_type')}),
        ('Participants', {'fields': ('buyer', 'seller', 'arbitrator')}),
        ('Status', {'fields': ('status', 'previous_status')}),
        ('Financial', {'fields': ('total_amount', 'currency', 'platform_fee_percent')}),
        ('Terms', {'fields': ('terms', 'inspection_period_days', 'auto_release_days')}),
        ('Automation', {'fields': ('conditions', 'automation_enabled')}),
        ('Timeline', {'fields': ('expires_at', 'funded_at', 'completed_at', 'cancelled_at')}),
        ('Metadata', {'fields': ('notes', 'metadata')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ['escrow', 'title', 'amount', 'status', 'order', 'due_date']
    list_filter = ['status']
    search_fields = ['escrow__reference_code', 'title']


@admin.register(EscrowInvitation)
class EscrowInvitationAdmin(admin.ModelAdmin):
    list_display = ['escrow', 'email', 'role', 'is_accepted', 'expires_at']
    list_filter = ['is_accepted', 'role']
    search_fields = ['email', 'escrow__reference_code']
