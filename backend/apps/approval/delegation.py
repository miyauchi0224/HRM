"""
代理承認の判定と承認依頼通知

休暇・経費・打刻修正・電子稟議の各ビューから使う共通処理。
"""
from datetime import date

from django.db.models import Q

from apps.notifications.models import Notification
from .models import ApprovalDelegation


def active_delegations(on: date | None = None):
    on = on or date.today()
    return ApprovalDelegation.objects.filter(start_date__lte=on, end_date__gte=on).select_related(
        'delegator__user', 'delegate__user',
    )


def delegates_of(approver, on: date | None = None):
    """承認者に対して有効な代理人の一覧"""
    return [d.delegate for d in active_delegations(on).filter(delegator=approver)]


def delegators_for(employee, on: date | None = None):
    """この社員を代理人に指定している委任元の一覧"""
    if employee is None:
        return []
    return [d.delegator for d in active_delegations(on).filter(delegate=employee)]


def can_act_for(employee, approver, on: date | None = None) -> bool:
    """employee が approver として判断できるか（本人、または有効な代理人）"""
    if employee is None or approver is None:
        return False
    if employee.pk == approver.pk:
        return True
    return active_delegations(on).filter(delegator=approver, delegate=employee).exists()


def is_delegate_for_applicant(employee, applicant, on: date | None = None) -> bool:
    """employee が applicant の上司の誰かの代理人か（休暇・経費・打刻修正の承認判定用）"""
    if employee is None:
        return False
    manager_ids = list(applicant.managers.values_list('id', flat=True))
    return active_delegations(on).filter(delegator_id__in=manager_ids, delegate=employee).exists()


def delegated_applicant_filter(employee, field: str, on: date | None = None):
    """
    代理人として見られる申請の絞り込み条件（Q）。
    field は申請者を指すフィールド名（例: 'employee', 'applicant'）。
    """
    delegators = delegators_for(employee, on)
    if not delegators:
        return Q(pk__in=[])
    return Q(**{f'{field}__managers__in': delegators})


def notify_approvers(approvers, type_, title, message, related_url=''):
    """承認者と、その有効な代理人に承認依頼を通知する（同じ人には1回だけ）"""
    sent = set()
    for approver in approvers:
        if approver.pk not in sent:
            Notification.send(user=approver.user, type_=type_, title=title,
                              message=message, related_url=related_url)
            sent.add(approver.pk)
        for delegate in delegates_of(approver):
            if delegate.pk in sent:
                continue
            Notification.send(
                user=delegate.user, type_=type_, title=f'【代理】{title}',
                message=f'{approver.full_name}さんの代理として承認をお願いします。{message}',
                related_url=related_url,
            )
            sent.add(delegate.pk)
