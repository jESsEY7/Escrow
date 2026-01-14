"""
Transaction views for the Escrow Platform.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from apps.transactions.models import Transaction
from apps.transactions.serializers import (
    TransactionListSerializer,
    TransactionDetailSerializer,
)
from apps.transactions.services.payment_service import PaymentService
from apps.core.pagination import TransactionPagination


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing transactions.
    Read-only - transactions are created through escrow operations.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = TransactionPagination

    def get_queryset(self):
        user = self.request.user

        if user.role == 'admin':
            return Transaction.objects.all()

        if user.role == 'auditor':
            return Transaction.objects.all()

        # Users can see transactions from their escrows
        return Transaction.objects.filter(
            Q(escrow__buyer=user) |
            Q(escrow__seller=user) |
            Q(initiated_by=user) |
            Q(recipient=user)
        ).distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return TransactionListSerializer
        return TransactionDetailSerializer


class UserTransactionsView(APIView):
    """Get transactions for the current user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = PaymentService.get_user_transactions(request.user)
        serializer = TransactionListSerializer(transactions, many=True)
        return Response(serializer.data)
