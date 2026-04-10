from rest_framework import serializers
from .models import Employee, EmergencyContact, FamilyMember
from apps.accounts.models import User


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EmergencyContact
        fields = ['id', 'name', 'relationship', 'phone', 'sort_order']


class FamilyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FamilyMember
        fields = ['id', 'name', 'relationship', 'birth_date', 'is_dependent']


class EmployeeListSerializer(serializers.ModelSerializer):
    """一覧用（軽量）"""
    class Meta:
        model  = Employee
        fields = ['id', 'employee_number', 'last_name', 'first_name',
                  'department', 'position', 'grade', 'hire_date', 'retire_date']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['full_name']  = instance.full_name
        data['is_active']  = instance.retire_date is None
        return data


class EmployeeDetailSerializer(serializers.ModelSerializer):
    """詳細用"""
    emergency_contacts = EmergencyContactSerializer(many=True, read_only=True)
    family_members     = FamilyMemberSerializer(many=True, read_only=True)
    email              = serializers.EmailField(source='user.email', read_only=True)
    role               = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model  = Employee
        fields = [
            'id', 'employee_number', 'last_name', 'first_name',
            'last_name_kana', 'first_name_kana', 'birth_date', 'gender',
            'hire_date', 'retire_date', 'department', 'position', 'grade',
            'employment_type', 'phone', 'personal_email',
            'email', 'role', 'emergency_contacts', 'family_members',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CreateEmployeeSerializer(serializers.Serializer):
    """社員＋Userアカウントの同時作成用"""
    email           = serializers.EmailField()
    employee_number = serializers.CharField(max_length=20)
    last_name       = serializers.CharField(max_length=50)
    first_name      = serializers.CharField(max_length=50)
    last_name_kana  = serializers.CharField(max_length=50)
    first_name_kana = serializers.CharField(max_length=50)
    birth_date      = serializers.DateField()
    gender          = serializers.ChoiceField(choices=Employee.Gender.choices)
    hire_date       = serializers.DateField()
    department      = serializers.CharField(max_length=100)
    position        = serializers.CharField(max_length=100)
    grade           = serializers.IntegerField(default=1)
    employment_type = serializers.ChoiceField(choices=Employee.EmploymentType.choices,
                                              default=Employee.EmploymentType.FULL_TIME)
    role            = serializers.ChoiceField(choices=User.Role.choices, default=User.Role.EMPLOYEE)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('このメールアドレスは既に使用されています')
        return value

    def validate_employee_number(self, value):
        if Employee.objects.filter(employee_number=value).exists():
            raise serializers.ValidationError('この社員番号は既に使用されています')
        return value
