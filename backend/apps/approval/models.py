import uuid
from django.db import models
from apps.accounts.models import User
from apps.employees.models import Employee
from apps.common.models import SoftDeleteModel


class ApprovalTemplate(SoftDeleteModel):
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


class ApprovalRequest(SoftDeleteModel):
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


class ApprovalAttachment(SoftDeleteModel):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request     = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='file_attachments')
    file        = models.FileField(upload_to='approval/attachments/%Y/%m/')
    file_name   = models.CharField(max_length=255)
    file_size   = models.PositiveIntegerField()
    content_type = models.CharField(max_length=100)
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True,
                                    related_name='approval_file_uploads')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '稟議添付ファイル'
        ordering     = ['uploaded_at']

    def __str__(self):
        return f'{self.request} - {self.file_name}'


class ApprovalStep(SoftDeleteModel):
    """稟議の承認ルート（各承認者）"""

    class Decision(models.TextChoices):
        PENDING = 'pending', '未決'
        APPROVED = 'approved', '承認'
        REJECTED = 'rejected', '却下'
        SKIPPED = 'skipped', 'スキップ'

    class StepRole(models.TextChoices):
        SUPERVISOR = 'supervisor', '上司'
        MANAGER = 'manager', '部門長'
        ACCOUNTING = 'accounting', '財務'
        CUSTOM = 'custom', 'カスタム'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE,
                                related_name='steps')
    approver = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                 related_name='approval_steps', verbose_name='承認者')
    step_role = models.CharField(max_length=20, choices=StepRole.choices,
                                 default=StepRole.CUSTOM, verbose_name='承認者の役割')
    order = models.PositiveSmallIntegerField(verbose_name='承認順序')
    decision = models.CharField(max_length=20, choices=Decision.choices,
                                default=Decision.PENDING)
    comment = models.TextField(blank=True, verbose_name='コメント')
    decided_at = models.DateTimeField(null=True, blank=True)
    # 実際に判断した人（代理承認のときは代理人。本人が判断したときは approver と同じ）
    decided_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approval_steps_decided', verbose_name='判断者')

    class Meta:
        verbose_name = '承認ステップ'
        ordering = ['order']
        unique_together = [['request', 'order']]


class ApprovalDelegation(SoftDeleteModel):
    """
    代理承認の設定

    委任元（delegator）が不在の期間、代理人（delegate）が委任元の権限で承認できる。
    対象は 休暇・経費・打刻修正・電子稟議。代理の代理は辿らない。
    """
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delegator  = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                   related_name='delegations_given', verbose_name='委任元')
    delegate   = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                   related_name='delegations_received', verbose_name='代理人')
    start_date = models.DateField(verbose_name='開始日')
    end_date   = models.DateField(verbose_name='終了日')
    reason     = models.CharField(max_length=200, blank=True, verbose_name='理由')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '代理承認設定'
        ordering     = ['-start_date']

    def __str__(self):
        return f'{self.delegator.full_name} → {self.delegate.full_name}（{self.start_date}〜{self.end_date}）'
