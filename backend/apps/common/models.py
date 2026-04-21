"""
SoftDeleteModel — 全モデル共通の論理削除ミックスイン
AuditLog      — 全ユーザ操作を1テーブルで記録するモデル

【設計方針】
- DBからの物理削除を禁止。is_deleted=True で「非表示」扱い。
- デフォルトのManagerは is_deleted=False のみ返す。
- all_objects Managerで削除済みを含む全件取得可能。
- AuditLogで誰がいつ何をしたかを追跡可能。
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        """QuerySet.delete() を上書きしてソフトデリートに変換"""
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        """物理削除（システム管理者専用・通常は使わない）"""
        return super().delete()

    def restore(self):
        """削除取り消し"""
        return self.update(is_deleted=False, deleted_at=None, deleted_by=None)


class SoftDeleteManager(models.Manager):
    """通常のManagerは削除済みを除外"""
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """削除済みを含む全件を返すManager"""
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(models.Model):
    """
    論理削除＋操作記録ミックスイン（abstract）

    継承するだけで以下が有効になる：
    - obj.soft_delete(user)  → is_deleted=True（物理削除ではない）
    - obj.restore()          → is_deleted=False に戻す
    - Model.objects          → 削除済みを除外（通常クエリ）
    - Model.all_objects      → 削除済みを含む全件
    """
    is_deleted  = models.BooleanField(default=False, db_index=True, verbose_name='削除済み')
    deleted_at  = models.DateTimeField(null=True, blank=True, verbose_name='削除日時')
    deleted_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name='削除者',
    )

    objects     = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        """論理削除（物理削除の代わりにこれを呼ぶ）"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        """削除取り消し"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def delete(self, using=None, keep_parents=False):
        """Model.delete() を上書きして物理削除をブロック"""
        self.soft_delete()


class AuditLog(models.Model):
    """
    全ユーザ操作ログ

    誰がいつどのレコードに何をしたかを記録する。
    ViewSetミックスイン（SoftDeleteViewSetMixin）が自動で記録する。
    """
    class Action(models.TextChoices):
        CREATE  = 'create',  '作成'
        UPDATE  = 'update',  '更新'
        DELETE  = 'delete',  '削除（非表示）'
        RESTORE = 'restore', '復元'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, on_delete=models.SET_NULL,
        related_name='audit_logs',
        verbose_name='操作者',
    )
    action     = models.CharField(max_length=20, choices=Action.choices, verbose_name='操作種別')
    app_label  = models.CharField(max_length=50, verbose_name='アプリ')
    model_name = models.CharField(max_length=100, verbose_name='モデル名')
    object_id  = models.CharField(max_length=100, verbose_name='レコードID')
    object_repr = models.CharField(max_length=500, blank=True, verbose_name='レコード概要')
    changes    = models.JSONField(default=dict, blank=True, verbose_name='変更内容')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IPアドレス')
    timestamp  = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='操作日時')

    class Meta:
        verbose_name = '操作ログ'
        ordering     = ['-timestamp']
        indexes      = [
            models.Index(fields=['app_label', 'model_name', 'object_id']),
            models.Index(fields=['user', 'timestamp']),
        ]

    def __str__(self):
        return f'[{self.timestamp:%Y-%m-%d %H:%M}] {self.user} → {self.action} {self.model_name}#{self.object_id}'

    @classmethod
    def log(cls, *, user, action, instance, changes=None, request=None):
        """操作ログを記録するクラスメソッド"""
        ip = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

        cls.objects.create(
            user       = user,
            action     = action,
            app_label  = instance._meta.app_label,
            model_name = instance._meta.model_name,
            object_id  = str(instance.pk),
            object_repr= str(instance)[:500],
            changes    = changes or {},
            ip_address = ip,
        )
