"""
ViewSet用ミックスイン

ModelViewSet に先に継承させることで：
- destroy() → ソフトデリート（物理削除禁止）
- restore  → 非表示解除アクション（HR/管理者のみ）
- AuditLog は signals.py でシグナルベースに自動記録
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AuditLog


class SoftDeleteViewSetMixin:
    """
    使い方:
        class MyViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
            ...

    注意: 継承順は SoftDeleteViewSetMixin を先に書くこと（MROの関係）
    """

    def destroy(self, request, *args, **kwargs):
        """DELETE → 物理削除ではなく is_deleted=True に変更"""
        instance = self.get_object()

        if hasattr(instance, 'soft_delete'):
            instance.soft_delete(user=request.user)
        else:
            instance.delete()

        AuditLog.log(
            user=request.user,
            action=AuditLog.Action.DELETE,
            instance=instance,
            request=request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='restore')
    def restore(self, request, *args, **kwargs):
        """非表示レコードを復元する"""
        model = self.get_queryset().model
        pk = kwargs.get('pk')
        try:
            instance = model.all_objects.get(pk=pk, is_deleted=True)
        except (model.DoesNotExist, AttributeError):
            return Response({'detail': '削除済みレコードが見つかりません'}, status=status.HTTP_404_NOT_FOUND)

        instance.restore()
        AuditLog.log(
            user=request.user,
            action=AuditLog.Action.RESTORE,
            instance=instance,
            request=request,
        )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
