"""資格の有効期限アラート（詳細設計書 11.2）"""
from datetime import timedelta

from apps.notifications.models import Notification
from apps.scheduler.registry import register_job
from .models import Skill

EXPIRY_NOTIFY_DAYS = (90, 30, 7)


@register_job('skills.check_expiry', '資格の有効期限アラート', order=60)
def check_expiry(run_date):
    target_dates = [run_date + timedelta(days=d) for d in EXPIRY_NOTIFY_DAYS]
    notified = 0
    for skill in Skill.objects.filter(expiry_date__in=target_dates).select_related('employee__user'):
        days_left = (skill.expiry_date - run_date).days
        Notification.send(
            user=skill.employee.user,
            type_=Notification.NotificationType.SKILL_EXPIRY,
            title=f'資格有効期限アラート：{skill.skill_name}',
            message=f'{skill.skill_name}の有効期限まであと{days_left}日です（{skill.expiry_date}）',
            related_url='/skills',
        )
        notified += 1
    return {'notified': notified}
