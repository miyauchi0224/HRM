from rest_framework import serializers
from .models import AccountItem, ExpenseRequest


class AccountItemSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AccountItem
        fields = ['id', 'code', 'name', 'category', 'is_active']


class ExpenseRequestSerializer(serializers.ModelSerializer):
    applicant_name   = serializers.CharField(source='applicant.full_name', read_only=True)
    approver_name    = serializers.CharField(source='approver.full_name', read_only=True, default=None)
    account_item_name = serializers.CharField(source='account_item.name', read_only=True)

    class Meta:
        model  = ExpenseRequest
        fields = [
            'id', 'expense_type', 'account_item', 'account_item_name',
            'amount', 'expense_date', 'description', 'receipt_url',
            'status', 'approved_at', 'created_at',
            'applicant_name', 'approver_name',
        ]
        read_only_fields = ['id', 'status', 'approved_at', 'created_at',
                            'applicant_name', 'approver_name', 'account_item_name']
