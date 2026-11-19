"""発令の反映（詳細設計書 7.5）"""
from apps.notifications.models import Notification
from apps.scheduler.registry import register_job
from .history import apply_history
from .models import EmploymentHistory


@register_job('employees.apply_scheduled_changes', '異動・昇格の発令を反映', order=50)
def apply_scheduled_changes(run_date):
    pending = EmploymentHistory.objects.filter(
        is_applied=False, effective_date__lte=run_date,
    ).select_related('employee__user').order_by('effective_date', 'created_at')
    applied = 0
    for history in pending:
        apply_history(history)
        Notification.send(
            user=history.employee.user,
            type_=Notification.NotificationType.SYSTEM,
            title=f'{history.get_change_type_display()}の発令が反映されました',
            message=f'{history.effective_date} 付の発令が社員情報に反映されました。',
            related_url='/employees',
        )
        applied += 1
    return {'applied': applied}
