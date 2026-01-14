"""
Escrow views for the Escrow Platform.
"""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from apps.escrow.models import EscrowAccount, Milestone
from apps.escrow.serializers import (
    EscrowListSerializer,
    EscrowDetailSerializer,
    EscrowCreateSerializer,
    EscrowFundSerializer,
    MilestoneSerializer,
    MilestoneCreateSerializer,
    MilestoneSubmitSerializer,
    MilestoneApproveSerializer,
    MilestoneRejectSerializer,
)
from apps.escrow.state_machine import EscrowStateMachine
from apps.core.permissions import (
    IsAuthenticated,
    IsEscrowParticipant,
    IsEscrowBuyer,
    IsEscrowSeller,
    IsKYCVerified,
    CanModifyEscrow,
)
from apps.core.enums import EscrowStatus, MilestoneStatus
from apps.audit.services.audit_service import AuditService
from apps.core.pagination import StandardResultsPagination


class EscrowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for escrow operations.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        """Filter escrows to those the user is part of."""
        user = self.request.user
        
        if user.role == 'admin':
            return EscrowAccount.objects.all()
        
        if user.role == 'auditor':
            return EscrowAccount.objects.all()
        
        if user.role == 'arbitrator':
            return EscrowAccount.objects.filter(
                Q(arbitrator=user) |
                Q(status=EscrowStatus.DISPUTED, arbitrator__isnull=True)
            )
        
        return EscrowAccount.objects.filter(
            Q(buyer=user) | Q(seller=user)
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return EscrowListSerializer
        if self.action == 'create':
            return EscrowCreateSerializer
        return EscrowDetailSerializer

    def get_permissions(self):
        if self.action in ['retrieve', 'list']:
            return [IsAuthenticated(), IsEscrowParticipant()]
        if self.action == 'create':
            return [IsAuthenticated(), IsKYCVerified()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsEscrowParticipant(), CanModifyEscrow()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """Create a new escrow."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        escrow = serializer.save()

        AuditService.log_action(
            entity_type='EscrowAccount',
            entity_id=str(escrow.id),
            action='create',
            actor=request.user,
            new_state=EscrowDetailSerializer(escrow, context={'request': request}).data,
        )

        return Response(
            EscrowDetailSerializer(escrow, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsEscrowBuyer])
    def fund(self, request, pk=None):
        """Fund the escrow."""
        escrow = self.get_object()

        if not EscrowStateMachine.can_fund(escrow):
            return Response(
                {'error': 'This escrow cannot be funded in its current state'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = EscrowFundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Verify amount matches escrow total
        if serializer.validated_data['amount'] != escrow.total_amount:
            return Response(
                {'error': f'Amount must equal escrow total: {escrow.total_amount}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process payment (simplified - in production would integrate with payment provider)
        from apps.transactions.services.payment_service import PaymentService
        
        try:
            transaction = PaymentService.process_deposit(
                escrow=escrow,
                amount=serializer.validated_data['amount'],
                payment_method=serializer.validated_data['payment_method'],
                initiated_by=request.user,
                payment_details=serializer.validated_data.get('payment_details'),
            )

            # Transition escrow to funded
            EscrowStateMachine.transition(
                escrow,
                EscrowStatus.FUNDED,
                actor=request.user,
                reason='Escrow funded'
            )

            # Auto-transition to milestone pending if no verification needed
            EscrowStateMachine.transition(
                escrow,
                EscrowStatus.MILESTONE_PENDING,
                actor=request.user,
                reason='Verification bypassed'
            )

            return Response({
                'message': 'Escrow funded successfully',
                'escrow': EscrowDetailSerializer(escrow, context={'request': request}).data,
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsEscrowBuyer])
    def cancel(self, request, pk=None):
        """Cancel the escrow (only if not funded)."""
        escrow = self.get_object()

        if escrow.status != EscrowStatus.CREATED:
            return Response(
                {'error': 'Only unfunded escrows can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        EscrowStateMachine.transition(
            escrow,
            EscrowStatus.CANCELLED,
            actor=request.user,
            reason=request.data.get('reason', 'Cancelled by buyer')
        )

        return Response({
            'message': 'Escrow cancelled',
            'escrow': EscrowDetailSerializer(escrow, context={'request': request}).data,
        })

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Get escrow timeline/history."""
        escrow = self.get_object()

        # Get audit logs for this escrow
        from apps.audit.models import AuditLog
        logs = AuditLog.objects.filter(
            entity_type='EscrowAccount',
            entity_id=str(escrow.id)
        ).order_by('-created_at')[:50]

        timeline = []
        for log in logs:
            timeline.append({
                'event_type': log.action,
                'title': log.action.replace('_', ' ').title(),
                'description': log.metadata.get('reason', '') if log.metadata else '',
                'timestamp': log.created_at,
                'actor': log.actor_email or 'System',
                'metadata': log.metadata,
            })

        return Response(timeline)


class MilestoneViewSet(viewsets.ModelViewSet):
    """
    ViewSet for milestone operations.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MilestoneSerializer

    def get_queryset(self):
        escrow_id = self.kwargs.get('escrow_pk')
        return Milestone.objects.filter(escrow_id=escrow_id)

    def get_escrow(self):
        escrow_id = self.kwargs.get('escrow_pk')
        return get_object_or_404(EscrowAccount, pk=escrow_id)

    @action(detail=True, methods=['post'])
    def submit(self, request, escrow_pk=None, pk=None):
        """Submit milestone for review (seller action)."""
        escrow = self.get_escrow()
        milestone = self.get_object()

        # Verify user is seller
        if escrow.seller != request.user:
            return Response(
                {'error': 'Only the seller can submit milestones'},
                status=status.HTTP_403_FORBIDDEN
            )

        if milestone.status != MilestoneStatus.PENDING:
            return Response(
                {'error': 'Milestone cannot be submitted in its current state'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = MilestoneSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        milestone.submit(notes=serializer.validated_data.get('notes', ''))

        if serializer.validated_data.get('deliverables'):
            milestone.deliverables = serializer.validated_data['deliverables']
            milestone.save()

        AuditService.log_action(
            entity_type='Milestone',
            entity_id=str(milestone.id),
            action='submit',
            actor=request.user,
            new_state={'status': milestone.status},
        )

        return Response(MilestoneSerializer(milestone).data)

    @action(detail=True, methods=['post'])
    def approve(self, request, escrow_pk=None, pk=None):
        """Approve milestone and trigger release (buyer action)."""
        escrow = self.get_escrow()
        milestone = self.get_object()

        # Verify user is buyer
        if escrow.buyer != request.user:
            return Response(
                {'error': 'Only the buyer can approve milestones'},
                status=status.HTTP_403_FORBIDDEN
            )

        if milestone.status != MilestoneStatus.SUBMITTED:
            return Response(
                {'error': 'Only submitted milestones can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )

        milestone.approve(approved_by=request.user)

        # Release funds for this milestone
        from apps.transactions.services.payment_service import PaymentService
        try:
            PaymentService.release_milestone(escrow, milestone, request.user)
            milestone.release()
        except Exception as e:
            return Response(
                {'error': f'Failed to release funds: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Check if all milestones are complete
        pending = escrow.milestones.exclude(status=MilestoneStatus.RELEASED).count()
        if pending == 0:
            EscrowStateMachine.transition(
                escrow,
                EscrowStatus.FULLY_RELEASED,
                actor=request.user,
                reason='All milestones completed'
            )
        else:
            # Update escrow to partially released if not already
            if escrow.status != EscrowStatus.PARTIALLY_RELEASED:
                EscrowStateMachine.transition(
                    escrow,
                    EscrowStatus.PARTIALLY_RELEASED,
                    actor=request.user,
                    reason=f'Milestone completed: {milestone.title}'
                )

        AuditService.log_action(
            entity_type='Milestone',
            entity_id=str(milestone.id),
            action='approve',
            actor=request.user,
            new_state={'status': milestone.status},
        )

        return Response(MilestoneSerializer(milestone).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, escrow_pk=None, pk=None):
        """Reject milestone (buyer action)."""
        escrow = self.get_escrow()
        milestone = self.get_object()

        if escrow.buyer != request.user:
            return Response(
                {'error': 'Only the buyer can reject milestones'},
                status=status.HTTP_403_FORBIDDEN
            )

        if milestone.status != MilestoneStatus.SUBMITTED:
            return Response(
                {'error': 'Only submitted milestones can be rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = MilestoneRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        milestone.reject(reason=serializer.validated_data['reason'])

        AuditService.log_action(
            entity_type='Milestone',
            entity_id=str(milestone.id),
            action='reject',
            actor=request.user,
            new_state={'status': milestone.status, 'reason': milestone.rejection_reason},
        )

        return Response(MilestoneSerializer(milestone).data)
