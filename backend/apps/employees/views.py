from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Employee
from .serializers import (
    EmployeeListSerializer, EmployeeDetailSerializer, CreateEmployeeSerializer
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
