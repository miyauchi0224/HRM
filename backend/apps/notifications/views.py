from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin, IsHR
from apps.common.mixins import SoftDeleteViewSetMixin
from .models import Notification, WebhookEndpoint
from .serializers import NotificationSerializer, WebhookEndpointSerializer, PersonalWebhookSerializer
from .webhooks import SENSITIVE_TYPES, build_payload, post_webhook


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
    qs = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({
        'unread_count': unread_count,
        'results': NotificationSerializer(qs, many=True).data,
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_read(request, pk):
    notif = Notification.objects.filter(pk=pk, user=request.user).first()
    if notif:
        notif.is_read = True
        notif.save()
    return Response({'status': 'ok'})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def read_all(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({'status': 'ok'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_types(request):
    """GET /api/v1/notifications/types/ — 通知種別の一覧（Webhook 設定画面用）"""
    return Response([
        {'value': v, 'label': label, 'sensitive': v in SENSITIVE_TYPES}
        for v, label in Notification.NotificationType.choices
    ])


class WebhookEndpointViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    """全社 Webhook（管理者が設定。人事は閲覧のみ）"""
    serializer_class = WebhookEndpointSerializer
    queryset         = WebhookEndpoint.objects.all()

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsHR()]
        return [IsAdmin()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='test')
    def test(self, request, pk=None):
        """POST /api/v1/notifications/webhooks/{id}/test/"""
        ep = self.get_object()
        ok = post_webhook(ep.provider, ep.url, build_payload(
            ep.provider, 'HRM 通知連携のテスト', f'「{ep.name}」への送信テストです。', '/notifications',
        ))
        if not ok:
            return Response({'error': '送信に失敗しました。URL を確認してください'},
                            status=status.HTTP_502_BAD_GATEWAY)
        return Response({'status': 'sent'})


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def personal_webhook(request):
    """GET/PUT /api/v1/notifications/personal-webhook/ — 本人宛て通知の転送先"""
    user = request.user
    if request.method == 'PUT':
        serializer = PersonalWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.personal_webhook_provider = serializer.validated_data['provider']
        user.personal_webhook_url      = serializer.validated_data['url']
        user.save(update_fields=['personal_webhook_provider', 'personal_webhook_url'])
    return Response({'provider': user.personal_webhook_provider, 'url': user.personal_webhook_url})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def personal_webhook_test(request):
    """POST /api/v1/notifications/personal-webhook/test/"""
    user = request.user
    if not user.personal_webhook_url:
        return Response({'error': '転送先が設定されていません'}, status=status.HTTP_400_BAD_REQUEST)
    ok = post_webhook(user.personal_webhook_provider, user.personal_webhook_url, build_payload(
        user.personal_webhook_provider, 'HRM 通知連携のテスト', 'この通知が届けば設定は完了です。', '/notifications',
    ))
    if not ok:
        return Response({'error': '送信に失敗しました。URL を確認してください'},
                        status=status.HTTP_502_BAD_GATEWAY)
    return Response({'status': 'sent'})
