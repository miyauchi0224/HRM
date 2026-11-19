"""承認待ちのリマインド（詳細設計書 7.3）"""
from django.conf import settings
from django.utils import timezone

from apps.notifications.models import Notification
from apps.scheduler.registry import register_job
from .delegation import notify_approvers
from .models import ApprovalRequest, ApprovalStep


def _is_remind_day(since, run_date, interval):
    """起算日から interval 日ごとの日か（0日目は除く）"""
    elapsed = (run_date - timezone.localtime(since).date()).days
    return elapsed >= interval and elapsed % interval == 0, elapsed


@register_job('approval.remind_pending', '承認待ちのリマインド', order=40)
def remind_pending(run_date):
    from apps.attendance.models import AttendanceModRequest
    from apps.expense.models import ExpenseRequest
    from apps.leave.models import LeaveRequest

    interval = settings.APPROVAL_REMIND_DAYS
    reminded = 0
    remind_type = Notification.NotificationType.APPROVAL_REMINDER

    # 休暇・経費・打刻修正: 承認者は申請者の上司
    targets = [
        (LeaveRequest.objects.filter(status=LeaveRequest.Status.PENDING).select_related('employee'),
         'employee', '休暇申請', '/leave'),
        (ExpenseRequest.objects.filter(status=ExpenseRequest.Status.PENDING).select_related('applicant'),
         'applicant', '経費申請', '/expense'),
        (AttendanceModRequest.objects.filter(status=AttendanceModRequest.Status.PENDING).select_related('applicant'),
         'applicant', '打刻修正申請', '/attendance/modification'),
    ]
    for qs, applicant_field, label, url in targets:
        for req in qs:
            due, elapsed = _is_remind_day(req.created_at, run_date, interval)
            if not due:
                continue
            applicant = getattr(req, applicant_field)
            notify_approvers(
                list(applicant.managers.select_related('user')),
                type_=remind_type,
                title=f'【リマインド】{label}が承認待ちです',
                message=f'{applicant.full_name}さんの{label}が {elapsed} 日間承認待ちになっています。',
                related_url=url,
            )
            reminded += 1

    # 電子稟議: 現在のステップ（未決のうち最も順序が早いもの）の承認者
    for req in ApprovalRequest.objects.filter(status=ApprovalRequest.Status.PENDING).select_related('applicant'):
        steps   = list(req.steps.select_related('approver__user').order_by('order'))
        current = next((s for s in steps if s.decision == ApprovalStep.Decision.PENDING), None)
        if current is None:
            continue
        decided = [s.decided_at for s in steps if s.order < current.order and s.decided_at]
        since   = max(decided) if decided else (req.submitted_at or req.created_at)
        due, elapsed = _is_remind_day(since, run_date, interval)
        if not due:
            continue
        notify_approvers(
            [current.approver],
            type_=remind_type,
            title='【リマインド】稟議が承認待ちです',
            message=f'「{req.title}」（申請者: {req.applicant.full_name}）が {elapsed} 日間承認待ちになっています。',
            related_url='/approval',
        )
        reminded += 1

    return {'reminded': reminded}
