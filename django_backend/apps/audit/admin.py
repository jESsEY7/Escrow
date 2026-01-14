"""
Django Admin configuration for Audit app.
"""
from django.contrib import admin
from apps.audit.models import AuditLog, SystemEvent, ComplianceReport


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['entity_type', 'entity_id', 'action', 'actor_email', 'ip_address', 'created_at']
    list_filter = ['entity_type', 'action']
    search_fields = ['entity_id', 'actor_email', 'ip_address']
    readonly_fields = [
        'id', 'entity_type', 'entity_id', 'action', 'actor', 'actor_email', 'actor_role',
        'ip_address', 'user_agent', 'request_id', 'previous_state', 'new_state',
        'changes', 'metadata', 'checksum', 'previous_checksum', 'created_at'
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SystemEvent)
class SystemEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'severity', 'title', 'source', 'is_resolved', 'created_at']
    list_filter = ['severity', 'is_resolved', 'event_type']
    search_fields = ['title', 'message', 'source']
    readonly_fields = ['created_at']


@admin.register(ComplianceReport)
class ComplianceReportAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'title', 'period_start', 'period_end', 'created_at']
    list_filter = ['report_type']
    search_fields = ['title']
    readonly_fields = ['created_at']
