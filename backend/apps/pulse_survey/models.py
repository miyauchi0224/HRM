"""
パルスサーベイ（詳細設計書 7.10）

匿名性を保つため「回答内容（PulseResponse）」と「回答済みの記録（PulseParticipation）」を分けて保存する。
匿名サーベイの PulseResponse には社員 ID を持たせない。
"""
import uuid
from django.db import models
from apps.accounts.models import User
from apps.employees.models import Employee
from apps.common.models import SoftDeleteModel


DEFAULT_QUESTIONS = [
    {'text': 'この職場を友人や知人にどの程度すすめたいですか？', 'kind': 'enps'},
    {'text': '今の仕事にやりがいを感じている',                   'kind': 'scale5'},
    {'text': '上司から必要なサポートを受けられている',           'kind': 'scale5'},
    {'text': 'チームの雰囲気はよい',                             'kind': 'scale5'},
    {'text': '職場について気になっていること・改善してほしいこと', 'kind': 'text', 'is_required': False},
]


class PulseSurvey(SoftDeleteModel):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title        = models.CharField(max_length=200, verbose_name='タイトル')
    description  = models.TextField(blank=True, verbose_name='説明')
    start_date   = models.DateField(verbose_name='回答開始日')
    end_date     = models.DateField(verbose_name='回答終了日')
    is_published = models.BooleanField(default=False, verbose_name='公開済み')
    is_anonymous = models.BooleanField(default=True, verbose_name='匿名')
    created_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'パルスサーベイ'
        ordering     = ['-start_date', '-created_at']

    def __str__(self):
        return self.title


class PulseQuestion(SoftDeleteModel):
    class Kind(models.TextChoices):
        SCALE5 = 'scale5', '5段階'
        ENPS   = 'enps',   'eNPS（0〜10）'
        TEXT   = 'text',   '自由記述'

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey      = models.ForeignKey(PulseSurvey, on_delete=models.CASCADE, related_name='questions')
    order       = models.PositiveIntegerField(default=0)
    text        = models.CharField(max_length=300, verbose_name='質問')
    kind        = models.CharField(max_length=10, choices=Kind.choices, default=Kind.SCALE5)
    is_required = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'パルスサーベイ質問'
        ordering     = ['order']


class PulseParticipation(SoftDeleteModel):
    """回答済みの記録（二重回答防止・未回答者へのリマインド用）。回答内容は持たない"""
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey       = models.ForeignKey(PulseSurvey, on_delete=models.CASCADE, related_name='participations')
    employee     = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='pulse_participations')
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name    = 'パルスサーベイ回答済み'
        unique_together = ('survey', 'employee')


class PulseResponse(SoftDeleteModel):
    """回答内容。匿名サーベイでは employee を NULL にする"""
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey       = models.ForeignKey(PulseSurvey, on_delete=models.CASCADE, related_name='responses')
    answers      = models.JSONField(default=dict, verbose_name='回答（質問ID→値）')
    department   = models.CharField(max_length=100, blank=True, verbose_name='回答時点の部署')
    employee     = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='pulse_responses')
    submitted_at = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = 'パルスサーベイ回答'
