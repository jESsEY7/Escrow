"""
Admin configuration for notifications app.
"""
from django.contrib import admin
from apps.notifications.models import (
    Notification, NotificationPreference, NotificationTemplate
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'type', 'title', 'is_read', 'priority', 'created_at']
    list_filter = ['type', 'is_read', 'priority', 'created_at']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['id', 'created_at', 'updated_at', 'delivery_status']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Notification', {
            'fields': ('id', 'user', 'type', 'priority')
        }),
        ('Content', {
            'fields': ('title', 'message', 'action_url')
        }),
        ('Entity Reference', {
            'fields': ('entity_type', 'entity_id')
        }),
        ('Delivery', {
            'fields': ('channels', 'delivery_status')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_enabled', 'sms_enabled', 'push_enabled', 'email_digest']
    list_filter = ['email_enabled', 'sms_enabled', 'push_enabled', 'email_digest']
    search_fields = ['user__email']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Channel Toggles', {
            'fields': ('email_enabled', 'sms_enabled', 'push_enabled')
        }),
        ('Type Preferences', {
            'fields': ('type_preferences',)
        }),
        ('Quiet Hours', {
            'fields': ('quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end', 'timezone')
        }),
        ('Digest', {
            'fields': ('email_digest', 'digest_frequency')
        }),
    )


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'is_active', 'updated_at']
    list_filter = ['type', 'is_active']
    search_fields = ['name', 'type']
    
    fieldsets = (
        ('Identification', {
            'fields': ('type', 'name', 'is_active')
        }),
        ('Email Template', {
            'fields': ('email_subject', 'email_body_html', 'email_body_text')
        }),
        ('SMS Template', {
            'fields': ('sms_body',)
        }),
        ('Push Template', {
            'fields': ('push_title', 'push_body')
        }),
        ('In-App Template', {
            'fields': ('in_app_title', 'in_app_body')
        }),
        ('Variables', {
            'fields': ('available_variables',),
            'classes': ('collapse',)
        }),
    )
