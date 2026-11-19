"""
approval/tests_delegation.py
============================
代理承認・承認リマインドのテスト（詳細設計書 7.3）。
"""
from datetime import date, timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from apps.approval.jobs import remind_pending
from apps.approval.models import ApprovalDelegation, ApprovalStep
from apps.leave.models import LeaveRequest
from apps.notifications.models import Notification
from conftest import ApprovalRequestFactory, EmployeeFactory, ExpenseRequestFactory, ManagerEmployeeFactory


def _delegate(delegator, delegate, start=None, end=None):
    today = date.today()
    return ApprovalDelegation.objects.create(
        delegator=delegator, delegate=delegate,
        start_date=start or today - timedelta(days=1), end_date=end or today + timedelta(days=5),
    )


@pytest.fixture
def team(db):
    """上司・部下・代理人（一般社員）"""
    manager  = ManagerEmployeeFactory()
    member   = EmployeeFactory()
    delegate = EmployeeFactory()
    member.managers.add(manager)
    return manager, member, delegate


def _client_for(api_client, employee):
    api_client.force_authenticate(user=employee.user)
    return api_client


@pytest.mark.django_db
class TestDelegationAPI:
    URL = '/api/v1/approval/delegations/'

    def test_create_for_self_notifies_delegate(self, api_client, team):
        manager, _, delegate = team
        c = _client_for(api_client, manager)
        res = c.post(self.URL, {'delegate': str(delegate.id), 'start_date': '2026-08-10',
                                'end_date': '2026-08-14', 'reason': '夏季休暇'})
        assert res.status_code == status.HTTP_201_CREATED, res.data
        assert res.data['delegator'] == manager.id
        assert Notification.objects.filter(user=delegate.user, title='代理承認者に設定されました').exists()

    def test_cannot_delegate_to_self_or_invert_dates(self, api_client, team):
        manager, _, delegate = team
        c = _client_for(api_client, manager)
        assert c.post(self.URL, {'delegate': str(manager.id), 'start_date': '2026-08-10',
                                 'end_date': '2026-08-14'}).status_code == 400
        assert c.post(self.URL, {'delegate': str(delegate.id), 'start_date': '2026-08-14',
                                 'end_date': '2026-08-10'}).status_code == 400

    def test_only_hr_can_set_for_others(self, api_client, hr_user, team):
        manager, member, delegate = team
        payload = {'delegator': str(manager.id), 'delegate': str(delegate.id),
                   'start_date': '2026-08-10', 'end_date': '2026-08-14'}
        assert _client_for(api_client, member).post(self.URL, payload).status_code == 403
        assert _client_for(api_client, hr_user).post(self.URL, payload).status_code == 201

    def test_list_only_related(self, api_client, team):
        manager, member, delegate = team
        _delegate(manager, delegate)
        assert len(_client_for(api_client, member).get(self.URL).data['results']) == 0
        assert len(_client_for(api_client, delegate).get(self.URL).data['results']) == 1


@pytest.mark.django_db
class TestDelegatedLeaveApproval:
    def _leave(self, member):
        today = date.today()
        return LeaveRequest.objects.create(employee=member, leave_type='special',
                                           start_date=today, end_date=today, days=1)

    def test_delegate_receives_request_notification(self, api_client, team):
        manager, member, delegate = team
        _delegate(manager, delegate)
        c = _client_for(api_client, member)
        today = date.today().isoformat()
        c.post('/api/v1/leave/requests/', {'leave_type': 'special', 'start_date': today,
                                           'end_date': today, 'days': '1'})
        assert Notification.objects.filter(user=manager.user, title='休暇申請').exists()
        assert Notification.objects.filter(user=delegate.user, title='【代理】休暇申請').exists()

    def test_delegate_can_see_and_approve(self, api_client, team):
        manager, member, delegate = team
        _delegate(manager, delegate)
        req = self._leave(member)
        c = _client_for(api_client, delegate)
        assert any(r['id'] == str(req.id) for r in c.get('/api/v1/leave/requests/').data['results'])
        res = c.patch(f'/api/v1/leave/requests/{req.id}/approve/', {'action': 'approve'})
        assert res.status_code == 200
        req.refresh_from_db()
        assert req.status == 'approved' and req.approver_id == delegate.id

    def test_expired_delegation_cannot_approve(self, api_client, team):
        manager, member, delegate = team
        _delegate(manager, delegate, start=date.today() - timedelta(days=10), end=date.today() - timedelta(days=1))
        req = self._leave(member)
        res = _client_for(api_client, delegate).patch(f'/api/v1/leave/requests/{req.id}/approve/',
                                                      {'action': 'approve'})
        assert res.status_code == 403

    def test_unrelated_delegate_cannot_approve(self, api_client, team):
        _, member, delegate = team
        other_manager = ManagerEmployeeFactory()
        _delegate(other_manager, delegate)
        req = self._leave(member)
        res = _client_for(api_client, delegate).patch(f'/api/v1/leave/requests/{req.id}/approve/',
                                                      {'action': 'approve'})
        assert res.status_code == 403

    def test_delegate_can_approve_expense(self, api_client, team):
        manager, member, delegate = team
        _delegate(manager, delegate)
        exp = ExpenseRequestFactory(applicant=member)
        res = _client_for(api_client, delegate).patch(f'/api/v1/expense/requests/{exp.id}/approve/',
                                                      {'action': 'approve'})
        assert res.status_code == 200
        exp.refresh_from_db()
        assert exp.status == 'approved' and exp.approver_id == delegate.id


