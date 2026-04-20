import uuid
from django.db import models
from apps.accounts.models import User
from apps.employees.models import Employee


class ApprovalTemplate(models.Model):
    """稟議テンプレート（購買申請・出張申請など）"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='テンプレート名')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '稟議テンプレート'
        ordering = ['name']

    def __str__(self):
        return self.name


class ApprovalRequest(models.Model):
    """電子稟議申請"""

    class Category(models.TextChoices):
        PURCHASE = 'purchase', '購買申請'
        TRAVEL = 'travel', '出張申請'
        CONTRACT = 'contract', '契約申請'
        BUDGET = 'budget', '予算申請'
        HR = 'hr', '人事申請'
        OTHER = 'other', 'その他'

    class Status(models.TextChoices):
        DRAFT = 'draft', '下書き'
        PENDING = 'pending', '審査中'
        APPROVED = 'approved', '承認済'
        REJECTED = 'rejected', '却下'
        WITHDRAWN = 'withdrawn', '取り下げ'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name='件名')
    category = models.CharField(max_length=20, choices=Category.choices, verbose_name='カテゴリ')
    applicant = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                  related_name='approval_requests', verbose_name='申請者')
    template = models.ForeignKey(ApprovalTemplate, on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name='requests')
    amount = models.PositiveIntegerField(null=True, blank=True, verbose_name='金額（円）')
    content = models.TextField(verbose_name='申請内容')
    attachments = models.JSONField(default=list, blank=True, verbose_name='添付ファイルURL一覧')
    status = models.CharField(max_length=20, choices=Status.choices,
                              default=Status.DRAFT, verbose_name='ステータス')
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '稟議申請'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ApprovalStep(models.Model):
    """稟議の承認ルート（各承認者）"""

    class Decision(models.TextChoices):
        PENDING = 'pending', '未決'
        APPROVED = 'approved', '承認'
        REJECTED = 'rejected', '却下'
        SKIPPED = 'skipped', 'スキップ'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE,
                                related_name='steps')
    approver = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                 related_name='approval_steps', verbose_name='承認者')
    order = models.PositiveSmallIntegerField(verbose_name='承認順序')
    decision = models.CharField(max_length=20, choices=Decision.choices,
                                default=Decision.PENDING)
    comment = models.TextField(blank=True, verbose_name='コメント')
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = '承認ステップ'
        ordering = ['order']
        unique_together = [['request', 'order']]
