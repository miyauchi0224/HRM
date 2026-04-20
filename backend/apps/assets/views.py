from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.permissions import IsHR, IsNotCustomer

from .models import Asset, AssetCategory, AssetHistory
from .serializers import AssetSerializer, AssetCategorySerializer, AssetHistorySerializer
from apps.employees.models import Employee


class AssetCategoryViewSet(viewsets.ModelViewSet):
    queryset = AssetCategory.objects.all()
    serializer_class = AssetCategorySerializer
    permission_classes = [IsNotCustomer]


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.select_related('category', 'assigned_to').prefetch_related('history').all()
    serializer_class = AssetSerializer
    permission_classes = [IsNotCustomer]

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        category_id = self.request.query_params.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs

    def get_permissions(self):
        if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return [IsHR()]
        return [IsNotCustomer()]

    @action(detail=True, methods=['post'], url_path='assign')
    def assign(self, request, pk=None):
        """資産を社員に貸出"""
        if not request.user.is_hr:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)
        asset = self.get_object()
        emp_id = request.data.get('employee_id')
        try:
            emp = Employee.objects.get(id=emp_id)
        except Employee.DoesNotExist:
            return Response({'error': '社員が見つかりません'}, status=status.HTTP_404_NOT_FOUND)

        asset.assigned_to = emp
        asset.assigned_at = timezone.now().date()
        asset.status = Asset.Status.IN_USE
        asset.save()
        AssetHistory.objects.create(
            asset=asset, event_type=AssetHistory.EventType.ASSIGNED,
            employee=emp, event_date=timezone.now().date(),
            note=request.data.get('note', ''),
        )
        return Response(AssetSerializer(asset).data)

    @action(detail=True, methods=['post'], url_path='return')
    def return_asset(self, request, pk=None):
        """資産を返却"""
        if not request.user.is_hr:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)
        asset = self.get_object()
        prev_emp = asset.assigned_to
        asset.assigned_to = None
        asset.assigned_at = None
        asset.status = Asset.Status.AVAILABLE
        asset.save()
        AssetHistory.objects.create(
            asset=asset, event_type=AssetHistory.EventType.RETURNED,
            employee=prev_emp, event_date=timezone.now().date(),
            note=request.data.get('note', ''),
        )
        return Response(AssetSerializer(asset).data)
