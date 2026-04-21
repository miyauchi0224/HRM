from rest_framework import serializers
from .models import ChatRoom, ChatMessage, MessageReadStatus, ChatAttachment
from apps.accounts.models import User


class UserMinSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email']

    def get_full_name(self, obj):
        try:
            return obj.employee.full_name
        except Exception:
            return obj.email


class ChatAttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ChatAttachment
        fields = ['id', 'file_name', 'file_size', 'content_type', 'is_image', 'url', 'created_at']

    def get_url(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return ''


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_avatar = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    attachments = ChatAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'room', 'sender', 'sender_name', 'sender_avatar', 'content',
                  'attachment_url', 'attachment_name', 'attachments',
                  'is_deleted', 'created_at', 'is_read']
        read_only_fields = ['sender', 'is_deleted']

    def get_sender_name(self, obj):
        if not obj.sender:
            return ''
        try:
            return obj.sender.employee.full_name
        except Exception:
            return obj.sender.email

    def get_sender_avatar(self, obj):
        if not obj.sender:
            return None
        try:
            emp = obj.sender.employee
            if emp.avatar:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(emp.avatar.url)
        except Exception:
            pass
        return None

    def get_is_read(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return obj.read_statuses.filter(user=request.user).exists()


class ChatRoomSerializer(serializers.ModelSerializer):
    members = UserMinSerializer(many=True, read_only=True)
    member_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['id', 'room_type', 'name', 'members', 'member_ids',
                  'created_by', 'created_at', 'last_message', 'unread_count']
        read_only_fields = ['created_by']

    def get_last_message(self, obj):
        msg = obj.messages.filter(is_deleted=False).last()
        if msg:
            sender_name = ''
            if msg.sender:
                try:
                    sender_name = msg.sender.employee.full_name
                except Exception:
                    sender_name = msg.sender.email
            has_attachments = msg.attachments.exists()
            content = msg.content or (f'[添付ファイル {msg.attachments.count()}件]' if has_attachments else '')
            return {'content': content, 'sender': sender_name, 'created_at': msg.created_at}
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request:
            return 0
        return obj.messages.filter(is_deleted=False).exclude(
            read_statuses__user=request.user
        ).exclude(sender=request.user).count()

    def create(self, validated_data):
        validated_data.pop('member_ids', [])
        return super().create(validated_data)
