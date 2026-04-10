from django.contrib import admin
from .models import Skill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'skill_name', 'category', 'level', 'expiry_date']
    list_filter   = ['category', 'level']
    search_fields = ['skill_name', 'employee__last_name']
