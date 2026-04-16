import uuid
from django.db import models
from apps.employees.models import Employee


class Project(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code       = models.CharField(max_length=50, unique=True, verbose_name='件番')
    name       = models.CharField(max_length=200, verbose_name='プロジェクト名')
    manager    = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True,
                                   related_name='managed_projects', verbose_name='管理者')
    is_active  = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date   = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'プロジェクト'
        ordering     = ['-created_at']

    def __str__(self):
        return f'{self.code} {self.name}'


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        DRAFT     = 'draft',     '下書き'
        CONFIRMED = 'confirmed', '確定'
        MODIFIED  = 'modified',  '修正済'

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee       = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    date           = models.DateField(verbose_name='日付')
    clock_in       = models.TimeField(null=True, blank=True, verbose_name='出勤時刻')
    clock_out      = models.TimeField(null=True, blank=True, verbose_name='退勤時刻')
    break_minutes  = models.PositiveIntegerField(default=60, verbose_name='休憩時間（分）')
    status         = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    note           = models.TextField(blank=True, verbose_name='備考')
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = '勤怠記録'
        unique_together     = ('employee', 'date')  # 同じ社員・同じ日は1件のみ
        ordering            = ['-date']

    def __str__(self):
        return f'{self.employee} - {self.date}'

    @property
    def work_minutes(self):
        """実労働時間（分）"""
        if not self.clock_in or not self.clock_out:
            return 0
        from datetime import datetime, date
        ci = datetime.combine(date.today(), self.clock_in)
        co = datetime.combine(date.today(), self.clock_out)
        return max(0, int((co - ci).total_seconds() / 60) - self.break_minutes)

    @property
    def overtime_minutes(self):
        """残業時間（分）= 実労働 - 480分（8時間）"""
        return max(0, self.work_minutes - 480)


class AttendanceProjectRecord(models.Model):
    """1つの勤怠レコードに対して複数のプロジェクト・作業時間を紐付ける中間モデル"""
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attendance = models.ForeignKey(AttendanceRecord, on_delete=models.CASCADE,
                                   related_name='project_records', verbose_name='勤怠記録')
    project    = models.ForeignKey(Project, on_delete=models.PROTECT,
                                   related_name='attendance_records', verbose_name='プロジェクト')
    minutes    = models.PositiveIntegerField(verbose_name='作業時間（分）')

    class Meta:
        verbose_name        = 'プロジェクト作業記録'
        unique_together     = ('attendance', 'project')  # 同じ勤怠に同じPJは1件のみ
        ordering            = ['project__code']

    def __str__(self):
        return f'{self.attendance} - {self.project.code} {self.minutes}分'


class AttendanceModRequest(models.Model):
    class Status(models.TextChoices):
        PENDING  = 'pending',  '申請中'
        APPROVED = 'approved', '承認済'
        REJECTED = 'rejected', '却下'

    id                   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attendance           = models.ForeignKey(AttendanceRecord, on_delete=models.CASCADE,
                                             related_name='mod_requests')
    applicant            = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                             related_name='mod_requests_sent')
    approver             = models.ForeignKey(Employee, on_delete=models.SET_NULL,
                                             null=True, blank=True, related_name='mod_requests_received')
    requested_clock_in   = models.TimeField(verbose_name='修正後出勤時刻')
    requested_clock_out  = models.TimeField(verbose_name='修正後退勤時刻')
    reason               = models.TextField(verbose_name='修正理由')
    status               = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approved_at          = models.DateTimeField(null=True, blank=True)
    created_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '打刻修正申請'
        ordering     = ['-created_at']
