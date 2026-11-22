from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'email', 'role', 'is_active']
        read_only_fields = ['id']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=12)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('現在のパスワードが正しくありません')
        return value

    def validate(self, data):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError

        user = self.context['request'].user
        new_password = data['new_password']
        if new_password == data['old_password']:
            raise serializers.ValidationError({'new_password': '現在と異なるパスワードを入力してください'})
        # settings.AUTH_PASSWORD_VALIDATORS（12文字以上・数字のみ不可・よくあるパスワード不可など）
        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})
        return data
