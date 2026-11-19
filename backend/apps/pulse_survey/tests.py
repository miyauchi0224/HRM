"""
pulse_survey/tests.py
=====================
パルスサーベイの回答・匿名性・集計（最小人数）のテスト（詳細設計書 7.10）。
"""
from datetime import date, timedelta

import pytest

from apps.notifications.models import Notification
from apps.pulse_survey.jobs import remind_unanswered
from apps.pulse_survey.models import PulseParticipation, PulseResponse, PulseSurvey
from apps.pulse_survey.services import build_results, submit_answers
from conftest import EmployeeFactory

URL = '/api/v1/pulse/surveys/'


def _survey(**kw):
    from apps.pulse_survey.serializers import PulseSurveySerializer
    s = PulseSurveySerializer(data={
        'title': '11月のパルス', 'start_date': (date.today() - timedelta(days=1)).isoformat(),
        'end_date': (date.today() + timedelta(days=7)).isoformat(), **kw,
    })
    s.is_valid(raise_exception=True)
    survey = s.save()
    survey.is_published = True
    survey.save()
    return survey


def _answers(survey, enps=9, scale=4, text='特になし'):
    out = {}
    for q in survey.questions.all():
        out[str(q.id)] = {'enps': enps, 'scale5': scale, 'text': text}[q.kind]
    return out


@pytest.mark.django_db
class TestSurveyAPI:
    def test_hr_creates_with_default_questions_and_publishes(self, hr_client):
        res = hr_client.post(URL, {'title': 'Q4', 'start_date': '2026-11-01', 'end_date': '2026-11-30'},
                             format='json')
        assert res.status_code == 201, res.data
        assert len(res.data['questions']) == 5
        EmployeeFactory()
        res = hr_client.post(f'{URL}{res.data["id"]}/publish/')
        assert res.status_code == 200
        assert Notification.objects.filter(type='pulse_survey').count() >= 2

    def test_employee_cannot_create_or_see_unpublished(self, auth_client):
        PulseSurvey.objects.create(title='draft', start_date=date(2026, 11, 1), end_date=date(2026, 11, 30))
        assert auth_client.get(URL).data['results'] == []
        assert auth_client.post(URL, {'title': 'x', 'start_date': '2026-11-01',
                                      'end_date': '2026-11-30'}, format='json').status_code == 403

    def test_answer_once_and_anonymous(self, auth_client, employee_user):
        survey = _survey()
        res = auth_client.post(f'{URL}{survey.id}/answer/', {'answers': _answers(survey)}, format='json')
        assert res.status_code == 201, res.data
        assert auth_client.post(f'{URL}{survey.id}/answer/', {'answers': _answers(survey)},
                                format='json').status_code == 400
        assert PulseResponse.objects.get().employee is None
        assert auth_client.get(f'{URL}{survey.id}/').data['has_answered'] is True

    def test_validation(self, auth_client):
        survey = _survey()
        bad = _answers(survey, scale=6)
        assert auth_client.post(f'{URL}{survey.id}/answer/', {'answers': bad}, format='json').status_code == 400
        missing = {k: v for k, v in _answers(survey).items() if isinstance(v, str)}
        assert auth_client.post(f'{URL}{survey.id}/answer/', {'answers': missing},
                                format='json').status_code == 400
        assert not PulseParticipation.objects.exists()

    def test_out_of_period(self, auth_client):
        survey = _survey()
        survey.end_date = date.today() - timedelta(days=1)
        survey.start_date = date.today() - timedelta(days=5)
        survey.save()
        assert auth_client.post(f'{URL}{survey.id}/answer/', {'answers': _answers(survey)},
                                format='json').status_code == 400

    def test_cannot_change_questions_after_publish(self, hr_client):
        survey = _survey()
        res = hr_client.patch(f'{URL}{survey.id}/', {'questions': [{'text': 'x', 'kind': 'scale5'}]},
                              format='json')
        assert res.status_code == 400

    def test_results_hr_only(self, auth_client):
        survey = _survey()
        assert auth_client.get(f'{URL}{survey.id}/results/').status_code == 403


@pytest.mark.django_db
class TestResults:
    def test_insufficient_below_min_group(self, settings):
        settings.PULSE_MIN_GROUP_SIZE = 3
        survey = _survey()
        for _ in range(2):
            submit_answers(survey, EmployeeFactory(), _answers(survey))
        r = build_results(survey)
        assert r['insufficient'] is True and r['questions'] == []

    def test_enps_and_department_threshold(self, settings):
        settings.PULSE_MIN_GROUP_SIZE = 3
        survey = _survey()
        for score in (10, 9, 7):
            submit_answers(survey, EmployeeFactory(department='開発部'), _answers(survey, enps=score))
        submit_answers(survey, EmployeeFactory(department='営業部'), _answers(survey, enps=2))
        r = build_results(survey)
        enps = next(q for q in r['questions'] if q['kind'] == 'enps')
        # 推奨者2・中立1・批判者1 / 4人 → (2-1)/4 = 25
        assert enps['enps'] == 25
        depts = {d['department']: d for d in r['departments']}
        assert depts['開発部']['response_count'] == 3
        assert depts['営業部'] == {'department': '営業部', 'insufficient': True}


@pytest.mark.django_db
class TestRemind:
    def test_remind_unanswered_two_days_before_end(self):
        survey = _survey()
        survey.end_date = date.today() + timedelta(days=2)
        survey.save()
        answered, pending = EmployeeFactory(), EmployeeFactory()
        submit_answers(survey, answered, _answers(survey))
        remind_unanswered(date.today())
        assert Notification.objects.filter(user=pending.user, type='pulse_survey').exists()
        assert not Notification.objects.filter(user=answered.user, type='pulse_survey').exists()
