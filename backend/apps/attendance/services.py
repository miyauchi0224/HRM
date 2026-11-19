"""
勤怠の日区分判定・勤務間インターバル（詳細設計書 7.4）
"""
from datetime import date, datetime

import holidays
from django.conf import settings
from django.utils import timezone

from apps.notifications.models import Notification
from .models import AttendanceRecord


def classify_day(d: date) -> str:
    """
    日の区分を返す。
    日曜 → 法定休日 / 土曜・祝日・年末年始（12/31〜1/3） → 所定休日 / それ以外 → 平日
    """
    if d.weekday() == 6:
        return AttendanceRecord.DayType.LEGAL_HOLIDAY
    if (
        d.weekday() == 5
        or d in holidays.Japan(years=d.year)
        or (d.month == 12 and d.day == 31)
        or (d.month == 1 and d.day <= 3)
    ):
        return AttendanceRecord.DayType.NON_LEGAL_HOLIDAY
    return AttendanceRecord.DayType.WEEKDAY


def rest_interval_minutes(employee, clock_in_at: datetime) -> int | None:
    """直前の勤務（退勤済み）の退勤から clock_in_at までの分数。前の勤務がなければ None"""
    prev = AttendanceRecord.objects.filter(
        employee=employee, date__lt=clock_in_at.date(), clock_out__isnull=False,
    ).order_by('-date').first()
    if prev is None:
        return None
    prev_out = timezone.make_aware(datetime.combine(prev.date, prev.clock_out), clock_in_at.tzinfo)
    return max(0, int((clock_in_at - prev_out).total_seconds() // 60))


def check_work_interval(employee, record: AttendanceRecord, clock_in_at: datetime):
    """勤務間インターバルを記録し、基準未満なら本人と上司に通知する（打刻は止めない）"""
    minutes = rest_interval_minutes(employee, clock_in_at)
    if minutes is None:
        return
    record.rest_interval_minutes = minutes
    record.save(update_fields=['rest_interval_minutes'])

    threshold = settings.WORK_INTERVAL_MINUTES
    if minutes >= threshold:
        return
    hours = f'{minutes // 60}時間{minutes % 60:02d}分'
    base  = f'{threshold // 60}時間'
    Notification.send(
        user=employee.user,
        type_=Notification.NotificationType.WORK_INTERVAL,
        title='勤務間インターバルが不足しています',
        message=f'前回の退勤から今回の出勤まで {hours} でした（基準 {base}）。体調に気をつけてください。',
        related_url='/attendance',
    )
    for manager in employee.managers.select_related('user'):
        Notification.send(
            user=manager.user,
            type_=Notification.NotificationType.WORK_INTERVAL,
            title=f'【勤務間インターバル】{employee.full_name}さん',
            message=f'{employee.full_name}さんの前回の退勤から今回の出勤までが {hours} でした（基準 {base}）。',
            related_url='/attendance',
        )
