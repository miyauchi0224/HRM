import uuid
from django.db import models
from apps.accounts.models import User
from apps.employees.models import Employee
from apps.common.models import SoftDeleteModel


class OneOnOneMeeting(SoftDeleteModel):
    """
    1on1 の記録（詳細設計書 7.7）

    閲覧・編集は参加者（上司・部下）のみ。manager_private_notes は上司にだけ返す。
    """
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', '予定'
        DONE      = 'done',      '実施済'
        CANCELLED = 'cancelled', '中止'

    id                    = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    manager               = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                              related_name='one_on_ones_as_manager', verbose_name='上司')
    member                = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                              related_name='one_on_ones_as_member', verbose_name='部下')
    scheduled_at          = models.DateTimeField(verbose_name='実施日時')
    duration_minutes      = models.PositiveIntegerField(default=30, verbose_name='時間（分）')
    status                = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    agenda                = models.TextField(blank=True, verbose_name='アジェンダ')
    shared_notes          = models.TextField(blank=True, verbose_name='共有メモ')
    manager_private_notes = models.TextField(blank=True, verbose_name='上司メモ（非公開）')
    action_items          = models.JSONField(default=list, blank=True, verbose_name='アクションアイテム')
    ai_summary            = models.TextField(blank=True, verbose_name='AI 要約')
    created_by            = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                              related_name='+')
    created_at            = models.DateTimeField(auto_now_add=True)
    updated_at            = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '1on1'
        ordering     = ['-scheduled_at']

    def __str__(self):
        return f'{self.manager.full_name} × {self.member.full_name} {self.scheduled_at:%Y-%m-%d}'
