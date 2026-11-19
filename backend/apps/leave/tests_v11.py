"""
leave/tests_v11.py
==================
有給の自動付与・年度繰越・年5日取得義務・代休のテスト（詳細設計書 7.2）。
"""
from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.leave import services
from apps.leave.models import LeaveBalance, LeaveGrant, LeaveRequest
from apps.notifications.models import Notification
from conftest import AttendanceRecordFactory, EmployeeFactory, LeaveBalanceFactory, ManagerEmployeeFactory


class TestGrantSchedule:
    def test_add_months_clamps_month_end(self):
        assert services.add_months(date(2026, 8, 31), 6) == date(2027, 2, 28)

    @pytest.mark.parametrize('today,expected', [
        (date(2026, 9, 30), None),                       # 6ヶ月前
        (date(2026, 10, 1), (date(2026, 10, 1), 10)),    # 初回付与
        (date(2027, 9, 30), (date(2026, 10, 1), 10)),
        (date(2027, 10, 1), (date(2027, 10, 1), 11)),    # 1年6ヶ月
        (date(2033, 10, 1), (date(2033, 10, 1), 20)),    # 7年6ヶ月 → 上限20日
    ])
    def test_latest_grant(self, today, expected):
        assert services.latest_grant(date(2026, 4, 1), today) == expected


@pytest.mark.django_db
class TestAutoGrant:
    def test_grants_on_grant_date_and_adds_to_balance(self):
        emp = EmployeeFactory(hire_date=date(2026, 4, 1))
        granted = services.grant_annual_leave(date(2026, 10, 1))
        assert [g.employee_id for g in granted] == [emp.id]
        g = granted[0]
        assert g.days == 10
        assert g.expires_on == date(2028, 9, 30)
        assert LeaveBalance.objects.get(employee=emp, fiscal_year=2026).granted_days == 10

    def test_idempotent(self):
        EmployeeFactory(hire_date=date(2026, 4, 1))
        services.grant_annual_leave(date(2026, 10, 1))
        assert services.grant_annual_leave(date(2026, 10, 2)) == []
        assert LeaveGrant.objects.count() == 1

    def test_catches_up_after_missed_days(self):
        EmployeeFactory(hire_date=date(2026, 4, 1))
        assert len(services.grant_annual_leave(date(2026, 10, 5))) == 1

    def test_excludes_part_time_and_retired(self):
        EmployeeFactory(hire_date=date(2026, 4, 1), employment_type='part_time')
        EmployeeFactory(hire_date=date(2026, 4, 1), retire_date=date(2026, 9, 1))
        assert services.grant_annual_leave(date(2026, 10, 1)) == []

    def test_deleted_grant_is_not_regranted(self):
        EmployeeFactory(hire_date=date(2026, 4, 1))
        g = services.grant_annual_leave(date(2026, 10, 1))[0]
        g.soft_delete()
        assert services.grant_annual_leave(date(2026, 10, 2)) == []

    def test_job_notifies_employee(self):
        from apps.leave.jobs import grant_annual_leave
        emp = EmployeeFactory(hire_date=date(2026, 4, 1))
        grant_annual_leave(date(2026, 10, 1))
        assert Notification.objects.filter(user=emp.user, type='leave_alert').exists()


@pytest.mark.django_db
class TestRollover:
    def test_carries_previous_remaining_capped_by_previous_grant(self):
        emp = EmployeeFactory()
        LeaveBalanceFactory(employee=emp, fiscal_year=2025, granted_days=11, carried_days=10, used_days=3)
        services.rollover_fiscal_year(date(2026, 4, 1))
        cur = LeaveBalance.objects.get(employee=emp, fiscal_year=2026)
        # 残18日だが、繰り越せるのは前年度付与の11日まで
        assert cur.carried_days == 11
        assert cur.rollover_done

    def test_runs_once(self):
        emp = EmployeeFactory()
        LeaveBalanceFactory(employee=emp, fiscal_year=2025, granted_days=10, used_days=2)
        services.rollover_fiscal_year(date(2026, 4, 1))
        LeaveBalance.objects.filter(employee=emp, fiscal_year=2025).update(used_days=0)
        assert services.rollover_fiscal_year(date(2026, 4, 2)) == 0
        assert LeaveBalance.objects.get(employee=emp, fiscal_year=2026).carried_days == 8

    def test_does_not_overwrite_manual_carry(self):
        emp = EmployeeFactory()
        LeaveBalanceFactory(employee=emp, fiscal_year=2025, granted_days=10)
        LeaveBalanceFactory(employee=emp, fiscal_year=2026, granted_days=0, carried_days=3)
        services.rollover_fiscal_year(date(2026, 4, 1))
        assert LeaveBalance.objects.get(employee=emp, fiscal_year=2026).carried_days == 3


