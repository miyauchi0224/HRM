import uuid
from django.db import models
from apps.accounts.models import User


class ChatRoom(models.Model):
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


class ChatMessage(models.Model):
    """チャットメッセージ"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                               related_name='sent_messages')
    content = models.TextField(verbose_name='メッセージ内容')
    attachment_url = models.URLField(blank=True, verbose_name='添付ファイルURL')
    attachment_name = models.CharField(max_length=200, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'チャットメッセージ'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender} @ {self.room}: {self.content[:30]}'


class MessageReadStatus(models.Model):
    """メッセージ既読管理"""
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='read_statuses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_messages')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['message', 'user']]
