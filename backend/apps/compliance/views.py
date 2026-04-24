from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import ComplianceChecklistSection, ComplianceChecklistItem, ComplianceChecklistProgress
from .serializers import (
    ComplianceChecklistSectionDetailSerializer,
    ComplianceChecklistSectionListSerializer,
    ComplianceChecklistProgressSerializer,
)


class ComplianceChecklistViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = ComplianceChecklistSection.objects.filter(is_deleted=False).order_by('order')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ComplianceChecklistSectionDetailSerializer
        return ComplianceChecklistSectionListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """全体進捗サマリー"""
        sections = self.get_queryset()
        total_items = 0
        total_completed = 0

        sections_data = []
        for section in sections:
            items_count = section.items.filter(is_deleted=False).count()
            completed_count = ComplianceChecklistProgress.objects.filter(
                user=request.user,
                item__section=section,
                is_completed=True
            ).count()

            total_items += items_count
            total_completed += completed_count

            sections_data.append({
                'id': str(section.id),
                'title': section.title,
                'item_count': items_count,
                'completed_count': completed_count,
                'progress_rate': round((completed_count / items_count * 100), 1) if items_count > 0 else 0,
            })

        overall_progress = round((total_completed / total_items * 100), 1) if total_items > 0 else 0

        return Response({
            'overall_progress': overall_progress,
            'total_items': total_items,
            'completed_items': total_completed,
            'sections': sections_data,
        })

    @action(detail=False, methods=['post'])
    def update_item_progress(self, request):
        """チェックリスト項目の完了状況を更新"""
        item_id = request.data.get('item_id')
        is_completed = request.data.get('is_completed', False)
        notes = request.data.get('notes', '')

        try:
            item = ComplianceChecklistItem.objects.get(id=item_id)
        except ComplianceChecklistItem.DoesNotExist:
            return Response(
                {'error': '項目が見つかりません'},
                status=status.HTTP_404_NOT_FOUND
            )

        progress, created = ComplianceChecklistProgress.objects.get_or_create(
            user=request.user,
            item=item
        )

        progress.is_completed = is_completed
        progress.notes = notes

        if is_completed and not progress.completed_at:
            progress.completed_at = timezone.now()
        elif not is_completed:
            progress.completed_at = None

        progress.save()

        return Response(
            ComplianceChecklistProgressSerializer(progress).data,
            status=status.HTTP_200_OK
        )
