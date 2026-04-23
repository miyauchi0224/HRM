import uuid
from django.db import models
from apps.employees.models import Employee
from apps.common.models import SoftDeleteModel
from django.utils import timezone


class OnboardingTemplate(SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name='テンプレート名')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, verbose_name='有効')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'オンボーディングテンプレート'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class OnboardingTemplateTask(SoftDeleteModel):
    class Category(models.TextChoices):
        DOCUMENT = 'document', '書類提出'
        IT       = 'it',       'IT環境設定'
        TRAINING = 'training', '研修受講'
        FACILITY = 'facility', '施設案内'
        OTHER    = 'other',    'その他'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        OnboardingTemplate,
        on_delete=models.CASCADE,
        related_name='tasks',
    )
    title = models.CharField(max_length=200, verbose_name='タスク名')
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
    )
    due_days_from_hire = models.PositiveIntegerField(
        default=7,
        verbose_name='入社後N日以内',
    )
    order = models.PositiveIntegerField(default=0, verbose_name='表示順')

    class Meta:
        verbose_name = 'テンプレートタスク'
        ordering = ['order', 'due_days_from_hire']

    def __str__(self):
        return self.title


class OnboardingAssignment(SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        OnboardingTemplate,
        on_delete=models.CASCADE,
        related_name='assignments',
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='onboarding_assignments',
    )
    assigned_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_onboardings',
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'オンボーディングアサイン'
        unique_together = [['template', 'employee']]

    def __str__(self):
        return f'{self.employee} - {self.template}'

    @property
    def progress_percent(self):
        total = self.task_items.count()
        if total == 0:
            return 0
        done = self.task_items.filter(is_completed=True).count()
        return round(done / total * 100)


class OnboardingTaskItem(SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(
        OnboardingAssignment,
        on_delete=models.CASCADE,
        related_name='task_items',
    )
    template_task = models.ForeignKey(
        OnboardingTemplateTask,
        on_delete=models.CASCADE,
        related_name='task_items',
    )
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'タスク進捗'
        unique_together = [['assignment', 'template_task']]

    def __str__(self):
        return f'{self.assignment} - {self.template_task}'
