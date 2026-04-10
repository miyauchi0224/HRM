from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'email', 'role', 'is_active']
        read_only_fields = ['id']


class LoginSerializer(TokenObtainPairSerializer):
    """JWTログイン + ユーザー情報を一緒に返す"""
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data['user'] = {
            'id':        str(user.id),
            'email':     user.email,
            'role':      user.role,
            'full_name': user.employee.full_name if hasattr(user, 'employee') else user.email,
        }
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=12)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('現在のパスワードが正しくありません')
        return value
