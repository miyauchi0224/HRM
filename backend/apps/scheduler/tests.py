"""
scheduler/tests.py
==================
定期実行基盤（登録・冪等性・失敗時の扱い・API）のテスト。
"""
from datetime import date

import pytest
from rest_framework import status

from apps.scheduler import registry
from apps.scheduler.models import JobRun
from apps.scheduler.runner import run_due_jobs, run_job
from conftest import UserFactory


@pytest.fixture
def temp_jobs(monkeypatch):
    """テスト用のジョブだけを登録した状態にする"""
    jobs = {}
    monkeypatch.setattr(registry, '_JOBS', jobs)
    return jobs


@pytest.mark.django_db
class TestRunner:
    def test_all_v11_jobs_are_registered(self):
        names = {j.name for j in registry.get_jobs()}
        assert {
            'leave.rollover_fiscal_year', 'leave.grant_annual_leave', 'leave.check_five_day_obligation',
            'approval.remind_pending', 'employees.apply_scheduled_changes', 'skills.check_expiry',
            'health_checkup.remind_followups', 'one_on_one.remind_upcoming', 'pulse_survey.remind_unanswered',
        } <= names

    def test_rollover_runs_before_grant(self):
        order = [j.name for j in registry.get_jobs()]
        assert order.index('leave.rollover_fiscal_year') < order.index('leave.grant_annual_leave')

    def test_job_runs_once_per_day(self, temp_jobs):
        calls = []
        registry.register_job('t.count', 'count')(lambda d: calls.append(d) or {'n': len(calls)})
        run_due_jobs(date(2026, 5, 1))
        run_due_jobs(date(2026, 5, 1))
        assert len(calls) == 1
        run_due_jobs(date(2026, 5, 2))
        assert len(calls) == 2

    def test_force_reruns(self, temp_jobs):
        calls = []
        registry.register_job('t.count', 'count')(lambda d: calls.append(d))
        run_due_jobs(date(2026, 5, 1))
        run_due_jobs(date(2026, 5, 1), force=True)
        assert len(calls) == 2

    def test_failure_is_recorded_and_next_job_still_runs(self, temp_jobs):
        def boom(d):
            raise RuntimeError('boom')
        registry.register_job('t.a_fail', 'fail', order=1)(boom)
        registry.register_job('t.b_ok', 'ok', order=2)(lambda d: {'ok': True})
        runs = run_due_jobs(date(2026, 5, 1))
        assert [r.status for r in runs] == ['failed', 'success']
        assert 'RuntimeError' in runs[0].error

    def test_failed_job_retries_next_call(self, temp_jobs):
        state = {'fail': True}

        def flaky(d):
            if state['fail']:
                raise RuntimeError('x')
            return {}
        job_func = registry.register_job('t.flaky', 'flaky')(flaky)
        run_due_jobs(date(2026, 5, 1))
        state['fail'] = False
        runs = run_due_jobs(date(2026, 5, 1))
        assert runs[0].status == 'success'


@pytest.mark.django_db
class TestSchedulerAPI:
    def test_hr_can_list_jobs(self, hr_client):
        res = hr_client.get('/api/v1/scheduler/jobs/')
        assert res.status_code == status.HTTP_200_OK
        assert any(j['name'] == 'leave.grant_annual_leave' for j in res.data)

    def test_employee_cannot_list_jobs(self, auth_client):
        assert auth_client.get('/api/v1/scheduler/jobs/').status_code == status.HTTP_403_FORBIDDEN

    def test_only_admin_can_run(self, hr_client, api_client):
        assert hr_client.post('/api/v1/scheduler/jobs/skills.check_expiry/run/').status_code == 403
        admin = UserFactory(role='admin', roles=['admin'])
        api_client.force_authenticate(user=admin)
        res = api_client.post('/api/v1/scheduler/jobs/skills.check_expiry/run/', {'date': '2026-05-01'})
        assert res.status_code == status.HTTP_201_CREATED
        assert JobRun.objects.filter(job_name='skills.check_expiry', run_date=date(2026, 5, 1)).exists()

    def test_unknown_job_404(self, api_client):
        admin = UserFactory(role='admin', roles=['admin'])
        api_client.force_authenticate(user=admin)
        assert api_client.post('/api/v1/scheduler/jobs/nope/run/').status_code == 404
