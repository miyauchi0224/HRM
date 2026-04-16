import csv
import io
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import HttpResponse
from django.utils import timezone

from .models import AccountItem, ExpenseRequest
from .serializers import AccountItemSerializer, ExpenseRequestSerializer
from apps.notifications.models import Notification


class IsHR(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_hr


class AccountItemViewSet(viewsets.ModelViewSet):
    queryset           = AccountItem.objects.filter(is_active=True)
    serializer_class   = AccountItemSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return [IsHR()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='export-csv')
    def export_csv(self, request):
        """
        GET /api/v1/expense/account-items/export-csv/
        勘定科目マスタを CSV でダウンロード
        """
        items = AccountItem.objects.all().order_by('code')
        buf   = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(['科目コード', '科目名', 'カテゴリ', '有効'])
        for item in items:
            writer.writerow([item.code, item.name, item.get_category_display(), '○' if item.is_active else '×'])

        response = HttpResponse(buf.getvalue(), content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="account_items.csv"'
        return response

    @action(detail=False, methods=['post'], url_path='import-csv',
            parser_classes=[MultiPartParser, FormParser])
    def import_csv(self, request):
        """
        POST /api/v1/expense/account-items/import-csv/
        CSV ファイルをアップロードして勘定科目を一括更新
        CSVフォーマット: 科目コード,科目名,カテゴリコード,有効(true/false)
        """
        if not request.user.is_hr:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)

        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'ファイルが指定されていません'}, status=status.HTTP_400_BAD_REQUEST)

        # カテゴリコードの逆引きマップ
        category_map = {v: k for k, v in AccountItem.Category.choices}
        # 表示名でも対応
        category_display_map = {v: k for k, v in AccountItem.Category.choices}

        decoded   = file.read().decode('utf-8-sig')
        reader    = csv.DictReader(io.StringIO(decoded))
        created   = 0
        updated   = 0
        errors    = []

        for i, row in enumerate(reader, start=2):  # 2行目から（1行目はヘッダー）
            try:
                code     = row.get('科目コード', '').strip()
                name     = row.get('科目名', '').strip()
                category = row.get('カテゴリ', '').strip()
                is_active = row.get('有効', 'true').strip().lower() not in ('false', '×', '0', 'no')

                if not code or not name:
                    errors.append(f'行{i}: 科目コードと科目名は必須です')
                    continue

                # カテゴリを解決（コードまたは表示名）
                cat_key = category_map.get(category) or category
                valid_cats = [k for k, _ in AccountItem.Category.choices]
                if cat_key not in valid_cats:
                    cat_key = 'other'

                obj, is_created = AccountItem.objects.update_or_create(
                    code=code,
                    defaults={'name': name, 'category': cat_key, 'is_active': is_active}
                )
                if is_created:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                errors.append(f'行{i}: {str(e)}')

        return Response({
            'created': created,
            'updated': updated,
            'errors':  errors,
        })


class ExpenseRequestViewSet(viewsets.ModelViewSet):
    serializer_class   = ExpenseRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_manager:
            return ExpenseRequest.objects.select_related(
                'applicant', 'approver', 'account_item'
            ).all()
        return ExpenseRequest.objects.filter(applicant__user=user).select_related(
            'applicant', 'approver', 'account_item'
        )

    def perform_create(self, serializer):
        employee = self.request.user.employee
        req = serializer.save(applicant=employee)
        for manager in employee.managers.all():
            Notification.send(
                user=manager.user,
                type_=Notification.NotificationType.EXPENSE_REQUEST,
                title='経費申請',
                message=f'{employee.full_name}さんから経費申請が届きました（¥{req.amount:,}）',
                related_url='/expense',
            )

    @action(detail=True, methods=['patch'], url_path='approve')
    def approve(self, request, pk=None):
        """PATCH /api/v1/expense/requests/{id}/approve/"""
        if not request.user.is_manager:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)

        req = self.get_object()
        if req.status != ExpenseRequest.Status.PENDING:
            return Response({'error': '申請中の記録のみ操作できます'}, status=status.HTTP_400_BAD_REQUEST)

        action_type = request.data.get('action', 'approve')
        if action_type == 'approve':
            req.status      = ExpenseRequest.Status.APPROVED
            req.approver    = request.user.employee
            req.approved_at = timezone.now()
            msg = '経費申請が承認されました'
        else:
            req.status          = ExpenseRequest.Status.REJECTED
            req.rejected_reason = request.data.get('rejected_reason', '')
            msg = '経費申請が却下されました'

        req.save()
        Notification.send(
            user=req.applicant.user,
            type_=Notification.NotificationType.EXPENSE_REQUEST,
            title=msg,
            message=f'¥{req.amount:,}の経費申請が{"承認" if action_type == "approve" else "却下"}されました',
            related_url='/expense',
        )
        return Response(ExpenseRequestSerializer(req).data)
