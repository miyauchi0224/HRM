"""
health_checkup/tests.py
=======================
健康診断の権限・集計・リマインドのテスト（詳細設計書 7.6）。
"""
from datetime import date, timedelta

import pytest

from apps.health_checkup.jobs import remind_followups
from apps.health_checkup.models import HealthCheckup
from apps.notifications.models import Notification
from conftest import EmployeeFactory, UserFactory

URL = '/api/v1/health-checkups/'


@pytest.fixture
def labor_client(api_client):
    emp = EmployeeFactory(user=UserFactory(role='labor', roles=['labor']))
    api_client.force_authenticate(user=emp.user)
    return api_client


def _hc(emp, **kw):
    defaults = dict(fiscal_year=2026, checkup_type='regular', checkup_date=date(2026, 6, 1), result='a_normal')
    defaults.update(kw)
    return HealthCheckup.objects.create(employee=emp, **defaults)


@pytest.mark.django_db
class TestPermissions:
    def test_employee_sees_only_own_and_cannot_write(self, auth_client, employee_user):
        _hc(employee_user)
        _hc(EmployeeFactory())
        res = auth_client.get(URL)
        assert res.status_code == 200
        assert len(res.data['results']) == 1
        assert auth_client.post(URL, {'employee': str(employee_user.id), 'fiscal_year': 2026}).status_code == 403

    def test_manager_cannot_see_subordinate(self, manager_client, manager_user):
        sub = EmployeeFactory()
        sub.managers.add(manager_user)
        _hc(sub)
        assert manager_client.get(URL).data['results'] == []

    def test_labor_can_crud(self, labor_client):
        emp = EmployeeFactory()
        res = labor_client.post(URL, {'employee': str(emp.id), 'fiscal_year': 2026, 'checkup_type': 'regular',
                                      'checkup_date': '2026-06-01', 'result': 'd_reexam',
                                      'followup_due_date': '2026-07-31'})
        assert res.status_code == 201, res.data
        assert res.data['followup_required'] and res.data['followup_pending']

    def test_result_requires_checkup_date(self, labor_client):
        res = labor_client.post(URL, {'employee': str(EmployeeFactory().id), 'fiscal_year': 2026,
                                      'result': 'a_normal'})
        assert res.status_code == 400


@pytest.mark.django_db
class TestSummary:
    def test_rate_and_unchecked(self, labor_client):
        a, b, c = EmployeeFactory(), EmployeeFactory(), EmployeeFactory()
        _hc(a)
        _hc(b, result='d_reexam', followup_due_date=date(2026, 8, 1))
        _hc(c, checkup_date=None, result='')  # 予定のみ
        EmployeeFactory(retire_date=date(2025, 1, 1))  # 退職者は対象外
        res = labor_client.get(URL + 'summary/?fiscal_year=2026')
        assert res.status_code == 200
        d = res.data
        # 対象: a, b, c ＋ labor_client 本人
        assert d['target_count'] == 4 and d['checked_count'] == 2
        assert d['checkup_rate'] == 50.0
        assert d['followup_pending_count'] == 1
        assert str(c.id) in {u['employee_id'] for u in d['unchecked']}

    def test_employee_forbidden(self, auth_client):
        assert auth_client.get(URL + 'summary/').status_code == 403


@pytest.mark.django_db
class TestRemindFollowups:
    def test_due_and_overdue(self, hr_user):
        emp = EmployeeFactory()
        hc = _hc(emp, result='e_treatment', followup_due_date=date(2026, 8, 1))
        remind_followups(date(2026, 8, 1) - timedelta(days=7))
        assert Notification.objects.filter(user=emp.user, type='health_checkup').count() == 1
        remind_followups(date(2026, 8, 1) - timedelta(days=6))
        assert Notification.objects.filter(user=emp.user, type='health_checkup').count() == 1
        remind_followups(date(2026, 8, 8))  # 7日超過 → 本人と人事
        assert Notification.objects.filter(user=hr_user.user, type='health_checkup').count() == 1

        hc.followup_completed_date = date(2026, 8, 9)
        hc.save()
        remind_followups(date(2026, 8, 15))
        assert Notification.objects.filter(user=hr_user.user, type='health_checkup').count() == 1
