import uuid
from django.db import models
from apps.employees.models import Employee
from apps.accounts.models import User


class LearningCourse(models.Model):
    """研修・eラーニングコース"""

    class CourseType(models.TextChoices):
        ELEARNING = 'elearning', 'eラーニング'
        CLASSROOM = 'classroom', '集合研修'
        OJT = 'ojt', 'OJT'
        EXTERNAL = 'external', '外部研修'

    class Status(models.TextChoices):
        DRAFT = 'draft', '下書き'
        PUBLISHED = 'published', '公開中'
        ARCHIVED = 'archived', 'アーカイブ'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name='コースタイトル')
    description = models.TextField(verbose_name='コース説明')
    course_type = models.CharField(max_length=20, choices=CourseType.choices)
    thumbnail_url = models.URLField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=0, verbose_name='所要時間（分）')
    is_required = models.BooleanField(default=False, verbose_name='必須研修')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    target_roles = models.JSONField(default=list, blank=True, verbose_name='対象ロール')
    tags = models.JSONField(default=list, blank=True, verbose_name='タグ')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'コース'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class CourseContent(models.Model):
    """コースコンテンツ（章・節）"""

    class ContentType(models.TextChoices):
        TEXT = 'text', 'テキスト'
        VIDEO = 'video', '動画'
        SLIDE = 'slide', 'スライド'
        QUIZ = 'quiz', 'クイズ'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(LearningCourse, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=ContentType.choices)
    body = models.TextField(blank=True, verbose_name='テキストコンテンツ')
    url = models.URLField(blank=True, verbose_name='動画・スライドURL')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'コンテンツ'
        ordering = ['order']


class CourseEnrollment(models.Model):
    """受講記録"""

    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', '未受講'
        IN_PROGRESS = 'in_progress', '受講中'
        COMPLETED = 'completed', '修了'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(LearningCourse, on_delete=models.CASCADE,
                               related_name='enrollments')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                 related_name='enrollments')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    progress_pct = models.PositiveSmallIntegerField(default=0, verbose_name='進捗率（%）')
    score = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='テストスコア')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True, verbose_name='期限日')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '受講記録'
        unique_together = [['course', 'employee']]
        ordering = ['-created_at']
