from rest_framework import serializers
from .models import Asset, AssetCategory, AssetHistory


class AssetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetCategory
        fields = '__all__'


class AssetHistorySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = AssetHistory
        fields = '__all__'


class AssetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.full_name', read_only=True)
    history = AssetHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Asset
        fields = '__all__'
