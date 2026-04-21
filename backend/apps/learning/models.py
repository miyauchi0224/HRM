import uuid
from django.db import models
from apps.employees.models import Employee
from apps.accounts.models import User
from apps.common.models import SoftDeleteModel


class LearningCourse(SoftDeleteModel):
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


class CourseContent(SoftDeleteModel):
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


class CourseAttachment(SoftDeleteModel):
    """コース添付ファイル"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(LearningCourse, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='learning/attachments/%Y/%m/')
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(verbose_name='ファイルサイズ(bytes)')
    content_type = models.CharField(max_length=100)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_image(self):
        return self.content_type.startswith('image/')

    class Meta:
        verbose_name = 'コース添付ファイル'
        ordering = ['created_at']


class CourseEnrollment(SoftDeleteModel):
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


# ---- 理解度確認テスト ----

class Quiz(SoftDeleteModel):
    """理解度確認テスト（コースに1つ）"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.OneToOneField(LearningCourse, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=200, default='理解度確認テスト')
    description = models.TextField(blank=True)
    pass_score = models.PositiveSmallIntegerField(default=70, verbose_name='合格点（%）')
    time_limit_minutes = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='制限時間（分）')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '理解度テスト'

    def __str__(self):
        return f'{self.course.title} - {self.title}'


class QuizQuestion(SoftDeleteModel):
    """テスト問題"""

    class QuestionType(models.TextChoices):
        CHOICE = 'choice', '選択式'
        FREE_TEXT = 'free_text', '自由記述'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField(verbose_name='問題文')
    question_type = models.CharField(max_length=20, choices=QuestionType.choices, default=QuestionType.CHOICE)
    order = models.PositiveSmallIntegerField(default=0)
    explanation = models.TextField(blank=True, verbose_name='解説（正解後に表示）')
    points = models.PositiveSmallIntegerField(default=1, verbose_name='配点')

    class Meta:
        verbose_name = 'テスト問題'
        ordering = ['order']


class QuizChoice(SoftDeleteModel):
    """選択式問題の選択肢"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=500, verbose_name='選択肢テキスト')
    is_correct = models.BooleanField(default=False, verbose_name='正解')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = '選択肢'
        ordering = ['order']


class QuizAttempt(SoftDeleteModel):
    """テスト受験記録"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='quiz_attempts')
    score = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='スコア（%）')
    is_passed = models.BooleanField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'テスト受験記録'
        ordering = ['-started_at']


class QuizAnswer(SoftDeleteModel):
    """テスト回答"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='answers')
    selected_choice = models.ForeignKey(
        QuizChoice, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='選択した選択肢'
    )
    free_text_answer = models.TextField(blank=True, verbose_name='自由記述回答')
    is_correct = models.BooleanField(null=True, blank=True, verbose_name='正解フラグ（自由記述はNull）')

    class Meta:
        verbose_name = 'テスト回答'
        unique_together = [['attempt', 'question']]
