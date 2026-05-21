"""
employees/tests.py
==================
Employee CRUD・自己更新・緊急連絡先・権限チェックのテスト。
"""
import pytest
from rest_framework import status
from conftest import (
    EmployeeFactory, HREmployeeFactory, ManagerEmployeeFactory,
    CustomerUserFactory,
)

BASE = '/api/v1/employees/'


# ─────────────────────────────────────────────────────────────────────────────
# ▌ Employee モデル単体テスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEmployeeModel:
    def test_full_name(self):
        emp = EmployeeFactory(last_name='山田', first_name='太郎')
        assert emp.full_name == '山田 太郎'

    def test_str(self):
        emp = EmployeeFactory(last_name='鈴木', first_name='花子', employee_number='E001')
        assert '鈴木' in str(emp)
        assert 'E001' in str(emp)


# ─────────────────────────────────────────────────────────────────────────────
# ▌ Employee 一覧・詳細 API テスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEmployeeListAPI:
    """一覧取得の権限チェック"""

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(BASE)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_employee_sees_only_self(self, auth_client, employee_user):
        # 別の社員を作成
        EmployeeFactory()
        res = auth_client.get(BASE)
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        # 自分のレコードのみ返る
        assert len(results) == 1
        assert results[0]['employee_number'] == employee_user.employee_number

    def test_manager_sees_all(self, manager_client):
        EmployeeFactory()
        EmployeeFactory()
        res = manager_client.get(BASE)
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        assert len(results) >= 3  # manager 自身 + 2名

    def test_for_project_param_returns_all(self, auth_client):
        EmployeeFactory()
        res = auth_client.get(BASE + '?for_project=true')
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        assert len(results) >= 2


@pytest.mark.django_db
class TestEmployeeDetailAPI:
    """詳細取得のテスト"""

    def test_retrieve_self(self, auth_client, employee_user):
        res = auth_client.get(f'{BASE}{employee_user.id}/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['id'] == str(employee_user.id)

    def test_employee_cannot_retrieve_others(self, auth_client):
        other = EmployeeFactory()
        res = auth_client.get(f'{BASE}{other.id}/')
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_manager_can_retrieve_others(self, manager_client):
        other = EmployeeFactory()
        res = manager_client.get(f'{BASE}{other.id}/')
        assert res.status_code == status.HTTP_200_OK


# ─────────────────────────────────────────────────────────────────────────────
# ▌ Employee 作成 API テスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEmployeeCreateAPI:
    """社員作成はHRのみ可能"""

    PAYLOAD = {
        'email': 'newstaff@example.com',
        'employee_number': 'E9999',
        'last_name': '新規',
        'first_name': '社員',
        'last_name_kana': 'シンキ',
        'first_name_kana': 'シャイン',
        'birth_date': '1990-01-01',
        'hire_date': '2026-04-01',
        'department': '開発部',
        'position': '一般社員',
        'roles': ['employee'],
    }

    def test_hr_can_create_employee(self, hr_client):
        res = hr_client.post(BASE, self.PAYLOAD, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert 'temp_password' in res.data

    def test_employee_cannot_create(self, auth_client):
        res = auth_client.post(BASE, self.PAYLOAD, format='json')
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_duplicate_email_rejected(self, hr_client):
        existing = EmployeeFactory()
        payload = {**self.PAYLOAD, 'email': existing.user.email, 'employee_number': 'E8888'}
        res = hr_client.post(BASE, payload, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST


# ─────────────────────────────────────────────────────────────────────────────
# ▌ /me エンドポイント テスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEmployeeMeAPI:
    def test_get_my_profile(self, auth_client, employee_user):
        res = auth_client.get(BASE + 'me/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['id'] == str(employee_user.id)

    def test_patch_my_profile(self, auth_client, employee_user):
        res = auth_client.patch(BASE + 'me/', {'phone': '080-1111-2222'}, format='json')
        assert res.status_code == status.HTTP_200_OK
        employee_user.refresh_from_db()
        assert employee_user.phone == '080-1111-2222'

    def test_unauthenticated_cannot_get_me(self, api_client):
        res = api_client.get(BASE + 'me/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ─────────────────────────────────────────────────────────────────────────────
# ▌ 緊急連絡先 API テスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEmergencyContactAPI:
    def _url(self, emp_id):
        return f'{BASE}{emp_id}/emergency-contacts/'

    def test_add_emergency_contact(self, auth_client, employee_user):
        res = auth_client.post(self._url(employee_user.id), {
            'name': '山田 母',
            'relationship': '母',
            'phone': '03-0000-0001',
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['name'] == '山田 母'

    def test_list_emergency_contacts(self, auth_client, employee_user):
        # 1件追加
        auth_client.post(self._url(employee_user.id), {
            'name': 'テスト連絡先', 'relationship': '配偶者', 'phone': '090-0000-0001'
        }, format='json')
        res = auth_client.get(self._url(employee_user.id))
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1

    def test_update_emergency_contact(self, auth_client, employee_user):
        # 作成
        post_res = auth_client.post(self._url(employee_user.id), {
            'name': '旧名前', 'relationship': '父', 'phone': '03-0000-0002'
        }, format='json')
        contact_id = post_res.data['id']
        # 更新
        patch_res = auth_client.patch(
            f'{BASE}{employee_user.id}/emergency-contacts/{contact_id}/',
            {'name': '新名前'},
            format='json',
        )
        assert patch_res.status_code == status.HTTP_200_OK
        assert patch_res.data['name'] == '新名前'

    def test_delete_emergency_contact(self, auth_client, employee_user):
        post_res = auth_client.post(self._url(employee_user.id), {
            'name': '削除対象', 'relationship': '兄', 'phone': '03-0000-0003'
        }, format='json')
        contact_id = post_res.data['id']
        del_res = auth_client.delete(
            f'{BASE}{employee_user.id}/emergency-contacts/{contact_id}/'
        )
        assert del_res.status_code == status.HTTP_204_NO_CONTENT

    def test_other_employee_cannot_edit_contacts(self, api_client):
        emp1 = EmployeeFactory()
        emp2 = EmployeeFactory()
        api_client.force_authenticate(user=emp2.user)
        res = api_client.post(self._url(emp1.id), {
            'name': '不正アクセス', 'relationship': '他人', 'phone': '000-0000'
        }, format='json')
        assert res.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)
