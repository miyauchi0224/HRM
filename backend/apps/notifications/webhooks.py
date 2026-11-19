"""
通知の Slack / Teams 転送

Notification.send() から dispatch_notification() が呼ばれる。
- 全社 Webhook: 通知種別で絞り込んで転送（要配慮個人情報の種別は転送しない）
- 個人 Webhook: 本人宛ての通知をすべて転送

送信は別スレッドで行い、失敗してもアプリ内通知には影響させない（ログのみ）。
"""
import logging
import threading
from urllib.parse import urlparse

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# 全社 Webhook に転送しない通知種別（健康情報・ストレスチェックは要配慮個人情報）
SENSITIVE_TYPES = {'stress_check', 'health_checkup'}

# 送信先として許可するホスト（SSRF 対策）
_ALLOWED_HOSTS = {
    'slack': ('hooks.slack.com',),
    'teams': ('.webhook.office.com', '.logic.azure.com', '.powerplatform.com'),
}


def validate_webhook_url(provider: str, url: str) -> str | None:
    """問題があればエラーメッセージ、なければ None を返す"""
    parsed = urlparse(url or '')
    if parsed.scheme != 'https' or not parsed.hostname:
        return 'Webhook URL は https:// で始まる URL を指定してください'
    host = parsed.hostname.lower()
    allowed = _ALLOWED_HOSTS.get(provider)
    if not allowed:
        return '送信先の種類が正しくありません'
    if not any(host == a or (a.startswith('.') and host.endswith(a)) for a in allowed):
        if provider == 'slack':
            return 'Slack の Incoming Webhook URL（https://hooks.slack.com/...）を指定してください'
        return 'Teams の Webhook URL（*.webhook.office.com / *.logic.azure.com / *.powerplatform.com）を指定してください'
    return None


def build_payload(provider: str, title: str, message: str, related_url: str = '', prefix: str = '') -> dict:
    link = f'{settings.FRONTEND_URL.rstrip("/")}{related_url}' if related_url else ''
    heading = f'{prefix}{title}'
    if provider == 'slack':
        text = f'*{heading}*\n{message}'
        if link:
            text += f'\n<{link}|画面を開く>'
        return {'text': text}

    # Teams: Workflows の「Webhook 要求を受信したらチャネルに投稿する」が受け付ける Adaptive Card 形式
    body = [
        {'type': 'TextBlock', 'text': heading, 'weight': 'Bolder', 'wrap': True},
        {'type': 'TextBlock', 'text': message, 'wrap': True},
    ]
    card = {
        '$schema': 'http://adaptivecards.io/schemas/adaptive-card.json',
        'type': 'AdaptiveCard', 'version': '1.4', 'body': body,
    }
    if link:
        card['actions'] = [{'type': 'Action.OpenUrl', 'title': '画面を開く', 'url': link}]
    return {
        'type': 'message',
        'attachments': [{'contentType': 'application/vnd.microsoft.card.adaptive', 'content': card}],
    }


def post_webhook(provider: str, url: str, payload: dict) -> bool:
    """1件送信する。成功なら True"""
    if validate_webhook_url(provider, url):
        logger.warning('許可されていない Webhook URL への送信を中止しました: %s', url)
        return False
    try:
        res = requests.post(url, json=payload, timeout=settings.WEBHOOK_TIMEOUT_SECONDS)
        if res.status_code >= 400:
            logger.warning('Webhook 送信が失敗しました: %s %s', res.status_code, res.text[:200])
            return False
        return True
    except requests.RequestException:
        logger.exception('Webhook 送信でエラーが発生しました')
        return False


def _targets_for(notification):
    """(provider, url, payload) のリストを作る"""
    from .models import WebhookEndpoint
    targets = []
    user = notification.user

    if user.personal_webhook_provider and user.personal_webhook_url:
        targets.append((
            user.personal_webhook_provider, user.personal_webhook_url,
            build_payload(user.personal_webhook_provider, notification.title,
                          notification.message, notification.related_url),
        ))

    if notification.type not in SENSITIVE_TYPES:
        employee = getattr(user, 'employee', None)
        name = employee.full_name if employee else user.email
        for ep in WebhookEndpoint.objects.filter(is_active=True):
            if notification.type in (ep.notification_types or []):
                targets.append((
                    ep.provider, ep.url,
                    build_payload(ep.provider, notification.title, notification.message,
                                  notification.related_url, prefix=f'[{name}さん宛] '),
                ))
    return targets


def dispatch_notification(notification):
    try:
        targets = _targets_for(notification)
    except Exception:
        logger.exception('Webhook の送信先取得に失敗しました')
        return
    if not targets:
        return

    def _send():
        for provider, url, payload in targets:
            post_webhook(provider, url, payload)

    if settings.WEBHOOK_ASYNC:
        threading.Thread(target=_send, daemon=True).start()
    else:
        _send()
