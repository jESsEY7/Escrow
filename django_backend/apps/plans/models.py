import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Plan(models.Model):
    """
    Plan configuration table.
    Defines the business rules for each tier (Standard, Pro, Enterprise).
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True, help_text="e.g. Standard, Professional, Enterprise")
    
    # Financial Rules
    escrow_fee_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Transaction fee percentage (e.g. 1.5)"
    )
    
    # SLA Rules
    sla_hours = models.PositiveIntegerField(
        help_text="Time in hours before a dispute escalates or auto-resolves."
    )
    
    # Feature Flags & Limits
    has_api_access = models.BooleanField(default=False)
    has_dedicated_support = models.BooleanField(default=False)
    has_white_labeling = models.BooleanField(default=False)
    
    max_transaction_limit = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Maximum allowed transaction amount."
    )
    
    # UI/UX Config
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'plans'
        ordering = ['escrow_fee_percent']


class EnterpriseOverride(models.Model):
    """
    Enterprise-specific overrides for a particular user/organization.
    Allows for custom contracts without forking code.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # The entity this override applies to
    user = models.OneToOneField(
        'users.User', 
        on_delete=models.CASCADE,
        related_name='enterprise_override'
    )
    
    # Overrides (Nullable = use Plan default)
    custom_fee_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    custom_sla_hours = models.PositiveIntegerField(null=True, blank=True)
    
    # Custom Branding / White Label
    white_label_settings = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Custom logos, colors, domain settings (replaces branding_config)."
    )

    # Dedicated Support
    dedicated_support = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supported_enterprises',
        help_text="Staff member assigned to this account."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Override for {self.user}"

    class Meta:
        db_table = 'enterprise_overrides'
