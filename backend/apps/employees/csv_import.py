"""
社員 CSV 一括登録の処理

API（POST /api/v1/employees/import-csv/）とサンプルデータ投入コマンド（load_sample_data）の
両方から使う。初期パスワードは生年月日の 8 桁で、初回ログイン時に変更を求める。
"""
import csv
import io
from datetime import date

from django.db import transaction

from apps.accounts.models import User
from apps.accounts.passwords import initial_password_for
from .models import Employee

REQUIRED_COLUMNS = ['社員番号', '姓', '名', '姓（カナ）', '名（カナ）',
                    'メールアドレス', '生年月日', '性別', '入社日',
                    '雇用形態', '部署', '役職']


def _parse_date(val):
    if not val or not val.strip():
        return None
    val = val.strip().replace('/', '-')
    try:
        return date.fromisoformat(val)
    except ValueError:
        raise ValueError(f'日付の形式が正しくありません（例: 1990/04/01）: {val}')


def import_employees_csv(text: str) -> tuple[list[dict], list[dict]]:
    """
    CSV のテキストから社員とログインアカウントを作成する。
    戻り値: (作成した行の情報のリスト, エラーのリスト)
    """
    reader = csv.DictReader(io.StringIO(text))

    created = []
    errors  = []

    valid_roles     = [c[0] for c in User.Role.choices]
    valid_genders   = [c[0] for c in Employee.Gender.choices]
    valid_emp_types = [c[0] for c in Employee.EmploymentType.choices]

    for i, row in enumerate(reader, start=2):  # 2行目から（1行目はヘッダー）
        try:
            # ─── 必須項目チェック ───
            for field in REQUIRED_COLUMNS:
                if not (row.get(field) or '').strip():
                    raise ValueError(f'「{field}」は必須項目です')

            employee_number = row['社員番号'].strip()
            email           = row['メールアドレス'].strip()
            role            = (row.get('ロール') or 'employee').strip() or 'employee'
            gender          = row['性別'].strip()
            emp_type        = row['雇用形態'].strip()

            # ─── 値の検証 ───
            if role not in valid_roles:
                raise ValueError(f'ロールの値が無効です（{role}）。使用可能: {", ".join(valid_roles)}')
            if gender not in valid_genders:
                raise ValueError(f'性別の値が無効です（{gender}）。使用可能: male / female / other')
            if emp_type not in valid_emp_types:
                raise ValueError(f'雇用形態の値が無効です（{emp_type}）。使用可能: full_time / part_time / contract / dispatch')

            if User.objects.filter(email=email).exists():
                raise ValueError(f'メールアドレスが既に使用されています: {email}')
            if Employee.objects.filter(employee_number=employee_number).exists():
                raise ValueError(f'社員番号が既に使用されています: {employee_number}')

            birth_date  = _parse_date(row['生年月日'])
            hire_date   = _parse_date(row['入社日'])
            retire_date = _parse_date(row.get('退職日'))

            def col(name):
                return (row.get(name) or '').strip()

            # ─── 作成（ユーザーと社員情報を1行ずつまとめて登録。途中で失敗したら両方取り消す） ───
            with transaction.atomic():
                temp_password = initial_password_for(birth_date)
                user = User.objects.create_user(
                    email=email, password=temp_password, role=role, must_change_password=True,
                )

                Employee.objects.create(
                    user             = user,
                    employee_number  = employee_number,
                    last_name        = col('姓'),
                    first_name       = col('名'),
                    last_name_kana   = col('姓（カナ）'),
                    first_name_kana  = col('名（カナ）'),
                    birth_date       = birth_date,
                    gender           = gender,
                    hire_date        = hire_date,
                    retire_date      = retire_date,
                    employment_type  = emp_type,
                    department       = col('部署'),
                    position         = col('役職'),
                    grade            = int(col('等級') or '1'),
                    phone            = col('電話番号'),
                    personal_email   = col('個人メール'),
                    zip_code         = col('郵便番号'),
                    address          = col('住所'),
                    nearest_station  = col('最寄り駅'),
                    workplace_name   = col('勤務先名'),
                    workplace_address= col('勤務先住所'),
                    workplace_phone  = col('勤務先電話番号'),
                    commute_route    = col('通勤経路'),
                    bank_name        = col('銀行名'),
                    bank_branch      = col('支店名'),
                    bank_account_type= col('口座種別'),
                    bank_account_number = col('口座番号'),
                    bank_account_holder = col('口座名義'),
                )

            created.append({
                'row':             i,
                'employee_number': employee_number,
                'name':            f'{col("姓")} {col("名")}',
                'email':           email,
                'temp_password':   temp_password,
            })

        except Exception as e:
            errors.append({'row': i, 'error': str(e)})

    return created, errors
