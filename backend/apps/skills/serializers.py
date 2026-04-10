from rest_framework import serializers
from .models import Skill


class SkillSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model  = Skill
        fields = [
            'id', 'skill_name', 'category', 'category_display',
            'level', 'certified_date', 'expiry_date', 'note',
            'employee_name',
        ]
        read_only_fields = ['id', 'employee_name', 'category_display']

    def validate_level(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError('レベルは1〜5の範囲で入力してください')
        return value
