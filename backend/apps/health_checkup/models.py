import uuid
from django.db import models
from apps.employees.models import Employee
from apps.common.models import SoftDeleteModel


class HealthCheckup(SoftDeleteModel):
    """
    健康診断の受診記録（詳細設計書 7.6）

    健康情報は要配慮個人情報のため、本人・労務・人事・管理者のみ閲覧できる（上司には開示しない）。
    """
    class CheckupType(models.TextChoices):
        REGULAR = 'regular', '定期健康診断'
        HIRING  = 'hiring',  '雇入時健康診断'
        SPECIAL = 'special', '特殊健康診断'
        OTHER   = 'other',   'その他'

    class Result(models.TextChoices):
        NONE        = '',              '未判定'
        NORMAL      = 'a_normal',      'A 異常なし'
        MINOR       = 'b_minor',       'B 軽度異常'
        OBSERVATION = 'c_observation', 'C 要経過観察'
        REEXAM      = 'd_reexam',      'D 要再検査'
        TREATMENT   = 'e_treatment',   'E 要治療'

    FOLLOWUP_RESULTS = (Result.REEXAM, Result.TREATMENT)

    id                      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee                = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='health_checkups')
    fiscal_year             = models.PositiveIntegerField(verbose_name='年度')
    checkup_type            = models.CharField(max_length=20, choices=CheckupType.choices,
                                               default=CheckupType.REGULAR, verbose_name='種別')
    scheduled_date          = models.DateField(null=True, blank=True, verbose_name='受診予定日')
    checkup_date            = models.DateField(null=True, blank=True, verbose_name='受診日')
    institution             = models.CharField(max_length=200, blank=True, verbose_name='医療機関')
    result                  = models.CharField(max_length=20, choices=Result.choices, blank=True,
                                               default=Result.NONE, verbose_name='判定')
    followup_due_date       = models.DateField(null=True, blank=True, verbose_name='再検査・受診の期限')
    followup_completed_date = models.DateField(null=True, blank=True, verbose_name='再検査・受診の完了日')
    note                    = models.TextField(blank=True, verbose_name='備考')
    created_at              = models.DateTimeField(auto_now_add=True)
    updated_at              = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '健康診断'
        ordering     = ['-fiscal_year', '-checkup_date']

    def __str__(self):
        return f'{self.employee} {self.fiscal_year}年度 {self.get_checkup_type_display()}'

    @property
    def followup_required(self):
        return self.result in self.FOLLOWUP_RESULTS

    @property
    def followup_pending(self):
        return self.followup_required and self.followup_completed_date is None
