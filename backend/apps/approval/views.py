from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from django.db.models import Q

from .models import ApprovalRequest, ApprovalStep, ApprovalTemplate, ApprovalAttachment, ApprovalDelegation
from .serializers import (
    ApprovalRequestSerializer, ApprovalTemplateSerializer, ApprovalAttachmentSerializer,
    ApprovalDelegationSerializer,
)
from .delegation import can_act_for, delegators_for, notify_approvers
from apps.notifications.models import Notification
from apps.accounts.permissions import IsNotCustomer
from apps.common.mixins import SoftDeleteViewSetMixin
from apps.common.security import validate_upload, attachment_response, safe_filename


class ApprovalTemplateViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    queryset = ApprovalTemplate.objects.filter(is_active=True)
    serializer_class = ApprovalTemplateSerializer
    permission_classes = [IsNotCustomer]


class ApprovalRequestViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ApprovalRequestSerializer
    permission_classes = [IsNotCustomer]

    def get_queryset(self):
        user = self.request.user
        qs = ApprovalRequest.objects.select_related('applicant', 'template').prefetch_related('steps')
        if user.is_manager:
            return qs.all()
        # 自分の申請に加え、自分が承認者（または代理人）になっている申請も見られる
        employee   = getattr(user, 'employee', None)
        approvers  = [employee, *delegators_for(employee)] if employee else []
        return qs.filter(Q(applicant__user=user) | Q(steps__approver__in=approvers)).distinct()

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
        notify_approvers(
            [step.approver for step in obj.steps.filter(order=1).select_related('approver__user')],
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

        # 本人のステップ、または代理人として判断できるステップ（順序の早いもの）
        pending = obj.steps.filter(decision=ApprovalStep.Decision.PENDING).select_related('approver')
        step = next((s for s in pending if can_act_for(employee, s.approver)), None)
        if not step:
            return Response({'error': 'この申請の承認者ではありません'}, status=status.HTTP_403_FORBIDDEN)

        decision = request.data.get('decision', 'approved')
        step.decision = decision
        step.comment = request.data.get('comment', '')
        step.decided_at = timezone.now()
        step.decided_by = employee
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
                notify_approvers(
                    [next_step.approver],
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

        # get_queryset の prefetch（steps）は更新前のままなので取り直して返す
        obj = self.get_queryset().get(pk=obj.pk)
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

    @action(detail=True, methods=['post'], url_path='attachments',
            parser_classes=[MultiPartParser, FormParser])
    def upload_attachment(self, request, pk=None):
        """
        POST /api/v1/approval/requests/{id}/attachments/
        見積書などのファイルをアップロード
        """
        obj = self.get_object()
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'ファイルが指定されていません'}, status=status.HTTP_400_BAD_REQUEST)
        content_type = validate_upload(file)

        attach = ApprovalAttachment.objects.create(
            request      = obj,
            file         = file,
            file_name    = safe_filename(file.name),
            file_size    = file.size,
            content_type = content_type,
            uploaded_by  = request.user,
        )
        return Response(ApprovalAttachmentSerializer(attach).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='attachments/(?P<attach_id>[^/.]+)')
    def delete_attachment(self, request, pk=None, attach_id=None):
        """
        DELETE /api/v1/approval/requests/{id}/attachments/{attach_id}/
        添付ファイルを削除
        """
        obj = self.get_object()
        try:
            attach = ApprovalAttachment.objects.get(id=attach_id, request=obj)
        except ApprovalAttachment.DoesNotExist:
            return Response({'error': '添付ファイルが見つかりません'}, status=status.HTTP_404_NOT_FOUND)
        attach.file.delete(save=False)
        attach.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='attachments/(?P<attach_id>[^/.]+)/download')
    def download_attachment(self, request, pk=None, attach_id=None):
        """
        GET /api/v1/approval/requests/{id}/attachments/{attach_id}/download/
        添付ファイルをダウンロード
        """
        obj = self.get_object()
        try:
            attach = ApprovalAttachment.objects.get(id=attach_id, request=obj)
        except ApprovalAttachment.DoesNotExist:
            return Response({'error': '添付ファイルが見つかりません'}, status=status.HTTP_404_NOT_FOUND)
        return attachment_response(attach.file.open('rb'), attach.file_name)


class ApprovalDelegationViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    """
    代理承認の設定

    一覧: 自分が委任元・代理人のもの（人事は全件）
    登録: 自分を委任元として登録（人事は delegator を指定して他人の分も登録できる）
    """
    serializer_class   = ApprovalDelegationSerializer
    permission_classes = [IsNotCustomer]
    http_method_names  = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        qs = ApprovalDelegation.objects.select_related('delegator', 'delegate')
        if user.is_hr:
            return qs.all()
        return qs.filter(Q(delegator__user=user) | Q(delegate__user=user))

    def perform_create(self, serializer):
        from rest_framework.exceptions import PermissionDenied, ValidationError
        employee = getattr(self.request.user, 'employee', None)
        delegator = serializer.validated_data.get('delegator')
        if delegator is None:
            if employee is None:
                raise ValidationError({'delegator': '社員情報が登録されていません'})
            delegator = employee
        elif delegator != employee and not self.request.user.is_hr:
            raise PermissionDenied('他の社員の代理設定は人事のみ登録できます')
        if delegator.pk == serializer.validated_data['delegate'].pk:
            raise ValidationError({'delegate': '自分自身を代理人にはできません'})
        obj = serializer.save(delegator=delegator)
        Notification.send(
            user=obj.delegate.user,
            type_=Notification.NotificationType.SYSTEM,
            title='代理承認者に設定されました',
            message=f'{obj.start_date}〜{obj.end_date} の間、{obj.delegator.full_name}さんの代理で承認できます。',
            related_url='/approval/delegation',
        )

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.delegator.user != request.user and not request.user.is_hr:
            return Response({'error': '委任元本人または人事のみ削除できます'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
