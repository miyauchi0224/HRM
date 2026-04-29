from rest_framework import serializers
from django.conf import settings
from .models import Skill


class SkillSerializer(serializers.ModelSerializer):
    employee_name    = serializers.CharField(source='employee.full_name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    certificate_file = serializers.FileField(read_only=True)
    certificate_url  = serializers.SerializerMethodField()

    class Meta:
        model  = Skill
        fields = [
            'id', 'skill_name', 'category', 'category_display',
            'level', 'organizer', 'certified_date', 'expiry_date', 'note',
            'employee_name', 'certificate_file', 'certificate_url',
        ]
        read_only_fields = ['id', 'employee_name', 'category_display',
                            'certificate_file', 'certificate_url']

    def get_certificate_url(self, obj) -> str | None:
        if not obj.certificate_file:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.certificate_file.url)
        return obj.certificate_file.url
