"""翌日の1on1のリマインド（詳細設計書 7.7）"""
from datetime import timedelta

from apps.notifications.models import Notification
from apps.scheduler.registry import register_job
from .models import OneOnOneMeeting


@register_job('one_on_one.remind_upcoming', '翌日の1on1のリマインド', order=80)
def remind_upcoming(run_date):
    tomorrow = run_date + timedelta(days=1)
    meetings = OneOnOneMeeting.objects.filter(
        status=OneOnOneMeeting.Status.SCHEDULED, scheduled_at__date=tomorrow,
    ).select_related('manager__user', 'member__user')
    for m in meetings:
        for me, other in ((m.manager, m.member), (m.member, m.manager)):
            Notification.send(
                user=me.user,
                type_=Notification.NotificationType.ONE_ON_ONE,
                title='明日は1on1です',
                message=f'{other.full_name}さんとの1on1：{m.scheduled_at:%m/%d %H:%M}。アジェンダを確認しておきましょう。',
                related_url='/one-on-one',
            )
    return {'meetings': meetings.count()}
