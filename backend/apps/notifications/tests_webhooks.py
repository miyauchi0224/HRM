"""
notifications/tests_webhooks.py
===============================
Slack / Teams 転送（URL 制限・要配慮情報の除外・送信内容）のテスト（詳細設計書 7.8）。
"""
from unittest import mock

import pytest

from apps.notifications.models import Notification, WebhookEndpoint
from apps.notifications.webhooks import build_payload, validate_webhook_url
from conftest import EmployeeFactory, UserFactory

SLACK_URL = 'https://hooks.slack.com/services/T000/B000/XXXX'
TEAMS_URL = 'https://prod-00.japaneast.logic.azure.com/workflows/abc/triggers/manual/paths/invoke'


@pytest.fixture(autouse=True)
def sync_webhooks(settings):
    settings.WEBHOOK_ASYNC = False


@pytest.fixture
def admin_client(api_client):
    api_client.force_authenticate(user=UserFactory(role='admin', roles=['admin']))
    return api_client


class TestValidateUrl:
    @pytest.mark.parametrize('provider,url,ok', [
        ('slack', SLACK_URL, True),
        ('slack', 'http://hooks.slack.com/x', False),
        ('slack', 'https://evil.example.com/hooks.slack.com', False),
        ('slack', 'https://hooks.slack.com.evil.com/x', False),
        ('teams', TEAMS_URL, True),
        ('teams', 'https://contoso.webhook.office.com/webhookb2/x', True),
        ('teams', 'https://169.254.169.254/latest', False),
    ])
    def test_allowlist(self, provider, url, ok):
        assert (validate_webhook_url(provider, url) is None) is ok

    def test_payload_shapes(self, settings):
        settings.FRONTEND_URL = 'https://hrm.example.com'
        slack = build_payload('slack', 'T', 'M', '/leave')
        assert slack == {'text': '*T*\nM\n<https://hrm.example.com/leave|画面を開く>'}
        teams = build_payload('teams', 'T', 'M', '/leave')
        card = teams['attachments'][0]['content']
        assert card['type'] == 'AdaptiveCard'
        assert card['actions'][0]['url'] == 'https://hrm.example.com/leave'


@pytest.mark.django_db
class TestDispatch:
    def test_personal_webhook_gets_all_types(self):
        emp = EmployeeFactory()
        emp.user.personal_webhook_provider = 'slack'
        emp.user.personal_webhook_url = SLACK_URL
        emp.user.save()
        with mock.patch('apps.notifications.webhooks.requests.post') as post:
            post.return_value.status_code = 200
            Notification.send(emp.user, 'stress_check', 'ストレスチェック', '回答してください')
        assert post.call_count == 1

    def test_org_webhook_filters_by_type_and_excludes_sensitive(self):
        emp = EmployeeFactory()
        WebhookEndpoint.objects.create(name='労務', provider='slack', url=SLACK_URL,
                                       notification_types=['overtime_alert', 'health_checkup'])
        with mock.patch('apps.notifications.webhooks.requests.post') as post:
            post.return_value.status_code = 200
            Notification.send(emp.user, 'overtime_alert', '残業', '45h')
            Notification.send(emp.user, 'leave_request', '休暇', 'x')
            Notification.send(emp.user, 'health_checkup', '健診', 'x')
        assert post.call_count == 1
        assert emp.full_name in post.call_args.kwargs['json']['text']

    def test_failure_does_not_break_notification(self):
        emp = EmployeeFactory()
        emp.user.personal_webhook_provider = 'slack'
        emp.user.personal_webhook_url = SLACK_URL
        emp.user.save()
        import requests
        with mock.patch('apps.notifications.webhooks.requests.post', side_effect=requests.ConnectionError):
            n = Notification.send(emp.user, 'system', 't', 'm')
        assert Notification.objects.filter(pk=n.pk).exists()


@pytest.mark.django_db
class TestWebhookAPI:
    URL = '/api/v1/notifications/webhooks/'

    def test_admin_creates(self, admin_client):
        res = admin_client.post(self.URL, {'name': '労務', 'provider': 'slack', 'url': SLACK_URL,
                                           'notification_types': ['overtime_alert']}, format='json')
        assert res.status_code == 201, res.data

    @pytest.mark.parametrize('types', [[], ['stress_check'], ['nope']])
    def test_invalid_types(self, admin_client, types):
        res = admin_client.post(self.URL, {'name': 'x', 'provider': 'slack', 'url': SLACK_URL,
                                           'notification_types': types}, format='json')
        assert res.status_code == 400

    def test_rejects_disallowed_url(self, admin_client):
        res = admin_client.post(self.URL, {'name': 'x', 'provider': 'slack', 'url': 'https://example.com/x',
                                           'notification_types': ['system']}, format='json')
        assert res.status_code == 400

    def test_hr_read_only(self, hr_client):
        assert hr_client.get(self.URL).status_code == 200
        res = hr_client.post(self.URL, {'name': 'x', 'provider': 'slack', 'url': SLACK_URL,
                                        'notification_types': ['system']}, format='json')
        assert res.status_code == 403

    def test_personal_webhook(self, auth_client, employee_user):
        url = '/api/v1/notifications/personal-webhook/'
        assert auth_client.put(url, {'provider': 'slack', 'url': 'https://example.com'},
                               format='json').status_code == 400
        res = auth_client.put(url, {'provider': 'teams', 'url': TEAMS_URL}, format='json')
        assert res.status_code == 200 and res.data['provider'] == 'teams'
        res = auth_client.put(url, {'provider': '', 'url': ''}, format='json')
        assert res.data == {'provider': '', 'url': ''}

    def test_notification_types(self, auth_client):
        res = auth_client.get('/api/v1/notifications/types/')
        assert {'value': 'health_checkup', 'label': '健康診断', 'sensitive': True} in res.data
