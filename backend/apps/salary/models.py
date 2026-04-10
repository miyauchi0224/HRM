import uuid
from django.db import models
from apps.employees.models import Employee


class SalaryGrade(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grade        = models.PositiveIntegerField(unique=True, verbose_name='等級')
    base_salary  = models.PositiveIntegerField(verbose_name='基本給（円）')
    valid_from   = models.DateField(verbose_name='適用開始日')
    valid_to     = models.DateField(null=True, blank=True, verbose_name='適用終了日')

    class Meta:
        verbose_name = '給与等級マスタ'
        ordering     = ['grade']

    def __str__(self):
        return f'等級{self.grade}: ¥{self.base_salary:,}'


class Allowance(models.Model):
    class AllowanceType(models.TextChoices):
        HOUSING    = 'housing',    '住宅手当'
        SECONDMENT = 'secondment', '出向手当'
        TECHNICAL  = 'technical',  '技術手当'
        COMMUTE    = 'commute',    '通勤手当'
        OTHER      = 'other',      'その他手当'

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name           = models.CharField(max_length=100, verbose_name='手当名')
    allowance_type = models.CharField(max_length=20, choices=AllowanceType.choices)
    amount         = models.PositiveIntegerField(default=0, verbose_name='金額（円）')
    is_active      = models.BooleanField(default=True)

    class Meta:
        verbose_name = '手当マスタ'

    def __str__(self):
        return self.name


class EmployeeAllowance(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee   = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='allowances')
    allowance  = models.ForeignKey(Allowance, on_delete=models.CASCADE)
    amount     = models.PositiveIntegerField(null=True, blank=True, verbose_name='個別金額（空欄=マスタ金額使用）')
    valid_from = models.DateField(verbose_name='適用開始日')
    valid_to   = models.DateField(null=True, blank=True, verbose_name='適用終了日')

    class Meta:
        verbose_name = '社員手当'


class Payslip(models.Model):
    class Status(models.TextChoices):
        DRAFT     = 'draft',     '計算中'
        CONFIRMED = 'confirmed', '確定済'

    id                   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee             = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    year                 = models.PositiveIntegerField(verbose_name='年')
    month                = models.PositiveIntegerField(verbose_name='月')
    base_salary          = models.PositiveIntegerField(default=0, verbose_name='基本給')
    total_allowances     = models.PositiveIntegerField(default=0, verbose_name='手当合計')
    overtime_pay         = models.PositiveIntegerField(default=0, verbose_name='残業手当')
    gross_salary         = models.PositiveIntegerField(default=0, verbose_name='支給合計')
    health_insurance     = models.PositiveIntegerField(default=0, verbose_name='健康保険料')
    pension              = models.PositiveIntegerField(default=0, verbose_name='厚生年金')
    employment_insurance = models.PositiveIntegerField(default=0, verbose_name='雇用保険料')
    income_tax           = models.PositiveIntegerField(default=0, verbose_name='所得税')
    resident_tax         = models.PositiveIntegerField(default=0, verbose_name='住民税')
    total_deductions     = models.PositiveIntegerField(default=0, verbose_name='控除合計')
    net_salary           = models.PositiveIntegerField(default=0, verbose_name='差引支給額')
    status               = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    payslip_url          = models.URLField(blank=True, verbose_name='PDF URL')
    created_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name    = '給与明細'
        unique_together = ('employee', 'year', 'month')
        ordering        = ['-year', '-month']

    def __str__(self):
        return f'{self.employee} {self.year}年{self.month}月'
