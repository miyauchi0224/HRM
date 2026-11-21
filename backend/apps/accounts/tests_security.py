"""
accounts/tests_security.py
==========================
HttpOnly Cookie 認証・CSRF・リフレッシュ・ログアウト・パスワード変更・ログイン制限のテスト（詳細設計書 9.2・9.3）
"""
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from conftest import EmployeeFactory

PASSWORD = 'TestPass1234!'
LOGIN = '/api/v1/auth/login/'
ME = '/api/v1/auth/me/'


def make_employee():
    emp = EmployeeFactory()
    emp.user.set_password(PASSWORD)
    emp.user.save()
    return emp


def csrf_client():
    """CSRF 検証を有効にしたクライアント（ブラウザと同じ条件）"""
    return APIClient(enforce_csrf_checks=True)


def login(client, user, password=PASSWORD):
    return client.post(LOGIN, {'email': user.email, 'password': password}, format='json')


def csrf_header(client):
    token = client.get('/api/v1/auth/csrf/').data['csrfToken']
    return {'HTTP_X_CSRFTOKEN': token}


@pytest.mark.django_db
class TestCookieAuth:
    def test_login_sets_httponly_cookies_without_tokens_in_body(self):
        emp = make_employee()
        client = csrf_client()
        res = login(client, emp.user)
        assert res.status_code == 200
        assert 'access' not in res.data and 'refresh' not in res.data
        access, refresh = res.cookies['hrm_access'], res.cookies['hrm_refresh']
        assert access['httponly'] and refresh['httponly']
        assert access['samesite'] == 'Lax'
        assert refresh['path'] == '/api/v1/auth/'

    def test_cookie_authenticates_get(self):
        emp = make_employee()
        client = csrf_client()
        login(client, emp.user)
        res = client.get(ME)
        assert res.status_code == 200
        assert res.data['email'] == emp.user.email

    def test_unsafe_request_without_csrf_is_rejected(self):
        emp = make_employee()
        client = csrf_client()
        login(client, emp.user)
        res = client.post('/api/v1/todo/items/', {'title': 'x'}, format='json')
        assert res.status_code == 403
        assert 'CSRF' in str(res.data['detail'])

    def test_unsafe_request_with_csrf_is_accepted(self):
        emp = make_employee()
        client = csrf_client()
        login(client, emp.user)
        res = client.patch('/api/v1/employees/me/', {'phone': '090-0000-0000'}, format='json',
                           **csrf_header(client))
        assert res.status_code == 200

    def test_bearer_header_skips_csrf(self):
        """ブラウザ以外のクライアント（ヘッダー認証）は CSRF の対象外"""
        emp = make_employee()
        client = csrf_client()
        token = str(RefreshToken.for_user(emp.user).access_token)
        res = client.patch('/api/v1/employees/me/', {'phone': '090-1111-1111'}, format='json',
                           HTTP_AUTHORIZATION=f'Bearer {token}')
        assert res.status_code == 200

    def test_refresh_rotates_cookies(self):
        emp = make_employee()
        client = csrf_client()
        old_refresh = login(client, emp.user).cookies['hrm_refresh'].value
        res = client.post('/api/v1/auth/refresh/', **csrf_header(client))
        assert res.status_code == 200
        assert res.cookies['hrm_refresh'].value != old_refresh
        # 入れ替え前のリフレッシュトークンは使えない
        client.cookies['hrm_refresh'] = old_refresh
        res = client.post('/api/v1/auth/refresh/', **csrf_header(client))
        assert res.status_code == 401

    def test_refresh_requires_csrf(self):
        emp = make_employee()
        client = csrf_client()
        login(client, emp.user)
        assert client.post('/api/v1/auth/refresh/').status_code == 403

    def test_logout_clears_cookies_and_revokes_refresh(self):
        emp = make_employee()
        client = csrf_client()
        refresh = login(client, emp.user).cookies['hrm_refresh'].value
        res = client.post('/api/v1/auth/logout/', **csrf_header(client))
        assert res.status_code == 200
        assert res.cookies['hrm_access'].value == ''
        client.cookies['hrm_refresh'] = refresh
        assert client.post('/api/v1/auth/refresh/', **csrf_header(client)).status_code == 401

    def test_password_change_revokes_other_sessions(self):
        emp = make_employee()
        other_device = csrf_client()
        other_refresh = login(other_device, emp.user).cookies['hrm_refresh'].value

        client = csrf_client()
        login(client, emp.user)
        res = client.post('/api/v1/auth/password/change/',
                          {'old_password': PASSWORD, 'new_password': 'NewPassword5678!'},
                          format='json', **csrf_header(client))
        assert res.status_code == 200
        # 操作した端末には新しい Cookie が発行され、そのまま使える
        assert client.get(ME).status_code == 200
        # 他の端末のリフレッシュトークンは無効
        other_device.cookies['hrm_refresh'] = other_refresh
        assert other_device.post('/api/v1/auth/refresh/', **csrf_header(other_device)).status_code == 401

    def test_access_token_issued_before_password_change_is_rejected(self):
        emp = make_employee()
        token = str(RefreshToken.for_user(emp.user).access_token)
        emp.user.password_changed_at = timezone.now() + timedelta(seconds=5)
        emp.user.save(update_fields=['password_changed_at'])
        res = APIClient().get(ME, HTTP_AUTHORIZATION=f'Bearer {token}')
        assert res.status_code == 401


@pytest.mark.django_db
class TestLoginProtection:
    def test_wrong_password_and_unknown_user_same_message(self):
        emp = make_employee()
        a = login(APIClient(), emp.user, 'wrong-password')
        b = APIClient().post(LOGIN, {'email': 'nobody@example.com', 'password': 'x'}, format='json')
        assert a.status_code == b.status_code == 401
        assert a.data['detail'] == b.data['detail']

    def test_account_locks_after_max_failures(self, settings):
        settings.LOGIN_MAX_FAILURES = 3
        emp = make_employee()
        assert login(APIClient(), emp.user, 'bad').status_code == 401
        assert login(APIClient(), emp.user, 'bad').status_code == 401
        res = login(APIClient(), emp.user, 'bad')
        assert res.status_code == 403 and res.data['code'] == 'account_locked'
        # ロック中は正しいパスワードでも入れない
        assert login(APIClient(), emp.user).status_code == 403
        emp.user.refresh_from_db()
        assert emp.user.is_locked

    def test_lock_expires_and_success_resets_counter(self, settings):
        settings.LOGIN_MAX_FAILURES = 3
        emp = make_employee()
        login(APIClient(), emp.user, 'bad')
        emp.user.refresh_from_db()
        assert emp.user.failed_login_count == 1
        assert login(APIClient(), emp.user).status_code == 200
        emp.user.refresh_from_db()
        assert emp.user.failed_login_count == 0

        emp.user.locked_until = timezone.now() - timedelta(minutes=1)
        emp.user.save(update_fields=['locked_until'])
        assert login(APIClient(), emp.user).status_code == 200

    def test_login_rate_limited_per_ip(self, monkeypatch):
        monkeypatch.setattr(ScopedRateThrottle, 'THROTTLE_RATES', {'login': '3/min'})
        emp = make_employee()
        codes = [login(APIClient(), emp.user, 'bad').status_code for _ in range(4)]
        assert codes[-1] == 429
