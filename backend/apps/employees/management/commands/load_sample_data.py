"""
サンプルデータの投入（デモ・動作確認用）

    docker compose exec backend python manage.py load_sample_data
    docker compose exec backend python manage.py load_sample_data --reset   # 入れ直す

template/employees_sample_data.csv の 20 名を登録し、次のデータを作る。
  - 上司・部下の関係（同じ部署の部長・課長のうち、等級がいちばん近い上位者が上司。部署のトップは EMP0001）
  - 勤務ルール・給与等級・手当・勘定科目のマスタ（既にあれば作らない）
  - 有給の付与・取得、プロジェクト・タスク、直近 3 か月の勤怠
  - 給与明細（先々月は確定済、先月は計算中）、MBO 目標と月報、TODO・日報、経費、イントラ記事、資格

ログインの初期パスワードは各社員の生年月日 8 桁（YYYYMMDD）。初回ログイン時に変更を求める。
乱数のシードは固定なので、何度入れ直しても同じ内容になる。
"""
import csv
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path

import holidays
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.accounts.models import User
from apps.attendance.models import (
    AttendanceProjectRecord, AttendanceRecord, Project, ProjectManager, ProjectTask, WorkRule,
)
from apps.common.utils import fiscal_year_of
from apps.employees.csv_import import import_employees_csv
from apps.employees.models import Employee
from apps.expense.models import AccountItem, ExpenseRequest
from apps.intra.models import Article
from apps.leave import services as leave_services
from apps.leave.models import LeaveBalance, LeaveRequest
from apps.mbo.models import DailyReport as MBODailyReport, MBOGoal, MBOReport
from apps.salary.models import Allowance, EmployeeAllowance, Payslip, SalaryGrade
from apps.salary.views import _calculate_payslip
from apps.skills.models import Skill
from apps.todo.models import DailyReport as TodoDailyReport, TodoItem

CSV_NAME = 'employees_sample_data.csv'
TOP_EMPLOYEE_NUMBER = 'EMP0001'
MANAGER_POSITIONS = ('部長', '課長')  # 上司になれる役職
PROJECT_CODES = ['PJ-2026-001', 'PJ-2026-002', 'PJ-2026-003']

MBO_GOALS = {
    '経営企画部': [('中期経営計画の策定と全社展開', '3月の取締役会で承認を得る'),
                 ('新規事業の検討', '事業案を2件まとめ、経営会議に提案する')],
    '人事部':     [('中途採用目標の達成', '年間で中途5名を採用する'),
                 ('評価制度の運用改善', '評価面談の実施率100%')],
    '経理部':     [('月次決算の早期化', '毎月5営業日以内に締める'),
                 ('経費精算のペーパーレス化', '紙の申請を0件にする')],
    '開発部':     [('担当機能の品質向上', '不具合の件数を前期比で30%減らす'),
                 ('新しい技術の習得', '社内勉強会で2回発表する')],
    '営業部':     [('新規顧客の獲得', '期間中に新規5社と契約する'),
                 ('既存顧客の継続率向上', '継続率95%以上を保つ')],
    '総務部':     [('社内設備の更新計画の策定', '来期の更新計画を作成し承認を得る'),
                 ('防災訓練の実施', '年2回の訓練を実施し、参加率90%以上')],
}

SKILLS_BY_DEPT = {
    '開発部': [('Python', 'language', '実務5年', ''), ('AWS 認定ソリューションアーキテクト', 'certificate', 'アソシエイト', 'Amazon Web Services'),
             ('React', 'framework', '実務3年', ''), ('基本情報技術者', 'certificate', '', 'IPA')],
    '経理部': [('日商簿記', 'certificate', '2級', '日本商工会議所')],
    '人事部': [('社会保険労務士', 'certificate', '', '全国社会保険労務士会連合会')],
    '営業部': [('TOEIC', 'lang_spoken', '780点', 'IIBC')],
    '総務部': [('衛生管理者', 'certificate', '第一種', '安全衛生技術試験協会')],
}


def _csv_path(option):
    if option:
        return Path(option)
    for p in (Path(settings.BASE_DIR) / 'template' / CSV_NAME,
              Path(settings.BASE_DIR).parent / 'template' / CSV_NAME):
        if p.exists():
            return p
    raise CommandError(f'{CSV_NAME} が見つかりません。--csv でパスを指定してください')


