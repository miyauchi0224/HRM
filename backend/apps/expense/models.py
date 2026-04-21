import uuid
from django.db import models
from apps.employees.models import Employee
from apps.common.models import SoftDeleteModel


class AccountItem(SoftDeleteModel):
    class Category(models.TextChoices):
        TRAVEL        = 'travel',        '旅費交通費'
        SUPPLIES      = 'supplies',      '消耗品費'
        ENTERTAINMENT = 'entertainment', '接待交際費'
        COMMUNICATION = 'communication', '通信費'
        OTHER         = 'other',         'その他'

    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code      = models.CharField(max_length=20, unique=True, verbose_name='科目コード')
    name      = models.CharField(max_length=100, verbose_name='科目名')
    category  = models.CharField(max_length=20, choices=Category.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = '勘定科目'
        ordering     = ['code']

    def __str__(self):
        return f'{self.code} {self.name}'


class ExpenseRequest(SoftDeleteModel):
    class ExpenseType(models.TextChoices):
        TRANSPORTATION = 'transportation', '交通費'
        GENERAL        = 'general',        '一般経費'

    class PaymentType(models.TextChoices):
        REIMBURSEMENT = 'reimbursement', '立替払い'  # 社員が先に立て替えて後から精算
        ADVANCE       = 'advance',       '先払い申請'  # 会社が先に支払う

    class Status(models.TextChoices):
        PENDING   = 'pending',   '申請中'
        APPROVED  = 'approved',  '承認済'
        REJECTED  = 'rejected',  '却下'
        SETTLED   = 'settled',   '精算済'

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    applicant       = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                        related_name='expense_requests')
    approver        = models.ForeignKey(Employee, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='expense_approvals')
    account_item    = models.ForeignKey(AccountItem, on_delete=models.PROTECT)
    expense_type    = models.CharField(max_length=20, choices=ExpenseType.choices)
    payment_type    = models.CharField(max_length=20, choices=PaymentType.choices,
                                       default=PaymentType.REIMBURSEMENT, verbose_name='支払方法')
    amount          = models.PositiveIntegerField(verbose_name='金額（円）')
    expense_date    = models.DateField(verbose_name='費用発生日')
    description     = models.TextField(verbose_name='内容説明')
    receipt_url     = models.URLField(blank=True, verbose_name='領収書URL（S3）')
    status          = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    rejected_reason = models.TextField(blank=True, verbose_name='却下理由')
    approved_at     = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    # history       = HistoricalRecords()  # pip install django-simple-history 後に有効化

    class Meta:
        verbose_name = '経費申請'
        ordering     = ['-created_at']
