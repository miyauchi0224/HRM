"""
conftest.py
===========
pytest 共通フィクスチャ定義。

Factory Boy でモデルを生成し、APIClient に認証をセットアップする。
全テストで import せず @pytest.fixture スコープで自動提供される。

用語
----
- Factory : テスト用ダミーデータ生成クラス（factory_boy）
- Fixture : pytest が各テスト関数に注入するオブジェクト
"""
import pytest
import factory
from faker import Faker
from django.utils import timezone
from rest_framework.test import APIClient

fake = Faker('ja_JP')

# ─────────────────────────────────────────────────────────────────────────────
# ▌ Factory 定義
# ─────────────────────────────────────────────────────────────────────────────

class UserFactory(factory.django.DjangoModelFactory):
    """User モデル生成ファクトリー"""
    class Meta:
        model = 'accounts.User'

    email    = factory.LazyFunction(lambda: fake.unique.email())
    password = factory.PostGenerationMethodCall('set_password', 'TestPass1234!')
    role     = 'employee'
    roles    = factory.LazyAttribute(lambda o: [o.role])
    is_active = True


class HRUserFactory(UserFactory):
    """人事ロールのユーザー"""
    role  = 'hr'
    roles = ['hr']


class ManagerUserFactory(UserFactory):
    """管理職ロールのユーザー"""
    role  = 'manager'
    roles = ['manager']


class CustomerUserFactory(UserFactory):
    """顧客ロールのユーザー"""
    role  = 'customer'
    roles = ['customer']


class EmployeeFactory(factory.django.DjangoModelFactory):
    """Employee モデル生成ファクトリー"""
    class Meta:
        model = 'employees.Employee'

    user              = factory.SubFactory(UserFactory)
    employee_number   = factory.Sequence(lambda n: f'E{n:04d}')
    last_name         = factory.LazyFunction(lambda: fake.last_name())
    first_name        = factory.LazyFunction(lambda: fake.first_name())
    last_name_kana    = 'ヤマダ'
    first_name_kana   = 'タロウ'
    birth_date        = factory.LazyFunction(lambda: fake.date_of_birth(minimum_age=22, maximum_age=60))
    gender            = 'male'
    hire_date         = factory.LazyFunction(lambda: fake.date_between(start_date='-5y', end_date='today'))
    department        = factory.LazyFunction(lambda: fake.company())
    position          = '一般社員'
    grade             = 1
    employment_type   = 'full_time'
    phone             = '090-0000-0001'


class HREmployeeFactory(EmployeeFactory):
    """人事ロールの社員"""
    user = factory.SubFactory(HRUserFactory)


class ManagerEmployeeFactory(EmployeeFactory):
    """管理職ロールの社員"""
    user = factory.SubFactory(ManagerUserFactory)


class ProjectFactory(factory.django.DjangoModelFactory):
    """Project モデル生成ファクトリー"""
    class Meta:
        model = 'attendance.Project'

    code       = factory.Sequence(lambda n: f'PJ-{n:04d}')
    name       = factory.LazyFunction(lambda: fake.bs())
    is_active  = True
    start_date = factory.LazyFunction(lambda: fake.date_between(start_date='-1y', end_date='today'))


class AttendanceRecordFactory(factory.django.DjangoModelFactory):
    """AttendanceRecord モデル生成ファクトリー"""
    class Meta:
        model = 'attendance.AttendanceRecord'

    employee   = factory.SubFactory(EmployeeFactory)
    date       = factory.LazyFunction(lambda: timezone.now().date())
    clock_in   = '09:00:00'
    clock_out  = '18:00:00'
    break_minutes = 60
    status     = 'confirmed'


class ApprovalRequestFactory(factory.django.DjangoModelFactory):
    """ApprovalRequest モデル生成ファクトリー"""
    class Meta:
        model = 'approval.ApprovalRequest'

    title     = factory.LazyFunction(lambda: fake.sentence(nb_words=5))
    category  = 'other'
    applicant = factory.SubFactory(EmployeeFactory)
    content   = factory.LazyFunction(lambda: fake.paragraph())
    status    = 'draft'


class AccountItemFactory(factory.django.DjangoModelFactory):
    """AccountItem（勘定科目）生成ファクトリー"""
    class Meta:
        model = 'expense.AccountItem'

    code      = factory.Sequence(lambda n: f'AC{n:03d}')
    name      = factory.LazyFunction(lambda: fake.word())
    category  = 'travel'
    is_active = True


