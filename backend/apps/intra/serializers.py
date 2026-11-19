from rest_framework import serializers
from apps.common.security import sanitize_html
from .models import Article, ArticleRead, ArticleComment


class ArticleCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.full_name', read_only=True)

    class Meta:
        model  = ArticleComment
        fields = ['id', 'author_name', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author_name', 'created_at', 'updated_at']


class ArticleReadSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.employee.full_name', read_only=True)

    class Meta:
        model  = ArticleRead
        fields = ['id', 'user_name', 'read_at']
        read_only_fields = ['id', 'user_name', 'read_at']


class ArticleListSerializer(serializers.ModelSerializer):
    """一覧用（本文を除く軽量版）"""
    author_name   = serializers.CharField(source='author.full_name', read_only=True)
    approver_name = serializers.CharField(source='approver.full_name', read_only=True)
    read_count    = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    is_read       = serializers.SerializerMethodField()

    class Meta:
        model  = Article
        fields = [
            'id', 'title', 'category', 'format', 'is_pinned', 'status',
            'author_name', 'approver_name',
            'read_count', 'comment_count', 'is_read',
            'published_at', 'created_at',
        ]

    def get_is_read(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return obj.reads.filter(user=request.user).exists()


class ArticleDetailSerializer(serializers.ModelSerializer):
    """詳細用（本文・コメント含む）"""
    author_name   = serializers.CharField(source='author.full_name', read_only=True)
    approver_name = serializers.CharField(source='approver.full_name', read_only=True)
    read_count    = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    comments      = ArticleCommentSerializer(many=True, read_only=True)
    is_read       = serializers.SerializerMethodField()

    class Meta:
        model  = Article
        fields = [
            'id', 'title', 'content', 'format', 'category', 'is_pinned', 'status',
            'reject_reason',
            'author_name', 'approver_name',
            'read_count', 'comment_count', 'comments', 'is_read',
            'published_at', 'created_at', 'updated_at',
        ]

    def get_is_read(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return obj.reads.filter(user=request.user).exists()


class ArticleWriteSerializer(serializers.ModelSerializer):
    """作成・更新用"""
    class Meta:
        model  = Article
        fields = ['id', 'title', 'content', 'format', 'category']
        read_only_fields = ['id']

    def validate(self, attrs):
        # HTML 形式の本文は保存前に無害化する（script・イベント属性・javascript: URL を除去）
        fmt = attrs.get('format', getattr(self.instance, 'format', None))
        if fmt == 'html' and 'content' in attrs:
            attrs['content'] = sanitize_html(attrs['content'])
        elif fmt == 'html' and self.instance is not None and 'format' in attrs:
            attrs['content'] = sanitize_html(self.instance.content)
        return attrs
