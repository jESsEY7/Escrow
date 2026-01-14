from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from apps.users.models import User
from apps.plans.models import Plan, EnterpriseOverride

class FeeEngine:
    """
    Calculates transaction fees based on the user's plan or enterprise overrides.
    """
    
    @staticmethod
    def calculate_fee(amount, user):
        """
        Calculate the fee for a transaction.
        
        Args:
            amount (Decimal): Transaction amount
            user (User): The user initiating the transaction
            
        Returns:
            Decimal: Calculated fee amount
        """
        amount = Decimal(str(amount))
        fee_percent = FeeEngine.get_fee_percent(user)
        
        return (amount * fee_percent / 100).quantize(Decimal('0.01'))

    @staticmethod
    def get_fee_percent(user):
        """
        Determine the fee percentage for a user.
        Priority: Enterprise Override -> User Plan -> Default Platform Fee
        """
        # 1. Check for Enterprise Override
        if hasattr(user, 'enterprise_override'):
            override = user.enterprise_override
            if override.custom_fee_percent is not None:
                return override.custom_fee_percent
                
        # 2. Check for User Plan
        if user.plan:
            return user.plan.escrow_fee_percent
            
        # 3. Fallback to Default (from settings)
        default_fee = getattr(settings, 'ESCROW_SETTINGS', {}).get('DEFAULT_PLATFORM_FEE_PERCENT', 2.5)
        return Decimal(str(default_fee))


class SLAEngine:
    """
    Manages Service Level Agreements (SLA) for dispute resolution.
    """
    
    @staticmethod
    def get_sla_hours(user):
        """
        Get the SLA resolution time in hours for a user.
        Priority: Enterprise Override -> User Plan -> Default (72 hours)
        """
        # 1. Check for Enterprise Override
        if hasattr(user, 'enterprise_override'):
            override = user.enterprise_override
            if override.custom_sla_hours is not None:
                return override.custom_sla_hours
                
        # 2. Check for User Plan
        if user.plan:
            return user.plan.sla_hours
            
        # 3. Fallback
        return 72

    @staticmethod
    def start_sla_timer(dispute):
        """
        Start the SLA countdown for a dispute.
        """
        # Determine which user's SLA applies (usually the one being disputed against, or the platform standard)
        # For simplicity, we'll use the 'against' user (seller) or 'raised_by' (buyer) depending on policy.
        # Assuming SLA is a promise to the customer (raised_by), we check the raised_by user's plan.
        # OR if it's a platform promise, we check the raised_by user.
        
        user = dispute.raised_by
        sla_hours = SLAEngine.get_sla_hours(user)
        
        deadline = timezone.now() + timezone.timedelta(hours=sla_hours)
        
        # Update dispute with the calculated deadline
        dispute.resolution_deadline = deadline
        dispute.save(update_fields=['resolution_deadline'])
        
        # In a real production system, we would queue a Celery task here
        # e.g., check_sla_breach.apply_async(eta=deadline, args=[dispute.id])
        
        return deadline
