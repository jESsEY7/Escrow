"""
Audit and Admin URL configuration.
"""
from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from apps.core.permissions import IsAdmin, IsAuditor
from apps.audit.models import AuditLog, SystemEvent
from rest_framework import status

app_name = 'audit'


@api_view(['GET'])
@permission_classes([IsAuditor])
def audit_logs(request):
    """Get audit logs."""
    entity_type = request.query_params.get('entity_type')
    entity_id = request.query_params.get('entity_id')
    action = request.query_params.get('action')
    limit = int(request.query_params.get('limit', 100))

    logs = AuditLog.objects.all()

    if entity_type:
        logs = logs.filter(entity_type=entity_type)
    if entity_id:
        logs = logs.filter(entity_id=entity_id)
    if action:
        logs = logs.filter(action=action)

    logs = logs.order_by('-created_at')[:limit]

    data = [{
        'id': str(log.id),
        'entity_type': log.entity_type,
        'entity_id': log.entity_id,
        'action': log.action,
        'actor_email': log.actor_email,
        'ip_address': log.ip_address,
        'changes': log.changes,
        'created_at': log.created_at,
    } for log in logs]

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAdmin])
def system_events(request):
    """Get system events."""
    severity = request.query_params.get('severity')
    is_resolved = request.query_params.get('is_resolved')
    limit = int(request.query_params.get('limit', 100))

    events = SystemEvent.objects.all()

    if severity:
        events = events.filter(severity=severity)
    if is_resolved is not None:
        events = events.filter(is_resolved=is_resolved.lower() == 'true')

    events = events.order_by('-created_at')[:limit]

    data = [{
        'id': str(event.id),
        'event_type': event.event_type,
        'severity': event.severity,
        'title': event.title,
        'message': event.message,
        'source': event.source,
        'is_resolved': event.is_resolved,
        'created_at': event.created_at,
    } for event in events]

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAdmin])
def metrics(request):
    """Get platform metrics."""
    from django.db.models import Count, Sum
    from apps.escrow.models import EscrowAccount
    from apps.transactions.models import Transaction
    from apps.disputes.models import Dispute
    from apps.users.models import User
    from apps.core.enums import EscrowStatus, TransactionStatus, DisputeStatus

    # User metrics
    total_users = User.objects.count()
    active_users = User.objects.filter(status='active').count()

    # Escrow metrics
    total_escrows = EscrowAccount.objects.count()
    active_escrows = EscrowAccount.objects.filter(
        status__in=[
            EscrowStatus.CREATED, EscrowStatus.FUNDED,
            EscrowStatus.MILESTONE_PENDING, EscrowStatus.PARTIALLY_RELEASED
        ]
    ).count()
    disputed_escrows = EscrowAccount.objects.filter(status=EscrowStatus.DISPUTED).count()

    # Transaction metrics
    total_volume = Transaction.objects.filter(
        status=TransactionStatus.COMPLETED,
        type='deposit'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Dispute metrics
    open_disputes = Dispute.objects.filter(
        status__in=[DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW, DisputeStatus.ARBITRATION]
    ).count()

    return Response({
        'users': {
            'total': total_users,
            'active': active_users,
        },
        'escrows': {
            'total': total_escrows,
            'active': active_escrows,
            'disputed': disputed_escrows,
        },
        'transactions': {
            'total_volume': str(total_volume),
        },
        'disputes': {
            'open': open_disputes,
        },
    })


urlpatterns = [
    path('audit-logs/', audit_logs, name='audit_logs'),
    path('system-events/', system_events, name='system_events'),
    path('metrics/', metrics, name='metrics'),
]