def _approved_annual(emp, start, days):
    return LeaveRequest.objects.create(
        employee=emp, leave_type='annual', start_date=start, end_date=start,
        days=Decimal(str(days)), status='approved',
    )


@pytest.mark.django_db
class TestFiveDayObligation:
    def test_status_counts_half_days(self):
        emp = EmployeeFactory()
        grant = services.record_grant(emp, date(2026, 4, 1), 10)
        _approved_annual(emp, date(2026, 5, 1), 1)
        _approved_annual(emp, date(2026, 6, 1), 0.5)
        _approved_annual(emp, date(2027, 4, 1), 3)  # 基準期間外
        st = services.obligation_status(grant, date(2026, 7, 1))
        assert st['taken_days'] == 1.5
        assert st['remaining_required'] == 3.5
        assert st['deadline'] == date(2027, 3, 31)
        assert st['status'] == 'ok'  # 期限まで90日超

    @pytest.mark.parametrize('today,expected', [
        (date(2027, 1, 1), 'warning'),
        (date(2027, 4, 1), 'overdue'),
    ])
    def test_status_levels(self, today, expected):
        grant = services.record_grant(EmployeeFactory(), date(2026, 4, 1), 10)
        assert services.obligation_status(grant, today)['status'] == expected

    def test_job_notifies_employee_manager_and_hr_at_milestones(self, hr_user):
        from apps.leave.jobs import check_five_day_obligation
        mgr = ManagerEmployeeFactory()
        emp = EmployeeFactory()
        emp.managers.add(mgr)
        services.record_grant(emp, date(2026, 4, 1), 10)
        deadline = date(2027, 3, 31)

        check_five_day_obligation(deadline - timedelta(days=60))
        assert Notification.objects.filter(user=emp.user, type='leave_obligation').count() == 1
        assert Notification.objects.filter(user=mgr.user, type='leave_obligation').count() == 1
        assert not Notification.objects.filter(user=hr_user.user, type='leave_obligation').exists()

        check_five_day_obligation(deadline - timedelta(days=30))
        assert Notification.objects.filter(user=hr_user.user, type='leave_obligation').count() == 1

        check_five_day_obligation(deadline - timedelta(days=29))  # 通知日以外
        assert Notification.objects.filter(user=emp.user, type='leave_obligation').count() == 2

    def test_no_notice_when_taken(self):
        from apps.leave.jobs import check_five_day_obligation
        emp = EmployeeFactory()
        services.record_grant(emp, date(2026, 4, 1), 10)
        _approved_annual(emp, date(2026, 5, 1), 5)
        check_five_day_obligation(date(2027, 3, 31) - timedelta(days=30))
        assert not Notification.objects.filter(type='leave_obligation').exists()


