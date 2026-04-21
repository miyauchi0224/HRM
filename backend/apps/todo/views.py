from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from apps.accounts.permissions import IsNotCustomer
from rest_framework.response import Response

from .models import TodoItem, DailyReport
from .serializers import TodoItemSerializer, DailyReportSerializer
from apps.common.mixins import SoftDeleteViewSetMixin


class TodoItemViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class   = TodoItemSerializer
    permission_classes = [IsNotCustomer]

    def get_queryset(self):
        return TodoItem.objects.filter(
            employee__user=self.request.user
        ).select_related('project')

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user.employee)

    @action(detail=True, methods=['patch'], url_path='move')
    def move(self, request, pk=None):
        """ステータス変更（カンバン移動）"""
        item = self.get_object()
        new_status = request.data.get('status')
        if new_status not in [c[0] for c in TodoItem.Status.choices]:
            return Response({'error': '無効なステータスです'}, status=status.HTTP_400_BAD_REQUEST)
        item.status = new_status
        item.save()
        return Response(TodoItemSerializer(item).data)


class DailyReportViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    """
    日報 CRUD
    GET  /api/v1/todo/daily-reports/           一覧（自分の日報）
    POST /api/v1/todo/daily-reports/           作成
    PATCH /api/v1/todo/daily-reports/{id}/     更新
    PATCH /api/v1/todo/daily-reports/{id}/submit/  提出
    """
    serializer_class   = DailyReportSerializer
    permission_classes = [IsNotCustomer]

    def get_queryset(self):
        qs = DailyReport.objects.filter(employee__user=self.request.user)
        date = self.request.query_params.get('date')
        if date:
            qs = qs.filter(report_date=date)
        return qs

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user.employee)

    @action(detail=True, methods=['patch'], url_path='submit')
    def submit(self, request, pk=None):
        """日報を提出済みに変更"""
        report = self.get_object()
        report.status = DailyReport.Status.SUBMITTED
        report.save()
        return Response(DailyReportSerializer(report).data)
