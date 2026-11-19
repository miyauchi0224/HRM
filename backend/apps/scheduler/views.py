from datetime import date

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.accounts.permissions import IsHR, IsAdmin
from .models import JobRun
from .registry import get_jobs, get_job
from .runner import run_job


def _run_to_dict(run):
    if run is None:
        return None
    return {
        'id':          str(run.id),
        'job_name':    run.job_name,
        'run_date':    run.run_date,
        'status':      run.status,
        'result':      run.result,
        'error':       run.error,
        'started_at':  run.started_at,
        'finished_at': run.finished_at,
    }


@api_view(['GET'])
@permission_classes([IsHR])
def job_list(request):
    """GET /api/v1/scheduler/jobs/ — 登録ジョブと最終実行結果"""
    data = []
    for job in get_jobs():
        last = JobRun.objects.filter(job_name=job.name).first()
        data.append({
            'name':        job.name,
            'description': job.description,
            'order':       job.order,
            'last_run':    _run_to_dict(last),
        })
    return Response(data)


@api_view(['GET'])
@permission_classes([IsHR])
def run_list(request):
    """GET /api/v1/scheduler/runs/?job_name= — 実行履歴（最新100件）"""
    qs = JobRun.objects.all()
    job_name = request.query_params.get('job_name')
    if job_name:
        qs = qs.filter(job_name=job_name)
    return Response([_run_to_dict(r) for r in qs[:100]])


@api_view(['POST'])
@permission_classes([IsAdmin])
def run_now(request, job_name):
    """POST /api/v1/scheduler/jobs/{job_name}/run/ — 手動実行（管理者のみ）"""
    job = get_job(job_name)
    if job is None:
        return Response({'error': 'ジョブが見つかりません'}, status=status.HTTP_404_NOT_FOUND)

    run_date = date.today()
    if request.data.get('date'):
        try:
            run_date = date.fromisoformat(request.data['date'])
        except ValueError:
            return Response({'error': '日付は YYYY-MM-DD 形式で指定してください'},
                            status=status.HTTP_400_BAD_REQUEST)

    run = run_job(job, run_date, force=bool(request.data.get('force', True)))
    if run is None:
        return Response({'detail': 'この日は実行済みです'}, status=status.HTTP_200_OK)
    return Response(_run_to_dict(run), status=status.HTTP_201_CREATED)
