from rest_framework import serializers
from .models import UserCalendarToken


class UserCalendarTokenSerializer(serializers.ModelSerializer):
    provider_label = serializers.CharField(source='get_provider_display', read_only=True)

    class Meta:
        model = UserCalendarToken
        fields = ['id', 'provider', 'provider_label', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
