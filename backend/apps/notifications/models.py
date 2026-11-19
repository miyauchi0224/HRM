import uuid
from django.db import models
from apps.accounts.models import User
from apps.common.models import SoftDeleteModel


class Notification(SoftDeleteModel):
    class NotificationType(models.TextChoices):
        ATTENDANCE_MOD  = 'attendance_mod',  '打刻修正申請'
        LEAVE_REQUEST   = 'leave_request',   '休暇申請'
        MBO_FEEDBACK    = 'mbo_feedback',    'MBOフィードバック'
        EXPENSE_REQUEST = 'expense_request', '経費申請'
        OVERTIME_ALERT        = 'overtime_alert',        '残業時間アラート（月）'
        OVERTIME_ANNUAL_ALERT = 'overtime_annual_alert', '残業時間アラート（年）'
        LEAVE_ALERT           = 'leave_alert',           '有給残日数アラート'
        SKILL_EXPIRY          = 'skill_expiry',          '資格有効期限アラート'
        SYSTEM                = 'system',                'システム通知'
        STRESS_CHECK          = 'stress_check',          'ストレスチェック'
        ONBOARDING            = 'onboarding',            'オンボーディング'
        LEAVE_OBLIGATION      = 'leave_obligation',      '有給 年5日取得義務'
        APPROVAL_REMINDER     = 'approval_reminder',     '承認リマインド'
        WORK_INTERVAL         = 'work_interval',         '勤務間インターバル'
        HEALTH_CHECKUP        = 'health_checkup',        '健康診断'
        ONE_ON_ONE            = 'one_on_one',            '1on1'
        PULSE_SURVEY          = 'pulse_survey',          'パルスサーベイ'

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type        = models.CharField(max_length=30, choices=NotificationType.choices)
    title       = models.CharField(max_length=200, verbose_name='タイトル')
    message     = models.TextField(verbose_name='メッセージ')
    related_url = models.CharField(max_length=500, blank=True, verbose_name='関連URL')
    is_read     = models.BooleanField(default=False, verbose_name='既読')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '通知'
        ordering     = ['-created_at']

    @classmethod
    def send(cls, user, type_, title, message, related_url=''):
        """通知を作成するユーティリティメソッド（Slack / Teams への転送も行う）"""
        notification = cls.objects.create(
            user=user, type=type_, title=title,
            message=message, related_url=related_url
        )
        from .webhooks import dispatch_notification
        dispatch_notification(notification)
        return notification


class WebhookEndpoint(SoftDeleteModel):
    """
    全社向けの通知転送先（Slack / Teams の Incoming Webhook）

    notification_types に含まれる種別の通知だけを転送する。
    健康診断・ストレスチェックは要配慮個人情報のため転送対象にできない。
    """
    class Provider(models.TextChoices):
        SLACK = 'slack', 'Slack'
        TEAMS = 'teams', 'Microsoft Teams'

    id                 = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name               = models.CharField(max_length=100, verbose_name='名前')
    provider           = models.CharField(max_length=10, choices=Provider.choices)
    url                = models.CharField(max_length=500, verbose_name='Webhook URL')
    notification_types = models.JSONField(default=list, verbose_name='転送する通知種別')
    is_active          = models.BooleanField(default=True)
    created_by         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='+')
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '通知転送先（全社）'
        ordering     = ['name']

    def __str__(self):
        return self.name