def _month_start(d: date, months_back: int) -> date:
    """months_back か月前の月初（負の値なら先の月）"""
    idx = d.year * 12 + (d.month - 1) - months_back
    return date(idx // 12, idx % 12 + 1, 1)


def _num(emp) -> int:
    """社員番号の数字部分（乱数に頼らず社員ごとに決まった振り分けをするため）"""
    digits = ''.join(c for c in emp.employee_number if c.isdigit())
    return int(digits or 0)


class Command(BaseCommand):
    help = 'デモ・動作確認用のサンプルデータを投入する（初期パスワードは生年月日 8 桁）'

    def add_arguments(self, parser):
        parser.add_argument('--csv', help=f'社員 CSV のパス（省略時は template/{CSV_NAME}）')
        parser.add_argument('--reset', action='store_true',
                            help='投入済みのサンプルデータを削除してから入れ直す')
        parser.add_argument('--months', type=int, default=3, help='勤怠を作る月数（今月を含む。既定 3）')

    def handle(self, *args, **opts):
        path = _csv_path(opts['csv'])
        text = path.read_text(encoding='utf-8-sig')
        emails = [r['メールアドレス'].strip() for r in csv.DictReader(text.splitlines())]

        if opts['reset']:
            self._reset(emails)
        elif User.objects.filter(email__in=emails).exists():
            raise CommandError('サンプルデータは投入済みです。入れ直す場合は --reset を付けてください')

        self.rnd   = random.Random(42)
        self.today = timezone.localdate()
        self.jp_holidays = holidays.Japan(years=range(self.today.year - 1, self.today.year + 2))

        with transaction.atomic():
            created, errors = import_employees_csv(text)
            if errors:
                raise CommandError('社員の登録に失敗しました: ' +
                                   ' / '.join(f'{e["row"]}行目: {e["error"]}' for e in errors))
            self.emps = list(Employee.objects.filter(user__email__in=emails)
                             .select_related('user').order_by('employee_number'))
            self.by_no = {e.employee_number: e for e in self.emps}
            self.active = [e for e in self.emps
                           if e.hire_date and e.hire_date <= self.today
                           and (e.retire_date is None or e.retire_date > self.today)]

            self._managers()
            self._masters()
            leave_dates = self._leave()
            self._projects()
            self._attendance(opts['months'], leave_dates)
            self._payslips()
            self._mbo()
            self._todo()
            self._expense()
            self._intra()
            self._skills()

        self._report(created)

    # ─── 削除 ───────────────────────────────────────────────
    def _reset(self, emails):
        # ユーザーを消すと社員情報と、そこに紐づく勤怠・給与・申請などもまとめて消える
        deleted, _ = User.objects.filter(email__in=emails).delete()
        Project.all_objects.filter(code__in=PROJECT_CODES).hard_delete()
        self.stdout.write(f'既存のサンプルデータを削除しました（{deleted} 件）')

    # ─── 上司・部下 ─────────────────────────────────────────
    def _managers(self):
        top = self.by_no.get(TOP_EMPLOYEE_NUMBER)
        for emp in self.emps:
            if emp == top:
                continue
            higher = [o for o in self.emps
                      if o.department == emp.department and o.grade > emp.grade
                      and o.position in MANAGER_POSITIONS]
            manager = min(higher, key=lambda o: o.grade) if higher else top
            if manager:
                emp.managers.add(manager)

    # ─── マスタ ─────────────────────────────────────────────
    def _masters(self):
        if not WorkRule.objects.filter(is_default=True).exists():
            WorkRule.objects.get_or_create(
                name='標準勤務', defaults=dict(work_start=time(9), work_end=time(18), is_default=True))

        for g in range(1, 9):
            SalaryGrade.objects.get_or_create(
                grade=g, defaults=dict(base_salary=200000 + (g - 1) * 40000, valid_from=date(2020, 1, 1)))

        commute,  _ = Allowance.objects.get_or_create(name='通勤手当', defaults=dict(allowance_type='commute', amount=15000))
        housing,  _ = Allowance.objects.get_or_create(name='住宅手当', defaults=dict(allowance_type='housing', amount=20000))
        position, _ = Allowance.objects.get_or_create(name='役職手当', defaults=dict(allowance_type='position', amount=30000))
        for i, emp in enumerate(self.emps):
            start = emp.hire_date or date(2020, 1, 1)
            EmployeeAllowance.objects.create(employee=emp, allowance=commute, valid_from=start,
                                             amount=self.rnd.choice([8000, 12000, 15000, 22000]))
            if i % 3 == 0:
                EmployeeAllowance.objects.create(employee=emp, allowance=housing, valid_from=start)
            if emp.position in ('部長', '課長'):
                EmployeeAllowance.objects.create(employee=emp, allowance=position, valid_from=start,
                                                 amount=50000 if emp.position == '部長' else 30000)

        for code, name, cat in [('6101', '旅費交通費', 'travel'), ('6201', '消耗品費', 'supplies'),
                                ('6301', '接待交際費', 'entertainment'), ('6401', '通信費', 'communication')]:
            AccountItem.objects.get_or_create(code=code, defaults=dict(name=name, category=cat))

    # ─── 有給 ───────────────────────────────────────────────
    def _is_workday(self, d):
        return d.weekday() < 5 and d not in self.jp_holidays

    def _leave(self):
        """有給を付与し、付与日以降に 1〜3 日取得させる。勤怠を作らない日付を返す"""
        leave_services.grant_annual_leave(self.today)
        leave_dates = {}
        for emp in self.active:
            grant = leave_services.current_obligation_grant(emp, self.today) or \
                emp.leave_grants.order_by('-grant_date').first()
            if grant is None:
                continue
            candidates = [grant.grant_date + timedelta(days=n) for n in range((self.today - grant.grant_date).days)]
            candidates = [d for d in candidates if self._is_workday(d) and d < self.today]
            taken = sorted(self.rnd.sample(candidates, min(len(candidates), self.rnd.randint(1, 3))))
            approver = emp.managers.first()
            for d in taken:
                LeaveRequest.objects.create(
                    employee=emp, leave_type=LeaveRequest.LeaveType.ANNUAL, start_date=d, end_date=d,
                    days=1, reason='私用のため', status=LeaveRequest.Status.APPROVED,
                    approver=approver, approved_at=timezone.make_aware(datetime.combine(d - timedelta(days=7), time(10))),
                )
                LeaveBalance.objects.filter(employee=emp, fiscal_year=fiscal_year_of(d)) \
                    .update(used_days=F('used_days') + 1)
            leave_dates[emp.id] = set(taken)

            # 何人かは来月の申請を「申請中」で残す
            if _num(emp) % 3 == 0:
                d = _month_start(self.today, -1) + timedelta(days=9)
                while not self._is_workday(d):
                    d += timedelta(days=1)
                LeaveRequest.objects.create(
                    employee=emp, leave_type=LeaveRequest.LeaveType.ANNUAL, start_date=d, end_date=d,
                    days=1, reason='家族の行事のため',
                )
        return leave_dates

    # ─── プロジェクト ───────────────────────────────────────
    def _projects(self):
        e = self.by_no.get
        specs = [
            (PROJECT_CODES[0], '社内人事システム開発', '開発部', 'EMP0007',
             ['要件定義', '画面設計', 'API 実装', '結合テスト', 'リリース準備']),
            (PROJECT_CODES[1], '顧客向け EC サイト保守', '開発部', 'EMP0008',
             ['問い合わせ対応', '決済まわりの改修', 'セキュリティ更新']),
            (PROJECT_CODES[2], '営業支援ツールの導入', '営業部', 'EMP0013',
             ['ツール比較', '試験導入', '操作説明会']),
        ]
        self.projects = {}
        for code, name, dept, manager_no, tasks in specs:
            pj = Project.objects.create(code=code, name=name, description=f'{dept}のサンプルプロジェクト',
                                        start_date=date(self.today.year, 4, 1))
            if e(manager_no):
                ProjectManager.objects.create(project=pj, employee=e(manager_no), role=ProjectManager.Role.PRIMARY)
            members = [x for x in self.active if x.department == dept]
            statuses = ['done', 'done', 'in_progress', 'review', 'todo']
            for i, title in enumerate(tasks):
                st = statuses[i % len(statuses)]
                ProjectTask.objects.create(
                    project=pj, title=title, assignee=members[i % len(members)] if members else None,
                    status=st, progress={'done': 100, 'review': 90, 'in_progress': 50, 'todo': 0}[st],
                    start_date=self.today - timedelta(days=60 - i * 10),
                    end_date=self.today + timedelta(days=i * 10), order=i,
                )
            self.projects.setdefault(dept, []).append(pj)

    # ─── 勤怠 ───────────────────────────────────────────────
    def _attendance(self, months, leave_dates):
        start = _month_start(self.today, max(months, 1) - 1)
        records, links = [], []
        for emp in self.active:
            busy = emp.department in ('開発部', '営業部')
            d = max(start, emp.hire_date)
            while d < self.today:
                if self._is_workday(d) and d not in leave_dates.get(emp.id, ()):
                    ci = datetime.combine(d, time(9)) - timedelta(minutes=self.rnd.randint(0, 15))
                    r = self.rnd.random()
                    if r < (0.5 if busy else 0.75):
                        ot = self.rnd.randint(0, 30)
                    elif r < 0.93:
                        ot = self.rnd.randint(30, 120)
                    else:
                        ot = self.rnd.randint(120, 210)
                    co = datetime.combine(d, time(18)) + timedelta(minutes=ot)
                    rec = AttendanceRecord(
                        employee=emp, date=d, clock_in=ci.time(), clock_out=co.time(),
                        stamped_clock_in=ci.time(), stamped_clock_out=co.time(),
                        break_minutes=60, status=AttendanceRecord.Status.CONFIRMED,
                        day_type=AttendanceRecord.DayType.WEEKDAY,
                    )
                    records.append(rec)
                d += timedelta(days=1)
        AttendanceRecord.objects.bulk_create(records, batch_size=500)

        # 開発部・営業部はプロジェクト別の作業時間も記録する
        for rec in records:
            pjs = self.projects.get(rec.employee.department)
            if pjs:
                links.append(AttendanceProjectRecord(
                    attendance=rec, project=pjs[_num(rec.employee) % len(pjs)],
                    minutes=rec.work_minutes))
        AttendanceProjectRecord.objects.bulk_create(links, batch_size=500)

    # ─── 給与明細 ───────────────────────────────────────────
    def _payslips(self):
        for back, confirmed in ((2, True), (1, False)):
            m = _month_start(self.today, back)
            for emp in self.active:
                if emp.hire_date > m.replace(day=28):
                    continue
                p = _calculate_payslip(emp, m.year, m.month)
                p.resident_tax = 5000 + emp.grade * 3000
                p.cutoff_date  = (_month_start(m, -1) - timedelta(days=1))
                p.payment_date = _month_start(m, -1).replace(day=25)
                if confirmed:
                    p.status = Payslip.Status.CONFIRMED
                p.recompute_totals()
                p.save()

    # ─── MBO ────────────────────────────────────────────────
    def _mbo(self):
        year = self.today.year
        current = 'first_half' if self.today.month < 10 else 'second_half'
        report_months = [_month_start(self.today, b) for b in (1, 0)]
        for emp in self.active:
            goals = MBO_GOALS.get(emp.department, MBO_GOALS['総務部'])
            # 上期は評価済み（今が下期の場合のみ）
            if current == 'second_half' and emp.hire_date <= date(year, 4, 1):
                for (title, level), weight in zip(goals, (60, 40)):
                    MBOGoal.objects.create(
                        employee=emp, year=year, period='first_half', title=title, target_level=level,
                        weight=weight, status=MBOGoal.Status.EVALUATED,
                        self_score=self.rnd.choice([3.0, 3.5, 4.0, 4.5]),
                        manager_score=self.rnd.choice([3.0, 3.5, 4.0]),
                    )
            # 今期は承認済み、月報つき（今月分は下書き）
            for (title, level), weight in zip(goals, (60, 40)):
                goal = MBOGoal.objects.create(
                    employee=emp, year=year, period=current, title=title, target_level=level,
                    weight=weight, status=MBOGoal.Status.APPROVED,
                )
                for month in report_months:
                    if month < emp.hire_date.replace(day=1):
                        continue
                    is_current = month == report_months[-1]
                    MBOReport.objects.create(
                        goal=goal, month=month,
                        action_content=f'{title}に向けて、担当業務の見直しと関係者との調整を進めた。',
                        result='計画どおりに進んでいる。一部の作業で遅れがあり、来月に取り戻す。',
                        next_month_issue='遅れている作業の巻き返しと、進捗の共有方法の改善。',
                        self_score=None if is_current else self.rnd.choice([3.0, 3.5, 4.0]),
                        manager_comment='' if is_current else 'よく進めています。引き続きお願いします。',
                        status=MBOReport.Status.DRAFT if is_current else MBOReport.Status.COMMENTED,
                    )
            # 直近の日報（MBO）
            d = self.today - timedelta(days=1)
            for _ in range(3):
                while not self._is_workday(d):
                    d -= timedelta(days=1)
                MBODailyReport.objects.create(employee=emp, report_date=d, status='submitted',
                                              content='担当業務を進め、定例会議で進捗を報告した。')
                d -= timedelta(days=1)

    # ─── TODO・日報 ─────────────────────────────────────────
    def _todo(self):
        items = [('週次報告の作成', 'done'), ('資料のレビュー', 'in_progress'),
                 ('来月の作業計画を立てる', 'not_started'), ('研修の受講', 'not_started')]
        for emp in self.active:
            for i, (title, st) in enumerate(items):
                TodoItem.objects.create(employee=emp, title=title, status=st, order=i,
                                        due_date=self.today + timedelta(days=i * 3 - 2))
            d = self.today - timedelta(days=1)
            while not self._is_workday(d):
                d -= timedelta(days=1)
            TodoDailyReport.objects.create(
                employee=emp, report_date=d, status='submitted',
                content='午前は定例会議、午後は担当作業を進めた。', tomorrow='引き続き担当作業。',
            )

    # ─── 経費 ───────────────────────────────────────────────
    def _expense(self):
        travel   = AccountItem.objects.get(code='6101')
        supplies = AccountItem.objects.get(code='6201')
        approver = self.by_no.get('EMP0005')  # 経理部長
        for i, emp in enumerate(self.active):
            if i % 2:
                continue
            d = self.today - timedelta(days=20 + i)
            ExpenseRequest.objects.create(
                applicant=emp, approver=approver, account_item=travel, expense_type='transportation',
                amount=self.rnd.choice([640, 1280, 2350]), expense_date=d,
                description='顧客先への訪問（往復）', status='approved',
                approved_at=timezone.make_aware(datetime.combine(d + timedelta(days=2), time(15))),
            )
            ExpenseRequest.objects.create(
                applicant=emp, account_item=supplies, expense_type='general',
                amount=self.rnd.choice([1980, 3300, 5480]), expense_date=self.today - timedelta(days=3),
                description='業務で使う文具・備品の購入',
            )

    # ─── イントラ記事 ───────────────────────────────────────
    def _intra(self):
        author   = self.by_no.get('EMP0002') or self.emps[0]
        approver = self.by_no.get(TOP_EMPLOYEE_NUMBER)
        articles = [
            ('年末年始の休業について', 'announcement', True,
             '## 年末年始の休業\n\n12月29日〜1月3日は休業です。\n\n- 緊急の連絡は総務部まで\n- 勤怠の締めは12月26日です'),
            ('ストレスチェック実施のお知らせ', 'announcement', False,
             '今年度のストレスチェックを実施します。期間内に回答してください。'),
            ('社内勉強会の報告（React 入門）', 'technical', False,
             '開発部で React の勉強会を開きました。資料は共有フォルダにあります。'),
        ]
        for n, (title, cat, pinned, content) in enumerate(articles):
            Article.objects.create(
                author=author, approver=approver, title=title, content=content, category=cat,
                is_pinned=pinned, status=Article.Status.APPROVED,
                published_at=timezone.now() - timedelta(days=n * 7 + 1),
            )

    # ─── 資格 ───────────────────────────────────────────────
    def _skills(self):
        for emp in self.active:
            for j, (name, cat, level, org) in enumerate(SKILLS_BY_DEPT.get(emp.department, [])):
                if (_num(emp) + j) % 2 and j:
                    continue
                Skill.objects.create(
                    employee=emp, skill_name=name, category=cat, level=level, organizer=org,
                    certified_date=emp.hire_date + timedelta(days=365) if emp.hire_date else None,
                )

    # ─── 結果表示 ───────────────────────────────────────────
    def _report(self, created):
        self.stdout.write(self.style.SUCCESS(f'サンプルデータを投入しました（社員 {len(created)} 名）'))
        self.stdout.write('ログインの初期パスワードは生年月日 8 桁（YYYYMMDD）です。初回ログイン時に変更を求めます。\n')
        roles = {e.user.email: e.user.role for e in self.emps}
        for r in created:
            self.stdout.write(f'  {r["employee_number"]}  {r["name"]:<8}  {roles.get(r["email"], ""):<10}  '
                              f'{r["email"]:<34}  {r["temp_password"]}')
