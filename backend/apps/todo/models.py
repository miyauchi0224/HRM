import uuid
from django.db import models
from apps.employees.models import Employee
from apps.common.models import SoftDeleteModel


class TodoItem(SoftDeleteModel):
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', '未着手'
        IN_PROGRESS = 'in_progress', '作業中'
        DONE        = 'done',        '実施済み'

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='todos')
    # プロジェクト紐づけ（出退勤管理の Project モデルを共有）
    project     = models.ForeignKey(
        'attendance.Project', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='todo_items', verbose_name='プロジェクト'
    )
    title       = models.CharField(max_length=200, verbose_name='タイトル')
    description = models.TextField(blank=True, verbose_name='詳細')
    status      = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NOT_STARTED, verbose_name='ステータス'
    )
    due_date    = models.DateField(null=True, blank=True, verbose_name='期限')
    order       = models.PositiveIntegerField(default=0, verbose_name='表示順')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'TODOアイテム'
        ordering     = ['status', 'order', '-created_at']

    def __str__(self):
        return f'{self.employee} - {self.title}'


class DailyReport(SoftDeleteModel):
    """日報（TODO画面から記入）"""
    class Status(models.TextChoices):
        DRAFT     = 'draft',     '下書き'
        SUBMITTED = 'submitted', '提出済'

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='todo_daily_reports')
    report_date = models.DateField(verbose_name='報告日')
    content     = models.TextField(verbose_name='本日の作業内容')
    tomorrow    = models.TextField(blank=True, verbose_name='明日の予定')
    issues      = models.TextField(blank=True, verbose_name='課題・連絡事項')
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name    = '日報'
        unique_together = ('employee', 'report_date')
        ordering        = ['-report_date']

    def __str__(self):
        return f'{self.employee} - {self.report_date}'
