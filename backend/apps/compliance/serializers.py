from rest_framework import serializers
from .models import ComplianceChecklistSection, ComplianceChecklistItem, ComplianceChecklistProgress


class ComplianceChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceChecklistItem
        fields = ['id', 'title', 'order', 'is_critical']


class ComplianceChecklistProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceChecklistProgress
        fields = ['id', 'item', 'is_completed', 'completed_at', 'notes']


class ComplianceChecklistSectionDetailSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    progress_rate = serializers.SerializerMethodField()

    class Meta:
        model = ComplianceChecklistSection
        fields = ['id', 'title', 'order', 'items', 'progress_rate']

    def get_items(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        items = obj.items.filter(is_deleted=False).order_by('order')

        result = []
        for item in items:
            item_data = ComplianceChecklistItemSerializer(item).data

            if user and user.is_authenticated:
                try:
                    progress = ComplianceChecklistProgress.objects.get(user=user, item=item)
                    item_data['is_completed'] = progress.is_completed
                    item_data['completed_at'] = progress.completed_at
                    item_data['notes'] = progress.notes
                except ComplianceChecklistProgress.DoesNotExist:
                    item_data['is_completed'] = False
                    item_data['completed_at'] = None
                    item_data['notes'] = ''

            result.append(item_data)
        return result

    def get_progress_rate(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None

        if not user or not user.is_authenticated:
            return 0

        items = obj.items.filter(is_deleted=False)
        if not items.exists():
            return 0

        completed = ComplianceChecklistProgress.objects.filter(
            user=user,
            item__in=items,
            is_completed=True
        ).count()

        return round((completed / items.count()) * 100, 1)


class ComplianceChecklistSectionListSerializer(serializers.ModelSerializer):
    progress_rate = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    completed_count = serializers.SerializerMethodField()

    class Meta:
        model = ComplianceChecklistSection
        fields = ['id', 'title', 'order', 'item_count', 'completed_count', 'progress_rate']

    def get_item_count(self, obj):
        return obj.items.filter(is_deleted=False).count()

    def get_completed_count(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None

        if not user or not user.is_authenticated:
            return 0

        return ComplianceChecklistProgress.objects.filter(
            user=user,
            item__section=obj,
            is_completed=True
        ).count()

    def get_progress_rate(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None

        if not user or not user.is_authenticated:
            return 0

        items = obj.items.filter(is_deleted=False)
        if not items.exists():
            return 0

        completed = ComplianceChecklistProgress.objects.filter(
            user=user,
            item__in=items,
            is_completed=True
        ).count()

        return round((completed / items.count()) * 100, 1)
