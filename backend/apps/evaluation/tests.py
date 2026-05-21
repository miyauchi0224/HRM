"""
evaluation/tests.py
===================
評価期間・評価質問・360度評価の CRUD・権限チェックのテスト。
"""
import pytest
from rest_framework import status
from conftest import (
    EmployeeFactory, HREmployeeFactory, ManagerEmployeeFactory,
    EvaluationPeriodFactory, EvaluationQuestionFactory,
)

PERIOD_BASE   = '/api/v1/evaluation/periods/'
QUESTION_BASE = '/api/v1/evaluation/questions/'
EVAL_BASE     = '/api/v1/evaluation/evaluations/'


@pytest.mark.django_db
class TestEvaluationPeriodModel:
    def test_str(self):
        period = EvaluationPeriodFactory(fiscal_year=2026)
        assert '2026' in str(period)

    def test_unique_together(self):
        from django.db import IntegrityError
        EvaluationPeriodFactory(fiscal_year=2026, period_type='first_half')
        with pytest.raises(IntegrityError):
            EvaluationPeriodFactory(fiscal_year=2026, period_type='first_half')


@pytest.mark.django_db
class TestEvaluationPeriodAPI:
    """評価期間: 読み取りは全ユーザー、書き込みはHRのみ"""

    def test_list_periods_as_employee(self, auth_client):
        EvaluationPeriodFactory()
        res = auth_client.get(PERIOD_BASE)
        assert res.status_code == status.HTTP_200_OK

    def test_list_periods_unauthenticated(self, api_client):
        res = api_client.get(PERIOD_BASE)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_period_as_hr(self, hr_client):
        res = hr_client.post(PERIOD_BASE, {
            'fiscal_year': 2027,
            'period_type': 'first_half',
            'start_date': '2027-04-01',
            'end_date': '2027-09-30',
            'is_active': True,
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED

    def test_create_period_as_employee_forbidden(self, auth_client):
        res = auth_client.post(PERIOD_BASE, {
            'fiscal_year': 2028,
            'period_type': 'first_half',
            'start_date': '2028-04-01',
            'end_date': '2028-09-30',
        }, format='json')
        assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestEvaluationQuestionAPI:
    def test_list_questions_as_employee(self, auth_client):
        EvaluationQuestionFactory()
        res = auth_client.get(QUESTION_BASE)
        assert res.status_code == status.HTTP_200_OK

    def test_create_question_as_hr(self, hr_client):
        res = hr_client.post(QUESTION_BASE, {
            'category': 'performance',
            'text': 'この期間の目標達成度を評価してください',
            'order': 1,
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED

    def test_create_question_as_employee_forbidden(self, auth_client):
        res = auth_client.post(QUESTION_BASE, {
            'category': 'attitude',
            'text': '不正アクセステスト',
            'order': 99,
        }, format='json')
        assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestEvaluation360API:
    def test_create_evaluation(self, auth_client, employee_user):
        period = EvaluationPeriodFactory()
        subject = EmployeeFactory()
        res = auth_client.post(EVAL_BASE, {
            'period': str(period.id),
            'subject': str(subject.id),
            'evaluator_type': 'peer',
            'scores': [],
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED

    def test_list_own_evaluations(self, auth_client, employee_user):
        period = EvaluationPeriodFactory()
        from apps.evaluation.models import Evaluation360
        Evaluation360.objects.create(
            period=period,
            subject=employee_user,
            evaluator=employee_user,
            evaluator_type='self',
        )
        res = auth_client.get(EVAL_BASE)
        assert res.status_code == status.HTTP_200_OK

    def test_submit_evaluation(self, auth_client, employee_user):
        period = EvaluationPeriodFactory()
        from apps.evaluation.models import Evaluation360
        ev = Evaluation360.objects.create(
            period=period,
            subject=EmployeeFactory(),
            evaluator=employee_user,
            evaluator_type='peer',
        )
        res = auth_client.post(f'{EVAL_BASE}{ev.id}/submit/')
        assert res.status_code == status.HTTP_200_OK
        ev.refresh_from_db()
        assert ev.is_submitted

    def test_summary_endpoint(self, manager_client):
        period = EvaluationPeriodFactory()
        res = manager_client.get(f'{EVAL_BASE}summary/?period={period.id}')
        assert res.status_code == status.HTTP_200_OK

    def test_customer_cannot_access(self, api_client):
        from conftest import CustomerUserFactory
        user = CustomerUserFactory()
        api_client.force_authenticate(user=user)
        res = api_client.get(EVAL_BASE)
        assert res.status_code == status.HTTP_403_FORBIDDEN
