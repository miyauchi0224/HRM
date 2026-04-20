from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import ApprovalRequest, ApprovalStep, ApprovalTemplate
from .serializers import ApprovalRequestSerializer, ApprovalTemplateSerializer
from apps.notifications.models import Notification
from apps.accounts.permissions import IsNotCustomer


class ApprovalTemplateViewSet(viewsets.ModelViewSet):
    queryset = ApprovalTemplate.objects.filter(is_active=True)
    serializer_class = ApprovalTemplateSerializer
    permission_classes = [IsNotCustomer]


class ApprovalRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ApprovalRequestSerializer
    permission_classes = [IsNotCustomer]

    def get_queryset(self):
        user = self.request.user
        qs = ApprovalRequest.objects.select_related('applicant', 'template').prefetch_related('steps')
        if user.is_manager:
            return qs.all()
        return qs.filter(applicant__user=user)

    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user.employee)

    @action(detail=False, methods=['post'], url_path='build-default-steps')
    def build_default_steps(self, request):
        """
        申請者の組織階層から承認ルートを自動構築して返す。
        フロー: 上司(supervisor) → 部門長(manager) → 財務(accounting)
        """
        try:
            employee = request.user.employee
        except Exception:
            return Response({'error': '社員情報が見つかりません'}, status=status.HTTP_403_FORBIDDEN)

        steps = []
        # 1. 上司（直属マネージャーの中で最初の supervisor/manager）
        for mgr in employee.managers.select_related('user').all():
            if mgr.user.role in ('supervisor', 'manager', 'hr', 'accounting', 'admin'):
                steps.append({
                    'employee_id': str(mgr.id),
                    'name': mgr.full_name,
                    'step_role': 'supervisor',
                    'order': 1,
                })
                break

        # 2. 部門長（上司の上司、または manager ロール）
        from apps.employees.models import Employee as EmployeeModel
        managers_of_managers = EmployeeModel.objects.filter(
            subordinates__in=employee.managers.all(),
            user__role__in=('manager', 'hr', 'admin'),
        ).distinct()
        for mgr in managers_of_managers:
            if not any(s['employee_id'] == str(mgr.id) for s in steps):
                steps.append({
                    'employee_id': str(mgr.id),
                    'name': mgr.full_name,
                    'step_role': 'manager',
                    'order': 2,
                })
                break

        # 3. 財務（accounting または hr ロールを持つ社員）
        accounting_emp = EmployeeModel.objects.filter(
            user__role__in=('accounting', 'hr')
        ).first()
        if accounting_emp and not any(s['employee_id'] == str(accounting_emp.id) for s in steps):
            steps.append({
                'employee_id': str(accounting_emp.id),
                'name': accounting_emp.full_name,
                'step_role': 'accounting',
                'order': 3,
            })

        return Response({'steps': steps})

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        """下書きを申請中に変更"""
        obj = self.get_object()
        if obj.status != ApprovalRequest.Status.DRAFT:
            return Response({'error': '下書きのみ申請できます'}, status=status.HTTP_400_BAD_REQUEST)
        obj.status = ApprovalRequest.Status.PENDING
        obj.submitted_at = timezone.now()
        obj.save()
        for step in obj.steps.filter(order=1):
            Notification.send(
                user=step.approver.user,
                type_=Notification.NotificationType.EXPENSE_REQUEST,
                title='稟議申請',
                message=f'{obj.applicant.full_name}さんから稟議申請「{obj.title}」が届きました',
                related_url='/approval',
            )
        return Response(ApprovalRequestSerializer(obj).data)

    @action(detail=True, methods=['patch'], url_path='decide')
    def decide(self, request, pk=None):
        """承認者が承認/却下する"""
        obj = self.get_object()
        if obj.status != ApprovalRequest.Status.PENDING:
            return Response({'error': '審査中の申請のみ操作できます'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = request.user.employee
        except Exception:
            return Response({'error': '社員情報が見つかりません'}, status=status.HTTP_403_FORBIDDEN)

        step = obj.steps.filter(approver=employee, decision=ApprovalStep.Decision.PENDING).first()
        if not step:
            return Response({'error': 'この申請の承認者ではありません'}, status=status.HTTP_403_FORBIDDEN)

        decision = request.data.get('decision', 'approved')
        step.decision = decision
        step.comment = request.data.get('comment', '')
        step.decided_at = timezone.now()
        step.save()

        if decision == 'rejected':
            obj.status = ApprovalRequest.Status.REJECTED
            obj.save()
            Notification.send(
                user=obj.applicant.user,
                type_=Notification.NotificationType.EXPENSE_REQUEST,
                title='稟議が却下されました',
                message=f'「{obj.title}」が却下されました',
                related_url='/approval',
            )
        else:
            next_step = obj.steps.filter(order=step.order + 1, decision=ApprovalStep.Decision.PENDING).first()
            if next_step:
                Notification.send(
                    user=next_step.approver.user,
                    type_=Notification.NotificationType.EXPENSE_REQUEST,
                    title='稟議承認依頼',
                    message=f'「{obj.title}」の承認をお願いします',
                    related_url='/approval',
                )
            else:
                obj.status = ApprovalRequest.Status.APPROVED
                obj.save()
                Notification.send(
                    user=obj.applicant.user,
                    type_=Notification.NotificationType.EXPENSE_REQUEST,
                    title='稟議が承認されました',
                    message=f'「{obj.title}」が承認されました',
                    related_url='/approval',
                )

        return Response(ApprovalRequestSerializer(obj).data)

    @action(detail=True, methods=['post'], url_path='withdraw')
    def withdraw(self, request, pk=None):
        """申請を取り下げる"""
        obj = self.get_object()
        if obj.applicant.user != request.user:
            return Response({'error': '申請者のみ取り下げできます'}, status=status.HTTP_403_FORBIDDEN)
        if obj.status not in [ApprovalRequest.Status.DRAFT, ApprovalRequest.Status.PENDING]:
            return Response({'error': '取り下げできないステータスです'}, status=status.HTTP_400_BAD_REQUEST)
        obj.status = ApprovalRequest.Status.WITHDRAWN
        obj.save()
        return Response(ApprovalRequestSerializer(obj).data)
