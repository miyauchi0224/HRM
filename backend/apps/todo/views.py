from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import TodoItem
from .serializers import TodoItemSerializer


class TodoItemViewSet(viewsets.ModelViewSet):
    serializer_class   = TodoItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TodoItem.objects.filter(employee__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user.employee)

    @action(detail=True, methods=['patch'], url_path='move')
    def move(self, request, pk=None):
        """ステータス変更（カンバン移動）"""
        item = self.get_object()
        new_status = request.data.get('status')
        if new_status not in [c[0] for c in TodoItem.Status.choices]:
            return Response({'error': '無効なステータスです'}, status=status.HTTP_400_BAD_REQUEST)
        item.status = new_status
        item.save()
        return Response(TodoItemSerializer(item).data)
