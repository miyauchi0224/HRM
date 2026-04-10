from django.contrib import admin
from .models import AccountItem, ExpenseRequest


@admin.register(AccountItem)
class AccountItemAdmin(admin.ModelAdmin):
    list_display  = ['code', 'name', 'category', 'is_active']
    list_filter   = ['category', 'is_active']
    search_fields = ['code', 'name']


@admin.register(ExpenseRequest)
class ExpenseRequestAdmin(admin.ModelAdmin):
    list_display  = ['applicant', 'expense_type', 'amount', 'expense_date', 'status']
    list_filter   = ['status', 'expense_type']
    search_fields = ['applicant__last_name', 'applicant__first_name']
