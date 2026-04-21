from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import ChatRoom, ChatMessage, MessageReadStatus, ChatAttachment
from .serializers import ChatRoomSerializer, ChatMessageSerializer, ChatAttachmentSerializer
from apps.accounts.models import User
from apps.common.mixins import SoftDeleteViewSetMixin

MAX_TOTAL_SIZE = 10 * 1024 * 1024  # 10MB


class ChatRoomViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatRoom.objects.filter(members=self.request.user).prefetch_related('members', 'messages')

    def perform_create(self, serializer):
        room = serializer.save(created_by=self.request.user)
        room.members.add(self.request.user)
        member_ids = self.request.data.get('member_ids', [])
        if member_ids:
            users = User.objects.filter(id__in=member_ids)
            room.members.add(*users)

    @action(detail=False, methods=['post'], url_path='direct')
    def get_or_create_direct(self, request):
        """2人のDMルームを取得または作成"""
        other_id = request.data.get('user_id')
        if not other_id:
            return Response({'error': 'user_id が必要です'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            other = User.objects.get(id=other_id)
        except User.DoesNotExist:
            return Response({'error': 'ユーザーが見つかりません'}, status=status.HTTP_404_NOT_FOUND)

        room = ChatRoom.objects.filter(
            room_type=ChatRoom.RoomType.DIRECT,
            members=request.user,
        ).filter(members=other).first()

        if not room:
            room = ChatRoom.objects.create(
                room_type=ChatRoom.RoomType.DIRECT,
                created_by=request.user,
            )
            room.members.add(request.user, other)

        return Response(ChatRoomSerializer(room, context={'request': request}).data)


class ChatMessageViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        room_id = self.request.query_params.get('room')
        qs = ChatMessage.objects.filter(
            room__members=self.request.user,
            is_deleted=False,
        ).select_related('sender').prefetch_related('attachments', 'read_statuses')
        if room_id:
            qs = qs.filter(room_id=room_id)
        return qs.order_by('created_at')

    def perform_create(self, serializer):
        msg = serializer.save(sender=self.request.user)
        MessageReadStatus.objects.get_or_create(message=msg, user=self.request.user)
        self._save_attachments(msg, self.request)

    def _save_attachments(self, message, request):
        files = request.FILES.getlist('files')
        if not files:
            return
        total_size = sum(f.size for f in files)
        if total_size > MAX_TOTAL_SIZE:
            return  # フロントエンドで事前チェック済みだが念のため
        for f in files:
            ChatAttachment.objects.create(
                message=message,
                file=f,
                file_name=f.name,
                file_size=f.size,
                content_type=f.content_type or 'application/octet-stream',
            )

    @action(detail=True, methods=['post'], url_path='read')
    def mark_read(self, request, pk=None):
        msg = self.get_object()
        MessageReadStatus.objects.get_or_create(message=msg, user=request.user)
        return Response({'status': 'ok'})

    @action(detail=False, methods=['post'], url_path='read-all')
    def mark_all_read(self, request):
        room_id = request.data.get('room_id')
        msgs = ChatMessage.objects.filter(room_id=room_id, room__members=request.user, is_deleted=False)
        for msg in msgs:
            MessageReadStatus.objects.get_or_create(message=msg, user=request.user)
        return Response({'status': 'ok'})

