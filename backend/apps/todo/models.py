import uuid
from django.db import models
from apps.employees.models import Employee


class TodoItem(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', '未着手'
        IN_PROGRESS = 'in_progress', '作業中'
        DONE        = 'done',        '実施済み'

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='todos')
    title       = models.CharField(max_length=200, verbose_name='タイトル')
    description = models.TextField(blank=True, verbose_name='詳細')
    status      = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NOT_STARTED, verbose_name='ステータス'
    )
    due_date    = models.DateField(null=True, blank=True, verbose_name='期限')
    order       = models.PositiveIntegerField(default=0, verbose_name='表示順')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'TODOアイテム'
        ordering     = ['status', 'order', '-created_at']

    def __str__(self):
        return f'{self.employee} - {self.title}'
