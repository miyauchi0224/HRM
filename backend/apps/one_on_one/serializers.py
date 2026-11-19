from rest_framework import serializers
from .models import OneOnOneMeeting


class ActionItemSerializer(serializers.Serializer):
    text  = serializers.CharField(max_length=500)
    owner = serializers.ChoiceField(choices=['manager', 'member'], default='member')
    done  = serializers.BooleanField(default=False)


class OneOnOneMeetingSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source='manager.full_name', read_only=True)
    member_name  = serializers.CharField(source='member.full_name', read_only=True)
    action_items = ActionItemSerializer(many=True, required=False)
    my_role      = serializers.SerializerMethodField()

    class Meta:
        model  = OneOnOneMeeting
        fields = [
            'id', 'manager', 'manager_name', 'member', 'member_name', 'my_role',
            'scheduled_at', 'duration_minutes', 'status', 'agenda', 'shared_notes',
            'manager_private_notes', 'action_items', 'ai_summary', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'ai_summary', 'created_at', 'updated_at']

    def _me(self):
        request = self.context.get('request')
        return getattr(getattr(request, 'user', None), 'employee', None)

    def get_my_role(self, obj):
        me = self._me()
        if me is None:
            return None
        return 'manager' if obj.manager_id == me.id else 'member'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # 上司メモは上司本人にしか返さない
        me = self._me()
        if me is None or instance.manager_id != me.id:
            data.pop('manager_private_notes', None)
        return data

    def validate_action_items(self, value):
        # PATCH（partial）では入れ子の既定値が適用されないため、ここでそろえる
        return [{'text': i['text'], 'owner': i.get('owner', 'member'), 'done': i.get('done', False)}
                for i in value]

    def validate(self, data):
        me      = self._me()
        manager = data.get('manager') or getattr(self.instance, 'manager', None)
        member  = data.get('member') or getattr(self.instance, 'member', None)
        if self.instance is not None:
            # 参加者は変更できない
            if ('manager' in data and data['manager'] != self.instance.manager) or \
               ('member' in data and data['member'] != self.instance.member):
                raise serializers.ValidationError('参加者は変更できません')
            if 'manager_private_notes' in data and (me is None or self.instance.manager_id != me.id):
                raise serializers.ValidationError({'manager_private_notes': '上司メモは上司のみ編集できます'})
            return data

        if manager is None or member is None:
            raise serializers.ValidationError('上司と部下を指定してください')
        if manager.pk == member.pk:
            raise serializers.ValidationError('上司と部下に同じ人は指定できません')
        if me is None or me.pk not in (manager.pk, member.pk):
            raise serializers.ValidationError('自分が参加する1on1のみ登録できます')
        if not member.managers.filter(pk=manager.pk).exists():
            raise serializers.ValidationError({'manager': f'{manager.full_name}さんは{member.full_name}さんの上司として登録されていません'})
        if data.get('manager_private_notes') and me.pk != manager.pk:
            raise serializers.ValidationError({'manager_private_notes': '上司メモは上司のみ入力できます'})
        return data
