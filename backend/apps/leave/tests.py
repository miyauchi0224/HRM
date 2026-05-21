"""
leave/tests.py
==============
有給残高・休暇申請の CRUD・承認フローのテスト。
"""
import pytest
from rest_framework import status
from conftest import EmployeeFactory, ManagerEmployeeFactory, LeaveBalanceFactory

BALANCE_BASE = '/api/v1/leave/balances/'
REQUEST_BASE = '/api/v1/leave/requests/'


@pytest.mark.django_db
class TestLeaveBalanceModel:
    def test_remaining_days(self):
        balance = LeaveBalanceFactory(granted_days=20, carried_days=5, used_days=3)
        assert balance.remaining_days == 22  # 20 + 5 - 3

    def test_unique_together(self):
        from django.db import IntegrityError
        emp = EmployeeFactory()
        LeaveBalanceFactory(employee=emp, fiscal_year=2026)
        with pytest.raises(IntegrityError):
            LeaveBalanceFactory(employee=emp, fiscal_year=2026)


@pytest.mark.django_db
class TestLeaveBalanceAPI:
    def test_list_balances_as_employee(self, auth_client, employee_user):
        LeaveBalanceFactory(employee=employee_user)
        res = auth_client.get(BALANCE_BASE)
        assert res.status_code == status.HTTP_200_OK

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(BALANCE_BASE)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_balance_is_read_only(self, hr_client):
        """LeaveBalance は ReadOnlyModelViewSet なので POST は 405"""
        emp = EmployeeFactory()
        res = hr_client.post(BALANCE_BASE, {
            'employee': str(emp.id),
            'fiscal_year': 2026,
            'granted_days': '20.0',
        }, format='json')
        assert res.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_supervisor_can_list_all_balances(self, manager_client):
        """管理職はfull list が見える"""
        LeaveBalanceFactory()
        res = manager_client.get(BALANCE_BASE)
        assert res.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestLeaveRequestAPI:
    def test_create_leave_request(self, auth_client, employee_user):
        res = auth_client.post(REQUEST_BASE, {
            'leave_type': 'annual',
            'start_date': '2026-05-01',
            'end_date': '2026-05-02',
            'days': '2.0',
            'reason': 'プライベートのため',
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['status'] == 'pending'

    def test_list_own_requests(self, auth_client, employee_user):
        from apps.leave.models import LeaveRequest
        LeaveRequest.objects.create(
            employee=employee_user,
            leave_type='annual',
            start_date='2026-05-10',
            end_date='2026-05-10',
            days=1,
        )
        res = auth_client.get(REQUEST_BASE)
        assert res.status_code == status.HTTP_200_OK

    def test_approve_leave_request(self, api_client):
        """PATCH /approve/ で承認できる"""
        approver = ManagerEmployeeFactory()
        emp = EmployeeFactory()
        from apps.leave.models import LeaveRequest
        req = LeaveRequest.objects.create(
            employee=emp,
            leave_type='annual',
            start_date='2026-06-01',
            end_date='2026-06-01',
            days=1,
        )
        api_client.force_authenticate(user=approver.user)
        res = api_client.patch(f'{REQUEST_BASE}{req.id}/approve/', {'action': 'approve'}, format='json')
        assert res.status_code == status.HTTP_200_OK
        req.refresh_from_db()
        assert req.status == 'approved'

    def test_reject_leave_request(self, api_client):
        """PATCH /approve/ に action=reject で却下できる"""
        approver = ManagerEmployeeFactory()
        emp = EmployeeFactory()
        from apps.leave.models import LeaveRequest
        req = LeaveRequest.objects.create(
            employee=emp,
            leave_type='annual',
            start_date='2026-06-02',
            end_date='2026-06-02',
            days=1,
        )
        api_client.force_authenticate(user=approver.user)
        res = api_client.patch(f'{REQUEST_BASE}{req.id}/approve/', {'action': 'reject'}, format='json')
        assert res.status_code == status.HTTP_200_OK
        req.refresh_from_db()
        assert req.status == 'rejected'

    def test_cancel_own_request(self, auth_client, employee_user):
        """PATCH /cancel/ で自分の申請を取消できる"""
        from apps.leave.models import LeaveRequest
        req = LeaveRequest.objects.create(
            employee=employee_user,
            leave_type='annual',
            start_date='2026-07-01',
            end_date='2026-07-01',
            days=1,
        )
        res = auth_client.patch(f'{REQUEST_BASE}{req.id}/cancel/')
        assert res.status_code == status.HTTP_200_OK
        req.refresh_from_db()
        assert req.status == 'cancelled'
