"""
Escrow serializers for the Escrow Platform.
"""
from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from apps.escrow.models import EscrowAccount, Milestone, EscrowDocument, EscrowInvitation
from apps.users.serializers import UserSerializer
from apps.core.enums import EscrowStatus, EscrowType, MilestoneStatus


class MilestoneSerializer(serializers.ModelSerializer):
    """Serializer for milestones."""
    is_complete = serializers.BooleanField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Milestone
        fields = [
            'id', 'title', 'description', 'order', 'amount', 'status',
            'due_date', 'submitted_at', 'approved_at', 'released_at',
            'is_complete', 'is_overdue', 'deliverables', 'conditions',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'submitted_at', 'approved_at', 'released_at',
            'created_at', 'updated_at'
        ]


class MilestoneCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating milestones."""

    class Meta:
        model = Milestone
        fields = ['title', 'description', 'amount', 'order', 'due_date', 'conditions']


class EscrowDocumentSerializer(serializers.ModelSerializer):
    """Serializer for escrow documents."""

    class Meta:
        model = EscrowDocument
        fields = [
            'id', 'name', 'file_url', 'file_type', 'file_size', 'file_hash',
            'description', 'is_contract', 'is_signed', 'created_at'
        ]
        read_only_fields = ['id', 'file_hash', 'created_at']


class EscrowListSerializer(serializers.ModelSerializer):
    """Serializer for escrow list view (minimal data)."""
    buyer_name = serializers.CharField(source='buyer.full_name', read_only=True)
    seller_name = serializers.CharField(source='seller.full_name', read_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = EscrowAccount
        fields = [
            'id', 'reference_code', 'title', 'status', 'escrow_type',
            'total_amount', 'currency', 'buyer_name', 'seller_name',
            'progress_percentage', 'is_active', 'expires_at', 'created_at'
        ]


class EscrowDetailSerializer(serializers.ModelSerializer):
    """Serializer for escrow detail view (full data)."""
    buyer = UserSerializer(read_only=True)
    seller = UserSerializer(read_only=True)
    arbitrator = UserSerializer(read_only=True)
    milestones = MilestoneSerializer(many=True, read_only=True)
    documents = EscrowDocumentSerializer(many=True, read_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)
    platform_fee = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)
    net_amount = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_funded = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    wallet_balance = serializers.SerializerMethodField()
    allowed_actions = serializers.SerializerMethodField()

    class Meta:
        model = EscrowAccount
        fields = [
            'id', 'reference_code', 'buyer', 'seller', 'arbitrator',
            'status', 'previous_status', 'title', 'description', 'escrow_type',
            'total_amount', 'currency', 'platform_fee_percent', 'platform_fee', 'net_amount',
            'terms', 'inspection_period_days', 'auto_release_days',
            'conditions', 'automation_enabled',
            'expires_at', 'funded_at', 'completed_at', 'cancelled_at',
            'milestones', 'documents', 'progress_percentage',
            'is_active', 'is_funded', 'is_expired',
            'wallet_balance', 'allowed_actions',
            'notes', 'metadata', 'created_at', 'updated_at'
        ]

    def get_wallet_balance(self, obj):
        """Get wallet balance if exists."""
        try:
            wallet = obj.wallet
            return {
                'balance': str(wallet.balance),
                'held_balance': str(wallet.held_balance),
                'available_balance': str(wallet.available_balance),
                'released_amount': str(wallet.released_amount),
            }
        except:
            return None

    def get_allowed_actions(self, obj):
        """Get actions the current user can perform."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return []

        user = request.user
        actions = []

        from apps.escrow.state_machine import EscrowStateMachine

        # Check user role in this escrow
        is_buyer = obj.buyer_id == user.id
        is_seller = obj.seller_id == user.id
        is_arbitrator = obj.arbitrator_id == user.id if obj.arbitrator_id else False
        is_admin = user.role == 'admin'

        if is_buyer:
            if EscrowStateMachine.can_fund(obj):
                actions.append('fund')
            if obj.status == EscrowStatus.MILESTONE_PENDING:
                actions.append('approve_milestone')
            if obj.status == EscrowStatus.CREATED:
                actions.append('cancel')
            if EscrowStateMachine.can_dispute(obj):
                actions.append('dispute')

        if is_seller:
            if obj.status in [EscrowStatus.MILESTONE_PENDING, EscrowStatus.PARTIALLY_RELEASED]:
                actions.append('submit_milestone')
            if obj.status == EscrowStatus.FUNDED:
                actions.append('request_release')
            if EscrowStateMachine.can_dispute(obj):
                actions.append('dispute')

        if is_arbitrator or is_admin:
            if obj.status == EscrowStatus.DISPUTED:
                actions.append('make_ruling')

        if is_admin:
            actions.append('override')

        return actions


class EscrowCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new escrow."""
    milestones = MilestoneCreateSerializer(many=True, required=False)
    seller_email = serializers.EmailField(write_only=True, required=False)

    class Meta:
        model = EscrowAccount
        fields = [
            'title', 'description', 'escrow_type', 'total_amount', 'currency',
            'terms', 'inspection_period_days', 'auto_release_days',
            'milestones', 'seller_email'
        ]

    def validate_total_amount(self, value):
        """Validate escrow amount against limits."""
        settings_escrow = settings.ESCROW_SETTINGS
        
        if value < Decimal(str(settings_escrow['MIN_ESCROW_AMOUNT'])):
            raise serializers.ValidationError(
                f"Minimum escrow amount is {settings_escrow['MIN_ESCROW_AMOUNT']}"
            )
        
        if value > Decimal(str(settings_escrow['MAX_ESCROW_AMOUNT'])):
            raise serializers.ValidationError(
                f"Maximum escrow amount is {settings_escrow['MAX_ESCROW_AMOUNT']}"
            )
        
        return value

    def validate_milestones(self, value):
        """Validate milestones match total amount."""
        if value:
            total = sum(m['amount'] for m in value)
            # Total will be validated against escrow amount in create()
            return value
        return value

    def create(self, validated_data):
        milestones_data = validated_data.pop('milestones', [])
        seller_email = validated_data.pop('seller_email', None)
        
        # Set defaults
        validated_data['buyer'] = self.context['request'].user
        validated_data['expires_at'] = timezone.now() + timezone.timedelta(
            days=settings.ESCROW_SETTINGS['DEFAULT_EXPIRY_DAYS']
        )
        
        # Calculate and set platform fee based on user's plan/overrides
        from apps.plans.services import FeeEngine
        validated_data['platform_fee_percent'] = FeeEngine.get_fee_percent(self.context['request'].user)

        
        escrow = EscrowAccount.objects.create(**validated_data)

        # Create milestones
        for idx, milestone_data in enumerate(milestones_data):
            milestone_data['order'] = idx + 1
            Milestone.objects.create(escrow=escrow, **milestone_data)

        # Validate milestones total
        if milestones_data:
            milestones_total = sum(Decimal(str(m['amount'])) for m in milestones_data)
            if milestones_total != escrow.total_amount:
                raise serializers.ValidationError({
                    'milestones': f'Milestones total ({milestones_total}) must equal escrow amount ({escrow.total_amount})'
                })

        # Create wallet
        from apps.transactions.models import Wallet
        Wallet.objects.create(escrow=escrow, currency=escrow.currency)

        # Send invitation if seller email provided
        if seller_email:
            from apps.escrow.services.invitation_service import InvitationService
            InvitationService.send_invitation(escrow, seller_email, 'seller')

        return escrow


class EscrowFundSerializer(serializers.Serializer):
    """Serializer for funding an escrow."""
    payment_method = serializers.ChoiceField(
        choices=[
            ('bank_transfer', 'Bank Transfer'),
            ('credit_card', 'Credit Card'),
            ('mpesa', 'M-Pesa'),
        ]
    )
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    payment_details = serializers.JSONField(required=False)


class MilestoneSubmitSerializer(serializers.Serializer):
    """Serializer for submitting a milestone."""
    notes = serializers.CharField(required=False, allow_blank=True)
    deliverables = serializers.JSONField(required=False)


class MilestoneApproveSerializer(serializers.Serializer):
    """Serializer for approving a milestone."""
    notes = serializers.CharField(required=False, allow_blank=True)


class MilestoneRejectSerializer(serializers.Serializer):
    """Serializer for rejecting a milestone."""
    reason = serializers.CharField(required=True)


class EscrowTimelineSerializer(serializers.Serializer):
    """Serializer for escrow timeline events."""
    event_type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    timestamp = serializers.DateTimeField()
    actor = serializers.CharField()
    metadata = serializers.JSONField()
