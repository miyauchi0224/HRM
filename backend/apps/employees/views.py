import csv
import io
import secrets
from datetime import date

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from apps.accounts.permissions import IsNotCustomer, IsHR
from .models import Employee, EmergencyContact
from .serializers import (
    EmployeeListSerializer, EmployeeDetailSerializer, CreateEmployeeSerializer,
    EmergencyContactSerializer,
)
from apps.accounts.models import User
from apps.common.mixins import SoftDeleteViewSetMixin


class IsHROrAdmin(IsHR):
    """IsHR と同義（共通パーミッションクラスを再利用）"""


class EmployeeViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    permission_classes = [IsNotCustomer]

    def get_queryset(self):
        user  = self.request.user
        qs    = Employee.objects.select_related('user').prefetch_related(
            'emergency_contacts', 'family_members'
        )
        # 社員は自分のみ参照可
        if not user.is_manager:
            return qs.filter(user=user)
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        if self.action == 'create':
            return CreateEmployeeSerializer
        return EmployeeDetailSerializer

    def get_permissions(self):
        if self.action in ('create', 'destroy'):
            return [IsHROrAdmin()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """社員＋Userアカウントを同時作成（管理者・人事のみ）"""
        if not request.user.is_hr:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)

        serializer = CreateEmployeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        # User作成（仮パスワードを発行）
        import secrets
        temp_password = secrets.token_urlsafe(12)
        user = User.objects.create_user(
            email=d['email'],
            password=temp_password,
            role=d['role'],
        )
        # Employee作成
        Employee.objects.create(
            user=user,
            employee_number=d['employee_number'],
            last_name=d['last_name'],
            first_name=d['first_name'],
            last_name_kana=d['last_name_kana'],
            first_name_kana=d['first_name_kana'],
            birth_date=d['birth_date'],
            gender=d['gender'],
            hire_date=d['hire_date'],
            department=d['department'],
            position=d['position'],
            grade=d['grade'],
            employment_type=d['employment_type'],
        )
        return Response({
            'message': f'社員アカウントを作成しました',
            'email': user.email,
            'temp_password': temp_password,  # 初回ログイン後に変更を促す
        }, status=status.HTTP_201_CREATED)

    def _can_edit_employee(self, request, employee):
        """本人または管理職・人事・管理者のみ編集可"""
        return employee.user == request.user or request.user.is_manager

    @action(detail=True, methods=['patch'], url_path='update-phone')
    def update_phone(self, request, pk=None):
        """電話番号の更新（本人 or 管理職以上）"""
        emp = self.get_object()
        if not self._can_edit_employee(request, emp):
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)
        phone = request.data.get('phone', '').strip()
        emp.phone = phone
        emp.save(update_fields=['phone'])
        return Response({'phone': emp.phone})

    @action(detail=True, methods=['get', 'post'], url_path='emergency-contacts')
    def emergency_contacts(self, request, pk=None):
        emp = self.get_object()
        if request.method == 'GET':
            contacts = emp.emergency_contacts.order_by('sort_order')
            return Response(EmergencyContactSerializer(contacts, many=True).data)

        # POST: 新規追加
        if not self._can_edit_employee(request, emp):
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)
        serializer = EmergencyContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = EmergencyContact.objects.create(
            employee=emp,
            name=serializer.validated_data['name'],
            relationship=serializer.validated_data['relationship'],
            phone=serializer.validated_data['phone'],
            sort_order=emp.emergency_contacts.count(),
        )
        return Response(EmergencyContactSerializer(contact).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch', 'delete'],
            url_path=r'emergency-contacts/(?P<contact_id>[^/.]+)')
    def emergency_contact_detail(self, request, pk=None, contact_id=None):
        emp = self.get_object()
        if not self._can_edit_employee(request, emp):
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)
        contact = get_object_or_404(EmergencyContact, id=contact_id, employee=emp)

        if request.method == 'DELETE':
            contact.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        # PATCH
        serializer = EmergencyContactSerializer(contact, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='upload-avatar',
            parser_classes=[MultiPartParser, FormParser])
    def upload_avatar(self, request, pk=None):
        """
        POST /api/v1/employees/{id}/upload-avatar/
        アバター画像をアップロード（本人 or 管理職以上）
        """
        emp = self.get_object()
        if not self._can_edit_employee(request, emp):
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)

        file = request.FILES.get('avatar')
        if not file:
            return Response({'error': 'ファイルが指定されていません'}, status=status.HTTP_400_BAD_REQUEST)

        # 既存アバターを削除
        if emp.avatar:
            emp.avatar.delete(save=False)

        emp.avatar = file
        emp.save(update_fields=['avatar'])

        avatar_url = request.build_absolute_uri(emp.avatar.url) if emp.avatar else None
        return Response({'avatar_url': avatar_url})

    @action(detail=False, methods=['get'], url_path='template-csv')
    def template_csv(self, request):
        """
        GET /api/v1/employees/template-csv/
        社員一括登録用 CSV テンプレートをダウンロード（人事以上のみ）
        """
        if not request.user.is_hr:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            '社員番号', '姓', '名', '姓（カナ）', '名（カナ）',
            'メールアドレス', 'ロール', '生年月日', '性別',
            '入社日', '退職日', '雇用形態',
            '部署', '役職', '等級',
            '電話番号', '個人メール',
            '郵便番号', '住所', '最寄り駅',
            '勤務先名', '勤務先住所', '勤務先電話番号', '通勤経路',
            '銀行名', '支店名', '口座種別', '口座番号', '口座名義',
        ])
        # サンプル行1（必須項目のみ）
        writer.writerow([
            'EMP001', '山田', '太郎', 'ヤマダ', 'タロウ',
            'yamada.taro@example.com', 'employee', '1990/04/01', 'male',
            '2020/04/01', '', 'full_time',
            '開発部', '主任', '3',
            '090-1234-5678', '',
            '', '', '',
            '', '', '', '',
            '', '', '', '', '',
        ])
        # サンプル行2（任意項目も含む）
        writer.writerow([
            'EMP002', '鈴木', '花子', 'スズキ', 'ハナコ',
            'suzuki.hanako@example.com', 'employee', '1995/08/15', 'female',
            '2021/10/01', '', 'part_time',
            '営業部', '係員', '1',
            '080-9876-5432', 'suzuki.personal@example.com',
            '100-0001', '東京都千代田区1-1', '東京駅',
            '株式会社〇〇', '東京都渋谷区1-1', '03-1234-5678', 'JR山手線 渋谷駅 徒歩5分',
            '三菱UFJ銀行', '渋谷支店', '普通', '1234567', 'スズキ ハナコ',
        ])

        response = HttpResponse(buf.getvalue(), content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="employees_upload_template.csv"'
        return response

    @action(detail=False, methods=['post'], url_path='import-csv',
            parser_classes=[MultiPartParser, FormParser])
    def import_csv(self, request):
        """
        POST /api/v1/employees/import-csv/
        社員を CSV で一括登録（人事以上のみ）

        CSVフォーマット: テンプレートの列順に従う
        成功した行はアカウント作成、失敗した行はエラーとして返す。
        仮パスワードは自動生成し、レスポンスに含める（初回ログイン後に変更を促す）。

        対応するロール値: employee / supervisor / manager / hr / accounting / customer / admin
        対応する性別値:   male / female / other
        対応する雇用形態: full_time / part_time / contract / dispatch
        日付フォーマット: YYYY/MM/DD または YYYY-MM-DD
        """
        if not request.user.is_hr:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)

        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'ファイルが指定されていません'}, status=status.HTTP_400_BAD_REQUEST)

        decoded = file.read().decode('utf-8-sig')
        reader  = csv.DictReader(io.StringIO(decoded))

        created = []
        errors  = []

        valid_roles   = [c[0] for c in User.Role.choices]
        valid_genders = [c[0] for c in Employee.Gender.choices]
        valid_emp_types = [c[0] for c in Employee.EmploymentType.choices]

        def parse_date(val):
            if not val or not val.strip():
                return None
            val = val.strip().replace('/', '-')
            try:
                return date.fromisoformat(val)
            except ValueError:
                raise ValueError(f'日付の形式が正しくありません（例: 1990/04/01）: {val}')

        for i, row in enumerate(reader, start=2):  # 2行目から（1行目はヘッダー）
            try:
                # ─── 必須項目チェック ───
                required = ['社員番号', '姓', '名', '姓（カナ）', '名（カナ）',
                            'メールアドレス', '生年月日', '性別', '入社日',
                            '雇用形態', '部署', '役職']
                for field in required:
                    if not row.get(field, '').strip():
                        raise ValueError(f'「{field}」は必須項目です')

                employee_number = row['社員番号'].strip()
                email           = row['メールアドレス'].strip()
                role            = row.get('ロール', 'employee').strip() or 'employee'
                gender          = row['性別'].strip()
                emp_type        = row['雇用形態'].strip()

                # ─── 値の検証 ───
                if role not in valid_roles:
                    raise ValueError(f'ロールの値が無効です（{role}）。使用可能: {", ".join(valid_roles)}')
                if gender not in valid_genders:
                    raise ValueError(f'性別の値が無効です（{gender}）。使用可能: male / female / other')
                if emp_type not in valid_emp_types:
                    raise ValueError(f'雇用形態の値が無効です（{emp_type}）。使用可能: full_time / part_time / contract / dispatch')

                if User.objects.filter(email=email).exists():
                    raise ValueError(f'メールアドレスが既に使用されています: {email}')
                if Employee.objects.filter(employee_number=employee_number).exists():
                    raise ValueError(f'社員番号が既に使用されています: {employee_number}')

                birth_date  = parse_date(row['生年月日'])
                hire_date   = parse_date(row['入社日'])
                retire_date = parse_date(row.get('退職日'))

                # ─── 作成 ───
                temp_password = secrets.token_urlsafe(12)
                user = User.objects.create_user(email=email, password=temp_password, role=role)

                Employee.objects.create(
                    user             = user,
                    employee_number  = employee_number,
                    last_name        = row['姓'].strip(),
                    first_name       = row['名'].strip(),
                    last_name_kana   = row['姓（カナ）'].strip(),
                    first_name_kana  = row['名（カナ）'].strip(),
                    birth_date       = birth_date,
                    gender           = gender,
                    hire_date        = hire_date,
                    retire_date      = retire_date,
                    employment_type  = emp_type,
                    department       = row['部署'].strip(),
                    position         = row['役職'].strip(),
                    grade            = int(row.get('等級', '1').strip() or '1'),
                    phone            = row.get('電話番号', '').strip(),
                    personal_email   = row.get('個人メール', '').strip(),
                    zip_code         = row.get('郵便番号', '').strip(),
                    address          = row.get('住所', '').strip(),
                    nearest_station  = row.get('最寄り駅', '').strip(),
                    workplace_name   = row.get('勤務先名', '').strip(),
                    workplace_address= row.get('勤務先住所', '').strip(),
                    workplace_phone  = row.get('勤務先電話番号', '').strip(),
                    commute_route    = row.get('通勤経路', '').strip(),
                    bank_name        = row.get('銀行名', '').strip(),
                    bank_branch      = row.get('支店名', '').strip(),
                    bank_account_type= row.get('口座種別', '').strip(),
                    bank_account_number = row.get('口座番号', '').strip(),
                    bank_account_holder = row.get('口座名義', '').strip(),
                )

                created.append({
                    'row':           i,
                    'employee_number': employee_number,
                    'name':          f'{row["姓"]} {row["名"]}',
                    'email':         email,
                    'temp_password': temp_password,
                })

            except Exception as e:
                errors.append({'row': i, 'error': str(e)})

        return Response({
            'created': len(created),
            'errors':  len(errors),
            'results': created,
            'error_details': errors,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='org-chart')
    def org_chart(self, request):
        """GET /api/v1/employees/org-chart/ - 組織図データ"""
        employees = Employee.objects.prefetch_related('managers', 'subordinates').all()
        data = []
        for emp in employees:
            data.append({
                'id':           str(emp.id),
                'full_name':    emp.full_name,
                'department':   emp.department,
                'position':     emp.position,
                'manager_ids':  [str(m.id) for m in emp.managers.all()],
            })
        return Response(data)