@pytest.mark.django_db
class TestDelegatedApprovalStep:
    def test_delegate_decides_step_and_is_recorded(self, api_client, team):
        manager, member, delegate = team
        _delegate(manager, delegate)
        req = ApprovalRequestFactory(applicant=member, status='pending', submitted_at=timezone.now())
        ApprovalStep.objects.create(request=req, approver=manager, order=1)
        c = _client_for(api_client, delegate)
        res = c.patch(f'/api/v1/approval/requests/{req.id}/decide/', {'decision': 'approved'})
        assert res.status_code == 200, res.data
        step = req.steps.get()
        assert step.decision == 'approved'
        assert step.decided_by_id == delegate.id
        assert res.data['steps'][0]['decided_by_name'] == delegate.full_name

    def test_non_delegate_cannot_decide(self, api_client, team):
        manager, member, delegate = team
        req = ApprovalRequestFactory(applicant=member, status='pending', submitted_at=timezone.now())
        ApprovalStep.objects.create(request=req, approver=manager, order=1)
        res = _client_for(api_client, delegate).patch(f'/api/v1/approval/requests/{req.id}/decide/',
                                                      {'decision': 'approved'})
        assert res.status_code in (403, 404)


@pytest.mark.django_db
class TestRemindPending:
    def _age(self, obj, days):
        type(obj).objects.filter(pk=obj.pk).update(created_at=timezone.now() - timedelta(days=days))

    @pytest.mark.parametrize('age,expected', [(2, 0), (3, 1), (4, 0), (6, 1)])
    def test_leave_reminder_every_n_days(self, team, settings, age, expected):
        settings.APPROVAL_REMIND_DAYS = 3
        manager, member, _ = team
        today = date.today()
        req = LeaveRequest.objects.create(employee=member, leave_type='special',
                                          start_date=today, end_date=today, days=1)
        self._age(req, age)
        remind_pending(timezone.localdate())
        assert Notification.objects.filter(user=manager.user, type='approval_reminder').count() == expected

    def test_reminder_also_goes_to_delegate(self, team, settings):
        settings.APPROVAL_REMIND_DAYS = 3
        manager, member, delegate = team
        _delegate(manager, delegate)
        exp = ExpenseRequestFactory(applicant=member)
        self._age(exp, 3)
        remind_pending(timezone.localdate())
        assert Notification.objects.filter(user=delegate.user, type='approval_reminder').exists()

    def test_approval_step_counts_from_previous_decision(self, team, settings):
        settings.APPROVAL_REMIND_DAYS = 3
        manager, member, _ = team
        second = ManagerEmployeeFactory()
        req = ApprovalRequestFactory(applicant=member, status='pending',
                                     submitted_at=timezone.now() - timedelta(days=10))
        ApprovalStep.objects.create(request=req, approver=manager, order=1, decision='approved',
                                    decided_at=timezone.now() - timedelta(days=3))
        ApprovalStep.objects.create(request=req, approver=second, order=2)
        remind_pending(timezone.localdate())
        assert Notification.objects.filter(user=second.user, type='approval_reminder').count() == 1
        assert not Notification.objects.filter(user=manager.user, type='approval_reminder').exists()
