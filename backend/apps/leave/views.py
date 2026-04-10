from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .models import LeaveBalance, LeaveRequest
from .serializers import LeaveBalanceSerializer, LeaveRequestSerializer
from apps.notifications.models import Notification


class LeaveBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = LeaveBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_manager:
            emp_id = self.request.query_params.get('employee_id')
            if emp_id:
                return LeaveBalance.objects.filter(employee_id=emp_id)
            return LeaveBalance.objects.all()
        return LeaveBalance.objects.filter(employee__user=user)


class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class   = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_manager:
            return LeaveRequest.objects.select_related('employee', 'approver').all()
        return LeaveRequest.objects.filter(employee__user=user)

    def perform_create(self, serializer):
        employee = self.request.user.employee
        req = serializer.save(employee=employee)
        # 上司へ通知
        for manager in employee.managers.all():
            Notification.send(
                user=manager.user,
                type_=Notification.NotificationType.LEAVE_REQUEST,
                title='休暇申請',
                message=f'{employee.full_name}さんから休暇申請が届きました（{req.start_date}〜{req.end_date}）',
                related_url='/leave',
            )

    @action(detail=True, methods=['patch'], url_path='approve')
    def approve(self, request, pk=None):
        """PATCH /api/v1/leave/requests/{id}/approve/"""
        if not request.user.is_manager:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)

        req = self.get_object()
        if req.status != LeaveRequest.Status.PENDING:
            return Response({'error': '申請中の記録のみ操作できます'}, status=status.HTTP_400_BAD_REQUEST)

        action_type = request.data.get('action', 'approve')
        if action_type == 'approve':
            req.status      = LeaveRequest.Status.APPROVED
            req.approver    = request.user.employee
            req.approved_at = timezone.now()
            req.save()
            # 有給の場合は残日数を更新
            if req.leave_type == LeaveRequest.LeaveType.ANNUAL:
                from django.db.models import F
                import datetime
                fiscal_year = req.start_date.year if req.start_date.month >= 4 else req.start_date.year - 1
                LeaveBalance.objects.filter(
                    employee=req.employee, fiscal_year=fiscal_year
                ).update(used_days=F('used_days') + req.days)
            msg = '休暇申請が承認されました'
        else:
            req.status = LeaveRequest.Status.REJECTED
            req.save()
            msg = '休暇申請が却下されました'

        Notification.send(
            user=req.employee.user,
            type_=Notification.NotificationType.LEAVE_REQUEST,
            title=msg,
            message=f'{req.start_date}〜{req.end_date}の休暇申請が{"承認" if action_type == "approve" else "却下"}されました',
            related_url='/leave',
        )
        return Response(LeaveRequestSerializer(req).data)

    @action(detail=True, methods=['patch'], url_path='cancel')
    def cancel(self, request, pk=None):
        """PATCH /api/v1/leave/requests/{id}/cancel/"""
        req = self.get_object()
        if req.employee.user != request.user:
            return Response({'error': '自分の申請のみ取り消せます'}, status=status.HTTP_403_FORBIDDEN)
        if req.status not in (LeaveRequest.Status.PENDING, LeaveRequest.Status.APPROVED):
            return Response({'error': 'この申請は取り消せません'}, status=status.HTTP_400_BAD_REQUEST)

        # 承認済みで有給の場合は残日数を戻す
        if req.status == LeaveRequest.Status.APPROVED and req.leave_type == LeaveRequest.LeaveType.ANNUAL:
            from django.db.models import F
            fiscal_year = req.start_date.year if req.start_date.month >= 4 else req.start_date.year - 1
            LeaveBalance.objects.filter(
                employee=req.employee, fiscal_year=fiscal_year
            ).update(used_days=F('used_days') - req.days)

        req.status = LeaveRequest.Status.CANCELLED
        req.save()
        return Response(LeaveRequestSerializer(req).data)
