import os
import sys
import django
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escrow_platform.settings.development')
django.setup()

from apps.users.models import User
from apps.plans.models import Plan, EnterpriseOverride
from apps.escrow.models import EscrowAccount
from apps.escrow.services import EscrowService
from apps.core.enums import EscrowStatus
from apps.audit.models import AuditLog

def verify_advanced_schema():
    print("🚀 Starting Advanced Schema Verification...")

    # 1. Setup Plan & User
    print("\n1. Setting up Plan & User...")
    plan, _ = Plan.objects.get_or_create(
        name='Enterprise Test',
        defaults={
            'escrow_fee_percent': 1.5,
            'sla_hours': 24,
            'display_name': 'Enterprise Test Plan',
            'max_transaction_limit': 1000000
        }
    )
    
    buyer_email = f'buyer_{timezone.now().timestamp()}@example.com'
    seller_email = f'seller_{timezone.now().timestamp()}@example.com'
    
    buyer = User.objects.create_user(email=buyer_email, password='password123', first_name='Buyer')
    seller = User.objects.create_user(email=seller_email, password='password123', first_name='Seller')
    
    # Assign Plan
    buyer.plan = plan
    buyer.save()
    
    # Create Enterprise Override for High Priority SLA (4 hours instead of 24)
    EnterpriseOverride.objects.create(
        user=buyer,
        custom_sla_hours=4,
        white_label_settings={'theme': 'dark'}
    )
    print("   ✅ User and Plan with Override created.")

    # 2. Create Escrow
    print("\n2. Creating Escrow...")
    escrow = EscrowAccount.objects.create(
        buyer=buyer,
        seller=seller,
        title="Test Transaction",
        total_amount=Decimal('1000.00'),
        currency='USD',
        status=EscrowStatus.CREATED,
        expires_at=timezone.now() + timedelta(days=30)
    )
    print(f"   ✅ Escrow {escrow.reference_code} created.")

    # 3. Transition to FUNDED (Trigger Logic)
    print("\n3. Testing Atomic Transition to FUNDED...")
    try:
        updated_escrow = EscrowService.transition_status(
            escrow_id=escrow.id,
            next_status=EscrowStatus.FUNDED,
            actor=buyer,
            reason="Payment received via Wire"
        )
        print("   ✅ Transition successful.")
    except Exception as e:
        print(f"   ❌ Transition FAILED: {e}")
        return

    # 4. Verify Calculations
    print("\n4. Verifying Logic & Schema...")
    
    # Check SLA (Should be 4 hours due to override, not 24)
    expected_release = updated_escrow.funded_at + timedelta(hours=4)
    # Allow small delta for execution time
    time_diff = abs((updated_escrow.auto_release_at - expected_release).total_seconds())
    
    if time_diff < 10:
        print(f"   ✅ SLA Logic Correct: Release set for {updated_escrow.auto_release_at} (approx 4 hours from now)")
    else:
        print(f"   ❌ SLA Logic FAILED: Expected ~{expected_release}, got {updated_escrow.auto_release_at}")

    # Check Audit Log
    logs = AuditLog.objects.filter(entity_id=escrow.id)
    if logs.exists():
        print(f"   ✅ Audit Log Found: {logs.count()} entries.")
        latest = logs.first()
        print(f"      - Action: {latest.action}")
        print(f"      - Changes: {latest.changes or latest.new_value}")
        if latest.actor == buyer:
             print("      - Actor Correct.")
    else:
        print("   ❌ NO Audit Logs created!")

    # Check Fee Applied
    if updated_escrow.fee_applied is not None:
         print(f"   ✅ Fee Applied Recorded: {updated_escrow.fee_applied}")
    else:
         print("   ❌ Fee Applied NOT Recorded.")

if __name__ == '__main__':
    verify_advanced_schema()
