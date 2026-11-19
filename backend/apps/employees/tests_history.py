"""
employees/tests_history.py
==========================
異動・昇格履歴（自動記録・発令予約・過去時点の組織図）のテスト（詳細設計書 7.5）。
"""
from datetime import date, timedelta

import pytest
from django.utils import timezone

from apps.employees.history import infer_change_type, snapshot_as_of
from apps.employees.jobs import apply_scheduled_changes
from apps.employees.models import EmploymentHistory
from conftest import EmployeeFactory


class TestInferChangeType:
    @pytest.mark.parametrize('before,after,expected', [
        ({'grade': 2, 'department': 'A'}, {'grade': 3, 'department': 'B'}, 'promotion'),
        ({'grade': 3}, {'grade': 2}, 'demotion'),
        ({'grade': 2, 'department': 'A'}, {'grade': 2, 'department': 'B'}, 'transfer'),
        ({'grade': 2, 'department': 'A', 'position': 'x'},
         {'grade': 2, 'department': 'A', 'position': 'y'}, 'position_change'),
    ])
    def test_priority(self, before, after, expected):
        assert infer_change_type(before, after) == expected


@pytest.mark.django_db
class TestAutoRecord:
    def test_change_creates_history(self):
        emp = EmployeeFactory(department='開発部', grade=2)
        emp.department = '営業部'
        emp.save()
        h = emp.employment_histories.get()
        assert (h.change_type, h.department_before, h.department_after) == ('transfer', '開発部', '営業部')
        assert h.is_applied and h.effective_date == timezone.localdate()

    def test_unrelated_change_does_not_record(self):
        emp = EmployeeFactory()
        emp.phone = '090-9999-9999'
        emp.save()
        assert not emp.employment_histories.exists()

    def test_api_update_records_operator(self, hr_client):
        emp = EmployeeFactory(grade=1)
        res = hr_client.patch(f'/api/v1/employees/{emp.id}/', {'grade': 2}, format='json')
        assert res.status_code == 200
        h = emp.employment_histories.get()
        assert h.change_type == 'promotion' and h.created_by is not None


@pytest.mark.django_db
class TestOrders:
    def test_past_dated_order_applies_immediately_without_duplicate(self, hr_client):
        emp = EmployeeFactory(department='開発部', position='一般社員')
        res = hr_client.post(f'/api/v1/employees/{emp.id}/history/', {
            'effective_date': timezone.localdate().isoformat(), 'department': '企画部', 'note': '定期異動',
        }, format='json')
        assert res.status_code == 201, res.data
        emp.refresh_from_db()
        assert emp.department == '企画部'
        assert emp.employment_histories.count() == 1
        assert emp.employment_histories.get().position_after == '一般社員'  # 空欄は変更なし

    def test_future_order_is_applied_by_job(self, hr_client):
        emp = EmployeeFactory(grade=2)
        future = timezone.localdate() + timedelta(days=10)
        hr_client.post(f'/api/v1/employees/{emp.id}/history/',
                       {'effective_date': future.isoformat(), 'grade': 3}, format='json')
        emp.refresh_from_db()
        assert emp.grade == 2
        assert apply_scheduled_changes(future - timedelta(days=1)) == {'applied': 0}
        assert apply_scheduled_changes(future) == {'applied': 1}
        emp.refresh_from_db()
        assert emp.grade == 3
        assert emp.employment_histories.count() == 1

    def test_order_requires_change(self, hr_client):
        emp = EmployeeFactory()
        res = hr_client.post(f'/api/v1/employees/{emp.id}/history/',
                             {'effective_date': '2026-04-01'}, format='json')
        assert res.status_code == 400

    def test_permissions(self, auth_client, employee_user):
        assert auth_client.get(f'/api/v1/employees/{employee_user.id}/history/').status_code == 200
        res = auth_client.post(f'/api/v1/employees/{employee_user.id}/history/',
                               {'effective_date': '2026-04-01', 'grade': 5}, format='json')
        assert res.status_code == 403


@pytest.mark.django_db
class TestAsOf:
    def _hist(self, emp, d, before, after):
        return EmploymentHistory.objects.create(
            employee=emp, effective_date=d, change_type='transfer',
            department_before=before, department_after=after, is_applied=True,
        )

    def test_snapshot(self):
        emp = EmployeeFactory(department='C')
        hs = [self._hist(emp, date(2025, 4, 1), 'A', 'B'), self._hist(emp, date(2026, 4, 1), 'B', 'C')]
        assert snapshot_as_of(emp, date(2024, 1, 1), hs)['department'] == 'A'
        assert snapshot_as_of(emp, date(2025, 10, 1), hs)['department'] == 'B'
        assert snapshot_as_of(emp, date(2026, 10, 1), hs)['department'] == 'C'
        assert snapshot_as_of(emp, date(2024, 1, 1), [])['department'] == 'C'

    def test_org_chart_as_of(self, manager_client):
        emp = EmployeeFactory(department='C', hire_date=date(2020, 4, 1))
        self._hist(emp, date(2026, 4, 1), 'B', 'C')
        EmployeeFactory(hire_date=date(2026, 5, 1))  # 指定日にはまだ入社していない
        res = manager_client.get('/api/v1/employees/org-chart/?as_of=2026-01-01')
        assert res.status_code == 200
        row = next(r for r in res.data if r['id'] == str(emp.id))
        assert row['department'] == 'B'
        assert all(r['id'] != '' for r in res.data)
        assert len([r for r in res.data if r['department'] == 'B']) == 1

    def test_org_chart_as_of_requires_manager(self, auth_client):
        assert auth_client.get('/api/v1/employees/org-chart/?as_of=2026-01-01').status_code == 403
