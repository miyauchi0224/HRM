import os
import sys
import django

# manage.py と同じディレクトリに置いて実行
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.accounts.models import User
from apps.employees.models import Employee
from datetime import date

# 全ユーザーを表示
print("=== 登録済みユーザー ===")
for u in User.objects.all():
    has_emp = hasattr(u, 'employee') and u.employee is not None
    try:
        u.employee
        has_emp = True
    except Exception:
        has_emp = False
    print(f"  id={u.id} | email={u.email} | superuser={u.is_superuser} | employee={has_emp}")

print()

# Employeeがいないユーザーにテストデータを作成
for u in User.objects.all():
    try:
        u.employee
        print(f"{u.email} は既に Employee があります")
    except Exception:
        print(f"{u.email} に Employee を作成します...")
        emp = Employee.objects.create(
            user=u,
            employee_number='EMP001',
            last_name='テスト',
            first_name='ユーザー',
            last_name_kana='テスト',
            first_name_kana='ユーザー',
            birth_date=date(1990, 1, 1),
            gender='male',
            hire_date=date(2020, 4, 1),
            department='開発部',
            position='エンジニア',
        )
        print(f"  → Employee 作成完了: {emp}")

print()
print("完了！")
