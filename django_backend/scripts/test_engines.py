import os
import django
import sys
from decimal import Decimal

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escrow_platform.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.plans.models import Plan, EnterpriseOverride
from apps.plans.services import FeeEngine, SLAEngine
from apps.escrow.models import EscrowAccount
from django.conf import settings

User = get_user_model()

def run_tests():
    print("🚀 Starting Engine Verification...")
    
    # 1. Setup Plans
    print("\n1. Setting up Plans...")
    std_plan, _ = Plan.objects.get_or_create(
        name='Standard',
        defaults={'escrow_fee_percent': 1.5, 'sla_hours': 72}
    )
    pro_plan, _ = Plan.objects.get_or_create(
        name='Professional',
        defaults={'escrow_fee_percent': 1.0, 'sla_hours': 24}
    )
    print(f"✅ Plans Created: {std_plan}, {pro_plan}")

    # 2. Setup Users
    print("\n2. Setting up Users...")
    # Standard User
    user_std, _ = User.objects.get_or_create(email='std@test.com', defaults={'first_name': 'Stan'})
    user_std.plan = std_plan
    user_std.save()
    
    # Pro User
    user_pro, _ = User.objects.get_or_create(email='pro@test.com', defaults={'first_name': 'Pro'})
    user_pro.plan = pro_plan
    user_pro.save()
    
    # Enterprise User (No Plan, but Override)
    user_ent, _ = User.objects.get_or_create(email='ent@test.com', defaults={'first_name': 'Ent'})
    # Override
    override, _ = EnterpriseOverride.objects.get_or_create(
        user=user_ent,
        defaults={'custom_fee_percent': 0.5, 'custom_sla_hours': 4}
    )
    print("✅ Users Created and Configured")

    # 3. Test Fee Engine
    print("\n3. Testing Fee Engine...")
    
    # Test Standard
    fee_std = FeeEngine.get_fee_percent(user_std)
    assert fee_std == Decimal('1.50'), f"Expected 1.50, got {fee_std}"
    print(f"✅ Standard User Fee: {fee_std}%")
    
    # Test Pro
    fee_pro = FeeEngine.get_fee_percent(user_pro)
    assert fee_pro == Decimal('1.00'), f"Expected 1.00, got {fee_pro}"
    print(f"✅ Pro User Fee: {fee_pro}%")
    
    # Test Enterprise Override
    fee_ent = FeeEngine.get_fee_percent(user_ent)
    assert fee_ent == Decimal('0.50'), f"Expected 0.50, got {fee_ent}"
    print(f"✅ Enterprise User Fee: {fee_ent}% (Override)")
    
    # 4. Test SLA Engine
    print("\n4. Testing SLA Engine...")
    
    sla_std = SLAEngine.get_sla_hours(user_std)
    assert sla_std == 72, f"Expected 72, got {sla_std}"
    print(f"✅ Standard SLA: {sla_std}h")
    
    sla_ent = SLAEngine.get_sla_hours(user_ent)
    assert sla_ent == 4, f"Expected 4, got {sla_ent}"
    print(f"✅ Enterprise SLA: {sla_ent}h (Override)")

    # 5. Test Integration (Mocking Request)
    print("\n5. Testing DB Integration...")
    # Clean up previous runs
    EscrowAccount.objects.filter(buyer=user_std).delete()
    
    # Create Escrow manually mimicking serializer logic
    # We can't easily use serializer here without a request object, but we verify the logic:
    # Logic: percent = FeeEngine.get_fee_percent(user)
    
    escrow = EscrowAccount.objects.create(
        buyer=user_std,
        seller=user_pro, # Irrelevant for fee
        title="Test Escrow",
        total_amount=1000,
        expires_at=django.utils.timezone.now(),
        platform_fee_percent=FeeEngine.get_fee_percent(user_std)
    )
    
    assert escrow.platform_fee_percent == Decimal('1.50')
    print(f"✅ Escrow created with fee: {escrow.platform_fee_percent}%")
    
    print("\n🎉 ALL TESTS PASSED!")

if __name__ == '__main__':
    run_tests()
