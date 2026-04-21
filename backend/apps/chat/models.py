import uuid
from django.db import models
from apps.accounts.models import User
from apps.common.models import SoftDeleteModel


class ChatRoom(SoftDeleteModel):
    """チャットルーム（DM または グループ）"""

    class RoomType(models.TextChoices):
        DIRECT = 'direct', 'ダイレクトメッセージ'
        GROUP = 'group', 'グループ'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_type = models.CharField(max_length=10, choices=RoomType.choices)
    name = models.CharField(max_length=100, blank=True, verbose_name='ルーム名（グループのみ）')
    members = models.ManyToManyField(User, related_name='chat_rooms', verbose_name='メンバー')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='created_rooms')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'チャットルーム'
        ordering = ['-created_at']

    def __str__(self):
        return self.name or f'DM-{self.id}'


class ChatMessage(SoftDeleteModel):
    """チャットメッセージ"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                               related_name='sent_messages')
    content = models.TextField(verbose_name='メッセージ内容')
    attachment_url = models.URLField(blank=True, verbose_name='添付ファイルURL')
    attachment_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'チャットメッセージ'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender} @ {self.room}: {self.content[:30]}'


class MessageReadStatus(SoftDeleteModel):
    """メッセージ既読管理"""
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='read_statuses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_messages')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['message', 'user']]


class ChatAttachment(SoftDeleteModel):
    """チャット添付ファイル（複数可）"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='chat/attachments/%Y/%m/')
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(verbose_name='ファイルサイズ(bytes)')
    content_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_image(self):
        return self.content_type.startswith('image/')

    class Meta:
        verbose_name = '添付ファイル'
        ordering = ['created_at']
