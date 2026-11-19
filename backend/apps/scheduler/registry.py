"""
定期ジョブの登録簿

使い方（各アプリの jobs.py）:

    from apps.scheduler.registry import register_job

    @register_job('leave.grant_annual_leave', '有給の自動付与', order=20)
    def grant_annual_leave(run_date):
        ...
        return {'granted': 3}   # JobRun.result に保存される（JSON 化できる値）

ジョブは run_date（その回の「今日」）を受け取る。同じ日に何度呼ばれても
結果が重複しない（冪等な）作りにすること。
"""
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Job:
    name: str
    description: str
    order: int
    func: Callable


_JOBS: dict[str, Job] = {}


def register_job(name, description, order=100):
    def decorator(func):
        _JOBS[name] = Job(name=name, description=description, order=order, func=func)
        return func
    return decorator


def get_jobs():
    """登録済みジョブを実行順に返す"""
    return sorted(_JOBS.values(), key=lambda j: (j.order, j.name))


def get_job(name):
    return _JOBS.get(name)
