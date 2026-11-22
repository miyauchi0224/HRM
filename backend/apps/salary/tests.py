"""
salary/tests.py
===============
給与計算・明細の手動修正のテスト（不具合修正の回帰テストを含む）。
"""
from datetime import date

import pytest
from rest_framework import status

from apps.salary.models import Payslip, SalaryGrade
from conftest import EmployeeFactory, UserFactory

PAYSLIP_BASE = '/api/v1/salary/payslips/'


@pytest.fixture
def grade(db):
    return SalaryGrade.objects.create(grade=1, base_salary=300000, valid_from=date(2020, 1, 1))


def _calc(client, emp=None, year=2026, month=4):
    body = {'year': year, 'month': month}
    if emp is not None:
        body['employee_id'] = str(emp.id)
    return client.post(f'{PAYSLIP_BASE}calculate/', body, format='json')


@pytest.mark.django_db
class TestPayslipCalculate:
    def test_employee_without_birth_date(self, hr_client, grade):
        emp = EmployeeFactory(birth_date=None)
        res = _calc(hr_client)
        assert res.status_code == status.HTTP_200_OK
        assert Payslip.objects.get(employee=emp, year=2026, month=4).nursing_insurance == 0

    def test_recalculate_keeps_manual_deductions_in_totals(self, hr_client, grade):
        emp = EmployeeFactory()
        _calc(hr_client, emp)
        p = Payslip.objects.get(employee=emp, year=2026, month=4)
        hr_client.patch(f'{PAYSLIP_BASE}{p.id}/update/', {'resident_tax': 10000}, format='json')
        p.refresh_from_db()
        before = p.total_deductions

        _calc(hr_client, emp)
        p.refresh_from_db()
        assert p.resident_tax == 10000
        assert p.total_deductions == before
        assert p.net_salary == p.gross_salary - p.total_deductions

    def test_confirmed_payslip_is_not_recalculated(self, hr_client, grade):
        emp = EmployeeFactory()
        _calc(hr_client, emp)
        p = Payslip.objects.get(employee=emp, year=2026, month=4)
        hr_client.patch(f'{PAYSLIP_BASE}{p.id}/update/', {'status': 'confirmed', 'note': '確定'}, format='json')

        res = _calc(hr_client, emp)
        assert res.data['calculated'] == 0
        assert res.data['skipped'] == 1
        p.refresh_from_db()
        assert p.status == 'confirmed'
        assert p.note == '確定'

    def test_retired_employee_is_skipped(self, hr_client, grade):
        emp = EmployeeFactory(retire_date=date(2026, 3, 31))
        _calc(hr_client)
        assert not Payslip.objects.filter(employee=emp).exists()

    def test_invalid_year_month(self, hr_client):
        assert _calc(hr_client, year='abc').status_code == status.HTTP_400_BAD_REQUEST
        assert _calc(hr_client, month=13).status_code == status.HTTP_400_BAD_REQUEST

    def test_employee_cannot_calculate(self, auth_client):
        assert _calc(auth_client).status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestPayslipUpdate:
    def _payslip(self):
        return Payslip.objects.create(employee=EmployeeFactory(), year=2026, month=5, base_salary=300000)

    def test_string_number_is_accepted(self, hr_client):
        p = self._payslip()
        res = hr_client.patch(f'{PAYSLIP_BASE}{p.id}/update/', {'resident_tax': '1000'}, format='json')
        assert res.status_code == status.HTTP_200_OK
        p.refresh_from_db()
        assert p.resident_tax == 1000
        assert p.total_deductions == 1000

    def test_invalid_values_are_rejected(self, hr_client):
        p = self._payslip()
        for body in ({'resident_tax': 'abc'}, {'resident_tax': -1}, {'status': 'paid'}):
            res = hr_client.patch(f'{PAYSLIP_BASE}{p.id}/update/', body, format='json')
            assert res.status_code == status.HTTP_400_BAD_REQUEST, body

    def test_accounting_can_update(self, api_client):
        acc = EmployeeFactory(user=UserFactory(role='accounting', roles=['accounting']))
        api_client.force_authenticate(user=acc.user)
        p = self._payslip()
        res = api_client.patch(f'{PAYSLIP_BASE}{p.id}/update/', {'resident_tax': 500}, format='json')
        assert res.status_code == status.HTTP_200_OK

    def test_employee_cannot_update(self, auth_client, employee_user):
        p = Payslip.objects.create(employee=employee_user, year=2026, month=5)
        res = auth_client.patch(f'{PAYSLIP_BASE}{p.id}/update/', {'resident_tax': 0}, format='json')
        assert res.status_code == status.HTTP_403_FORBIDDEN
