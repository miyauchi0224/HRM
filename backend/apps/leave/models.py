import uuid
from django.db import models
from apps.employees.models import Employee
from apps.common.models import SoftDeleteModel


class LeaveBalance(SoftDeleteModel):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee      = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    fiscal_year   = models.PositiveIntegerField(verbose_name='年度')
    granted_days  = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name='付与日数')
    used_days     = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name='使用日数')
    carried_days  = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name='繰越日数')
    rollover_done = models.BooleanField(default=False, verbose_name='年度繰越の処理済み')

    class Meta:
        unique_together = ('employee', 'fiscal_year')
        verbose_name    = '有給残日数'

    @property
    def remaining_days(self):
        return self.granted_days + self.carried_days - self.used_days


class LeaveRequest(SoftDeleteModel):
    class LeaveType(models.TextChoices):
        ANNUAL        = 'annual',        '有給休暇'
        SPECIAL       = 'special',       '特別休暇'
        SICK          = 'sick',          '病気休暇'
        MATERNITY     = 'maternity',     '産休'
        CHILDCARE     = 'childcare',     '育休'
        BEREAVEMENT   = 'bereavement',   '忌引き'
        COMPENSATORY  = 'compensatory',  '代休'

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
    # 代休のときの元になった休日出勤
    holiday_work = models.ForeignKey('attendance.AttendanceRecord', on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='compensatory_leaves',
                                     verbose_name='休日出勤')
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '休暇申請'
        ordering     = ['-created_at']


# 勤続年数（月数）ごとの年次有給の付与日数（労働基準法 第39条・通常の労働者）
ANNUAL_LEAVE_GRANT_TABLE = [
    (6,  10), (18, 11), (30, 12), (42, 14), (54, 16), (66, 18), (78, 20),
]


class LeaveGrant(SoftDeleteModel):
    """
    年次有給の付与履歴

    付与日ごとに1件。年5日取得義務の基準期間（付与日〜1年後の前日）の判定に使う。
    """
    class Source(models.TextChoices):
        AUTO   = 'auto',   '自動付与'
        MANUAL = 'manual', '手動付与'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee   = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_grants')
    grant_date = models.DateField(verbose_name='付与日')
    days       = models.DecimalField(max_digits=4, decimal_places=1, verbose_name='付与日数')
    expires_on = models.DateField(verbose_name='時効日')
    source     = models.CharField(max_length=10, choices=Source.choices, default=Source.AUTO)
    note       = models.TextField(blank=True, verbose_name='備考')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name    = '有給付与履歴'
        unique_together = ('employee', 'grant_date')
        ordering        = ['-grant_date']

    def __str__(self):
        return f'{self.employee} {self.grant_date} {self.days}日'
