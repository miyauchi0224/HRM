"""
employees/tests_import.py
=========================
社員 CSV 一括登録（POST /api/v1/employees/import-csv/）のテスト。
"""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import User
from apps.employees.models import Employee

URL = '/api/v1/employees/import-csv/'
HEADER = ('社員番号,姓,名,姓（カナ）,名（カナ）,メールアドレス,ロール,生年月日,性別,入社日,退職日,雇用形態,'
          '部署,役職,等級,電話番号,個人メール,郵便番号,住所,最寄り駅,勤務先名,勤務先住所,勤務先電話番号,通勤経路,'
          '銀行名,支店名,口座種別,口座番号,口座名義')


def row(no, email, role='employee', grade='3'):
    return (f'{no},山田,太郎,ヤマダ,タロウ,{email},{role},1990/04/01,male,2020/04/01,,full_time,'
            f'開発部,一般,{grade},,,,,,,,,,,,,,')


def upload(client, *rows):
    body = '\r\n'.join((HEADER,) + rows).encode('utf-8-sig')
    return client.post(URL, {'file': SimpleUploadedFile('e.csv', body, content_type='text/csv')},
                       format='multipart')


@pytest.mark.django_db
class TestEmployeeImport:
    def test_import_creates_users_with_roles(self, hr_client):
        res = upload(hr_client, row('T001', 't1@example.com', 'manager'), row('T002', 't2@example.com'))
        assert res.status_code == 200
        assert res.data['created'] == 2 and res.data['errors'] == 0
        assert User.objects.get(email='t1@example.com').is_manager
        assert all(len(r['temp_password']) >= 12 for r in res.data['results'])

    def test_failed_row_leaves_no_orphan_user(self, hr_client):
        """社員情報の作成で失敗したら、ユーザーも作られない（再取り込みできる）"""
        res = upload(hr_client, row('T003', 't3@example.com', grade='abc'))
        assert res.data['created'] == 0 and res.data['errors'] == 1
        assert not User.objects.filter(email='t3@example.com').exists()

        res = upload(hr_client, row('T003', 't3@example.com', grade='2'))
        assert res.data['created'] == 1
        assert Employee.objects.get(employee_number='T003').grade == 2

    def test_employee_cannot_import(self, auth_client):
        assert upload(auth_client, row('T004', 't4@example.com')).status_code == 403
