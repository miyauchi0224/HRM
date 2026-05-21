"""
accounts/tests.py
=================
User モデル・認証API・パスワード変更・APIキー管理のテスト。
"""
import pytest
from django.urls import reverse
from rest_framework import status
from conftest import UserFactory, EmployeeFactory


# ─────────────────────────────────────────────────────────────────────────────
# ▌ User モデル単体テスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserModel:
    """User モデルのロールヘルパープロパティを検証"""

    def test_employee_role_properties(self):
        user = UserFactory(role='employee', roles=['employee'])
        assert not user.is_manager
        assert not user.is_hr
        assert not user.is_accounting
        assert not user.is_customer

    def test_hr_role_properties(self):
        user = UserFactory(role='hr', roles=['hr'])
        assert user.is_manager
        assert user.is_hr
        assert user.is_accounting   # HR は経理権限も持つ

    def test_manager_role_properties(self):
        user = UserFactory(role='manager', roles=['manager'])
        assert user.is_manager
        assert not user.is_hr

    def test_accounting_role_properties(self):
        user = UserFactory(role='accounting', roles=['accounting'])
        assert user.is_accounting
        assert not user.is_hr

    def test_customer_role_properties(self):
        user = UserFactory(role='customer', roles=['customer'])
        assert user.is_customer
        assert not user.is_manager

    def test_roles_sync_on_save(self):
        """role フィールドを設定して保存すると roles も同期される"""
        user = UserFactory(role='employee', roles=[])
        # role のみ設定して保存
        user.roles = []
        user.role  = 'hr'
        user.save()
        user.refresh_from_db()
        assert 'hr' in user.roles

    def test_multi_role(self):
        """複数ロール保持時のプロパティ確認"""
        user = UserFactory(role='employee', roles=['employee', 'manager'])
        assert user.is_manager

    def test_str_returns_email(self):
        user = UserFactory()
        assert str(user) == user.email


# ─────────────────────────────────────────────────────────────────────────────
# ▌ 認証 API テスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLoginAPI:
    """JWT ログイン・me エンドポイントのテスト"""

    def test_login_success(self, api_client):
        emp = EmployeeFactory()
        emp.user.set_password('TestPass1234!')
        emp.user.save()
        res = api_client.post('/api/v1/auth/login/', {
            'email': emp.user.email,
            'password': 'TestPass1234!',
        })
        assert res.status_code == status.HTTP_200_OK
        assert 'access' in res.data

    def test_login_wrong_password(self, api_client):
        emp = EmployeeFactory()
        res = api_client.post('/api/v1/auth/login/', {
            'email': emp.user.email,
            'password': 'WrongPassword',
        })
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_endpoint_authenticated(self, auth_client):
        res = auth_client.get('/api/v1/auth/me/')
        assert res.status_code == status.HTTP_200_OK
        assert 'email' in res.data

    def test_me_endpoint_unauthenticated(self, api_client):
        res = api_client.get('/api/v1/auth/me/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPasswordChangeAPI:
    """パスワード変更エンドポイントのテスト"""

    def test_change_password_success(self, api_client):
        emp = EmployeeFactory()
        emp.user.set_password('OldPass1234!')
        emp.user.save()
        api_client.force_authenticate(user=emp.user)
        res = api_client.post('/api/v1/auth/password/change/', {
            'old_password': 'OldPass1234!',
            'new_password': 'NewPass5678!',
        })
        assert res.status_code == status.HTTP_200_OK
        emp.user.refresh_from_db()
        assert emp.user.check_password('NewPass5678!')

    def test_change_password_wrong_old(self, auth_client):
        res = auth_client.post('/api/v1/auth/password/change/', {
            'old_password': 'WrongOld!',
            'new_password': 'NewPass5678!',
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_unauthenticated(self, api_client):
        res = api_client.post('/api/v1/auth/password/change/', {
            'old_password': 'OldPass1234!',
            'new_password': 'NewPass5678!',
        })
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
