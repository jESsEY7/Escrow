"""
Dispute views for the Escrow Platform.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from apps.disputes.models import Dispute, Evidence, DisputeResponse, ArbitrationDecision, DisputeTimeline
from apps.disputes.serializers import (
    DisputeListSerializer,
    DisputeDetailSerializer,
    DisputeCreateSerializer,
    DisputeRespondSerializer,
    EvidenceSerializer,
    EvidenceCreateSerializer,
    ArbitrationRulingSerializer,
    ArbitrationDecisionSerializer,
)
from apps.escrow.models import EscrowAccount
from apps.escrow.state_machine import EscrowStateMachine
from apps.core.permissions import IsAuthenticated, IsDisputeParticipant, IsArbitrator, IsAdminOrArbitrator
from apps.core.enums import DisputeStatus, EscrowStatus
from apps.core.exceptions import DisputeAlreadyExistsError
from apps.audit.services.audit_service import AuditService
from apps.core.pagination import StandardResultsPagination


class DisputeViewSet(viewsets.ModelViewSet):
    """ViewSet for dispute operations."""
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        user = self.request.user

        if user.role == 'admin':
            return Dispute.objects.all()

        if user.role == 'auditor':
            return Dispute.objects.all()

        if user.role == 'arbitrator':
            return Dispute.objects.filter(
                Q(assigned_arbitrator=user) |
                Q(status=DisputeStatus.OPEN, assigned_arbitrator__isnull=True)
            )

        # Users can see disputes from their escrows
        return Dispute.objects.filter(
            Q(escrow__buyer=user) | Q(escrow__seller=user)
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return DisputeListSerializer
        if self.action == 'create':
            return DisputeCreateSerializer
        return DisputeDetailSerializer

    def create(self, request, *args, **kwargs):
        """Create a new dispute."""
        serializer = DisputeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        escrow_id = serializer.validated_data['escrow_id']
        escrow = get_object_or_404(EscrowAccount, pk=escrow_id)

        # Verify user is part of escrow
        user = request.user
        if user not in [escrow.buyer, escrow.seller]:
            return Response(
                {'error': 'You are not a participant in this escrow'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if escrow can be disputed
        if not EscrowStateMachine.can_dispute(escrow):
            return Response(
                {'error': 'This escrow cannot be disputed in its current state'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for existing active dispute
        existing = Dispute.objects.filter(
            escrow=escrow,
            status__in=[DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW, DisputeStatus.ARBITRATION]
        ).exists()

        if existing:
            raise DisputeAlreadyExistsError()

        # Determine who the dispute is against
        against = escrow.seller if user == escrow.buyer else escrow.buyer

        # Create dispute
        escrow_settings = settings.ESCROW_SETTINGS
        
        # Calculate SLA based on Plan
        from apps.plans.services import SLAEngine
        sla_hours = SLAEngine.get_sla_hours(user)
        resolution_deadline = timezone.now() + timezone.timedelta(hours=sla_hours)
        
        dispute = Dispute.objects.create(
            escrow=escrow,
            raised_by=user,
            against=against,
            reason=serializer.validated_data['reason'],
            description=serializer.validated_data['description'],
            disputed_amount=serializer.validated_data.get('disputed_amount', escrow.total_amount),
            response_deadline=timezone.now() + timezone.timedelta(days=escrow_settings['DISPUTE_RESPONSE_DAYS']),
            resolution_deadline=resolution_deadline,
        )
        
        # Start SLA timer (Redis/Celery)
        SLAEngine.start_sla_timer(dispute)

        # Transition escrow to disputed
        EscrowStateMachine.transition(
            escrow,
            EscrowStatus.DISPUTED,
            actor=user,
            reason=f'Dispute raised: {dispute.reason}'
        )

        # Create timeline entry
        DisputeTimeline.objects.create(
            dispute=dispute,
            event_type='dispute_created',
            title='Dispute Created',
            description=serializer.validated_data['description'],
            actor=user,
        )

        AuditService.log_action(
            entity_type='Dispute',
            entity_id=str(dispute.id),
            action='dispute_raised',
            actor=user,
            new_state={
                'reason': dispute.reason,
                'escrow': escrow.reference_code,
            },
        )

        return Response(
            DisputeDetailSerializer(dispute).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Respond to a dispute."""
        dispute = self.get_object()

        # Verify user is the party against whom dispute was raised
        if dispute.against != request.user:
            return Response(
                {'error': 'Only the respondent can respond to this dispute'},
                status=status.HTTP_403_FORBIDDEN
            )

        if dispute.status not in [DisputeStatus.OPEN, DisputeStatus.AWAITING_EVIDENCE]:
            return Response(
                {'error': 'This dispute is not open for responses'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = DisputeRespondSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response = DisputeResponse.objects.create(
            dispute=dispute,
            responder=request.user,
            content=serializer.validated_data['content'],
            accepts_claim=serializer.validated_data.get('accepts_claim'),
            counter_offer=serializer.validated_data.get('counter_offer'),
        )

        # Update dispute status
        dispute.status = DisputeStatus.UNDER_REVIEW
        dispute.save()

        DisputeTimeline.objects.create(
            dispute=dispute,
            event_type='response_submitted',
            title='Response Submitted',
            description=f'Respondent {"accepts" if response.accepts_claim else "rejects"} the claim',
            actor=request.user,
        )

        return Response(DisputeDetailSerializer(dispute).data)

    @action(detail=True, methods=['post'])
    def evidence(self, request, pk=None):
        """Submit evidence for a dispute."""
        dispute = self.get_object()

        # Verify user is participant
        if request.user not in [dispute.raised_by, dispute.against]:
            return Response(
                {'error': 'You are not a participant in this dispute'},
                status=status.HTTP_403_FORBIDDEN
            )

        if dispute.is_resolved:
            return Response(
                {'error': 'Cannot submit evidence to a resolved dispute'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = EvidenceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_data = {}
        if 'file' in request.FILES:
            file_obj = request.FILES['file']
            
            # Create directory
            import os
            from django.conf import settings
            evidence_dir = os.path.join(settings.MEDIA_ROOT, 'evidence', str(dispute.id))
            os.makedirs(evidence_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(evidence_dir, file_obj.name)
            with open(file_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)
            
            # Compute Hash
            import hashlib
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

            file_data = {
                'file_url': f'/media/evidence/{dispute.id}/{file_obj.name}',
                'file_name': file_obj.name,
                'file_size': file_obj.size,
                'file_hash': file_hash,
                'evidence_type': 'document'  # Default to document
            }

        evidence = Evidence.objects.create(
            dispute=dispute,
            submitted_by=request.user,
            **serializer.validated_data,
            **file_data
        )

        DisputeTimeline.objects.create(
            dispute=dispute,
            event_type='evidence_submitted',
            title='Evidence Submitted',
            description=f'New evidence: {evidence.title}',
            actor=request.user,
        )

        return Response(EvidenceSerializer(evidence).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrArbitrator])
    def assign_arbitrator(self, request, pk=None):
        """Assign an arbitrator to the dispute."""
        dispute = self.get_object()

        if dispute.assigned_arbitrator:
            return Response(
                {'error': 'Arbitrator already assigned'},
                status=status.HTTP_400_BAD_REQUEST
            )

        dispute.assign_arbitrator(request.user)

        DisputeTimeline.objects.create(
            dispute=dispute,
            event_type='arbitrator_assigned',
            title='Arbitrator Assigned',
            description=f'Arbitrator: {request.user.email}',
            actor=request.user,
        )

        return Response(DisputeDetailSerializer(dispute).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrArbitrator])
    def ruling(self, request, pk=None):
        """Make an arbitration ruling."""
        dispute = self.get_object()

        if dispute.status != DisputeStatus.ARBITRATION:
            return Response(
                {'error': 'Dispute is not in arbitration'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if dispute.assigned_arbitrator != request.user and request.user.role != 'admin':
            return Response(
                {'error': 'You are not the assigned arbitrator'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ArbitrationRulingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create decision
        decision = ArbitrationDecision.objects.create(
            dispute=dispute,
            arbitrator=request.user,
            ruling=serializer.validated_data['ruling'],
            reasoning=serializer.validated_data['reasoning'],
            buyer_amount=serializer.validated_data['buyer_amount'],
            seller_amount=serializer.validated_data['seller_amount'],
            fee_paid_by=serializer.validated_data['fee_paid_by'],
            appeal_deadline=timezone.now() + timezone.timedelta(days=7),
        )

        # Update dispute
        dispute.resolve(summary=decision.reasoning)

        # Transition escrow
        EscrowStateMachine.transition(
            dispute.escrow,
            EscrowStatus.RESOLVED,
            actor=request.user,
            reason=f'Arbitration ruling: {decision.ruling}'
        )

        DisputeTimeline.objects.create(
            dispute=dispute,
            event_type='ruling_made',
            title='Arbitration Ruling',
            description=f'Ruling: {decision.ruling}',
            actor=request.user,
            metadata={
                'buyer_amount': str(decision.buyer_amount),
                'seller_amount': str(decision.seller_amount),
            }
        )

        AuditService.log_action(
            entity_type='ArbitrationDecision',
            entity_id=str(decision.id),
            action='ruling_made',
            actor=request.user,
            new_state={
                'ruling': decision.ruling,
                'buyer_amount': str(decision.buyer_amount),
                'seller_amount': str(decision.seller_amount),
            },
        )

        return Response(ArbitrationDecisionSerializer(decision).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrArbitrator])
    def execute_ruling(self, request, pk=None):
        """Execute the arbitration ruling (trigger fund transfers)."""
        dispute = self.get_object()

        if not hasattr(dispute, 'decision'):
            return Response(
                {'error': 'No ruling has been made'},
                status=status.HTTP_400_BAD_REQUEST
            )

        decision = dispute.decision

        if decision.is_executed:
            return Response(
                {'error': 'Ruling has already been executed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            decision.execute()

            DisputeTimeline.objects.create(
                dispute=dispute,
                event_type='ruling_executed',
                title='Ruling Executed',
                description='Fund transfers completed',
                actor=request.user,
            )

            return Response({'message': 'Ruling executed successfully'})

        except Exception as e:
            return Response(
                {'error': f'Failed to execute ruling: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
