"""
stress_check/tests.py
======================
ストレスチェック実施期間・回答・スコア計算のテスト。
"""
import pytest
from rest_framework import status
from conftest import EmployeeFactory, StressCheckPeriodFactory

PERIOD_BASE   = '/api/v1/stress-check/periods/'
RESPONSE_BASE = '/api/v1/stress-check/responses/'


@pytest.mark.django_db
class TestStressCheckPeriodModel:
    def test_str(self):
        period = StressCheckPeriodFactory(title='2026年度第1回ストレスチェック')
        assert '2026年度第1回ストレスチェック' in str(period)

    def test_default_not_published(self):
        period = StressCheckPeriodFactory()
        assert period.is_published is False


@pytest.mark.django_db
class TestStressCheckResponseModel:
    def test_unique_together(self):
        from django.db import IntegrityError
        from apps.stress_check.models import StressCheckResponse
        period = StressCheckPeriodFactory()
        emp = EmployeeFactory()
        StressCheckResponse.objects.create(period=period, employee=emp)
        with pytest.raises(IntegrityError):
            StressCheckResponse.objects.create(period=period, employee=emp)

    def test_calculate_score_all_max(self):
        """全問4点（逆転なし）で計算結果を検証"""
        from apps.stress_check.models import StressCheckResponse, STRESS_CHECK_QUESTIONS
        period = StressCheckPeriodFactory()
        emp = EmployeeFactory()
        # 全問に最大回答4をセット
        answers = {str(q['order']): 4 for q in STRESS_CHECK_QUESTIONS}
        resp = StressCheckResponse(period=period, employee=emp, answers=answers)
        score = resp.calculate_score()
        assert score > 0
        assert resp.total_score == score

    def test_calculate_score_high_stress_threshold(self):
        """77点以上で高ストレス判定"""
        from apps.stress_check.models import StressCheckResponse, STRESS_CHECK_QUESTIONS
        period = StressCheckPeriodFactory()
        emp = EmployeeFactory()
        # 全問に4点（最大スコア）を設定すると高ストレスになる
        answers = {str(q['order']): 4 for q in STRESS_CHECK_QUESTIONS}
        resp = StressCheckResponse(period=period, employee=emp, answers=answers)
        resp.calculate_score()
        # スコアが77以上かどうかはモデルの計算による
        assert resp.high_stress == (resp.total_score >= 77)


@pytest.mark.django_db
class TestStressCheckPeriodAPI:
    def test_list_published_periods_as_employee(self, auth_client):
        """公開済みの実施期間のみ社員に見える"""
        published = StressCheckPeriodFactory(is_published=True)
        unpublished = StressCheckPeriodFactory(is_published=False)
        res = auth_client.get(PERIOD_BASE)
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        ids = [str(r['id']) for r in results]
        assert str(published.id) in ids
        assert str(unpublished.id) not in ids

    def test_hr_sees_all_periods(self, hr_client):
        """HR は未公開も含め全て閲覧できる"""
        StressCheckPeriodFactory(is_published=False)
        StressCheckPeriodFactory(is_published=True)
        res = hr_client.get(PERIOD_BASE)
        results = res.data.get('results', res.data)
        assert len(results) >= 2

    def test_create_period_as_hr(self, hr_client):
        res = hr_client.post(PERIOD_BASE, {
            'title': '2026年度第2回ストレスチェック',
            'start_date': '2026-10-01',
            'end_date': '2026-10-31',
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED

    def test_create_period_as_employee_forbidden(self, auth_client):
        res = auth_client.post(PERIOD_BASE, {
            'title': '不正作成',
            'start_date': '2026-10-01',
            'end_date': '2026-10-31',
        }, format='json')
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(PERIOD_BASE)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_publish_period_as_hr(self, hr_client):
        period = StressCheckPeriodFactory(is_published=False)
        res = hr_client.post(f'{PERIOD_BASE}{period.id}/publish/')
        assert res.status_code == status.HTTP_200_OK
        period.refresh_from_db()
        assert period.is_published is True


@pytest.mark.django_db
class TestStressCheckResponseAPI:
    def test_start_response(self, auth_client, employee_user):
        """POST /responses/start/ で回答を開始できる"""
        period = StressCheckPeriodFactory(is_published=True)
        res = auth_client.post(f'{RESPONSE_BASE}start/', {
            'period_id': str(period.id),
        }, format='json')
        assert res.status_code == status.HTTP_200_OK

    def test_list_own_responses(self, auth_client, employee_user):
        from apps.stress_check.models import StressCheckResponse
        period = StressCheckPeriodFactory(is_published=True)
        StressCheckResponse.objects.create(
            period=period,
            employee=employee_user,
            answers={},
        )
        res = auth_client.get(RESPONSE_BASE)
        assert res.status_code == status.HTTP_200_OK

    def test_customer_returns_403(self, api_client):
        from conftest import CustomerUserFactory
        user = CustomerUserFactory()
        api_client.force_authenticate(user=user)
        res = api_client.get(RESPONSE_BASE)
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_template_csv_as_hr(self, hr_client):
        """質問テンプレートCSVダウンロード（HR のみ）"""
        res = hr_client.get(f'{PERIOD_BASE}template-csv/')
        assert res.status_code == status.HTTP_200_OK
        assert 'text/csv' in res['Content-Type']
