"""
accounts/tests_initial_password.py
==================================
初期パスワード（生年月日）と、初回ログイン時のパスワード変更のテスト。
"""
from datetime import date

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.accounts.passwords import initial_password_for
from conftest import EmployeeFactory

ME     = '/api/v1/auth/me/'
CHANGE = '/api/v1/auth/password/change/'


def test_initial_password_is_birth_date():
    assert initial_password_for(date(1990, 4, 1)) == '19900401'
    assert len(initial_password_for(None)) >= 12


@pytest.mark.django_db
class TestCreateEmployeeInitialPassword:
    def test_created_from_form_uses_birth_date(self, hr_client):
        res = hr_client.post('/api/v1/employees/', {
            'email': 'new@example.com', 'employee_number': 'E9001', 'last_name': '新規', 'first_name': '社員',
            'last_name_kana': 'シンキ', 'first_name_kana': 'シャイン', 'birth_date': '1995-07-15',
            'hire_date': '2026-04-01', 'department': '開発部', 'position': '一般', 'roles': ['employee'],
        }, format='json')
        assert res.status_code == 201
        assert res.data['temp_password'] == '19950715'
        user = User.objects.get(email='new@example.com')
        assert user.must_change_password


@pytest.mark.django_db
class TestFirstLoginPasswordChange:
    def _user(self):
        emp = EmployeeFactory(birth_date=date(1990, 4, 1))
        emp.user.set_password('19900401')
        emp.user.must_change_password = True
        emp.user.save()
        client = APIClient()
        client.force_authenticate(user=emp.user)
        return emp.user, client

    def test_me_reports_flag(self):
        _, client = self._user()
        assert client.get(ME).data['must_change_password'] is True

    def test_change_clears_flag(self):
        user, client = self._user()
        res = client.post(CHANGE, {'old_password': '19900401', 'new_password': 'Sakura-Blue-2026'}, format='json')
        assert res.status_code == 200
        user.refresh_from_db()
        assert not user.must_change_password
        assert user.check_password('Sakura-Blue-2026')

    @pytest.mark.parametrize('new_password', ['19900401', '202611221234', 'password1234'])
    def test_weak_or_same_password_rejected(self, new_password):
        user, client = self._user()
        res = client.post(CHANGE, {'old_password': '19900401', 'new_password': new_password}, format='json')
        assert res.status_code == 400
        user.refresh_from_db()
        assert user.must_change_password


@pytest.mark.django_db
class TestLoadSampleData:
    def test_load_and_reset(self):
        from apps.attendance.models import AttendanceRecord
        from apps.mbo.models import MBOGoal
        from apps.salary.models import Payslip
        from apps.employees.models import Employee

        call_command('load_sample_data', verbosity=0)
        aoki = User.objects.get(email='aoki.makoto@example.com')
        assert aoki.check_password('19750512')
        assert aoki.must_change_password
        assert Employee.objects.filter(employee_number__startswith='EMP').count() == 20
        # 部下には上司が設定されている
        assert Employee.objects.get(employee_number='EMP0010').managers.exists()
        assert AttendanceRecord.objects.exists()
        assert MBOGoal.objects.exists()
        assert Payslip.objects.filter(status='confirmed').exists()

        # 2回目は --reset なしではエラー、--reset で入れ直せる
        with pytest.raises(Exception):
            call_command('load_sample_data', verbosity=0)
        call_command('load_sample_data', '--reset', verbosity=0)
        assert Employee.objects.filter(employee_number__startswith='EMP').count() == 20
