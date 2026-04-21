import uuid
from django.db import models
from apps.accounts.models import User
from apps.employees.models import Employee
from apps.common.models import SoftDeleteModel


class JobPosting(SoftDeleteModel):
    """求人票"""

    class EmploymentType(models.TextChoices):
        FULL_TIME = 'full_time', '正社員'
        PART_TIME = 'part_time', 'パートタイム'
        CONTRACT = 'contract', '契約社員'
        INTERN = 'intern', 'インターン'

    class Status(models.TextChoices):
        DRAFT = 'draft', '下書き'
        OPEN = 'open', '募集中'
        CLOSED = 'closed', '募集終了'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name='求人タイトル')
    department = models.CharField(max_length=100, blank=True, verbose_name='部署')
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices)
    description = models.TextField(verbose_name='仕事内容')
    requirements = models.TextField(verbose_name='応募要件')
    preferred = models.TextField(blank=True, verbose_name='歓迎要件')
    salary_range = models.CharField(max_length=100, blank=True, verbose_name='給与レンジ')
    location = models.CharField(max_length=200, blank=True, verbose_name='勤務地')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    open_date = models.DateField(null=True, blank=True)
    close_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '求人票'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Candidate(SoftDeleteModel):
    """応募者"""

    class Status(models.TextChoices):
        NEW = 'new', '新規'
        SCREENING = 'screening', '書類選考'
        INTERVIEW1 = 'interview1', '一次面接'
        INTERVIEW2 = 'interview2', '二次面接'
        FINAL = 'final', '最終面接'
        OFFER = 'offer', '内定'
        HIRED = 'hired', '入社'
        REJECTED = 'rejected', '不採用'
        WITHDRAWN = 'withdrawn', '辞退'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE,
                                    related_name='candidates', verbose_name='応募求人')
    full_name = models.CharField(max_length=100, verbose_name='氏名')
    email = models.EmailField(verbose_name='メールアドレス')
    phone = models.CharField(max_length=20, blank=True)
    resume_url = models.URLField(blank=True, verbose_name='履歴書URL')
    portfolio_url = models.URLField(blank=True, verbose_name='ポートフォリオURL')
    source = models.CharField(max_length=100, blank=True, verbose_name='応募経路')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    note = models.TextField(blank=True, verbose_name='メモ')
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_candidates', verbose_name='担当者')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '応募者'
        ordering = ['-applied_at']

    def __str__(self):
        return self.full_name


class Interview(SoftDeleteModel):
    """面接スケジュール"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE,
                                  related_name='interviews')
    interviewer = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True,
                                    related_name='interviews_conducted', verbose_name='面接官')
    scheduled_at = models.DateTimeField(verbose_name='面接日時')
    location = models.CharField(max_length=200, blank=True, verbose_name='場所/URL')
    result = models.CharField(max_length=20, blank=True, verbose_name='結果（pass/fail/tbd）')
    feedback = models.TextField(blank=True, verbose_name='フィードバック')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '面接'
        ordering = ['scheduled_at']
