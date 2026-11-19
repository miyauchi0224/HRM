import uuid
from django.db import models
from apps.employees.models import Employee
from apps.common.models import SoftDeleteModel


class ProjectManager(SoftDeleteModel):
    """プロジェクトの管理者（主・従）を管理する中間モデル"""
    class Role(models.TextChoices):
        PRIMARY = 'primary', '主管理者'
        SECONDARY = 'secondary', '従管理者'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='project_managers')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='managed_project_roles')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.SECONDARY, verbose_name='役割')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'プロジェクト管理者'
        unique_together = ('project', 'employee')
        ordering = ['role', 'created_at']

    def __str__(self):
        return f'{self.project.code} - {self.employee.full_name} ({self.get_role_display()})'


class Project(SoftDeleteModel):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code        = models.CharField(max_length=50, unique=True, verbose_name='件番')
    name        = models.CharField(max_length=200, verbose_name='プロジェクト名')
    description = models.TextField(blank=True, verbose_name='概要')
    is_active    = models.BooleanField(default=True)
    start_date  = models.DateField(null=True, blank=True)
    end_date    = models.DateField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'プロジェクト'
        ordering     = ['-created_at']

    def __str__(self):
        return f'{self.code} {self.name}'

    @property
    def primary_managers(self):
        """主管理者一覧を取得（M2M対応）"""
        return self.project_managers.filter(role=ProjectManager.Role.PRIMARY).select_related('employee')

    @property
    def secondary_managers(self):
        """従管理者一覧を取得（M2M対応）"""
        return self.project_managers.filter(role=ProjectManager.Role.SECONDARY).select_related('employee')


class ProjectTask(SoftDeleteModel):
    """プロジェクトチケット（作業項目）"""
    class Status(models.TextChoices):
        TODO       = 'todo',       '未着手'
        IN_PROGRESS= 'in_progress','進行中'
        REVIEW     = 'review',     'レビュー中'
        DONE       = 'done',       '完了'

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project     = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks',
                                    verbose_name='プロジェクト')
    title       = models.CharField(max_length=200, verbose_name='タスク名')
    description = models.TextField(blank=True, verbose_name='詳細')
    assignee    = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_tasks', verbose_name='担当者')
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    start_date  = models.DateField(null=True, blank=True, verbose_name='開始予定日')
    end_date    = models.DateField(null=True, blank=True, verbose_name='終了予定日')
    progress    = models.PositiveSmallIntegerField(default=0, verbose_name='進捗率(%)')
    order       = models.PositiveIntegerField(default=0, verbose_name='表示順')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'プロジェクトタスク'
        ordering     = ['order', 'start_date']

    def __str__(self):
        return f'{self.project.code} - {self.title}'


class WorkRule(SoftDeleteModel):
    """
    勤怠ルールマスタ。
    定時時間・休憩時間などをハードコードせずDBで管理する。
    複数の就業パターン（本社・出向先など）に対応可能。
    """
    name               = models.CharField(max_length=100, unique=True, verbose_name='ルール名')
    work_start         = models.TimeField(verbose_name='定時開始')
    work_end           = models.TimeField(verbose_name='定時終了')
    standard_minutes   = models.PositiveIntegerField(default=480, verbose_name='所定労働時間（分）')
    break_minutes      = models.PositiveIntegerField(default=60,  verbose_name='標準休憩時間（分）')
    overtime_threshold = models.PositiveIntegerField(default=480, verbose_name='残業開始基準（分）')
    is_default         = models.BooleanField(default=False, verbose_name='デフォルトルール')

    class Meta:
        verbose_name = '勤怠ルール'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # デフォルトは1件のみ
        if self.is_default:
            WorkRule.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class AttendanceRecord(SoftDeleteModel):
    class Status(models.TextChoices):
        DRAFT     = 'draft',     '下書き'
        CONFIRMED = 'confirmed', '確定'
        MODIFIED  = 'modified',  '修正済'

    class DayType(models.TextChoices):
        WEEKDAY           = 'weekday',           '平日'
        NON_LEGAL_HOLIDAY = 'non_legal_holiday', '所定休日'
        LEGAL_HOLIDAY     = 'legal_holiday',     '法定休日'

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee       = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    date           = models.DateField(verbose_name='日付')
    clock_in       = models.TimeField(null=True, blank=True, verbose_name='出勤時刻')
    clock_out      = models.TimeField(null=True, blank=True, verbose_name='退勤時刻')
    stamped_clock_in  = models.TimeField(null=True, blank=True, verbose_name='出勤打刻時刻（原本）')
    stamped_clock_out = models.TimeField(null=True, blank=True, verbose_name='退勤打刻時刻（原本）')
    break_minutes  = models.PositiveIntegerField(default=60, verbose_name='休憩時間（分）')
    status         = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    day_type       = models.CharField(max_length=20, choices=DayType.choices, default=DayType.WEEKDAY,
                                      verbose_name='日の区分')
    rest_interval_minutes = models.PositiveIntegerField(null=True, blank=True,
                                                        verbose_name='勤務間インターバル（分）')
    # 打刻時の IP・位置（位置はブラウザで許可された場合のみ）
    clock_in_ip         = models.GenericIPAddressField(null=True, blank=True, verbose_name='出勤打刻 IP')
    clock_out_ip        = models.GenericIPAddressField(null=True, blank=True, verbose_name='退勤打刻 IP')
    clock_in_latitude   = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clock_in_longitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clock_out_latitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clock_out_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    note           = models.TextField(blank=True, verbose_name='備考')
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)
    # history      = HistoricalRecords()  # pip install django-simple-history 後に有効化

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
        """
        時間外労働（分）。36協定の集計にも使う。
        平日: 実労働 - 480分 / 所定休日: 実労働の全時間 / 法定休日: 0（休日労働として別計上）
        """
        if self.day_type == self.DayType.LEGAL_HOLIDAY:
            return 0
        if self.day_type == self.DayType.NON_LEGAL_HOLIDAY:
            return self.work_minutes
        return max(0, self.work_minutes - 480)

    @property
    def holiday_work_minutes(self):
        """法定休日の労働時間（分）。割増率 1.35"""
        return self.work_minutes if self.day_type == self.DayType.LEGAL_HOLIDAY else 0

    @property
    def late_night_minutes(self):
        """深夜（22:00〜翌5:00）に重なる分数。退勤は当日中の前提で、休憩は控除しない概算"""
        if not self.clock_in or not self.clock_out:
            return 0
        start = self.clock_in.hour * 60 + self.clock_in.minute
        end   = self.clock_out.hour * 60 + self.clock_out.minute
        if end <= start:
            return 0
        overlap = lambda a, b: max(0, min(end, b) - max(start, a))
        return overlap(0, 5 * 60) + overlap(22 * 60, 24 * 60)


class AttendanceProjectRecord(SoftDeleteModel):
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


class AttendanceModRequest(SoftDeleteModel):
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
