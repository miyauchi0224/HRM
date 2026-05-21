"""
approval/tests.py
=================
稟議申請・承認ステップ・権限チェックのテスト。
"""
import pytest
from django.utils import timezone
from rest_framework import status
from conftest import (
    EmployeeFactory, HREmployeeFactory, ManagerEmployeeFactory,
    ApprovalRequestFactory,
)

BASE = '/api/v1/approval/requests/'


# ─────────────────────────────────────────────────────────────────────────────
# ▌ ApprovalRequest モデル単体テスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestApprovalRequestModel:
    def test_str(self):
        req = ApprovalRequestFactory(title='テスト稟議')
        assert 'テスト稟議' in str(req)

    def test_default_status_is_draft(self):
        req = ApprovalRequestFactory()
        assert req.status == 'draft'

    def test_status_choices(self):
        from apps.approval.models import ApprovalRequest
        statuses = [c[0] for c in ApprovalRequest.Status.choices]
        assert 'draft' in statuses
        assert 'approved' in statuses
        assert 'rejected' in statuses


# ─────────────────────────────────────────────────────────────────────────────
# ▌ ApprovalRequest API テスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestApprovalRequestAPI:
    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(BASE)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_own_requests(self, auth_client, employee_user):
        ApprovalRequestFactory(applicant=employee_user)
        res = auth_client.get(BASE)
        assert res.status_code == status.HTTP_200_OK

    def test_create_request(self, auth_client, employee_user):
        res = auth_client.post(BASE, {
            'title': '備品購入申請',
            'category': 'purchase',
            'content': 'ノートパソコンを購入したい',
            'amount': 150000,
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['title'] == '備品購入申請'
        assert res.data['status'] == 'draft'

    def test_submit_request(self, auth_client, employee_user):
        req = ApprovalRequestFactory(applicant=employee_user)
        res = auth_client.post(f'{BASE}{req.id}/submit/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['status'] == 'pending'

    def test_withdraw_request(self, auth_client, employee_user):
        req = ApprovalRequestFactory(applicant=employee_user, status='pending')
        res = auth_client.post(f'{BASE}{req.id}/withdraw/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['status'] == 'withdrawn'

    def test_cannot_submit_others_request(self, auth_client):
        other_emp = EmployeeFactory()
        req = ApprovalRequestFactory(applicant=other_emp)
        res = auth_client.post(f'{BASE}{req.id}/submit/')
        assert res.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)

    def test_manager_sees_all_requests(self, manager_client):
        ApprovalRequestFactory()
        ApprovalRequestFactory()
        res = manager_client.get(BASE)
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        assert len(results) >= 2


# ─────────────────────────────────────────────────────────────────────────────
# ▌ 承認ステップ テスト（decide エンドポイント）
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestApprovalStepAPI:
    def test_approve_step(self, api_client):
        """管理職が PATCH /decide/ で承認できる"""
        approver = ManagerEmployeeFactory()
        applicant = EmployeeFactory()
        req = ApprovalRequestFactory(applicant=applicant, status='pending')
        from apps.approval.models import ApprovalStep
        step = ApprovalStep.objects.create(
            request=req,
            approver=approver,
            step_role='manager',
            order=1,
            decision='pending',
        )
        api_client.force_authenticate(user=approver.user)
        res = api_client.patch(f'{BASE}{req.id}/decide/', {
            'decision': 'approved',
            'comment': '承認します',
        }, format='json')
        assert res.status_code == status.HTTP_200_OK
        step.refresh_from_db()
        assert step.decision == 'approved'

    def test_reject_step(self, api_client):
        """管理職が PATCH /decide/ で却下できる"""
        approver = ManagerEmployeeFactory()
        applicant = EmployeeFactory()
        req = ApprovalRequestFactory(applicant=applicant, status='pending')
        from apps.approval.models import ApprovalStep
        step = ApprovalStep.objects.create(
            request=req,
            approver=approver,
            step_role='manager',
            order=1,
            decision='pending',
        )
        api_client.force_authenticate(user=approver.user)
        res = api_client.patch(f'{BASE}{req.id}/decide/', {
            'decision': 'rejected',
            'comment': '却下します',
        }, format='json')
        assert res.status_code == status.HTTP_200_OK
        step.refresh_from_db()
        assert step.decision == 'rejected'

    def test_non_approver_cannot_decide(self, auth_client, employee_user):
        """申請ステップの承認者でない社員は decide できない"""
        approver = ManagerEmployeeFactory()
        req = ApprovalRequestFactory(applicant=employee_user, status='pending')
        from apps.approval.models import ApprovalStep
        ApprovalStep.objects.create(
            request=req, approver=approver, step_role='manager', order=1, decision='pending',
        )
        res = auth_client.patch(f'{BASE}{req.id}/decide/', {
            'decision': 'approved',
        }, format='json')
        assert res.status_code == status.HTTP_403_FORBIDDEN


# ─────────────────────────────────────────────────────────────────────────────
# ▌ ApprovalTemplate API テスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestApprovalTemplateAPI:
    TEMPLATE_BASE = '/api/v1/approval/templates/'

    def test_list_templates(self, auth_client):
        res = auth_client.get(self.TEMPLATE_BASE)
        assert res.status_code == status.HTTP_200_OK

    def test_create_template_as_employee(self, auth_client):
        """テンプレート作成は IsNotCustomer なら可能"""
        res = auth_client.post(self.TEMPLATE_BASE, {
            'name': '購買申請テンプレート',
            'description': '備品購入用',
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED

    def test_create_template_as_customer_forbidden(self, api_client):
        """顧客ロールはテンプレート作成不可"""
        from conftest import CustomerUserFactory
        user = CustomerUserFactory()
        api_client.force_authenticate(user=user)
        res = api_client.post(self.TEMPLATE_BASE, {
            'name': '不正テンプレート',
        }, format='json')
        assert res.status_code == status.HTTP_403_FORBIDDEN
