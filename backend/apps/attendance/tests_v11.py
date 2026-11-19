"""
attendance/tests_v11.py
=======================
日の区分・休日労働／深夜時間・勤務間インターバル・打刻時の IP／位置のテスト（詳細設計書 7.4）。
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest import mock

import pytest
from django.utils import timezone

from apps.attendance.models import AttendanceRecord
from apps.attendance.services import classify_day, rest_interval_minutes
from apps.notifications.models import Notification
from conftest import AttendanceRecordFactory, EmployeeFactory, ManagerEmployeeFactory


class TestClassifyDay:
    @pytest.mark.parametrize('d,expected', [
        (date(2026, 11, 16), 'weekday'),            # 月曜
        (date(2026, 11, 21), 'non_legal_holiday'),  # 土曜
        (date(2026, 11, 22), 'legal_holiday'),      # 日曜
        (date(2026, 11, 3),  'non_legal_holiday'),  # 文化の日（火曜）
        (date(2026, 12, 31), 'non_legal_holiday'),  # 年末
        (date(2027, 1, 4),   'weekday'),
    ])
    def test_classify(self, d, expected):
        assert classify_day(d) == expected


@pytest.mark.django_db
class TestMinutes:
    def _rec(self, day_type, ci, co, br=60):
        return AttendanceRecordFactory(day_type=day_type, clock_in=ci, clock_out=co, break_minutes=br)

    def test_weekday_overtime(self):
        r = self._rec('weekday', time(9), time(20))
        assert (r.work_minutes, r.overtime_minutes, r.holiday_work_minutes) == (600, 120, 0)

    def test_non_legal_holiday_is_all_overtime(self):
        r = self._rec('non_legal_holiday', time(9), time(13), br=0)
        assert (r.overtime_minutes, r.holiday_work_minutes) == (240, 0)

    def test_legal_holiday_is_holiday_work_not_overtime(self):
        r = self._rec('legal_holiday', time(9), time(18))
        assert (r.overtime_minutes, r.holiday_work_minutes) == (0, 480)

    @pytest.mark.parametrize('ci,co,expected', [
        (time(9), time(18), 0),
        (time(9), time(23, 30), 90),
        (time(4), time(12), 60),
        (time(4), time(23), 120),
    ])
    def test_late_night(self, ci, co, expected):
        assert self._rec('weekday', ci, co).late_night_minutes == expected


@pytest.mark.django_db
class TestPayslipPremiums:
    def test_holiday_and_late_night_go_to_extra_overtime(self):
        from apps.salary.models import SalaryGrade
        from apps.salary.views import _calculate_payslip
        emp = EmployeeFactory(grade=1, birth_date=date(1995, 1, 1))
        SalaryGrade.objects.create(grade=1, base_salary=320000, valid_from=date(2020, 1, 1))
        # 時給 2,000円。法定休日 8h → 2,000×8×1.35 = 21,600 / 深夜 1h → 2,000×1×0.25 = 500
        AttendanceRecordFactory(employee=emp, date=date(2026, 11, 22), day_type='legal_holiday',
                                clock_in=time(9), clock_out=time(18), break_minutes=60)
        AttendanceRecordFactory(employee=emp, date=date(2026, 11, 24), day_type='weekday',
                                clock_in=time(13), clock_out=time(23), break_minutes=60)
        payslip = _calculate_payslip(emp, 2026, 11)
        assert payslip.extra_overtime_pay == 22100
        # 平日の残業 1h（9h - 8h）のみが通常の残業手当
        assert payslip.overtime_pay == 2500


@pytest.mark.django_db
class TestClockInOut:
    def test_clock_in_records_ip_location_and_day_type(self, auth_client, employee_user):
        res = auth_client.post('/api/v1/attendance/clock-in/',
                               {'latitude': 35.6812362, 'longitude': 139.7671248},
                               format='json', HTTP_X_FORWARDED_FOR='203.0.113.5, 10.0.0.1')
        assert res.status_code == 201, res.data
        rec = AttendanceRecord.objects.get(employee=employee_user)
        assert rec.clock_in_ip == '203.0.113.5'
        assert rec.clock_in_latitude == Decimal('35.681236')
        assert rec.day_type == classify_day(date.today())

    def test_clock_in_without_location(self, auth_client, employee_user):
        assert auth_client.post('/api/v1/attendance/clock-in/', {}, format='json').status_code == 201
        assert AttendanceRecord.objects.get(employee=employee_user).clock_in_latitude is None

    def test_invalid_location_rejected(self, auth_client):
        res = auth_client.post('/api/v1/attendance/clock-in/', {'latitude': 120, 'longitude': 0}, format='json')
        assert res.status_code == 400

    def test_clock_out_records_location(self, auth_client, employee_user):
        auth_client.post('/api/v1/attendance/clock-in/', {}, format='json')
        res = auth_client.post('/api/v1/attendance/clock-out/',
                               {'break_minutes': 60, 'latitude': 34.7, 'longitude': 135.5}, format='json')
        assert res.status_code == 200
        assert res.data['clock_out_longitude'] is not None

    def test_employee_cannot_change_day_type(self, auth_client, employee_user):
        rec = AttendanceRecordFactory(employee=employee_user, day_type='weekday')
        res = auth_client.patch(f'/api/v1/attendance/{rec.id}/', {'day_type': 'legal_holiday'}, format='json')
        assert res.status_code == 400

    def test_manager_can_change_day_type(self, manager_client):
        rec = AttendanceRecordFactory(day_type='weekday')
        res = manager_client.patch(f'/api/v1/attendance/{rec.id}/?employee_id={rec.employee_id}',
                                   {'day_type': 'legal_holiday'}, format='json')
        assert res.status_code == 200, res.data
        rec.refresh_from_db()
        assert rec.day_type == 'legal_holiday'


@pytest.mark.django_db
class TestWorkInterval:
    def test_rest_interval_minutes(self):
        emp = EmployeeFactory()
        AttendanceRecordFactory(employee=emp, date=date(2026, 11, 16), clock_in=time(9), clock_out=time(23))
        at = timezone.make_aware(datetime(2026, 11, 17, 8, 0))
        assert rest_interval_minutes(emp, at) == 9 * 60

    def test_short_interval_notifies_employee_and_manager(self, auth_client, employee_user):
        mgr = ManagerEmployeeFactory()
        employee_user.managers.add(mgr)
        # 打刻 API は date.today() を勤怠日に使うため、テストも同じ「今日」を基準にする
        yesterday = date.today() - timedelta(days=1)
        AttendanceRecordFactory(employee=employee_user, date=yesterday, clock_in=time(9), clock_out=time(23, 30))
        fake_now = timezone.make_aware(datetime.combine(date.today(), time(7, 0)))
        with mock.patch('apps.attendance.views.timezone.localtime', return_value=fake_now):
            res = auth_client.post('/api/v1/attendance/clock-in/', {}, format='json')
        assert res.status_code == 201
        assert res.data['rest_interval_minutes'] == 450
        assert Notification.objects.filter(user=employee_user.user, type='work_interval').exists()
        assert Notification.objects.filter(user=mgr.user, type='work_interval').exists()

    def test_enough_interval_no_notice(self, auth_client, employee_user):
        yesterday = date.today() - timedelta(days=1)
        AttendanceRecordFactory(employee=employee_user, date=yesterday, clock_in=time(9), clock_out=time(18))
        fake_now = timezone.make_aware(datetime.combine(date.today(), time(9, 0)))
        with mock.patch('apps.attendance.views.timezone.localtime', return_value=fake_now):
            auth_client.post('/api/v1/attendance/clock-in/', {}, format='json')
        assert not Notification.objects.filter(type='work_interval').exists()
