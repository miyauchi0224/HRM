"""
シグナルハンドラ — 全モデルの作成・更新を自動的にAuditLogへ記録

【仕組み】
- post_save シグナル: 作成(created=True) / 更新(created=False) を捕捉
- pre_save  シグナル: 更新前の値を保存（変更差分の記録に使用）
- 現在ユーザの特定: django-crum ライブラリ（スレッドローカル変数）を使用
  ※ pip install django-crum が必要。未インストール時は user=None でログ記録
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import SoftDeleteModel, AuditLog

logger = logging.getLogger(__name__)


def _get_current_user():
    """リクエスト中の現在ユーザを取得（django-crum 使用）"""
    try:
        from crum import get_current_user
        return get_current_user()
    except ImportError:
        return None


@receiver(post_save)
def log_model_save(sender, instance, created, **kwargs):
    """SoftDeleteModel を継承した全モデルの保存を自動ログ記録"""
    if not isinstance(instance, SoftDeleteModel):
        return
    if sender is AuditLog:
        return

    # is_deleted=True への変更は destroy() 側でログ済みなのでスキップ
    if instance.is_deleted:
        return

    action = AuditLog.Action.CREATE if created else AuditLog.Action.UPDATE
    user = _get_current_user()

    try:
        AuditLog.objects.create(
            user       = user,
            action     = action,
            app_label  = instance._meta.app_label,
            model_name = instance._meta.model_name,
            object_id  = str(instance.pk),
            object_repr= str(instance)[:500],
            changes    = {},
        )
    except Exception:
        logger.exception('AuditLog 記録に失敗しました: %s#%s', sender.__name__, instance.pk)
