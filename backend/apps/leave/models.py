import uuid
from django.db import models
from apps.employees.models import Employee


class LeaveBalance(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee      = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    fiscal_year   = models.PositiveIntegerField(verbose_name='年度')
    granted_days  = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name='付与日数')
    used_days     = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name='使用日数')
    carried_days  = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name='繰越日数')

    class Meta:
        unique_together = ('employee', 'fiscal_year')
        verbose_name    = '有給残日数'

    @property
    def remaining_days(self):
        return self.granted_days + self.carried_days - self.used_days


class LeaveRequest(models.Model):
    class LeaveType(models.TextChoices):
        ANNUAL        = 'annual',        '有給休暇'
        SPECIAL       = 'special',       '特別休暇'
        SICK          = 'sick',          '病気休暇'
        MATERNITY     = 'maternity',     '産休'
        CHILDCARE     = 'childcare',     '育休'
        BEREAVEMENT   = 'bereavement',   '忌引き'

    class Status(models.TextChoices):
        PENDING  = 'pending',  '申請中'
        APPROVED = 'approved', '承認済'
        REJECTED = 'rejected', '却下'
        CANCELLED = 'cancelled', '取消'

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    approver    = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='leave_approvals')
    leave_type  = models.CharField(max_length=20, choices=LeaveType.choices, verbose_name='休暇種別')
    start_date  = models.DateField(verbose_name='開始日')
    end_date    = models.DateField(verbose_name='終了日')
    days        = models.DecimalField(max_digits=4, decimal_places=1, verbose_name='日数')
    reason      = models.TextField(blank=True, verbose_name='理由')
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '休暇申請'
        ordering     = ['-created_at']
