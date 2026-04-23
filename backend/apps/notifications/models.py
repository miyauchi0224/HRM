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
        """通知を作成するユーティリティメソッド"""
        return cls.objects.create(
            user=user, type=type_, title=title,
            message=message, related_url=related_url
        )
