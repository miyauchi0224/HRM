from rest_framework import serializers
from apps.accounts.models import User
from .models import Notification, WebhookEndpoint
from .webhooks import SENSITIVE_TYPES, validate_webhook_url


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notification
        fields = ['id', 'type', 'title', 'message', 'related_url', 'is_read', 'created_at']


class WebhookEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model  = WebhookEndpoint
        fields = ['id', 'name', 'provider', 'url', 'notification_types', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_notification_types(self, value):
        valid = {c[0] for c in Notification.NotificationType.choices}
        if not value:
            raise serializers.ValidationError('転送する通知種別を1つ以上選んでください')
        unknown = [v for v in value if v not in valid]
        if unknown:
            raise serializers.ValidationError(f'不明な通知種別です: {", ".join(unknown)}')
        if any(v in SENSITIVE_TYPES for v in value):
            raise serializers.ValidationError('健康診断・ストレスチェックの通知は全社の転送先に設定できません')
        return value

    def validate(self, data):
        provider = data.get('provider') or getattr(self.instance, 'provider', '')
        url      = data.get('url') or getattr(self.instance, 'url', '')
        error = validate_webhook_url(provider, url)
        if error:
            raise serializers.ValidationError({'url': error})
        return data


class PersonalWebhookSerializer(serializers.Serializer):
    """本人宛て通知の転送先。url を空にすると解除"""
    provider = serializers.ChoiceField(choices=User.WebhookProvider.choices, required=False, allow_blank=True)
    url      = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate(self, data):
        provider = data.get('provider', '')
        url      = data.get('url', '')
        if not url:
            return {'provider': '', 'url': ''}
        if not provider:
            raise serializers.ValidationError({'provider': '送信先の種類を選んでください'})
        error = validate_webhook_url(provider, url)
        if error:
            raise serializers.ValidationError({'url': error})
        return data
