import uuid
from django.db import models
from apps.employees.models import Employee
from apps.common.models import SoftDeleteModel


class MBOGoal(SoftDeleteModel):
    class Period(models.TextChoices):
        FIRST_HALF  = 'first_half',  '上期'
        SECOND_HALF = 'second_half', '下期'

    class Status(models.TextChoices):
        DRAFT     = 'draft',     '下書き'
        SUBMITTED = 'submitted', '提出済'
        APPROVED  = 'approved',  '承認済'
        EVALUATED = 'evaluated', '評価済'

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee         = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='mbo_goals')
    year             = models.PositiveIntegerField(verbose_name='年度')
    period           = models.CharField(max_length=20, choices=Period.choices, verbose_name='期')
    # 期間の細分化（1〜6ヶ月）。null の場合は period（上期/下期）の標準期間
    period_start_month = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='期間開始月（1-12）'
    )
    period_end_month   = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='期間終了月（1-12）'
    )
    title            = models.CharField(max_length=200, verbose_name='目標タイトル')
    target_level     = models.TextField(blank=True, verbose_name='達成水準')
    weight           = models.PositiveIntegerField(default=100, verbose_name='ウェイト（%）')
    self_score       = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True,
                                           verbose_name='自己評価')
    manager_score    = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True,
                                           verbose_name='上司評価')
    status           = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'MBO目標'
        ordering     = ['-year', 'period']

    def __str__(self):
        return f'{self.employee} {self.year}年{self.get_period_display()} {self.title}'

    @property
    def period_months_count(self):
        """目標の対象月数（1〜6）"""
        if self.period_start_month and self.period_end_month:
            return self.period_end_month - self.period_start_month + 1
        # デフォルト：上期・下期 = 6ヶ月
        return 6


class MBOReport(SoftDeleteModel):
    class Status(models.TextChoices):
        DRAFT     = 'draft',     '下書き'
        SUBMITTED = 'submitted', '提出済'
        COMMENTED = 'commented', 'コメント済'

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal             = models.ForeignKey(MBOGoal, on_delete=models.CASCADE, related_name='reports')
    month            = models.DateField(verbose_name='対象月（月初日を格納）')
    action_content   = models.TextField(blank=True, verbose_name='行動内容')
    result           = models.TextField(blank=True, verbose_name='結果・考察')
    manager_comment  = models.TextField(blank=True, verbose_name='上司コメント')
    ai_suggestion    = models.TextField(blank=True, verbose_name='AI提案')
    status           = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name    = 'MBO月間報告'
        unique_together = ('goal', 'month')
        ordering        = ['-month']


class DailyReport(SoftDeleteModel):
    class Status(models.TextChoices):
        DRAFT     = 'draft',     '下書き'
        SUBMITTED = 'submitted', '提出済'

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='daily_reports')
    report_date = models.DateField(verbose_name='報告日')
    content     = models.TextField(verbose_name='内容')
    ai_suggestion = models.TextField(blank=True, verbose_name='AI提案')
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'report_date')
        ordering        = ['-report_date']