@pytest.mark.django_db
class TestGrantAPI:
    def test_own_obligation(self, auth_client, employee_user):
        services.record_grant(employee_user, date.today() - timedelta(days=30), 10)
        res = auth_client.get('/api/v1/leave/grants/obligation/')
        assert res.status_code == 200
        assert res.data['required_days'] == 5

    def test_obligation_not_applicable(self, auth_client):
        assert auth_client.get('/api/v1/leave/grants/obligation/').data == {'status': 'not_applicable'}

    def test_summary_permissions(self, auth_client, hr_user):
        assert auth_client.get('/api/v1/leave/grants/obligation-summary/').status_code == 403
        services.record_grant(EmployeeFactory(), date.today() - timedelta(days=300), 10)
        hr_client = APIClient()
        hr_client.force_authenticate(user=hr_user.user)
        res = hr_client.get('/api/v1/leave/grants/obligation-summary/')
        assert res.status_code == 200
        assert res.data[0]['status'] == 'warning'

    def test_manager_summary_only_subordinates(self, manager_client, manager_user):
        sub = EmployeeFactory()
        sub.managers.add(manager_user)
        services.record_grant(sub, date.today() - timedelta(days=10), 10)
        services.record_grant(EmployeeFactory(), date.today() - timedelta(days=10), 10)
        res = manager_client.get('/api/v1/leave/grants/obligation-summary/')
        assert [r['employee_id'] for r in res.data] == [str(sub.id)]

    def test_hr_manual_grant_and_delete(self, hr_client):
        emp = EmployeeFactory(employment_type='part_time')
        res = hr_client.post('/api/v1/leave/grants/', {
            'employee': str(emp.id), 'grant_date': '2026-10-01', 'days': '5', 'note': '比例付与',
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['source'] == 'manual'
        assert LeaveBalance.objects.get(employee=emp, fiscal_year=2026).granted_days == 5
        assert hr_client.delete(f'/api/v1/leave/grants/{res.data["id"]}/').status_code == 204
        assert LeaveBalance.objects.get(employee=emp, fiscal_year=2026).granted_days == 0

    def test_employee_cannot_grant(self, auth_client, employee_user):
        res = auth_client.post('/api/v1/leave/grants/', {
            'employee': str(employee_user.id), 'grant_date': '2026-10-01', 'days': '5',
        })
        assert res.status_code == 403


def _holiday_work(emp, d, **kw):
    return AttendanceRecordFactory(employee=emp, date=d, day_type='legal_holiday',
                                   clock_in=time(9), clock_out=time(15), **kw)


@pytest.mark.django_db
class TestCompensatoryLeave:
    URL = '/api/v1/leave/requests/'

    def _payload(self, hw, start):
        return {'leave_type': 'compensatory', 'start_date': start, 'end_date': start, 'days': '1',
                'holiday_work': str(hw.id)}

    def test_create_ok(self, auth_client, employee_user):
        hw = _holiday_work(employee_user, date.today() - timedelta(days=3))
        res = auth_client.post(self.URL, self._payload(hw, date.today().isoformat()))
        assert res.status_code == status.HTTP_201_CREATED, res.data
        assert res.data['holiday_work_date'] == hw.date.isoformat()

    def test_requires_holiday_work(self, auth_client):
        today = date.today().isoformat()
        res = auth_client.post(self.URL, {'leave_type': 'compensatory', 'start_date': today,
                                          'end_date': today, 'days': '1'})
        assert res.status_code == 400

    def test_rejects_weekday_and_others_records(self, auth_client, employee_user):
        weekday = AttendanceRecordFactory(employee=employee_user, date=date.today() - timedelta(days=2),
                                          day_type='weekday')
        others  = _holiday_work(EmployeeFactory(), date.today() - timedelta(days=2))
        for hw in (weekday, others):
            res = auth_client.post(self.URL, self._payload(hw, date.today().isoformat()))
            assert res.status_code == 400

    def test_one_leave_per_holiday_work(self, auth_client, employee_user):
        hw = _holiday_work(employee_user, date.today() - timedelta(days=3))
        assert auth_client.post(self.URL, self._payload(hw, date.today().isoformat())).status_code == 201
        assert auth_client.post(self.URL, self._payload(hw, date.today().isoformat())).status_code == 400

    def test_must_be_within_valid_days(self, auth_client, employee_user, settings):
        settings.COMPENSATORY_LEAVE_VALID_DAYS = 30
        hw = _holiday_work(employee_user, date.today() - timedelta(days=40))
        assert auth_client.post(self.URL, self._payload(hw, date.today().isoformat())).status_code == 400

    def test_holiday_work_list(self, auth_client, employee_user):
        hw = _holiday_work(employee_user, date.today() - timedelta(days=3))
        AttendanceRecordFactory(employee=employee_user, date=date.today() - timedelta(days=4))
        res = auth_client.get('/api/v1/attendance/holiday-work/?unused=true')
        assert [r['id'] for r in res.data] == [str(hw.id)]
        auth_client.post(self.URL, self._payload(hw, date.today().isoformat()))
        assert auth_client.get('/api/v1/attendance/holiday-work/?unused=true').data == []

    def test_non_annual_leave_ignores_holiday_work(self, auth_client, employee_user):
        hw = _holiday_work(employee_user, date.today() - timedelta(days=3))
        today = date.today().isoformat()
        res = auth_client.post(self.URL, {'leave_type': 'special', 'start_date': today, 'end_date': today,
                                          'days': '1', 'holiday_work': str(hw.id)})
        assert res.status_code == 201
        assert res.data['holiday_work'] is None
