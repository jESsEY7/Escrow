"""
Django Admin configuration for Users app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.users.models import User, UserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'full_name', 'role', 'status', 'kyc_status', 'created_at']
    list_filter = ['role', 'status', 'kyc_status', 'email_verified', 'two_factor_enabled']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'profile_image')}),
        ('Role & Status', {'fields': ('role', 'status')}),
        ('KYC', {'fields': ('kyc_status', 'kyc_submitted_at', 'kyc_verified_at')}),
        ('Security', {'fields': ('email_verified', 'two_factor_enabled', 'failed_login_attempts', 'lockout_until')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Timestamps', {'fields': ('last_login_at', 'created_at', 'updated_at')}),
    )
    readonly_fields = ['created_at', 'updated_at', 'last_login_at']

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role'),
        }),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'is_active', 'created_at', 'last_used_at']
    list_filter = ['is_active']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['created_at', 'last_used_at']
