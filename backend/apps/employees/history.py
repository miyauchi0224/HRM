"""
異動・昇格履歴の記録・反映・過去時点の再現（詳細設計書 7.5）
"""
from datetime import date

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Employee, EmploymentHistory

TRACKED_FIELDS = ('department', 'position', 'grade', 'employment_type')


def infer_change_type(before: dict, after: dict) -> str:
    """変更内容から種別を決める（等級 → 部署 → 役職 → 雇用形態 の優先順）"""
    CT = EmploymentHistory.ChangeType
    gb, ga = before.get('grade'), after.get('grade')
    if gb is not None and ga is not None and ga != gb:
        return CT.PROMOTION if ga > gb else CT.DEMOTION
    if after.get('department') != before.get('department'):
        return CT.TRANSFER
    if after.get('position') != before.get('position'):
        return CT.POSITION_CHANGE
    if after.get('employment_type') != before.get('employment_type'):
        return CT.EMPLOYMENT_TYPE
    return CT.OTHER


def _history_kwargs(before: dict, after: dict) -> dict:
    return {f'{f}_{suffix}': (src.get(f) if src.get(f) is not None else ('' if f != 'grade' else None))
            for f in TRACKED_FIELDS for suffix, src in (('before', before), ('after', after))}


@receiver(pre_save, sender=Employee)
def _remember_tracked_values(sender, instance, **kwargs):
    if instance.pk is None or kwargs.get('raw'):
        instance._history_before = None
        return
    old = Employee.all_objects.filter(pk=instance.pk).values(*TRACKED_FIELDS).first()
    instance._history_before = old


@receiver(post_save, sender=Employee)
def _record_history(sender, instance, created, **kwargs):
    """部署・役職・等級・雇用形態の変更を自動記録する（発令の反映時は二重に作らない）"""
    before = getattr(instance, '_history_before', None)
    if created or before is None or getattr(instance, '_skip_history', False):
        return
    after = {f: getattr(instance, f) for f in TRACKED_FIELDS}
    if all(before[f] == after[f] for f in TRACKED_FIELDS):
        return
    EmploymentHistory.objects.create(
        employee=instance,
        effective_date=timezone.localdate(),
        change_type=infer_change_type(before, after),
        is_applied=True,
        applied_at=timezone.now(),
        created_by=getattr(instance, '_history_user', None),
        **_history_kwargs(before, after),
    )


@transaction.atomic
def apply_history(history: EmploymentHistory):
    """予約された発令を社員情報に反映する（空欄の「変更後」は変更しない）"""
    emp = history.employee
    if history.department_after:
        emp.department = history.department_after
    if history.position_after:
        emp.position = history.position_after
    if history.grade_after is not None:
        emp.grade = history.grade_after
    if history.employment_type_after:
        emp.employment_type = history.employment_type_after
    emp._skip_history = True
    emp.save(update_fields=list(TRACKED_FIELDS) + ['updated_at'])
    history.is_applied = True
    history.applied_at = timezone.now()
    history.save(update_fields=['is_applied', 'applied_at'])


def create_order(employee: Employee, effective_date: date, after: dict, note: str, user) -> EmploymentHistory:
    """
    人事の発令登録。発令日が今日以前ならすぐ反映、未来日なら予約する。
    「変更前」は登録時点の社員情報、空欄の「変更後」は変更前と同じ値として記録する。
    """
    before = {f: getattr(employee, f) for f in TRACKED_FIELDS}
    merged = {f: (after.get(f) if after.get(f) not in (None, '') else before[f]) for f in TRACKED_FIELDS}
    history = EmploymentHistory.objects.create(
        employee=employee,
        effective_date=effective_date,
        change_type=after.get('change_type') or infer_change_type(before, merged),
        note=note,
        is_applied=False,
        created_by=user,
        **_history_kwargs(before, merged),
    )
    if effective_date <= timezone.localdate():
        apply_history(history)
    return history


def snapshot_as_of(employee: Employee, as_of: date, histories: list[EmploymentHistory]) -> dict:
    """
    指定日時点の部署・役職・等級・雇用形態を返す。
    histories はこの社員の反映済み履歴（発令日の昇順）。
    """
    current = {f: getattr(employee, f) for f in TRACKED_FIELDS}
    if not histories:
        return current
    past = [h for h in histories if h.effective_date <= as_of]
    if past:
        h, suffix = past[-1], 'after'
    else:
        h, suffix = histories[0], 'before'
    snap = {}
    for f in TRACKED_FIELDS:
        v = getattr(h, f'{f}_{suffix}')
        snap[f] = v if v not in (None, '') else current[f]
    return snap
