"""有給休暇の定期ジョブ（詳細設計書 7.2）"""
from apps.common.utils import users_with_roles
from apps.notifications.models import Notification
from apps.scheduler.registry import register_job
from .models import LeaveGrant
from . import services

# 年5日取得義務の通知タイミング（期限までの残り日数）
OBLIGATION_NOTIFY_DAYS       = (90, 60, 30, 14, 7)
OBLIGATION_NOTIFY_DAYS_STAFF = (30, 7)


@register_job('leave.rollover_fiscal_year', '有給の年度繰越', order=10)
def rollover_fiscal_year(run_date):
    return {'rolled_over': services.rollover_fiscal_year(run_date)}


@register_job('leave.grant_annual_leave', '有給の自動付与', order=20)
def grant_annual_leave(run_date):
    granted = services.grant_annual_leave(run_date)
    for grant in granted:
        Notification.send(
            user=grant.employee.user,
            type_=Notification.NotificationType.LEAVE_ALERT,
            title='年次有給休暇が付与されました',
            message=f'{grant.grant_date} に {grant.days} 日付与されました（有効期限 {grant.expires_on}）。',
            related_url='/leave',
        )
    return {'granted': len(granted)}


@register_job('leave.check_five_day_obligation', '有給 年5日取得義務のチェック', order=30)
def check_five_day_obligation(run_date):
    staff = users_with_roles('hr', 'labor')
    notified = 0
    grants = LeaveGrant.objects.filter(
        days__gte=services.OBLIGATION_MIN_GRANT,
        grant_date__lte=run_date,
        grant_date__gt=services.add_years(run_date, -1),
    ).select_related('employee__user').prefetch_related('employee__managers__user')

    for grant in grants:
        st = services.obligation_status(grant, run_date)
        if st['remaining_required'] == 0 or st['days_until_deadline'] not in OBLIGATION_NOTIFY_DAYS:
            continue
        emp = grant.employee
        days_left = st['days_until_deadline']
        msg = (f'{emp.full_name}さんの有給取得は {st["taken_days"]} 日です。'
               f'{st["deadline"]} までにあと {st["remaining_required"]} 日の取得が必要です（残り {days_left} 日）。')

        Notification.send(
            user=emp.user, type_=Notification.NotificationType.LEAVE_OBLIGATION,
            title=f'有給の年5日取得義務：あと {st["remaining_required"]} 日', message=msg, related_url='/leave',
        )
        recipients = {m.user for m in emp.managers.all()}
        if days_left in OBLIGATION_NOTIFY_DAYS_STAFF:
            recipients.update(staff)
        recipients.discard(emp.user)
        for user in recipients:
            Notification.send(
                user=user, type_=Notification.NotificationType.LEAVE_OBLIGATION,
                title=f'【年5日取得義務】{emp.full_name}さん', message=msg, related_url='/leave/obligation',
            )
        notified += 1
    return {'notified_employees': notified}
