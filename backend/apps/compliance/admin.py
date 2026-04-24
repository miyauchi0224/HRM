from django.contrib import admin
from .models import ComplianceChecklistSection, ComplianceChecklistItem, ComplianceChecklistProgress


class ComplianceChecklistItemInline(admin.TabularInline):
    model = ComplianceChecklistItem
    fields = ['title', 'order', 'is_critical', 'is_deleted']
    extra = 1


@admin.register(ComplianceChecklistSection)
class ComplianceChecklistSectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'item_count', 'created_at']
    list_filter = ['created_at', 'is_deleted']
    search_fields = ['title']
    ordering = ['order']
    inlines = [ComplianceChecklistItemInline]

    def item_count(self, obj):
        return obj.items.filter(is_deleted=False).count()
    item_count.short_description = '項目数'


@admin.register(ComplianceChecklistItem)
class ComplianceChecklistItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'section', 'order', 'is_critical', 'created_at']
    list_filter = ['section', 'is_critical', 'created_at', 'is_deleted']
    search_fields = ['title']
    ordering = ['section', 'order']


@admin.register(ComplianceChecklistProgress)
class ComplianceChecklistProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'item_title', 'is_completed', 'completed_at', 'updated_at']
    list_filter = ['is_completed', 'completed_at', 'is_deleted']
    search_fields = ['user__username', 'item__title']
    ordering = ['item__section', 'user']

    def item_title(self, obj):
        return f'{obj.item.section.title} - {obj.item.title}'
    item_title.short_description = '項目'
