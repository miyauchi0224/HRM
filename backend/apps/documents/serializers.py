from rest_framework import serializers
from .models import DocumentCategory, Document, DocumentFile


class DocumentCategorySerializer(serializers.ModelSerializer):
    document_count = serializers.SerializerMethodField()

    class Meta:
        model = DocumentCategory
        fields = ['id', 'name', 'slug', 'order', 'document_count']
        read_only_fields = ['id']

    def get_document_count(self, obj):
        return obj.documents.count()


class DocumentFileSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(
        source='uploaded_by.get_full_name', read_only=True, default=None
    )
    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = DocumentFile
        fields = [
            'id', 'version', 'file_name', 'file_size', 'file_size_display',
            'content_type', 'uploaded_by_name', 'uploaded_at',
        ]
        read_only_fields = ['id', 'version', 'uploaded_at']

    def get_file_size_display(self, obj):
        size = obj.file_size
        if size < 1024:
            return f'{size} B'
        elif size < 1024 * 1024:
            return f'{size / 1024:.1f} KB'
        else:
            return f'{size / (1024 * 1024):.1f} MB'


class DocumentSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    target_employee_name = serializers.CharField(
        source='target_employee.full_name', read_only=True, default=None
    )
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, default=None)
    latest_file = DocumentFileSerializer(read_only=True)
    file_count = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'category', 'category_name', 'target_employee',
            'target_employee_name', 'visibility', 'description',
            'created_by_name', 'created_at', 'updated_at', 'latest_file', 'file_count',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_file_count(self, obj):
        return obj.files.count()
