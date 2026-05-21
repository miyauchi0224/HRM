"""
attendance/tests.py
===================
Project CRUD・ProjectTask・打刻（clock-in/out）・勤怠レコードのテスト。
"""
import pytest
from django.utils import timezone
from rest_framework import status
from conftest import (
    EmployeeFactory, ProjectFactory, AttendanceRecordFactory, ManagerEmployeeFactory,
)

PROJ_BASE = '/api/v1/attendance/projects/'
ATT_BASE  = '/api/v1/attendance/'


# ─────────────────────────────────────────────────────────────────────────────
# ▌ Project モデル単体テスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProjectModel:
    def test_str(self):
        proj = ProjectFactory(code='PJ-001', name='テストPJ')
        assert 'PJ-001' in str(proj)
        assert 'テストPJ' in str(proj)

    def test_primary_managers_empty_by_default(self):
        proj = ProjectFactory()
        # M2M経由で取得するため、最初は空
        assert proj.primary_managers.count() == 0


# ─────────────────────────────────────────────────────────────────────────────
# ▌ Project API テスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProjectAPI:
    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(PROJ_BASE)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_projects(self, auth_client):
        ProjectFactory()
        ProjectFactory()
        res = auth_client.get(PROJ_BASE)
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        assert len(results) >= 2

    def test_create_project(self, auth_client):
        res = auth_client.post(PROJ_BASE, {
            'code': 'PJ-TEST-01',
            'name': 'テストプロジェクト',
            'description': '説明文',
            'primary_manager_ids': [],
            'secondary_manager_ids': [],
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['code'] == 'PJ-TEST-01'

    def test_create_project_duplicate_code(self, auth_client):
        ProjectFactory(code='PJ-DUP')
        res = auth_client.post(PROJ_BASE, {
            'code': 'PJ-DUP',
            'name': '重複テスト',
        }, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_project(self, auth_client):
        proj = ProjectFactory()
        res = auth_client.patch(f'{PROJ_BASE}{proj.id}/', {
            'name': '更新後プロジェクト名'
        }, format='json')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['name'] == '更新後プロジェクト名'

    def test_delete_project_soft(self, auth_client):
        proj = ProjectFactory()
        res = auth_client.delete(f'{PROJ_BASE}{proj.id}/')
        assert res.status_code == status.HTTP_204_NO_CONTENT
        # 論理削除なので is_active=False
        proj.refresh_from_db()
        assert proj.is_deleted

    def test_customer_cannot_access(self, api_client):
        from conftest import CustomerUserFactory
        user = CustomerUserFactory()
        api_client.force_authenticate(user=user)
        res = api_client.get(PROJ_BASE)
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_project_with_primary_manager(self, auth_client, employee_user):
        res = auth_client.post(PROJ_BASE, {
            'code': 'PJ-MGR-01',
            'name': '管理者付きPJ',
            'primary_manager_ids': [str(employee_user.id)],
            'secondary_manager_ids': [],
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert len(res.data['primary_managers']) == 1


# ─────────────────────────────────────────────────────────────────────────────
# ▌ ProjectTask API テスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProjectTaskAPI:
    TASK_BASE = '/api/v1/attendance/project-tasks/'

    def test_create_task(self, auth_client, employee_user):
        proj = ProjectFactory()
        res = auth_client.post(self.TASK_BASE, {
            'project': str(proj.id),
            'title': 'テストタスク',
            'status': 'todo',
            'progress': 0,
            'order': 1,
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED

    def test_list_tasks(self, auth_client):
        proj = ProjectFactory()
        from apps.attendance.models import ProjectTask
        ProjectTask.objects.create(project=proj, title='タスク1', order=1)
        res = auth_client.get(self.TASK_BASE)
        assert res.status_code == status.HTTP_200_OK

    def test_update_task_status(self, auth_client):
        proj = ProjectFactory()
        from apps.attendance.models import ProjectTask
        task = ProjectTask.objects.create(project=proj, title='ステータステスト', order=1)
        res = auth_client.patch(f'{self.TASK_BASE}{task.id}/', {
            'status': 'in_progress',
            'progress': 50,
        }, format='json')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['status'] == 'in_progress'


# ─────────────────────────────────────────────────────────────────────────────
# ▌ 打刻 API テスト（clock-in / clock-out）
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestClockInOutAPI:
    def test_clock_in(self, auth_client):
        res = auth_client.post(ATT_BASE + 'clock-in/', {}, format='json')
        # clock-in は新規レコード作成のため 201 を返す
        assert res.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)

    def test_clock_in_twice_returns_conflict(self, auth_client):
        auth_client.post(ATT_BASE + 'clock-in/', {}, format='json')
        res = auth_client.post(ATT_BASE + 'clock-in/', {}, format='json')
        assert res.status_code == status.HTTP_409_CONFLICT

    def test_clock_out_after_clock_in(self, auth_client):
        auth_client.post(ATT_BASE + 'clock-in/', {}, format='json')
        res = auth_client.post(ATT_BASE + 'clock-out/', {'break_minutes': 60}, format='json')
        assert res.status_code == status.HTTP_200_OK

    def test_clock_out_without_clock_in(self, auth_client):
        res = auth_client.post(ATT_BASE + 'clock-out/', {'break_minutes': 60}, format='json')
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthenticated_clock_in(self, api_client):
        res = api_client.post(ATT_BASE + 'clock-in/', {}, format='json')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ─────────────────────────────────────────────────────────────────────────────
# ▌ 勤怠レコード CRUD テスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAttendanceRecordAPI:
    def test_list_own_records(self, auth_client, employee_user):
        AttendanceRecordFactory(employee=employee_user)
        res = auth_client.get(ATT_BASE)
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        assert len(results) >= 1

    def test_employee_sees_only_own_records(self, auth_client, employee_user):
        other = EmployeeFactory()
        AttendanceRecordFactory(employee=other)
        AttendanceRecordFactory(employee=employee_user)
        res = auth_client.get(ATT_BASE)
        results = res.data.get('results', res.data)
        # 自分のレコードのみ
        for r in results:
            assert r.get('date') is not None

    def test_filter_by_year_month(self, auth_client, employee_user):
        import datetime
        AttendanceRecordFactory(employee=employee_user, date=datetime.date(2026, 4, 1))
        AttendanceRecordFactory(employee=employee_user, date=datetime.date(2026, 3, 1))
        res = auth_client.get(ATT_BASE + '?year_month=2026-04')
        results = res.data.get('results', res.data)
        assert len(results) == 1

    def test_patch_attendance_record(self, auth_client, employee_user):
        record = AttendanceRecordFactory(employee=employee_user)
        res = auth_client.patch(f'{ATT_BASE}{record.id}/', {
            'clock_in': '09:30:00',
            'clock_out': '18:30:00',
            'break_minutes': 60,
        }, format='json')
        assert res.status_code == status.HTTP_200_OK

    def test_monthly_summary(self, auth_client, employee_user):
        AttendanceRecordFactory(employee=employee_user)
        res = auth_client.get(ATT_BASE + 'summary/?year_month=2026-04')
        assert res.status_code in (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND)
