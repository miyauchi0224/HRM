"""
one_on_one/tests.py
===================
1on1 の参加者制限・上司メモの非公開・AI 要約（API 呼び出しはモック）のテスト（詳細設計書 7.7）。
"""
from datetime import timedelta
from unittest import mock

import pytest
from django.utils import timezone

from apps.notifications.models import Notification
from apps.one_on_one.jobs import remind_upcoming
from apps.one_on_one.models import OneOnOneMeeting
from conftest import EmployeeFactory, ManagerEmployeeFactory

URL = '/api/v1/one-on-one/meetings/'


@pytest.fixture
def pair(db):
    manager = ManagerEmployeeFactory()
    member  = EmployeeFactory()
    member.managers.add(manager)
    return manager, member


def _as(api_client, emp):
    api_client.force_authenticate(user=emp.user)
    return api_client


def _meeting(manager, member, **kw):
    return OneOnOneMeeting.objects.create(manager=manager, member=member,
                                          scheduled_at=kw.pop('scheduled_at', timezone.now()), **kw)


@pytest.mark.django_db
class TestMeetingAPI:
    def test_manager_creates_and_member_is_notified(self, api_client, pair):
        manager, member = pair
        res = _as(api_client, manager).post(URL, {
            'manager': str(manager.id), 'member': str(member.id),
            'scheduled_at': (timezone.now() + timedelta(days=2)).isoformat(),
            'agenda': 'キャリアについて', 'manager_private_notes': '評価面談の前に確認',
        }, format='json')
        assert res.status_code == 201, res.data
        assert res.data['my_role'] == 'manager'
        assert Notification.objects.filter(user=member.user, type='one_on_one').exists()

    def test_requires_manager_relationship(self, api_client, pair):
        manager, _ = pair
        stranger = EmployeeFactory()
        res = _as(api_client, manager).post(URL, {
            'manager': str(manager.id), 'member': str(stranger.id), 'scheduled_at': timezone.now().isoformat(),
        }, format='json')
        assert res.status_code == 400

    def test_cannot_create_for_others(self, api_client, pair):
        manager, member = pair
        res = _as(api_client, EmployeeFactory()).post(URL, {
            'manager': str(manager.id), 'member': str(member.id), 'scheduled_at': timezone.now().isoformat(),
        }, format='json')
        assert res.status_code == 400

    def test_private_notes_hidden_from_member(self, api_client, pair):
        manager, member = pair
        m = _meeting(manager, member, manager_private_notes='秘密')
        res = _as(api_client, member).get(f'{URL}{m.id}/')
        assert res.status_code == 200
        assert 'manager_private_notes' not in res.data
        res = _as(api_client, member).patch(f'{URL}{m.id}/', {'manager_private_notes': 'x'}, format='json')
        assert res.status_code == 400
        assert _as(api_client, manager).get(f'{URL}{m.id}/').data['manager_private_notes'] == '秘密'

    def test_non_participant_cannot_see(self, api_client, hr_client, pair):
        m = _meeting(*pair)
        assert hr_client.get(f'{URL}{m.id}/').status_code == 404

    def test_member_can_edit_shared_notes_and_action_items(self, api_client, pair):
        manager, member = pair
        m = _meeting(manager, member)
        res = _as(api_client, member).patch(f'{URL}{m.id}/', {
            'shared_notes': '話した内容', 'action_items': [{'text': '資料を作る', 'owner': 'member'}],
        }, format='json')
        assert res.status_code == 200, res.data
        assert res.data['action_items'] == [{'text': '資料を作る', 'owner': 'member', 'done': False}]

    def test_partners(self, api_client, pair):
        manager, member = pair
        res = _as(api_client, manager).get(URL + 'partners/')
        assert [p['id'] for p in res.data['members']] == [str(member.id)]
        res = _as(api_client, member).get(URL + 'partners/')
        assert [p['id'] for p in res.data['managers']] == [str(manager.id)]


def _fake_response(body):
    raw = mock.MagicMock()
    raw.http_response.json.return_value = body
    client = mock.MagicMock()
    client.with_options.return_value.messages.with_raw_response.create.return_value = raw
    return client


@pytest.mark.django_db
class TestAISummary:
    def test_summary_excludes_private_notes(self, api_client, pair):
        manager, member = pair
        _meeting(manager, member, scheduled_at=timezone.now() - timedelta(days=14),
                 action_items=[{'text': '前回の宿題', 'owner': 'member', 'done': False}])
        m = _meeting(manager, member, agenda='目標の進捗', shared_notes='順調', manager_private_notes='極秘メモ')
        body = {
            'stop_reason': 'end_turn',
            'content': [
                {'type': 'thinking', 'thinking': ''},
                {'type': 'text', 'text': '{"summary": "順調に進んでいる", '
                                         '"action_items": [{"text": "次の資料", "owner": "member"}], '
                                         '"next_agenda": ["前回の宿題の確認"]}'},
            ],
        }
        client = _fake_response(body)
        with mock.patch('apps.one_on_one.ai.get_client', return_value=client):
            res = _as(api_client, manager).post(f'{URL}{m.id}/ai-summary/')
        assert res.status_code == 200, res.data
        assert res.data['action_items'] == [{'text': '次の資料', 'owner': 'member', 'done': False}]
        m.refresh_from_db()
        assert m.ai_summary == '順調に進んでいる'

        kwargs = client.with_options.return_value.messages.with_raw_response.create.call_args.kwargs
        sent = kwargs['messages'][0]['content']
        assert '極秘メモ' not in sent
        assert '前回の宿題' in sent
        assert kwargs['model'] == 'claude-opus-5-5'
        assert kwargs['extra_body']['output_config']['format']['type'] == 'json_schema'

    def test_refusal(self, api_client, pair):
        m = _meeting(*pair, agenda='x')
        client = _fake_response({'stop_reason': 'refusal', 'content': []})
        with mock.patch('apps.one_on_one.ai.get_client', return_value=client):
            res = _as(api_client, pair[0]).post(f'{URL}{m.id}/ai-summary/')
        assert res.status_code == 422

    def test_no_api_key(self, api_client, pair):
        m = _meeting(*pair, agenda='x')
        with mock.patch('apps.one_on_one.ai.get_client', return_value=None):
            assert _as(api_client, pair[0]).post(f'{URL}{m.id}/ai-summary/').status_code == 503

    def test_empty_meeting(self, api_client, pair):
        m = _meeting(*pair)
        with mock.patch('apps.one_on_one.ai.get_client', return_value=mock.MagicMock()):
            assert _as(api_client, pair[0]).post(f'{URL}{m.id}/ai-summary/').status_code == 400


@pytest.mark.django_db
class TestRemind:
    def test_remind_tomorrow(self, pair):
        manager, member = pair
        tomorrow = timezone.localtime() + timedelta(days=1)
        _meeting(manager, member, scheduled_at=tomorrow)
        _meeting(manager, member, scheduled_at=tomorrow, status='cancelled')
        assert remind_upcoming(timezone.localdate()) == {'meetings': 1}
        assert Notification.objects.filter(type='one_on_one', user=member.user).count() == 1
        assert Notification.objects.filter(type='one_on_one', user=manager.user).count() == 1
