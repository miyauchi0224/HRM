"""
todo/tests.py
=============
TODOアイテム・日報の CRUD・ステータス遷移のテスト。
"""
import pytest
from rest_framework import status
from conftest import EmployeeFactory, TodoItemFactory

TODO_BASE  = '/api/v1/todo/items/'
DAILY_BASE = '/api/v1/todo/daily-reports/'


@pytest.mark.django_db
class TestTodoItemModel:
    def test_str(self):
        item = TodoItemFactory(title='DB設計完了')
        assert 'DB設計完了' in str(item)

    def test_default_status_not_started(self):
        item = TodoItemFactory()
        assert item.status == 'not_started'

    def test_status_choices(self):
        from apps.todo.models import TodoItem
        choices = [c[0] for c in TodoItem.Status.choices]
        assert 'not_started' in choices
        assert 'in_progress' in choices
        assert 'done' in choices


@pytest.mark.django_db
class TestTodoItemAPI:
    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(TODO_BASE)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_todo(self, auth_client, employee_user):
        res = auth_client.post(TODO_BASE, {
            'title': '資料作成',
            'description': 'プレゼン用スライドを準備する',
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['title'] == '資料作成'
        assert res.data['status'] == 'not_started'

    def test_list_own_todos(self, auth_client, employee_user):
        TodoItemFactory(employee=employee_user, title='自分のTODO')
        res = auth_client.get(TODO_BASE)
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        assert any(t['title'] == '自分のTODO' for t in results)

    def test_cannot_see_others_todos(self, auth_client, employee_user):
        other = EmployeeFactory()
        TodoItemFactory(employee=other, title='他人のTODO')
        res = auth_client.get(TODO_BASE)
        results = res.data.get('results', res.data)
        assert not any(t['title'] == '他人のTODO' for t in results)

    def test_move_status_to_in_progress(self, auth_client, employee_user):
        item = TodoItemFactory(employee=employee_user, status='not_started')
        res = auth_client.patch(f'{TODO_BASE}{item.id}/move/', {
            'status': 'in_progress',
        }, format='json')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['status'] == 'in_progress'

    def test_move_status_to_done(self, auth_client, employee_user):
        item = TodoItemFactory(employee=employee_user, status='in_progress')
        res = auth_client.patch(f'{TODO_BASE}{item.id}/move/', {
            'status': 'done',
        }, format='json')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['status'] == 'done'

    def test_invalid_status_rejected(self, auth_client, employee_user):
        item = TodoItemFactory(employee=employee_user)
        res = auth_client.patch(f'{TODO_BASE}{item.id}/move/', {
            'status': 'invalid_status',
        }, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_customer_returns_403(self, api_client):
        from conftest import CustomerUserFactory
        user = CustomerUserFactory()
        api_client.force_authenticate(user=user)
        res = api_client.get(TODO_BASE)
        assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestTodoDailyReportAPI:
    def test_create_daily_report(self, auth_client, employee_user):
        res = auth_client.post(DAILY_BASE, {
            'report_date': '2026-05-01',
            'content': '本日の作業: 仕様書作成',
            'tomorrow': '明日の予定: コードレビュー',
            'issues': '特になし',
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['status'] == 'draft'

    def test_submit_daily_report(self, auth_client, employee_user):
        res = auth_client.post(DAILY_BASE, {
            'report_date': '2026-05-02',
            'content': '提出テスト用日報',
        }, format='json')
        report_id = res.data['id']
        sub = auth_client.patch(f'{DAILY_BASE}{report_id}/submit/')
        assert sub.status_code == status.HTTP_200_OK
        assert sub.data['status'] == 'submitted'

    def test_duplicate_date_rejected(self, auth_client, employee_user):
        auth_client.post(DAILY_BASE, {
            'report_date': '2026-05-03',
            'content': '最初の日報',
        }, format='json')
        res = auth_client.post(DAILY_BASE, {
            'report_date': '2026-05-03',
            'content': '重複日報',
        }, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_by_date(self, auth_client, employee_user):
        auth_client.post(DAILY_BASE, {
            'report_date': '2026-05-04',
            'content': '4日の日報',
        }, format='json')
        auth_client.post(DAILY_BASE, {
            'report_date': '2026-05-05',
            'content': '5日の日報',
        }, format='json')
        res = auth_client.get(f'{DAILY_BASE}?date=2026-05-04')
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        assert len(results) == 1
        assert results[0]['report_date'] == '2026-05-04'

    def test_list_own_reports(self, auth_client, employee_user):
        auth_client.post(DAILY_BASE, {
            'report_date': '2026-05-06',
            'content': '自分の日報',
        }, format='json')
        res = auth_client.get(DAILY_BASE)
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        assert len(results) >= 1
