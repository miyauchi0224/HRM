"""
有給休暇の自動付与・年度繰越・年5日取得義務の判定

詳細設計書 7.2 に対応。定期ジョブ（jobs.py）と API（views.py）の両方から使う。
"""
import calendar
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import F, Sum

from apps.common.utils import fiscal_year_of
from apps.employees.models import Employee
from .models import ANNUAL_LEAVE_GRANT_TABLE, LeaveBalance, LeaveGrant, LeaveRequest

# 自動付与の対象とする雇用形態（パートの比例付与・派遣は手動で付与する）
AUTO_GRANT_EMPLOYMENT_TYPES = (Employee.EmploymentType.FULL_TIME, Employee.EmploymentType.CONTRACT)

OBLIGATION_REQUIRED_DAYS = Decimal('5')
OBLIGATION_MIN_GRANT     = Decimal('10')
CARRY_OVER_LIMIT         = Decimal('20')


def add_months(d: date, months: int) -> date:
    """月を加算する。月末を超える日は月末に丸める（1/31 + 1ヶ月 = 2/28）"""
    month_index = d.month - 1 + months
    year  = d.year + month_index // 12
    month = month_index % 12 + 1
    day   = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def add_years(d: date, years: int) -> date:
    return add_months(d, years * 12)


def grant_days_for(months_of_service: int) -> int:
    days = 0
    for months, grant in ANNUAL_LEAVE_GRANT_TABLE:
        if months_of_service >= months:
            days = grant
    return days


def latest_grant(hire_date: date, today: date):
    """
    today 時点の直近の付与日と付与日数を返す。まだ最初の付与日前なら None。
    付与日 = 入社日の6ヶ月後、以降1年ごと。
    """
    first = add_months(hire_date, 6)
    if today < first:
        return None
    months = 6
    grant_date = first
    while add_months(hire_date, months + 12) <= today:
        months += 12
        grant_date = add_months(hire_date, months)
    return grant_date, grant_days_for(months)


def is_auto_grant_target(employee: Employee, today: date) -> bool:
    return (
        employee.hire_date is not None
        and employee.employment_type in AUTO_GRANT_EMPLOYMENT_TYPES
        and (employee.retire_date is None or employee.retire_date > today)
        and not employee.user.is_customer
    )


@transaction.atomic
def record_grant(employee, grant_date: date, days, source=LeaveGrant.Source.AUTO, note='') -> LeaveGrant:
    """付与履歴を作成し、付与日の属する年度の残高に加算する"""
    days = Decimal(str(days))
    grant = LeaveGrant.objects.create(
        employee=employee, grant_date=grant_date, days=days,
        expires_on=add_years(grant_date, 2) - timedelta(days=1),
        source=source, note=note,
    )
    balance, _ = LeaveBalance.objects.get_or_create(employee=employee, fiscal_year=fiscal_year_of(grant_date))
    LeaveBalance.objects.filter(pk=balance.pk).update(granted_days=F('granted_days') + days)
    return grant


def grant_annual_leave(today: date) -> list[LeaveGrant]:
    """付与日を迎えた（または過ぎて未付与の）社員に付与する"""
    granted = []
    for emp in Employee.objects.select_related('user').filter(hire_date__isnull=False):
        if not is_auto_grant_target(emp, today):
            continue
        latest = latest_grant(emp.hire_date, today)
        if latest is None:
            continue
        grant_date, days = latest
        # 人事が削除（論理削除）した付与も「処理済み」とみなして再付与しない
        if LeaveGrant.all_objects.filter(employee=emp, grant_date=grant_date).exists():
            continue
        granted.append(record_grant(emp, grant_date, days))
    return granted


def rollover_fiscal_year(today: date) -> int:
    """前年度の残日数を今年度へ繰り越す。処理した件数を返す"""
    fy = fiscal_year_of(today)
    count = 0
    for prev in LeaveBalance.objects.filter(fiscal_year=fy - 1).select_related('employee'):
        current, _ = LeaveBalance.objects.get_or_create(employee=prev.employee, fiscal_year=fy)
        if current.rollover_done:
            continue
        if current.carried_days == 0:
            # 時効2年のため、繰り越せるのは前年度に付与された分まで
            carried = min(max(prev.remaining_days, Decimal('0')), prev.granted_days, CARRY_OVER_LIMIT)
            current.carried_days = carried
        current.rollover_done = True
        current.save(update_fields=['carried_days', 'rollover_done'])
        count += 1
    return count


def available_annual_days(employee, start_date: date, exclude_pk=None) -> Decimal:
    """
    start_date の年度で、新たに申請できる有給の日数。
    残日数（承認済みは used_days に反映済み）から、申請中の有給の日数を差し引く。
    残高レコードがない場合は 0 日。
    """
    fy = fiscal_year_of(start_date)
    balance = LeaveBalance.objects.filter(employee=employee, fiscal_year=fy).first()
    remaining = balance.remaining_days if balance else Decimal('0')

    pending = LeaveRequest.objects.filter(
        employee=employee,
        leave_type=LeaveRequest.LeaveType.ANNUAL,
        status=LeaveRequest.Status.PENDING,
    )
    if exclude_pk is not None:
        pending = pending.exclude(pk=exclude_pk)
    pending_days = sum(
        (r.days for r in pending if fiscal_year_of(r.start_date) == fy), Decimal('0')
    )
    return max(remaining - pending_days, Decimal('0'))


def taken_annual_days(employee, start: date, end: date) -> Decimal:
    """期間内に開始する承認済み有給の日数合計"""
    total = LeaveRequest.objects.filter(
        employee=employee,
        leave_type=LeaveRequest.LeaveType.ANNUAL,
        status=LeaveRequest.Status.APPROVED,
        start_date__gte=start, start_date__lte=end,
    ).aggregate(total=Sum('days'))['total']
    return total or Decimal('0')


def obligation_status(grant: LeaveGrant, today: date) -> dict:
    """1件の付与について年5日取得義務の状況を返す"""
    deadline  = add_years(grant.grant_date, 1) - timedelta(days=1)
    taken     = taken_annual_days(grant.employee, grant.grant_date, deadline)
    remaining = max(OBLIGATION_REQUIRED_DAYS - taken, Decimal('0'))
    days_left = (deadline - today).days

    if remaining == 0:
        state = 'ok'
    elif days_left < 0:
        state = 'overdue'
    elif days_left <= 90:
        state = 'warning'
    else:
        state = 'ok'

    return {
        'employee_id':         str(grant.employee_id),
        'full_name':           grant.employee.full_name,
        'department':          grant.employee.department,
        'grant_date':          grant.grant_date,
        'deadline':            deadline,
        'granted_days':        float(grant.days),
        'taken_days':          float(taken),
        'required_days':       int(OBLIGATION_REQUIRED_DAYS),
        'remaining_required':  float(remaining),
        'days_until_deadline': days_left,
        'status':              state,
    }


def current_obligation_grant(employee, today: date):
    """today を基準期間に含む、10日以上の付与のうち最新のもの"""
    return LeaveGrant.objects.filter(
        employee=employee,
        days__gte=OBLIGATION_MIN_GRANT,
        grant_date__lte=today,
        grant_date__gt=add_years(today, -1),
    ).select_related('employee').order_by('-grant_date').first()
