import csv
import io
from datetime import date

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from apps.accounts.permissions import IsNotCustomer, IsAccounting
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import HttpResponse
from django.utils import timezone

from .models import AccountItem, ExpenseRequest
from .serializers import AccountItemSerializer, ExpenseRequestSerializer
from apps.notifications.models import Notification
from apps.employees.models import Employee
from apps.common.mixins import SoftDeleteViewSetMixin


class AccountItemViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    """勘定科目マスタ：参照は社員以上、編集は経理以上"""
    queryset           = AccountItem.objects.filter(is_active=True)
    serializer_class   = AccountItemSerializer
    permission_classes = [IsNotCustomer]

    def get_permissions(self):
        if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return [IsAccounting()]
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


class ExpenseRequestViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class   = ExpenseRequestSerializer
    permission_classes = [IsNotCustomer]

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
        if not request.user.is_supervisor:
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

    @action(detail=False, methods=['get'], url_path='template-csv',
            permission_classes=[IsAccounting])
    def template_csv(self, request):
        """
        GET /api/v1/expense/requests/template-csv/
        経費申請一括登録用 CSV テンプレートをダウンロード（経理・人事・管理者のみ）
        """
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            '社員番号', '経費区分', '支払方法', '勘定科目コード',
            '金額', '費用発生日', '内容説明', '領収書URL',
        ])
        # 選択肢の説明コメント行
        writer.writerow([
            '# 経費区分: transportation（交通費）/ general（一般経費）',
            '# 支払方法: reimbursement（立替払い）/ advance（先払い申請）',
            '# 勘定科目コード: /api/v1/expense/account-items/ で確認',
            '', '', '', '', '',
        ])
        # サンプル行
        today = date.today()
        writer.writerow([
            'EMP001', 'transportation', 'reimbursement', '1002',
            '2500', today.strftime('%Y/%m/%d'), '客先への交通費（渋谷→新宿）', '',
        ])
        writer.writerow([
            'EMP001', 'general', 'reimbursement', '1001',
            '5000', today.strftime('%Y/%m/%d'), 'チームランチ代（接待）', '',
        ])
        writer.writerow([
            'EMP002', 'transportation', 'advance', '1002',
            '15000', today.strftime('%Y/%m/%d'), '出張 東京→大阪（新幹線）',
            'https://example.com/receipt/123.pdf',
        ])
        response = HttpResponse(buf.getvalue(), content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="expense_upload_template.csv"'
        return response

    @action(detail=False, methods=['post'], url_path='import-csv',
            parser_classes=[MultiPartParser, FormParser],
            permission_classes=[IsAccounting])
    def import_csv(self, request):
        """
        POST /api/v1/expense/requests/import-csv/
        経費申請を CSV で一括登録（経理・人事・管理者のみ）

        各行を個別の経費申請として登録する（status=pending で作成）。
        勘定科目コードは AccountItem.code で検索する。
        """
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'ファイルが指定されていません'}, status=status.HTTP_400_BAD_REQUEST)

        decoded = file.read().decode('utf-8-sig')
        reader  = csv.DictReader(io.StringIO(decoded))

        valid_expense_types = [c[0] for c in ExpenseRequest.ExpenseType.choices]
        valid_payment_types = [c[0] for c in ExpenseRequest.PaymentType.choices]

        created = 0
        errors  = []

        for i, row in enumerate(reader, start=2):
            # コメント行をスキップ
            emp_number = row.get('社員番号', '').strip()
            if not emp_number or emp_number.startswith('#'):
                continue
            try:
                expense_type = row.get('経費区分', '').strip()
                payment_type = row.get('支払方法', '').strip()
                account_code = row.get('勘定科目コード', '').strip()
                amount_str   = row.get('金額', '').strip().replace(',', '')
                expense_date_str = row.get('費用発生日', '').strip()
                description  = row.get('内容説明', '').strip()
                receipt_url  = row.get('領収書URL', '').strip()

                # 必須チェック
                if not all([emp_number, expense_type, payment_type, account_code, amount_str, expense_date_str, description]):
                    raise ValueError('社員番号・経費区分・支払方法・勘定科目コード・金額・費用発生日・内容説明は必須です')

                if expense_type not in valid_expense_types:
                    raise ValueError(f'経費区分が無効です（{expense_type}）。transportation / general のいずれかを指定してください')
                if payment_type not in valid_payment_types:
                    raise ValueError(f'支払方法が無効です（{payment_type}）。reimbursement / advance のいずれかを指定してください')

                employee = Employee.objects.filter(employee_number=emp_number).first()
                if not employee:
                    raise ValueError(f'社員番号が見つかりません: {emp_number}')

                account_item = AccountItem.objects.filter(code=account_code, is_active=True).first()
                if not account_item:
                    raise ValueError(f'勘定科目コードが見つかりません: {account_code}')

                amount = int(amount_str)
                if amount <= 0:
                    raise ValueError(f'金額は1以上を指定してください: {amount}')

                expense_date = date.fromisoformat(expense_date_str.replace('/', '-'))

                ExpenseRequest.objects.create(
                    applicant    = employee,
                    account_item = account_item,
                    expense_type = expense_type,
                    payment_type = payment_type,
                    amount       = amount,
                    expense_date = expense_date,
                    description  = description,
                    receipt_url  = receipt_url,
                    status       = ExpenseRequest.Status.PENDING,
                )
                created += 1

            except Exception as e:
                errors.append({'row': i, 'error': str(e)})

        return Response({
            'created': created,
            'errors':  len(errors),
            'error_details': errors,
        })
