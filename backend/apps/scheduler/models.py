import uuid
from django.db import models


class JobRun(models.Model):
    """
    定期ジョブの実行履歴

    AuditLog と同じくログ扱いのため SoftDeleteModel は継承しない。
    同じ job_name × run_date で success があれば、その日は再実行しない。
    """
    class Status(models.TextChoices):
        RUNNING = 'running', '実行中'
        SUCCESS = 'success', '成功'
        FAILED  = 'failed',  '失敗'

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_name    = models.CharField(max_length=100, db_index=True, verbose_name='ジョブ名')
    run_date    = models.DateField(verbose_name='対象日')
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)
    result      = models.JSONField(default=dict, blank=True, verbose_name='結果')
    error       = models.TextField(blank=True, verbose_name='エラー')
    started_at  = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = '定期ジョブ実行履歴'
        ordering     = ['-started_at']
        indexes      = [models.Index(fields=['job_name', 'run_date'])]

    def __str__(self):
        return f'{self.job_name} {self.run_date} {self.status}'
