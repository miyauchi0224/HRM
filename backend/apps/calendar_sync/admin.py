from django.contrib import admin
from .models import UserCalendarToken


@admin.register(UserCalendarToken)
class UserCalendarTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'created_at', 'updated_at')
    list_filter = ('provider', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
