"""
Django Admin configuration for Disputes app.
"""
from django.contrib import admin
from apps.disputes.models import (
    Dispute, DisputeResponse, Evidence, ArbitrationDecision, DisputeTimeline
)


class EvidenceInline(admin.TabularInline):
    model = Evidence
    extra = 0
    readonly_fields = ['file_hash', 'created_at']


class DisputeResponseInline(admin.TabularInline):
    model = DisputeResponse
    extra = 0
    readonly_fields = ['created_at']


class DisputeTimelineInline(admin.TabularInline):
    model = DisputeTimeline
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'escrow', 'reason', 'status',
        'raised_by', 'assigned_arbitrator', 'created_at'
    ]
    list_filter = ['status', 'reason']
    search_fields = ['escrow__reference_code', 'raised_by__email', 'against__email']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    inlines = [EvidenceInline, DisputeResponseInline, DisputeTimelineInline]

    fieldsets = (
        (None, {'fields': ('escrow', 'reason', 'description')}),
        ('Parties', {'fields': ('raised_by', 'against', 'assigned_arbitrator', 'assigned_at')}),
        ('Status', {'fields': ('status', 'disputed_amount')}),
        ('Timeline', {'fields': ('response_deadline', 'resolution_deadline', 'escalation_deadline')}),
        ('Resolution', {'fields': ('resolved_at', 'resolution_summary')}),
        ('Metadata', {'fields': ('metadata',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ['dispute', 'title', 'evidence_type', 'submitted_by', 'is_verified', 'created_at']
    list_filter = ['evidence_type', 'is_verified']
    search_fields = ['title', 'dispute__escrow__reference_code']


@admin.register(ArbitrationDecision)
class ArbitrationDecisionAdmin(admin.ModelAdmin):
    list_display = [
        'dispute', 'ruling', 'buyer_amount', 'seller_amount',
        'is_final', 'is_executed', 'created_at'
    ]
    list_filter = ['ruling', 'is_final', 'is_executed']
    readonly_fields = ['created_at', 'updated_at', 'executed_at']
