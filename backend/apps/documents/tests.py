"""
documents/tests.py
==================
ドキュメントカテゴリ・ドキュメントの CRUD・可視性チェックのテスト。
"""
import pytest
from rest_framework import status
from conftest import EmployeeFactory, HREmployeeFactory

CATEGORY_BASE = '/api/v1/documents/categories/'
DOC_BASE      = '/api/v1/documents/'


@pytest.mark.django_db
class TestDocumentCategoryModel:
    def test_str(self):
        from apps.documents.models import DocumentCategory
        cat = DocumentCategory.objects.create(name='規程・規則', slug='rules', order=1)
        assert '規程・規則' in str(cat)

    def test_ordering_by_order(self):
        from apps.documents.models import DocumentCategory
        DocumentCategory.objects.create(name='B', slug='b', order=2)
        DocumentCategory.objects.create(name='A', slug='a', order=1)
        cats = list(DocumentCategory.objects.all())
        assert cats[0].name == 'A'


@pytest.mark.django_db
class TestDocumentCategoryAPI:
    def test_list_as_employee(self, auth_client):
        from apps.documents.models import DocumentCategory
        DocumentCategory.objects.create(name='社内規程', slug='regs', order=1)
        res = auth_client.get(CATEGORY_BASE)
        assert res.status_code == status.HTTP_200_OK

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(CATEGORY_BASE)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_as_hr(self, hr_client):
        res = hr_client.post(CATEGORY_BASE, {
            'name': '人事制度',
            'slug': 'hr-policy',
            'order': 1,
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED

    def test_create_as_employee_forbidden(self, auth_client):
        res = auth_client.post(CATEGORY_BASE, {
            'name': '不正カテゴリ',
            'slug': 'invalid',
            'order': 99,
        }, format='json')
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_customer_returns_403(self, api_client):
        from conftest import CustomerUserFactory
        user = CustomerUserFactory()
        api_client.force_authenticate(user=user)
        res = api_client.get(CATEGORY_BASE)
        assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestDocumentModel:
    def test_str(self):
        from apps.documents.models import Document
        hr_emp = HREmployeeFactory()
        doc = Document.objects.create(
            title='就業規則',
            visibility='all',
            created_by=hr_emp.user,
        )
        assert '就業規則' in str(doc)

    def test_visibility_choices(self):
        from apps.documents.models import Document
        choices = [c[0] for c in Document.Visibility.choices]
        assert 'all' in choices
        assert 'hr_only' in choices
        assert 'personal' in choices
        assert 'role_manager' in choices
        assert 'project' in choices


@pytest.mark.django_db
class TestDocumentAPI:
    def test_list_all_visibility_as_employee(self, auth_client, employee_user):
        """visibility='all' のドキュメントは一般社員でも閲覧可"""
        from apps.documents.models import Document
        hr_emp = HREmployeeFactory()
        Document.objects.create(
            title='全社向け規則',
            visibility='all',
            created_by=hr_emp.user,
        )
        res = auth_client.get(DOC_BASE)
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        assert any(d['title'] == '全社向け規則' for d in results)

    def test_hr_only_hidden_from_employee(self, auth_client, employee_user):
        """visibility='hr_only' は一般社員から不可視"""
        from apps.documents.models import Document
        hr_emp = HREmployeeFactory()
        Document.objects.create(
            title='人事機密文書',
            visibility='hr_only',
            created_by=hr_emp.user,
        )
        res = auth_client.get(DOC_BASE)
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        assert not any(d['title'] == '人事機密文書' for d in results)

    def test_hr_sees_all_documents(self, hr_client):
        """HR ユーザーは全ドキュメントを閲覧可"""
        from apps.documents.models import Document
        hr_emp = HREmployeeFactory()
        Document.objects.create(title='HR専用', visibility='hr_only', created_by=hr_emp.user)
        Document.objects.create(title='全社向け', visibility='all', created_by=hr_emp.user)
        res = hr_client.get(DOC_BASE)
        assert res.status_code == status.HTTP_200_OK

    def test_create_as_hr(self, hr_client):
        res = hr_client.post(DOC_BASE, {
            'title': '新規規程',
            'visibility': 'all',
            'description': 'テスト用ドキュメント',
        })
        assert res.status_code == status.HTTP_201_CREATED

    def test_create_as_employee_forbidden(self, auth_client):
        res = auth_client.post(DOC_BASE, {
            'title': '不正ドキュメント',
            'visibility': 'all',
        })
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(DOC_BASE)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_personal_document_visible_to_target_employee(self, auth_client, employee_user):
        """visibility='personal' はtarget_employee本人のみ見える"""
        from apps.documents.models import Document
        hr_emp = HREmployeeFactory()
        doc = Document.objects.create(
            title='個人雇用契約書',
            visibility='personal',
            target_employee=employee_user,
            created_by=hr_emp.user,
        )
        res = auth_client.get(DOC_BASE)
        results = res.data.get('results', res.data)
        assert any(d['title'] == '個人雇用契約書' for d in results)
