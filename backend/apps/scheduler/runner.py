"""
定期ジョブの実行

run_due_jobs() を管理コマンド・常駐スケジューラ・API から呼び出す。
"""
import logging
import traceback
from datetime import date

from django.utils import timezone

from .models import JobRun
from .registry import get_jobs, get_job

logger = logging.getLogger(__name__)


def run_job(job, run_date: date, force: bool = False) -> JobRun | None:
    """1つのジョブを実行する。その日に成功済みで force でなければ None を返す"""
    if not force and JobRun.objects.filter(
        job_name=job.name, run_date=run_date, status=JobRun.Status.SUCCESS,
    ).exists():
        return None

    run = JobRun.objects.create(job_name=job.name, run_date=run_date)
    try:
        result = job.func(run_date) or {}
        run.status = JobRun.Status.SUCCESS
        run.result = result
    except Exception:
        logger.exception('定期ジョブが失敗しました: %s', job.name)
        run.status = JobRun.Status.FAILED
        run.error  = traceback.format_exc()
        _notify_admins_of_failure(job.name, run_date)
    run.finished_at = timezone.now()
    run.save()
    return run


def run_due_jobs(run_date: date | None = None, only: str | None = None, force: bool = False) -> list[JobRun]:
    """
    登録済みジョブを順に実行する。

    - only を指定するとそのジョブだけ実行する
    - 1つのジョブが失敗しても後続のジョブは実行する
    """
    run_date = run_date or timezone.localdate()
    if only:
        job = get_job(only)
        if job is None:
            raise ValueError(f'ジョブが見つかりません: {only}')
        jobs = [job]
    else:
        jobs = get_jobs()

    runs = []
    for job in jobs:
        run = run_job(job, run_date, force=force)
        if run is not None:
            runs.append(run)
    return runs


def _notify_admins_of_failure(job_name, run_date):
    from apps.common.utils import users_with_roles
    from apps.notifications.models import Notification
    for user in users_with_roles('admin'):
        try:
            Notification.send(
                user=user,
                type_=Notification.NotificationType.SYSTEM,
                title='定期ジョブが失敗しました',
                message=f'{run_date} の {job_name} が失敗しました。実行履歴を確認してください。',
                related_url='/system',
            )
        except Exception:
            logger.exception('失敗通知の送信に失敗しました')
