from django.conf import settings
from django.views.static import serve
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

# 顧客ロールにも見せてよいメディア（イントラの公開記事の画像）
CUSTOMER_VISIBLE_PREFIXES = ('intra/',)


class ProtectedMediaView(APIView):
    """
    GET /media/<path> - アップロードファイルをログインしている人にだけ配信する（v1.3）
    個別の閲覧権限（他人の領収書など）は各機能のダウンロード API で確認する。
    保護用のヘッダーは MediaSecurityHeadersMiddleware が付ける。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, path):
        if request.user.is_customer and not path.startswith(CUSTOMER_VISIBLE_PREFIXES):
            raise PermissionDenied('このファイルへのアクセス権限がありません。')
        # serve() はパスの正規化（../ の拒否）と 404 を行う
        return serve(request._request, path, document_root=settings.MEDIA_ROOT)
