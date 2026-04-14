"""
テスト用 Employee レコードを PostgreSQL に直接作成するスクリプト
docker-compose.yml の設定に基づいた接続情報を使用
"""
import uuid
from datetime import date

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("psycopg2 が見つかりません。インストールします...")
    import subprocess, sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary'])
    import psycopg2
    from psycopg2.extras import RealDictCursor

# docker-compose.yml の設定
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    dbname='hrm',
    user='hrm_admin',
    password='localpassword'
)
cur = conn.cursor(cursor_factory=RealDictCursor)

# ユーザー一覧を確認
print("=== 登録済みユーザー ===")
cur.execute("SELECT id, email, is_superuser FROM accounts_user ORDER BY id;")
users = cur.fetchall()
for u in users:
    cur.execute("SELECT id FROM employees_employee WHERE user_id = %s;", (u['id'],))
    emp = cur.fetchone()
    print(f"  id={u['id']} | email={u['email']} | superuser={u['is_superuser']} | employee={'あり' if emp else 'なし'}")

print()

# Employee がいないユーザーに作成
emp_number = 1
for u in users:
    cur.execute("SELECT id FROM employees_employee WHERE user_id = %s;", (u['id'],))
    if cur.fetchone():
        print(f"{u['email']}: 既に Employee があります（スキップ）")
        continue

    emp_id = str(uuid.uuid4())
    emp_num = f'EMP{emp_number:03d}'
    cur.execute("""
        INSERT INTO employees_employee (
            id, user_id, employee_number,
            last_name, first_name, last_name_kana, first_name_kana,
            birth_date, gender, hire_date,
            department, position, grade, employment_type,
            phone, personal_email,
            created_at, updated_at
        ) VALUES (
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s,
            NOW(), NOW()
        )
    """, (
        emp_id, u['id'], emp_num,
        'テスト', 'ユーザー', 'テスト', 'ユーザー',
        date(1990, 1, 1), 'male', date(2020, 4, 1),
        '開発部', 'エンジニア', 1, 'full_time',
        '', ''
    ))
    print(f"{u['email']}: Employee 作成完了 → {emp_num}")
    emp_number += 1

conn.commit()
cur.close()
conn.close()
print("\n完了！ブラウザでリロードしてください。")
