"""
Notification serializers for the API.
"""
from rest_framework import serializers
from apps.notifications.models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notification list and detail views."""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'message', 'action_url',
            'priority', 'entity_type', 'entity_id',
            'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = fields


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user notification preferences."""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'email_enabled', 'sms_enabled', 'push_enabled',
            'type_preferences',
            'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end',
            'timezone', 'email_digest', 'digest_frequency'
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        return NotificationPreference.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class MarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read."""
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    mark_all = serializers.BooleanField(default=False)
