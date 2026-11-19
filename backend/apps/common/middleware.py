import os

from django.conf import settings

# ブラウザ内で表示してよい形式（それ以外はダウンロードさせる）
INLINE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.mp4', '.webm', '.mov', '.mp3', '.m4a'}


class MediaSecurityHeadersMiddleware:
    """
    /media/ 配下のファイルに保護用ヘッダーを付ける。
    過去にアップロードされた HTML・SVG などが開かれてもスクリプトが動かないようにする。
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        media_url = settings.MEDIA_URL or '/media/'
        if not request.path.startswith(media_url):
            return response

        response['X-Content-Type-Options'] = 'nosniff'
        ext = os.path.splitext(request.path)[1].lower()
        if ext == '.pdf':
            # sandbox を付けるとブラウザの PDF ビューアが動かないため script のみ禁止
            response['Content-Security-Policy'] = "script-src 'none'; object-src 'none'"
        else:
            response['Content-Security-Policy'] = (
                "sandbox; default-src 'none'; img-src 'self'; media-src 'self'; style-src 'unsafe-inline'"
            )
        if ext not in INLINE_EXTENSIONS:
            response['Content-Disposition'] = 'attachment'
        return response
