"""
skills/tests.py
===============
スキル・資格の CRUD・権限チェック・有効期限アラートのテスト。
"""
import pytest
from datetime import date, timedelta
from rest_framework import status
from conftest import EmployeeFactory, SkillFactory, ManagerEmployeeFactory

SKILL_BASE = '/api/v1/skills/'


@pytest.mark.django_db
class TestSkillModel:
    def test_default_ordering(self):
        """category → skill_name でソート"""
        emp = EmployeeFactory()
        SkillFactory(employee=emp, category='language', skill_name='Python')
        SkillFactory(employee=emp, category='framework', skill_name='Django')
        from apps.skills.models import Skill
        skills = list(Skill.objects.filter(employee=emp))
        # framework が language より先にソートされる
        assert skills[0].category == 'framework'

    def test_category_choices(self):
        from apps.skills.models import Skill
        choices = [c[0] for c in Skill.Category.choices]
        assert 'language' in choices
        assert 'framework' in choices
        assert 'certificate' in choices


@pytest.mark.django_db
class TestSkillAPI:
    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(SKILL_BASE)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_skill(self, auth_client, employee_user):
        res = auth_client.post(SKILL_BASE, {
            'skill_name': 'Python',
            'category': 'language',
            'level': '上級',
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['skill_name'] == 'Python'

    def test_list_own_skills(self, auth_client, employee_user):
        SkillFactory(employee=employee_user, skill_name='React')
        res = auth_client.get(SKILL_BASE)
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        assert any(s['skill_name'] == 'React' for s in results)

    def test_employee_cannot_see_others_skills(self, auth_client, employee_user):
        other = EmployeeFactory()
        SkillFactory(employee=other, skill_name='他人のスキル')
        res = auth_client.get(SKILL_BASE)
        results = res.data.get('results', res.data)
        assert not any(s['skill_name'] == '他人のスキル' for s in results)

    def test_manager_can_see_all_skills(self, api_client):
        manager = ManagerEmployeeFactory()
        emp = EmployeeFactory()
        SkillFactory(employee=emp, skill_name='部下のスキル')
        api_client.force_authenticate(user=manager.user)
        res = api_client.get(SKILL_BASE)
        assert res.status_code == status.HTTP_200_OK

    def test_manager_filter_by_employee_id(self, api_client):
        manager = ManagerEmployeeFactory()
        emp = EmployeeFactory()
        SkillFactory(employee=emp, skill_name='特定社員スキル')
        api_client.force_authenticate(user=manager.user)
        res = api_client.get(f'{SKILL_BASE}?employee_id={emp.id}')
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        assert any(s['skill_name'] == '特定社員スキル' for s in results)

    def test_update_own_skill(self, auth_client, employee_user):
        skill = SkillFactory(employee=employee_user, level='初級')
        res = auth_client.patch(f'{SKILL_BASE}{skill.id}/', {
            'level': '中級',
        }, format='json')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['level'] == '中級'

    def test_delete_own_skill(self, auth_client, employee_user):
        skill = SkillFactory(employee=employee_user)
        res = auth_client.delete(f'{SKILL_BASE}{skill.id}/')
        assert res.status_code == status.HTTP_204_NO_CONTENT

    def test_customer_returns_403(self, api_client):
        from conftest import CustomerUserFactory
        user = CustomerUserFactory()
        api_client.force_authenticate(user=user)
        res = api_client.get(SKILL_BASE)
        assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestSkillExpiryAlertAPI:
    ALERT_URL = f'{SKILL_BASE}expiry-alert/'

    def test_expiry_within_90_days(self, auth_client, employee_user):
        """有効期限が90日以内のスキルがアラートに含まれる"""
        expiring_date = date.today() + timedelta(days=30)
        SkillFactory(
            employee=employee_user,
            skill_name='期限切れ間近資格',
            expiry_date=expiring_date,
        )
        res = auth_client.get(self.ALERT_URL)
        assert res.status_code == status.HTTP_200_OK
        # expiry-alert は非ページネーションリストを返す
        results = res.data if isinstance(res.data, list) else res.data.get('results', [])
        assert any(s['skill_name'] == '期限切れ間近資格' for s in results)

    def test_expiry_far_future_not_included(self, auth_client, employee_user):
        """有効期限が90日超のスキルは含まれない"""
        far_date = date.today() + timedelta(days=200)
        SkillFactory(
            employee=employee_user,
            skill_name='まだ余裕の資格',
            expiry_date=far_date,
        )
        res = auth_client.get(self.ALERT_URL)
        assert res.status_code == status.HTTP_200_OK
        results = res.data if isinstance(res.data, list) else res.data.get('results', [])
        assert not any(s['skill_name'] == 'まだ余裕の資格' for s in results)

    def test_no_expiry_date_not_included(self, auth_client, employee_user):
        """expiry_date が None のスキルはアラートに含まれない"""
        SkillFactory(employee=employee_user, skill_name='無期限スキル', expiry_date=None)
        res = auth_client.get(self.ALERT_URL)
        results = res.data if isinstance(res.data, list) else res.data.get('results', [])
        assert not any(s['skill_name'] == '無期限スキル' for s in results)
