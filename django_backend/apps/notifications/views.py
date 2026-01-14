"""
Notification API views.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.serializers import (
    NotificationSerializer,
    NotificationPreferenceSerializer,
    MarkReadSerializer
)
from apps.notifications.services import NotificationService


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing notifications.
    
    list: Get all notifications for current user
    retrieve: Get a specific notification
    mark_read: Mark notifications as read
    unread_count: Get count of unread notifications
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        
        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        # Filter by type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(type=notification_type)
        
        return queryset.order_by('-created_at')

    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        """Mark notifications as read."""
        serializer = MarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if serializer.validated_data.get('mark_all'):
            count = NotificationService.mark_all_as_read(request.user)
        else:
            notification_ids = serializer.validated_data.get('notification_ids', [])
            count = NotificationService.mark_as_read(notification_ids, request.user)
        
        return Response({'marked_count': count})

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications."""
        count = NotificationService.get_unread_count(request.user)
        return Response({'unread_count': count})


class NotificationPreferenceViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing notification preferences.
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Get or create preferences for current user."""
        prefs, _ = NotificationPreference.objects.get_or_create(user=self.request.user)
        return prefs

    def list(self, request):
        """Get current user's notification preferences."""
        prefs = self.get_object()
        serializer = self.get_serializer(prefs)
        return Response(serializer.data)

    def create(self, request):
        """Update notification preferences."""
        prefs = self.get_object()
        serializer = self.get_serializer(prefs, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
