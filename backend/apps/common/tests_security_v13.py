"""
common/tests_security_v13.py
============================
アクセス制御の修正・秘密情報の暗号化・OAuth の state 検証・メディア配信のテスト（詳細設計書 9.1・9.4〜9.6）
"""
import uuid

import pytest
from django.db import connection
from rest_framework.test import APIClient

from conftest import EmployeeFactory, ManagerEmployeeFactory, HREmployeeFactory, CustomerUserFactory


def client_for(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


# ─────────────────────────────────────────────────────────────────────────────
# ▌ 社員 API
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEmployeeAccess:
    BASE = '/api/v1/employees/'

    def test_for_project_does_not_expose_detail_of_others(self):
        me, other = EmployeeFactory(), EmployeeFactory()
        c = client_for(me.user)
        assert c.get(f'{self.BASE}{other.id}/?for_project=true').status_code == 404
        res = c.patch(f'{self.BASE}{other.id}/?for_project=true', {'address': 'x'}, format='json')
        assert res.status_code == 404

    def test_for_project_list_still_works_without_sensitive_fields(self):
        me, other = EmployeeFactory(), EmployeeFactory()
        res = client_for(me.user).get(f'{self.BASE}?for_project=true&page_size=100')
        assert res.status_code == 200
        rows = res.data['results'] if isinstance(res.data, dict) else res.data
        assert str(other.id) in {r['id'] for r in rows}
        assert all('bank_account_number' not in r and 'address' not in r for r in rows)

    def test_employee_can_update_own_contact_fields(self):
        me = EmployeeFactory()
        res = client_for(me.user).patch(f'{self.BASE}{me.id}/', {'address': '東京都', 'phone': '03-1'}, format='json')
        assert res.status_code == 200
        me.refresh_from_db()
        assert me.address == '東京都'

    @pytest.mark.parametrize('field,value', [
        ('grade', '9'), ('department', '役員室'), ('position', '部長'),
        ('employee_number', 'X999'), ('bank_account_number', '9999999'), ('hire_date', '2000-01-01'),
    ])
    def test_employee_cannot_update_hr_fields(self, field, value):
        me = EmployeeFactory()
        res = client_for(me.user).patch(f'{self.BASE}{me.id}/', {field: value}, format='json')
        assert res.status_code == 403

    def test_manager_contact_only(self):
        mgr, other = ManagerEmployeeFactory(), EmployeeFactory()
        c = client_for(mgr.user)
        assert c.patch(f'{self.BASE}{other.id}/', {'address': '大阪'}, format='json').status_code == 200
        assert c.patch(f'{self.BASE}{other.id}/', {'grade': '9'}, format='json').status_code == 403

    def test_hr_can_update_all_fields(self):
        hr, other = HREmployeeFactory(), EmployeeFactory()
        res = client_for(hr.user).patch(f'{self.BASE}{other.id}/', {'department': '開発部'}, format='json')
        assert res.status_code == 200

    def test_customer_cannot_use_employee_api(self):
        customer = CustomerUserFactory()
        assert client_for(customer).get(f'{self.BASE}?for_project=true').status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# ▌ 社員別手当・ドキュメント・コンプライアンス・資産カテゴリ
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMasterWritePermissions:
    def test_employee_cannot_create_own_allowance(self):
        me = EmployeeFactory()
        c = client_for(me.user)
        res = c.post('/api/v1/salary/employee-allowances/', {'amount': 100000}, format='json')
        assert res.status_code == 403
        assert c.get('/api/v1/salary/employee-allowances/').status_code == 200

    @pytest.mark.parametrize('method,url', [
        ('patch', '/api/v1/documents/{id}/'),
        ('put', '/api/v1/documents/{id}/'),
        ('post', '/api/v1/compliance/checklists/'),
        ('patch', '/api/v1/compliance/checklists/{id}/'),
        ('delete', '/api/v1/compliance/checklists/{id}/'),
        ('post', '/api/v1/assets/categories/'),
        ('delete', '/api/v1/assets/categories/{id}/'),
    ])
    def test_employee_cannot_write(self, method, url):
        c = client_for(EmployeeFactory().user)
        res = getattr(c, method)(url.format(id=uuid.uuid4()), {'title': 'x', 'name': 'x'}, format='json')
        assert res.status_code == 403

    def test_compliance_read_still_allowed(self):
        assert client_for(EmployeeFactory().user).get('/api/v1/compliance/checklists/').status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# ▌ イントラ記事
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestArticleModify:
    BASE = '/api/v1/intra/articles/'

    def _approved_article(self, author):
        from apps.intra.models import Article
        return Article.objects.create(author=author, title='t', content='c', category='announcement',
                                      status=Article.Status.APPROVED, is_pinned=True)

    def test_other_employee_cannot_edit_or_delete(self):
        article = self._approved_article(EmployeeFactory())
        c = client_for(EmployeeFactory().user)
        assert c.patch(f'{self.BASE}{article.id}/', {'title': '改ざん'}, format='json').status_code == 403
        assert c.delete(f'{self.BASE}{article.id}/').status_code == 403
        article.refresh_from_db()
        assert article.title == 't' and not article.is_deleted

    def test_author_edit_of_approved_article_returns_to_draft(self):
        author = EmployeeFactory()
        article = self._approved_article(author)
        res = client_for(author.user).patch(f'{self.BASE}{article.id}/', {'title': '更新'}, format='json')
        assert res.status_code == 200
        article.refresh_from_db()
        assert article.title == '更新'
        assert article.status == 'draft' and not article.is_pinned

    def test_manager_edit_keeps_status(self):
        article = self._approved_article(EmployeeFactory())
        res = client_for(ManagerEmployeeFactory().user).patch(
            f'{self.BASE}{article.id}/', {'title': '修正'}, format='json')
        assert res.status_code == 200
        article.refresh_from_db()
        assert article.status == 'approved'


# ─────────────────────────────────────────────────────────────────────────────
# ▌ 秘密情報の暗号化
# ─────────────────────────────────────────────────────────────────────────────

def raw_value(table, column, pk):
    with connection.cursor() as cur:
        cur.execute(f'SELECT {column} FROM {table} WHERE id = %s', [pk])
        return cur.fetchone()[0]


@pytest.mark.django_db
class TestEncryption:
    def test_api_key_encrypted_at_rest(self):
        user = EmployeeFactory().user
        user.anthropic_api_key = 'sk-ant-secret-value'
        user.save()
        stored = raw_value('accounts_user', 'anthropic_api_key', user.pk)
        assert stored.startswith('enc:') and 'secret' not in stored
        user.refresh_from_db()
        assert user.anthropic_api_key == 'sk-ant-secret-value'

    def test_legacy_plaintext_still_readable(self):
        user = EmployeeFactory().user
        with connection.cursor() as cur:
            cur.execute('UPDATE accounts_user SET openai_api_key = %s WHERE id = %s', ['sk-plain', user.pk])
        user.refresh_from_db()
        assert user.openai_api_key == 'sk-plain'

    def test_webhook_and_calendar_tokens_encrypted(self):
        from apps.notifications.models import WebhookEndpoint
        from apps.calendar_sync.models import UserCalendarToken
        user = EmployeeFactory().user
        hook = WebhookEndpoint.objects.create(name='全社', provider='slack',
                                              url='https://hooks.slack.com/services/T/B/secret')
        token = UserCalendarToken.objects.create(user=user, provider='google',
                                                 access_token='ya29.secret', refresh_token='1//secret')
        assert raw_value('notifications_webhookendpoint', 'url', hook.pk).startswith('enc:')
        assert raw_value('calendar_sync_usercalendartoken', 'access_token', token.pk).startswith('enc:')
        token.refresh_from_db()
        assert token.access_token == 'ya29.secret'

    def test_wrong_key_does_not_leak_ciphertext(self, settings):
        from apps.common.fields import encrypt_value, decrypt_value
        from cryptography.fernet import Fernet
        encrypted = encrypt_value('secret')
        settings.FIELD_ENCRYPTION_KEY = Fernet.generate_key().decode()
        assert decrypt_value(encrypted) == ''


# ─────────────────────────────────────────────────────────────────────────────
# ▌ カレンダー連携の state 検証
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestOAuthState:
    CALLBACK = '/api/v1/calendar/oauth/{p}/callback/'

    def test_missing_state_rejected(self):
        c = client_for(EmployeeFactory().user)
        assert c.get(self.CALLBACK.format(p='ms') + '?code=abc').status_code == 400

    def test_state_of_other_user_rejected(self):
        from apps.calendar_sync.views import make_oauth_state
        attacker, victim = EmployeeFactory().user, EmployeeFactory().user
        state = make_oauth_state(attacker, 'google')
        res = client_for(victim).get(self.CALLBACK.format(p='google') + f'?code=abc&state={state}')
        assert res.status_code == 400

    def test_state_for_other_provider_rejected(self):
        from apps.calendar_sync.views import make_oauth_state
        user = EmployeeFactory().user
        state = make_oauth_state(user, 'google')
        res = client_for(user).get(self.CALLBACK.format(p='ms') + f'?code=abc&state={state}')
        assert res.status_code == 400

    def test_expired_state_rejected(self, monkeypatch):
        import apps.calendar_sync.views as v
        user = EmployeeFactory().user
        state = v.make_oauth_state(user, 'ms')
        monkeypatch.setattr(v, 'OAUTH_STATE_MAX_AGE', -1)
        assert not v.verify_oauth_state(state, user, 'ms')

    def test_valid_state_redirects_to_frontend(self, settings):
        from apps.calendar_sync.views import make_oauth_state
        settings.FRONTEND_URL = 'http://front.example'
        user = EmployeeFactory().user
        state = make_oauth_state(user, 'ms')
        res = client_for(user).get(self.CALLBACK.format(p='ms') + f'?state={state}')  # code なし（拒否された）
        assert res.status_code == 302
        assert res['Location'] == 'http://front.example/?calendar=error'

    def test_start_includes_state(self, settings):
        settings.GOOGLE_CLIENT_ID = 'cid'
        user = EmployeeFactory().user
        res = client_for(user).get('/api/v1/calendar/oauth/google/start/')
        assert res.status_code == 302 and 'state=' in res['Location']


# ─────────────────────────────────────────────────────────────────────────────
# ▌ メディア配信
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProtectedMedia:
    @pytest.fixture
    def media(self, settings, tmp_path):
        settings.MEDIA_ROOT = tmp_path
        (tmp_path / 'expense').mkdir()
        (tmp_path / 'expense' / 'r.pdf').write_bytes(b'%PDF-1.4')
        (tmp_path / 'intra').mkdir()
        (tmp_path / 'intra' / 'a.png').write_bytes(b'png')
        return tmp_path

    def test_anonymous_rejected(self, media):
        assert APIClient().get('/media/expense/r.pdf').status_code == 401

    def test_employee_can_fetch(self, media):
        res = client_for(EmployeeFactory().user).get('/media/expense/r.pdf')
        assert res.status_code == 200
        assert res['X-Content-Type-Options'] == 'nosniff'

    def test_customer_only_intra(self, media):
        c = client_for(CustomerUserFactory())
        assert c.get('/media/expense/r.pdf').status_code == 403
        assert c.get('/media/intra/a.png').status_code == 200

    def test_path_traversal_blocked(self, media):
        res = client_for(EmployeeFactory().user).get('/media/../settings.py')
        assert res.status_code in (400, 404)
