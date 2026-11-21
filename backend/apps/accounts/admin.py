from django.contrib import admin, messages

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display  = ('email', 'role', 'is_active', 'is_staff', 'failed_login_count', 'locked_until', 'last_login')
    list_filter   = ('role', 'is_active', 'is_staff')
    search_fields = ('email',)
    ordering      = ('email',)
    # 秘密情報・パスワードハッシュは管理画面に表示しない
    exclude       = ('password', 'anthropic_api_key', 'openai_api_key', 'personal_webhook_url')
    readonly_fields = ('last_login', 'password_changed_at', 'created_at', 'updated_at')
    actions       = ['unlock_accounts']

    @admin.action(description='ログインのロックを解除する')
    def unlock_accounts(self, request, queryset):
        count = queryset.update(failed_login_count=0, locked_until=None)
        self.message_user(request, f'{count} 件のロックを解除しました', messages.SUCCESS)
