"""再検査・受診の期限リマインド（詳細設計書 7.6）"""
from apps.common.utils import users_with_roles
from apps.notifications.models import Notification
from apps.scheduler.registry import register_job
from .models import HealthCheckup

DUE_NOTIFY_DAYS        = (14, 7, 1, 0)
OVERDUE_INTERVAL_DAYS  = 7


@register_job('health_checkup.remind_followups', '健康診断の再検査リマインド', order=70)
def remind_followups(run_date):
    staff = users_with_roles('labor', 'hr')
    notified = 0
    pending = HealthCheckup.objects.filter(
        result__in=HealthCheckup.FOLLOWUP_RESULTS,
        followup_completed_date__isnull=True,
        followup_due_date__isnull=False,
    ).select_related('employee__user')

    for hc in pending:
        days_left = (hc.followup_due_date - run_date).days
        emp = hc.employee
        if days_left in DUE_NOTIFY_DAYS:
            Notification.send(
                user=emp.user, type_=Notification.NotificationType.HEALTH_CHECKUP,
                title='健康診断の再検査・受診の期限が近づいています',
                message=f'{hc.fiscal_year}年度の健康診断（{hc.get_result_display()}）の再検査・受診期限は '
                        f'{hc.followup_due_date} です。受診したら労務担当に報告してください。',
                related_url='/health-checkup',
            )
            notified += 1
        elif days_left < 0 and (-days_left) % OVERDUE_INTERVAL_DAYS == 0:
            Notification.send(
                user=emp.user, type_=Notification.NotificationType.HEALTH_CHECKUP,
                title='健康診断の再検査・受診期限を過ぎています',
                message=f'再検査・受診の期限（{hc.followup_due_date}）を {-days_left} 日過ぎています。早めに受診してください。',
                related_url='/health-checkup',
            )
            for user in staff:
                Notification.send(
                    user=user, type_=Notification.NotificationType.HEALTH_CHECKUP,
                    title=f'【再検査未受診】{emp.full_name}さん',
                    message=f'{emp.full_name}さんの再検査・受診期限（{hc.followup_due_date}）を {-days_left} 日過ぎています。',
                    related_url='/health-checkup',
                )
            notified += 1
    return {'notified': notified}
