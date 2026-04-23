from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.accounts.permissions import IsNotCustomer, IsHR
from apps.common.mixins import SoftDeleteViewSetMixin
from apps.notifications.models import Notification
from .models import (
    OnboardingTemplate,
    OnboardingTemplateTask,
    OnboardingAssignment,
    OnboardingTaskItem,
)
from .serializers import (
    OnboardingTemplateSerializer,
    OnboardingTemplateTaskSerializer,
    OnboardingAssignmentSerializer,
    OnboardingTaskItemSerializer,
)
from django.utils import timezone


class OnboardingTemplateViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    """
    オンボーディングテンプレートの CRUD。
    HR/管理者のみアクセス可能。
    """
    serializer_class = OnboardingTemplateSerializer
    permission_classes = [IsHR]

    def get_queryset(self):
        return OnboardingTemplate.objects.prefetch_related('tasks').all()

    @action(detail=True, methods=['post'], url_path='add-task')
    def add_task(self, request, pk=None):
        """POST /api/v1/onboarding/templates/{id}/add-task/ — タスクを追加"""
        template = self.get_object()
        serializer = OnboardingTemplateTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(template=template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['delete'],
        url_path=r'tasks/(?P<task_id>[^/.]+)',
    )
    def remove_task(self, request, pk=None, task_id=None):
        """DELETE /api/v1/onboarding/templates/{id}/tasks/{task_id}/ — タスクを削除"""
        task = OnboardingTemplateTask.objects.filter(id=task_id, template_id=pk).first()
        if not task:
            return Response(
                {'error': 'タスクが見つかりません'},
                status=status.HTTP_404_NOT_FOUND,
            )
        task.soft_delete(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OnboardingAssignmentViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    """
    オンボーディングアサインの CRUD。
    - 一般社員: 自分のアサインのみ参照可能
    - HR/管理者: 全員分参照・作成・削除可能
    """
    serializer_class = OnboardingAssignmentSerializer
    permission_classes = [IsNotCustomer]

    def get_queryset(self):
        user = self.request.user
        qs = OnboardingAssignment.objects.select_related(
            'template', 'employee', 'assigned_by'
        ).prefetch_related('task_items__template_task').all()
        if not user.is_manager:
            return qs.filter(employee__user=user)
        return qs

    def get_permissions(self):
        if self.action in ('create', 'destroy'):
            return [IsHR()]
        return [IsNotCustomer()]

    def perform_create(self, serializer):
        assigned_by = getattr(self.request.user, 'employee', None)
        assignment = serializer.save(assigned_by=assigned_by)
        # テンプレートのタスクから OnboardingTaskItem を自動生成
        for task in assignment.template.tasks.all():
            OnboardingTaskItem.objects.get_or_create(
                assignment=assignment,
                template_task=task,
            )
        # 社員にオンボーディング開始通知を送信
        Notification.send(
            user=assignment.employee.user,
            type_=Notification.NotificationType.ONBOARDING,
            title='オンボーディングが開始されました',
            message=f'「{assignment.template.name}」のタスクが割り当てられました。確認してください。',
            related_url='/onboarding',
        )

    @action(detail=False, methods=['post'], url_path='assign', permission_classes=[IsHR])
    def assign(self, request):
        """POST /api/v1/onboarding/assignments/assign/ — テンプレートを社員にアサイン"""
        template_id = request.data.get('template_id')
        employee_id = request.data.get('employee_id')
        if not template_id or not employee_id:
            return Response(
                {'error': 'template_id と employee_id が必要です'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not request.user.is_manager:
            return Response(
                {'error': '権限がありません'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = OnboardingAssignmentSerializer(
            data={'template': template_id, 'employee': employee_id}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OnboardingTaskItemViewSet(viewsets.GenericViewSet):
    """
    タスク進捗の完了/未完了操作のみ提供する軽量 ViewSet。
    complete / uncomplete アクションを PATCH で呼び出す。
    """
    serializer_class = OnboardingTaskItemSerializer
    permission_classes = [IsNotCustomer]

    def get_queryset(self):
        user = self.request.user
        if user.is_manager:
            return OnboardingTaskItem.objects.select_related(
                'assignment__employee', 'template_task'
            ).all()
        return OnboardingTaskItem.objects.filter(
            assignment__employee__user=user
        ).select_related('template_task')

    @action(detail=True, methods=['patch'], url_path='complete')
    def complete(self, request, pk=None):
        """PATCH /api/v1/onboarding/task-items/{id}/complete/ — タスク完了"""
        item = self.get_queryset().filter(id=pk).first()
        if not item:
            return Response(
                {'error': 'タスクが見つかりません'},
                status=status.HTTP_404_NOT_FOUND,
            )
        item.is_completed = True
        item.completed_at = timezone.now()
        item.save(update_fields=['is_completed', 'completed_at'])
        return Response(OnboardingTaskItemSerializer(item).data)

    @action(detail=True, methods=['patch'], url_path='uncomplete')
    def uncomplete(self, request, pk=None):
        """PATCH /api/v1/onboarding/task-items/{id}/uncomplete/ — タスク未完了に戻す"""
        item = self.get_queryset().filter(id=pk).first()
        if not item:
            return Response(
                {'error': 'タスクが見つかりません'},
                status=status.HTTP_404_NOT_FOUND,
            )
        item.is_completed = False
        item.completed_at = None
        item.save(update_fields=['is_completed', 'completed_at'])
        return Response(OnboardingTaskItemSerializer(item).data)
