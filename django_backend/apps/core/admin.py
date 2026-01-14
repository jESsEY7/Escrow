from django.contrib import admin
from .models import WebhookEvent, ContactRequest

@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ('provider', 'event_type', 'status', 'retry_count', 'received_at')
    list_filter = ('provider', 'status', 'received_at')
    search_fields = ('idempotency_key', 'event_type')
    readonly_fields = ('payload', 'headers')

@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'transaction_type', 'created_at', 'is_resolved')
    list_filter = ('is_resolved', 'created_at', 'transaction_type')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    readonly_fields = ('created_at',)
    list_editable = ('is_resolved',)
