import mimetypes
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.http import FileResponse
from apps.accounts.permissions import IsNotCustomer, IsHR
from apps.common.mixins import SoftDeleteViewSetMixin
from .models import DocumentCategory, Document, DocumentFile
from .serializers import DocumentCategorySerializer, DocumentSerializer, DocumentFileSerializer

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class DocumentCategoryViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class = DocumentCategorySerializer
    permission_classes = [IsNotCustomer]

    def get_queryset(self):
        return DocumentCategory.objects.prefetch_related('documents').all()

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsHR()]
        return [IsNotCustomer()]


class DocumentViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsNotCustomer]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        qs = Document.objects.select_related(
            'category', 'target_employee', 'created_by'
        ).prefetch_related('files')

        if user.is_hr:
            return qs

        employee = getattr(user, 'employee', None)
        from django.db.models import Q
        return qs.filter(
            Q(visibility='all') |
            Q(visibility='personal', target_employee=employee)
        )

    def get_permissions(self):
        if self.action in ('create', 'destroy'):
            return [IsHR()]
        return [IsNotCustomer()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='upload',
            parser_classes=[MultiPartParser, FormParser])
    def upload(self, request, pk=None):
        doc = self.get_object()
        if not request.user.is_hr:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)

        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'ファイルが必要です'}, status=status.HTTP_400_BAD_REQUEST)
        if file.size > MAX_FILE_SIZE:
            return Response(
                {'error': 'ファイルサイズは50MB以内にしてください'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        latest = doc.files.order_by('-version').first()
        next_version = (latest.version + 1) if latest else 1
        content_type = (
            file.content_type
            or mimetypes.guess_type(file.name)[0]
            or 'application/octet-stream'
        )
        doc_file = DocumentFile.objects.create(
            document=doc,
            version=next_version,
            file=file,
            file_name=file.name,
            file_size=file.size,
            content_type=content_type,
            uploaded_by=request.user,
        )
        return Response(DocumentFileSerializer(doc_file).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        doc = self.get_object()
        latest = doc.files.order_by('-version').first()
        if not latest:
            return Response({'error': 'ファイルがありません'}, status=status.HTTP_404_NOT_FOUND)

        response = FileResponse(latest.file.open('rb'), content_type=latest.content_type)
        response['Content-Disposition'] = f'attachment; filename="{latest.file_name}"'
        return response
