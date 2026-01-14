"""
Dispute serializers for the Escrow Platform.
"""
from rest_framework import serializers
from apps.disputes.models import (
    Dispute, DisputeResponse, Evidence, ArbitrationDecision, DisputeTimeline
)
from apps.users.serializers import UserSerializer
from apps.core.enums import DisputeReason, RulingType


class EvidenceSerializer(serializers.ModelSerializer):
    """Serializer for evidence."""
    submitted_by_email = serializers.CharField(source='submitted_by.email', read_only=True)

    class Meta:
        model = Evidence
        fields = [
            'id', 'title', 'description', 'evidence_type',
            'file_url', 'file_name', 'file_size', 'file_hash',
            'text_content', 'external_url',
            'is_verified', 'submitted_by_email', 'created_at'
        ]
        read_only_fields = ['id', 'file_hash', 'is_verified', 'created_at']


class EvidenceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating evidence."""

    class Meta:
        model = Evidence
        fields = [
            'title', 'description', 'evidence_type',
            'file_url', 'file_name', 'file_size',
            'text_content', 'external_url', 'file'
        ]
    
    file = serializers.FileField(required=False, write_only=True)


class DisputeResponseSerializer(serializers.ModelSerializer):
    """Serializer for dispute responses."""
    responder_email = serializers.CharField(source='responder.email', read_only=True)

    class Meta:
        model = DisputeResponse
        fields = [
            'id', 'content', 'accepts_claim', 'counter_offer',
            'responder_email', 'created_at'
        ]


class DisputeTimelineSerializer(serializers.ModelSerializer):
    """Serializer for dispute timeline entries."""
    actor_email = serializers.CharField(source='actor.email', read_only=True, allow_null=True)

    class Meta:
        model = DisputeTimeline
        fields = [
            'id', 'event_type', 'title', 'description',
            'actor_email', 'metadata', 'created_at'
        ]


class ArbitrationDecisionSerializer(serializers.ModelSerializer):
    """Serializer for arbitration decisions."""
    arbitrator_email = serializers.CharField(source='arbitrator.email', read_only=True)
    total_amount = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)

    class Meta:
        model = ArbitrationDecision
        fields = [
            'id', 'ruling', 'reasoning',
            'buyer_amount', 'seller_amount', 'total_amount',
            'arbitration_fee', 'fee_paid_by',
            'is_final', 'is_executed', 'executed_at',
            'can_appeal', 'appeal_deadline',
            'arbitrator_email', 'created_at', 'updated_at'
        ]


class DisputeListSerializer(serializers.ModelSerializer):
    """Serializer for dispute list view."""
    escrow_reference = serializers.CharField(source='escrow.reference_code', read_only=True)
    raised_by_email = serializers.CharField(source='raised_by.email', read_only=True)
    is_open = serializers.BooleanField(read_only=True)
    days_until_deadline = serializers.IntegerField(read_only=True)

    class Meta:
        model = Dispute
        fields = [
            'id', 'escrow_reference', 'reason', 'status',
            'raised_by_email', 'disputed_amount',
            'is_open', 'days_until_deadline',
            'resolution_deadline', 'created_at'
        ]


class DisputeDetailSerializer(serializers.ModelSerializer):
    """Serializer for dispute detail view."""
    escrow_reference = serializers.CharField(source='escrow.reference_code', read_only=True)
    raised_by = UserSerializer(read_only=True)
    against = UserSerializer(read_only=True)
    assigned_arbitrator = UserSerializer(read_only=True)
    evidence = EvidenceSerializer(many=True, read_only=True)
    responses = DisputeResponseSerializer(many=True, read_only=True)
    timeline = DisputeTimelineSerializer(many=True, read_only=True)
    decision = ArbitrationDecisionSerializer(read_only=True)
    is_open = serializers.BooleanField(read_only=True)
    is_resolved = serializers.BooleanField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    days_until_deadline = serializers.IntegerField(read_only=True)

    class Meta:
        model = Dispute
        fields = [
            'id', 'escrow', 'escrow_reference',
            'reason', 'description', 'status', 'disputed_amount',
            'raised_by', 'against', 'assigned_arbitrator', 'assigned_at',
            'response_deadline', 'resolution_deadline', 'escalation_deadline',
            'resolved_at', 'resolution_summary',
            'evidence', 'responses', 'timeline', 'decision',
            'is_open', 'is_resolved', 'is_overdue', 'days_until_deadline',
            'metadata', 'created_at', 'updated_at'
        ]


class DisputeCreateSerializer(serializers.Serializer):
    """Serializer for creating a dispute."""
    escrow_id = serializers.UUIDField()
    reason = serializers.ChoiceField(choices=DisputeReason.choices)
    description = serializers.CharField()
    disputed_amount = serializers.DecimalField(
        max_digits=20, decimal_places=2, required=False
    )


class DisputeRespondSerializer(serializers.Serializer):
    """Serializer for responding to a dispute."""
    content = serializers.CharField()
    accepts_claim = serializers.BooleanField(required=False, allow_null=True)
    counter_offer = serializers.DecimalField(
        max_digits=20, decimal_places=2, required=False
    )


class ArbitrationRulingSerializer(serializers.Serializer):
    """Serializer for creating an arbitration ruling."""
    ruling = serializers.ChoiceField(choices=RulingType.choices)
    reasoning = serializers.CharField()
    buyer_amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    seller_amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    fee_paid_by = serializers.ChoiceField(
        choices=[('buyer', 'Buyer'), ('seller', 'Seller'), ('split', 'Split'), ('platform', 'Platform')],
        default='split'
    )

    def validate(self, attrs):
        """Ensure amounts are valid."""
        buyer = attrs['buyer_amount']
        seller = attrs['seller_amount']

        if buyer < 0 or seller < 0:
            raise serializers.ValidationError('Amounts cannot be negative')

        return attrs
