import csv
import io
from datetime import date
from django.utils import timezone
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
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

    @action(detail=False, methods=['get'], url_path='template-csv', permission_classes=[IsHR])
    def template_csv(self, request):
        """GET /api/v1/assets/items/template-csv/ — CSVテンプレートダウンロード"""
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            '資産番号', '資産名', 'カテゴリ名', 'メーカー', '型番',
            'シリアル番号', '購入日(YYYY-MM-DD)', '購入金額(円)', '保管場所', '備考'
        ])
        # サンプル行
        writer.writerow(['PC-001', 'ノートPC', 'PC・周辺機器', 'Dell', 'Latitude 5540',
                         'SN123456', date.today().strftime('%Y-%m-%d'), '150000', '東京オフィス', ''])
        writer.writerow(['PHONE-001', 'スマートフォン', 'スマートフォン', 'Apple', 'iPhone 15',
                         'IPHONE001', date.today().strftime('%Y-%m-%d'), '130000', '倉庫', '社用端末'])
        response = HttpResponse(buf.getvalue(), content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="asset_template.csv"'
        return response

    @action(detail=False, methods=['post'], url_path='import-csv',
            parser_classes=[MultiPartParser, FormParser], permission_classes=[IsHR])
    def import_csv(self, request):
        """POST /api/v1/assets/items/import-csv/ — CSV一括登録"""
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'ファイルが必要です'}, status=status.HTTP_400_BAD_REQUEST)

        decoded = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded))
        created = 0
        updated = 0
        errors = []

        for i, row in enumerate(reader, start=2):
            try:
                asset_number = row.get('資産番号', '').strip()
                name = row.get('資産名', '').strip()
                if not asset_number or not name:
                    raise ValueError('資産番号と資産名は必須です')

                category_name = row.get('カテゴリ名', '').strip()
                category = None
                if category_name:
                    category, _ = AssetCategory.objects.get_or_create(name=category_name)

                purchase_date_str = row.get('購入日(YYYY-MM-DD)', '').strip()
                purchase_date = None
                if purchase_date_str:
                    try:
                        purchase_date = date.fromisoformat(purchase_date_str)
                    except ValueError:
                        pass

                price_str = row.get('購入金額(円)', '').strip().replace(',', '')
                purchase_price = int(price_str) if price_str.isdigit() else None

                obj, is_created = Asset.objects.update_or_create(
                    asset_number=asset_number,
                    defaults={
                        'name': name,
                        'category': category,
                        'manufacturer': row.get('メーカー', '').strip(),
                        'model': row.get('型番', '').strip(),
                        'serial_number': row.get('シリアル番号', '').strip(),
                        'purchase_date': purchase_date,
                        'purchase_price': purchase_price,
                        'location': row.get('保管場所', '').strip(),
                        'note': row.get('備考', '').strip(),
                    }
                )
                if is_created:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                errors.append({'row': i, 'error': str(e)})

        return Response({'created': created, 'updated': updated, 'errors': errors})

    @action(detail=False, methods=['post'], url_path='delete-csv',
            parser_classes=[MultiPartParser, FormParser], permission_classes=[IsHR])
    def delete_csv(self, request):
        """POST /api/v1/assets/items/delete-csv/ — CSV一括削除（資産番号指定）"""
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'ファイルが必要です'}, status=status.HTTP_400_BAD_REQUEST)

        decoded = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded))
        deleted = 0
        not_found = []

        for row in reader:
            asset_number = row.get('資産番号', '').strip()
            if not asset_number:
                continue
            qs = Asset.objects.filter(asset_number=asset_number)
            if qs.exists():
                qs.delete()
                deleted += 1
            else:
                not_found.append(asset_number)

        return Response({'deleted': deleted, 'not_found': not_found})

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
