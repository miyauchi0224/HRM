"""パルスサーベイの未回答リマインド（詳細設計書 7.10）"""
from datetime import timedelta

from apps.employees.models import Employee
from apps.notifications.models import Notification
from apps.scheduler.registry import register_job
from .models import PulseSurvey

REMIND_DAYS_BEFORE_END = 2


@register_job('pulse_survey.remind_unanswered', 'パルスサーベイの未回答リマインド', order=90)
def remind_unanswered(run_date):
    surveys = PulseSurvey.objects.filter(
        is_published=True, end_date=run_date + timedelta(days=REMIND_DAYS_BEFORE_END),
        start_date__lte=run_date,
    )
    notified = 0
    for survey in surveys:
        answered = set(survey.participations.values_list('employee_id', flat=True))
        for emp in Employee.objects.select_related('user').filter(retire_date__isnull=True):
            if emp.id in answered or emp.user.is_customer:
                continue
            Notification.send(
                user=emp.user,
                type_=Notification.NotificationType.PULSE_SURVEY,
                title=f'【回答期限まで{REMIND_DAYS_BEFORE_END}日】{survey.title}',
                message=f'{survey.end_date} が回答期限です。まだの方は回答をお願いします。',
                related_url=f'/pulse/{survey.id}',
            )
            notified += 1
    return {'notified': notified}
