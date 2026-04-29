import uuid
from django.db import models
from django.conf import settings
from apps.common.models import SoftDeleteModel


class UserCalendarToken(SoftDeleteModel):
    """ユーザーのカレンダーOAuthトークン（Microsoft / Google）"""
    class Provider(models.TextChoices):
        MICROSOFT = 'ms', 'Microsoft'
        GOOGLE = 'google', 'Google'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calendar_tokens')
    provider = models.CharField(max_length=20, choices=Provider.choices, verbose_name='プロバイダー')
    access_token = models.TextField(verbose_name='アクセストークン')
    refresh_token = models.TextField(blank=True, verbose_name='リフレッシュトークン')
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='有効期限')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'カレンダーOAuthトークン'
        unique_together = ('user', 'provider')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} - {self.get_provider_display()}'


class CalendarEvent(SoftDeleteModel):
    """ユーザーのカレンダーイベント（DB保存）"""
    class Provider(models.TextChoices):
        MICROSOFT = 'ms', 'Microsoft'
        GOOGLE = 'google', 'Google'
        LOCAL = 'local', 'ローカル'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calendar_events')
    title = models.CharField(max_length=200, verbose_name='イベントタイトル')
    start_datetime = models.DateTimeField(verbose_name='開始日時')
    end_datetime = models.DateTimeField(verbose_name='終了日時')
    provider = models.CharField(max_length=20, choices=Provider.choices, default=Provider.LOCAL, verbose_name='プロバイダー')
    external_id = models.CharField(max_length=500, blank=True, verbose_name='外部カレンダーID')
    url = models.URLField(blank=True, verbose_name='イベントURL')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'カレンダーイベント'
        verbose_name_plural = 'カレンダーイベント'
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['user', 'start_datetime']),
        ]

    def __str__(self):
        return f'{self.user} - {self.title} ({self.start_datetime.strftime("%Y-%m-%d %H:%M")})'