class ExpenseRequestFactory(factory.django.DjangoModelFactory):
    """ExpenseRequest モデル生成ファクトリー"""
    class Meta:
        model = 'expense.ExpenseRequest'

    applicant    = factory.SubFactory(EmployeeFactory)
    account_item = factory.SubFactory(AccountItemFactory)
    expense_type = 'transportation'
    payment_type = 'reimbursement'
    amount       = 3000
    expense_date = factory.LazyFunction(lambda: timezone.now().date())
    description  = '出張交通費'
    status       = 'pending'


class MBOGoalFactory(factory.django.DjangoModelFactory):
    """MBOGoal モデル生成ファクトリー"""
    class Meta:
        model = 'mbo.MBOGoal'

    employee     = factory.SubFactory(EmployeeFactory)
    year         = 2026
    period       = 'first_half'
    title        = factory.LazyFunction(lambda: fake.sentence(nb_words=4))
    target_level = factory.LazyFunction(lambda: fake.sentence(nb_words=6))
    weight       = 30
    status       = 'draft'


class EvaluationPeriodFactory(factory.django.DjangoModelFactory):
    """EvaluationPeriod モデル生成ファクトリー"""
    class Meta:
        model = 'evaluation.EvaluationPeriod'

    fiscal_year = 2026
    period_type = 'first_half'
    start_date  = '2026-04-01'
    end_date    = '2026-09-30'
    is_active   = True


class EvaluationQuestionFactory(factory.django.DjangoModelFactory):
    """EvaluationQuestion モデル生成ファクトリー"""
    class Meta:
        model = 'evaluation.EvaluationQuestion'

    text      = factory.LazyFunction(lambda: fake.sentence(nb_words=8))
    category  = 'performance'
    is_active = True
    order     = factory.Sequence(lambda n: n)


class LeaveBalanceFactory(factory.django.DjangoModelFactory):
    """LeaveBalance モデル生成ファクトリー"""
    class Meta:
        model = 'leave.LeaveBalance'

    employee     = factory.SubFactory(EmployeeFactory)
    fiscal_year  = 2026
    granted_days = 20
    used_days    = 0
    carried_days = 0


class StressCheckPeriodFactory(factory.django.DjangoModelFactory):
    """StressCheckPeriod モデル生成ファクトリー"""
    class Meta:
        model = 'stress_check.StressCheckPeriod'

    title        = factory.LazyFunction(lambda: fake.sentence(nb_words=3))
    start_date   = '2026-04-01'
    end_date     = '2026-04-30'
    is_published = False


class TodoItemFactory(factory.django.DjangoModelFactory):
    """TodoItem モデル生成ファクトリー"""
    class Meta:
        model = 'todo.TodoItem'

    employee = factory.SubFactory(EmployeeFactory)
    title    = factory.LazyFunction(lambda: fake.sentence(nb_words=5))
    status   = 'not_started'


class SkillFactory(factory.django.DjangoModelFactory):
    """Skill モデル生成ファクトリー"""
    class Meta:
        model = 'skills.Skill'

    employee   = factory.SubFactory(EmployeeFactory)
    skill_name = factory.LazyFunction(lambda: fake.word())
    level      = '初級'
    category   = 'language'


# ─────────────────────────────────────────────────────────────────────────────
# ▌ pytest フィクスチャ
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    """認証なし APIクライアント"""
    return APIClient()


@pytest.fixture
def employee_user(db):
    """一般社員ユーザー＋Employeeレコード"""
    return EmployeeFactory()


@pytest.fixture
def hr_user(db):
    """人事ユーザー＋Employeeレコード"""
    return HREmployeeFactory()


@pytest.fixture
def manager_user(db):
    """管理職ユーザー＋Employeeレコード"""
    return ManagerEmployeeFactory()


@pytest.fixture
def auth_client(api_client, employee_user):
    """一般社員として認証済みのAPIクライアント"""
    api_client.force_authenticate(user=employee_user.user)
    return api_client


@pytest.fixture
def hr_client(api_client, hr_user):
    """人事として認証済みのAPIクライアント"""
    api_client.force_authenticate(user=hr_user.user)
    return api_client


@pytest.fixture
def manager_client(api_client, manager_user):
    """管理職として認証済みのAPIクライアント"""
    api_client.force_authenticate(user=manager_user.user)
    return api_client
