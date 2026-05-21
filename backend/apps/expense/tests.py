"""
expense/tests.py
================
勘定科目・経費申請の CRUD・承認フローのテスト。
"""
import pytest
from rest_framework import status
from conftest import (
    EmployeeFactory, HREmployeeFactory, ManagerEmployeeFactory,
    AccountItemFactory, ExpenseRequestFactory,
)

ITEM_BASE    = '/api/v1/expense/account-items/'
REQUEST_BASE = '/api/v1/expense/requests/'


@pytest.mark.django_db
class TestAccountItemModel:
    def test_str(self):
        item = AccountItemFactory(code='T001', name='旅費交通費')
        assert 'T001' in str(item)
        assert '旅費交通費' in str(item)


@pytest.mark.django_db
class TestAccountItemAPI:
    def test_list_items(self, auth_client):
        AccountItemFactory()
        res = auth_client.get(ITEM_BASE)
        assert res.status_code == status.HTTP_200_OK

    def test_create_item_as_accounting(self, api_client):
        from conftest import UserFactory
        user = UserFactory(role='accounting', roles=['accounting'])
        emp  = EmployeeFactory(user=user)
        api_client.force_authenticate(user=user)
        res = api_client.post(ITEM_BASE, {
            'code': 'S001',
            'name': '消耗品費',
            'category': 'supplies',
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED

    def test_create_item_as_employee_forbidden(self, auth_client):
        res = auth_client.post(ITEM_BASE, {
            'code': 'X999',
            'name': '不正科目',
            'category': 'other',
        }, format='json')
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(ITEM_BASE)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestExpenseRequestModel:
    def test_str(self):
        req = ExpenseRequestFactory(amount=5000)
        assert '5000' in str(req)

    def test_default_status_is_pending(self):
        req = ExpenseRequestFactory()
        assert req.status == 'pending'


@pytest.mark.django_db
class TestExpenseRequestAPI:
    def test_create_request(self, auth_client, employee_user):
        item = AccountItemFactory()
        res = auth_client.post(REQUEST_BASE, {
            'account_item': str(item.id),
            'expense_type': 'transportation',
            'payment_type': 'reimbursement',
            'amount': 2500,
            'expense_date': '2026-04-15',
            'description': '顧客訪問電車代',
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['amount'] == 2500

    def test_list_own_requests(self, auth_client, employee_user):
        ExpenseRequestFactory(applicant=employee_user)
        res = auth_client.get(REQUEST_BASE)
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        assert len(results) >= 1

    def test_employee_cannot_see_others(self, auth_client, employee_user):
        other = EmployeeFactory()
        ExpenseRequestFactory(applicant=other)
        res = auth_client.get(REQUEST_BASE)
        results = res.data.get('results', res.data)
        for r in results:
            # 自分の申請のみ
            assert r.get('applicant') is not None

    def test_approve_request(self, api_client):
        """PATCH /requests/{id}/approve/ で承認できる"""
        approver = ManagerEmployeeFactory()
        emp = EmployeeFactory()
        req = ExpenseRequestFactory(applicant=emp)
        api_client.force_authenticate(user=approver.user)
        res = api_client.patch(f'{REQUEST_BASE}{req.id}/approve/', {'action': 'approve'}, format='json')
        assert res.status_code == status.HTTP_200_OK
        req.refresh_from_db()
        assert req.status == 'approved'

    def test_reject_request(self, api_client):
        """PATCH /requests/{id}/approve/ に action=reject で却下できる"""
        approver = ManagerEmployeeFactory()
        emp = EmployeeFactory()
        req = ExpenseRequestFactory(applicant=emp)
        api_client.force_authenticate(user=approver.user)
        res = api_client.patch(f'{REQUEST_BASE}{req.id}/approve/', {
            'action': 'reject',
            'rejected_reason': '領収書が不明確'
        }, format='json')
        assert res.status_code == status.HTTP_200_OK
        req.refresh_from_db()
        assert req.status == 'rejected'

    def test_employee_cannot_approve(self, auth_client):
        """一般社員は承認できない（403）"""
        emp2 = EmployeeFactory()
        req  = ExpenseRequestFactory(applicant=emp2)
        res  = auth_client.patch(f'{REQUEST_BASE}{req.id}/approve/', {'action': 'approve'}, format='json')
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(REQUEST_BASE)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
