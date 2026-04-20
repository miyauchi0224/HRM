from rest_framework import serializers
from .models import ChatRoom, ChatMessage, MessageReadStatus
from apps.accounts.models import User


class UserMinSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email']


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ['id', 'room', 'sender', 'sender_name', 'content',
                  'attachment_url', 'attachment_name', 'is_deleted', 'created_at', 'is_read']
        read_only_fields = ['sender', 'is_deleted']

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
            return {'content': msg.content, 'sender': msg.sender.full_name if msg.sender else '',
                    'created_at': msg.created_at}
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request:
            return 0
        return obj.messages.filter(is_deleted=False).exclude(
            read_statuses__user=request.user
        ).exclude(sender=request.user).count()

    def create(self, validated_data):
        member_ids = validated_data.pop('member_ids', [])
        room = super().create(validated_data)
        room.members.set(member_ids + [validated_data.get('created_by').id if validated_data.get('created_by') else []])
        return room
