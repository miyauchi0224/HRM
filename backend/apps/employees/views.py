from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Employee, EmergencyContact
from .serializers import (
    EmployeeListSerializer, EmployeeDetailSerializer, CreateEmployeeSerializer,
    EmergencyContactSerializer,
)
from apps.accounts.models import User


class IsHROrAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_hr


class EmployeeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

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
