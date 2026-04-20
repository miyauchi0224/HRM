import uuid
from django.db import models
from apps.employees.models import Employee


class EvaluationPeriod(models.Model):
    """評価期間（上期/下期）"""

    class PeriodType(models.TextChoices):
        FIRST_HALF = 'first_half', '上期'
        SECOND_HALF = 'second_half', '下期'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fiscal_year = models.PositiveSmallIntegerField(verbose_name='年度')
    period_type = models.CharField(max_length=20, choices=PeriodType.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = '評価期間'
        unique_together = [['fiscal_year', 'period_type']]
        ordering = ['-fiscal_year', 'period_type']

    def __str__(self):
        return f'{self.fiscal_year}年度 {self.get_period_type_display()}'


class EvaluationQuestion(models.Model):
    """評価項目"""

    class Category(models.TextChoices):
        PERFORMANCE = 'performance', '業績評価'
        COMPETENCY = 'competency', 'コンピテンシー評価'
        ATTITUDE = 'attitude', '行動・姿勢'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=20, choices=Category.choices)
    text = models.TextField(verbose_name='評価項目テキスト')
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = '評価項目'
        ordering = ['category', 'order']


class Evaluation360(models.Model):
    """360度評価"""

    class EvaluatorType(models.TextChoices):
        SELF = 'self', '自己評価'
        SUPERVISOR = 'supervisor', '上司評価'
        PEER = 'peer', '同僚評価'
        SUBORDINATE = 'subordinate', '部下評価'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period = models.ForeignKey(EvaluationPeriod, on_delete=models.CASCADE,
                               related_name='evaluations')
    subject = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                related_name='received_evaluations', verbose_name='評価対象者')
    evaluator = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                  related_name='given_evaluations', verbose_name='評価者')
    evaluator_type = models.CharField(max_length=20, choices=EvaluatorType.choices)
    is_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    overall_comment = models.TextField(blank=True, verbose_name='総合コメント')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '360度評価'
        unique_together = [['period', 'subject', 'evaluator']]


class EvaluationScore(models.Model):
    """評価項目ごとのスコア"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluation = models.ForeignKey(Evaluation360, on_delete=models.CASCADE,
                                   related_name='scores')
    question = models.ForeignKey(EvaluationQuestion, on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField(verbose_name='スコア（1-5）')
    comment = models.TextField(blank=True)

    class Meta:
        unique_together = [['evaluation', 'question']]
