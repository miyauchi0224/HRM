import uuid
from django.db import models
from django.conf import settings
from apps.common.models import SoftDeleteModel


class ComplianceChecklistSection(SoftDeleteModel):
    """コンプライアンスチェックリスト - セクション"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100, verbose_name='セクションタイトル')
    order = models.PositiveIntegerField(default=0, verbose_name='表示順')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'チェックリスト - セクション'
        verbose_name_plural = 'チェックリスト - セクション'
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.title


class ComplianceChecklistItem(SoftDeleteModel):
    """コンプライアンスチェックリスト - 項目"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(ComplianceChecklistSection, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=200, verbose_name='項目内容')
    order = models.PositiveIntegerField(default=0, verbose_name='表示順')
    is_critical = models.BooleanField(default=False, verbose_name='重要項目フラグ')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'チェックリスト - 項目'
        verbose_name_plural = 'チェックリスト - 項目'
        ordering = ['section', 'order', 'created_at']

    def __str__(self):
        return f'{self.section.title} - {self.title}'


class ComplianceChecklistProgress(SoftDeleteModel):
    """チェックリスト進捗管理 - ユーザーごとの完了状況"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='compliance_progress')
    item = models.ForeignKey(ComplianceChecklistItem, on_delete=models.CASCADE, related_name='progress_records')
    is_completed = models.BooleanField(default=False, verbose_name='完了フラグ')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完了日時')
    notes = models.TextField(blank=True, verbose_name='備考')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'チェックリスト進捗'
        verbose_name_plural = 'チェックリスト進捗'
        unique_together = ('user', 'item')
        ordering = ['item__section', 'item__order']

    def __str__(self):
        return f'{self.user} - {self.item.title}: {"完了" if self.is_completed else "未完了"}'
