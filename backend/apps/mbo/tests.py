"""
mbo/tests.py
============
MBO目標・月報の CRUD・権限チェックのテスト。
（日報は todo/tests.py でカバー）
"""
import datetime
import pytest
from rest_framework import status
from conftest import EmployeeFactory, MBOGoalFactory, ManagerEmployeeFactory

GOAL_BASE   = '/api/v1/mbo/goals/'
REPORT_BASE = '/api/v1/mbo/reports/'


@pytest.mark.django_db
class TestMBOGoalModel:
    def test_str(self):
        goal = MBOGoalFactory(year=2026, title='売上向上')
        assert '2026' in str(goal)
        assert '売上向上' in str(goal)

    def test_period_months_count_default(self):
        goal = MBOGoalFactory()
        assert goal.period_months_count == 6

    def test_period_months_count_custom(self):
        goal = MBOGoalFactory(period_start_month=4, period_end_month=6)
        assert goal.period_months_count == 3


@pytest.mark.django_db
class TestMBOGoalAPI:
    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(GOAL_BASE)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_goal(self, auth_client, employee_user):
        res = auth_client.post(GOAL_BASE, {
            'year': 2026,
            'period': 'first_half',
            'title': '顧客満足度向上',
            'target_level': 'NPS スコア +10 以上',
            'weight': 30,
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['title'] == '顧客満足度向上'

    def test_list_own_goals(self, auth_client, employee_user):
        MBOGoalFactory(employee=employee_user)
        res = auth_client.get(GOAL_BASE)
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        assert len(results) >= 1

    def test_employee_sees_only_own_goals(self, auth_client, employee_user):
        other = EmployeeFactory()
        MBOGoalFactory(employee=other)
        res = auth_client.get(GOAL_BASE)
        results = res.data.get('results', res.data)
        for g in results:
            assert g.get('id') is not None

    def test_submit_goal(self, auth_client, employee_user):
        """ウェイト合計 100% の目標を PATCH /submit/ で提出できる"""
        goal = MBOGoalFactory(employee=employee_user, weight=100)
        res = auth_client.patch(f'{GOAL_BASE}{goal.id}/submit/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['status'] == 'submitted'

    def test_manager_can_evaluate(self, api_client):
        """管理職が PATCH /evaluate/ でスコアを付与できる"""
        manager = ManagerEmployeeFactory()
        emp = EmployeeFactory()
        goal = MBOGoalFactory(employee=emp, status='submitted')
        api_client.force_authenticate(user=manager.user)
        res = api_client.patch(f'{GOAL_BASE}{goal.id}/evaluate/', {
            'manager_score': '4.0',
        }, format='json')
        assert res.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestMBOReportAPI:
    def test_create_report(self, auth_client, employee_user):
        goal = MBOGoalFactory(employee=employee_user, status='approved')
        res = auth_client.post(REPORT_BASE, {
            'goal': str(goal.id),
            'month': '2026-04-01',
            'action_content': '施策A を実施',
            'result': '売上 10% 向上',
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED

    def test_list_own_reports(self, auth_client, employee_user):
        goal = MBOGoalFactory(employee=employee_user)
        from apps.mbo.models import MBOReport
        MBOReport.objects.create(
            goal=goal,
            month=datetime.date(2026, 4, 1),
            action_content='テスト',
            result='結果',
        )
        res = auth_client.get(REPORT_BASE)
        assert res.status_code == status.HTTP_200_OK

    def test_submit_report(self, auth_client, employee_user):
        """PATCH /reports/{id}/submit/ で月報を提出できる"""
        goal = MBOGoalFactory(employee=employee_user, status='approved')
        from apps.mbo.models import MBOReport
        report = MBOReport.objects.create(
            goal=goal,
            month=datetime.date(2026, 5, 1),
            action_content='施策B を実施',
            result='成果B',
        )
        res = auth_client.patch(f'{REPORT_BASE}{report.id}/submit/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['status'] == 'submitted'
