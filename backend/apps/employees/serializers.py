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
                  'department', 'position', 'grade', 'hire_date', 'retire_date', 'avatar']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['full_name']   = instance.full_name
        data['is_active']   = instance.retire_date is None
        data['avatar_url']  = self._build_avatar_url(instance)
        data['user']        = {'id': str(instance.user_id), 'email': instance.user.email}
        return data

    def _build_avatar_url(self, instance):
        if not instance.avatar:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(instance.avatar.url)
        return instance.avatar.url


class EmployeeDetailSerializer(serializers.ModelSerializer):
    """詳細用"""
    emergency_contacts = EmergencyContactSerializer(many=True, read_only=True)
    family_members     = FamilyMemberSerializer(many=True, read_only=True)
    email              = serializers.EmailField(source='user.email', read_only=True)
    role               = serializers.CharField(source='user.role', read_only=True)
    roles              = serializers.ListField(source='user.roles', read_only=True)
    full_name          = serializers.CharField(read_only=True)
    is_active          = serializers.SerializerMethodField()
    avatar_url         = serializers.SerializerMethodField()

    class Meta:
        model  = Employee
        fields = [
            'id', 'employee_number', 'full_name', 'last_name', 'first_name',
            'last_name_kana', 'first_name_kana', 'birth_date', 'gender',
            'hire_date', 'retire_date', 'department', 'position', 'grade',
            'employment_type', 'phone', 'personal_email',
            'zip_code', 'address', 'nearest_station',
            'workplace_name', 'workplace_address', 'workplace_phone', 'commute_route',
            'bank_name', 'bank_branch', 'bank_account_type', 'bank_account_number', 'bank_account_holder',
            'email', 'role', 'roles', 'is_active', 'avatar_url', 'emergency_contacts', 'family_members',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'full_name', 'is_active', 'avatar_url', 'created_at', 'updated_at']

    def get_is_active(self, obj):
        return obj.retire_date is None

    def get_avatar_url(self, obj):
        if not obj.avatar:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.avatar.url)
        return obj.avatar.url


class SelfUpdateSerializer(serializers.ModelSerializer):
    """
    本人が自分のプロフィールを更新するためのシリアライザー。
    HR のみ変更すべき項目（社員番号・等級・銀行口座等）は含めない。
    緊急連絡先は別エンドポイントで管理するため read_only で返すのみ。
    """
    emergency_contacts = EmergencyContactSerializer(many=True, read_only=True)

    class Meta:
        model  = Employee
        fields = [
            'id', 'last_name', 'first_name', 'last_name_kana', 'first_name_kana',
            'phone', 'personal_email',
            'zip_code', 'address', 'nearest_station', 'commute_route',
            'emergency_contacts',
        ]
        read_only_fields = ['id']


class CreateEmployeeSerializer(serializers.Serializer):
    """社員＋Userアカウントの同時作成用"""
    email           = serializers.CharField(max_length=254, required=False, allow_blank=True)
    employee_number = serializers.CharField(max_length=20)
    last_name       = serializers.CharField(max_length=50)
    first_name      = serializers.CharField(max_length=50, required=False, allow_blank=True)
    last_name_kana  = serializers.CharField(max_length=50, required=False, allow_blank=True)
    first_name_kana = serializers.CharField(max_length=50, required=False, allow_blank=True)
    birth_date      = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    gender          = serializers.ChoiceField(choices=Employee.Gender.choices, required=False, allow_null=True)
    hire_date       = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    department      = serializers.CharField(max_length=100, required=False, allow_blank=True)
    position        = serializers.CharField(max_length=100, required=False, allow_blank=True)
    phone           = serializers.CharField(max_length=20, required=False, allow_blank=True)
    grade           = serializers.IntegerField(default=1, required=False)
    employment_type = serializers.ChoiceField(choices=Employee.EmploymentType.choices,
                                              default=Employee.EmploymentType.FULL_TIME,
                                              required=False)
    roles           = serializers.ListField(
        child=serializers.ChoiceField(choices=User.Role.choices),
        min_length=1,
        required=True,
    )

    def validate(self, data):
        from django.core.validators import validate_email as django_validate_email
        from django.core.exceptions import ValidationError as DjangoValidationError
        import re

        # 空文字の日付フィールドを None に正規化
        for field in ('birth_date', 'hire_date'):
            val = data.get(field)
            if not val:
                data[field] = None
            else:
                # YYYY-MM-DD 形式チェック
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', val):
                    raise serializers.ValidationError({field: '日付は YYYY-MM-DD 形式で入力してください'})
                from datetime import date as date_type
                try:
                    from datetime import datetime
                    data[field] = datetime.strptime(val, '%Y-%m-%d').date()
                except ValueError:
                    raise serializers.ValidationError({field: '無効な日付です'})

        # メールアドレスの正規化と検証
        email = data.get('email', '') or ''
        try:
            django_validate_email(email)
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError({'email': 'このメールアドレスは既に使用されています'})
            data['email'] = email
        except DjangoValidationError:
            data['email'] = ''  # 無効なメールは空文字に正規化（顧客の場合は後でダミー生成）

        roles = data.get('roles', [])
        is_customer = User.Role.CUSTOMER in roles

        # 顧客以外は追加の必須フィールドをチェック
        if not is_customer:
            required_fields = {
                'first_name':      '名',
                'last_name_kana':  '姓（カナ）',
                'first_name_kana': '名（カナ）',
                'birth_date':      '生年月日',
                'hire_date':       '入社日',
                'department':      '部署',
            }
            errors = {}
            for field, label in required_fields.items():
                if not data.get(field):
                    errors[field] = f'{label}は必須です'
            if not data.get('email'):
                errors['email'] = 'メールアドレスは必須です'
            if errors:
                raise serializers.ValidationError(errors)

        return data

    def validate_employee_number(self, value):
        if Employee.objects.filter(employee_number=value).exists():
            raise serializers.ValidationError('この社員番号は既に使用されています')
        return value
