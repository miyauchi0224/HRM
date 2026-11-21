"""
Cookie に入った JWT で認証する（HttpOnly Cookie 方式）

- Authorization: Bearer ヘッダーがあればそれを使う（ブラウザ以外のクライアント用。CSRF 検証なし）
- なければ hrm_access Cookie を使う。この場合 POST などは CSRF を検証する
"""
from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication

SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS', 'TRACE')


class _CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        return reason


def enforce_csrf(request):
    django_request = getattr(request, '_request', request)
    check = _CSRFCheck(lambda req: None)
    check.process_request(django_request)
    reason = check.process_view(django_request, None, (), {})
    if reason:
        raise exceptions.PermissionDenied(f'CSRF 検証に失敗しました（{reason}）')


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is not None:
            return super().authenticate(request)

        raw_token = request.COOKIES.get(settings.AUTH_COOKIE_ACCESS)
        if not raw_token:
            return None
        validated = self.get_validated_token(raw_token.encode())
        user = self.get_user(validated)
        if request.method not in SAFE_METHODS:
            enforce_csrf(request)
        return user, validated

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        changed = getattr(user, 'password_changed_at', None)
        issued_at = validated_token.get('iat')
        if changed and issued_at is not None and int(changed.timestamp()) > int(issued_at):
            raise exceptions.AuthenticationFailed('パスワードが変更されたため、再度ログインしてください', code='password_changed')
        return user

    def authenticate_header(self, request):
        return 'Bearer realm="api"'


# ── Cookie の設定・削除 ───────────────────────────────────────

def _cookie_kwargs(path):
    return {
        'httponly': True,
        'secure':   settings.AUTH_COOKIE_SECURE,
        'samesite': settings.AUTH_COOKIE_SAMESITE,
        'domain':   settings.AUTH_COOKIE_DOMAIN or None,
        'path':     path,
    }


def set_auth_cookies(response, access: str, refresh: str | None = None):
    jwt = settings.SIMPLE_JWT
    response.set_cookie(
        settings.AUTH_COOKIE_ACCESS, access,
        max_age=int(jwt['ACCESS_TOKEN_LIFETIME'].total_seconds()),
        **_cookie_kwargs('/'),
    )
    if refresh:
        response.set_cookie(
            settings.AUTH_COOKIE_REFRESH, refresh,
            max_age=int(jwt['REFRESH_TOKEN_LIFETIME'].total_seconds()),
            **_cookie_kwargs(settings.AUTH_COOKIE_REFRESH_PATH),
        )
    return response


def clear_auth_cookies(response):
    response.delete_cookie(settings.AUTH_COOKIE_ACCESS, path='/',
                           domain=settings.AUTH_COOKIE_DOMAIN or None,
                           samesite=settings.AUTH_COOKIE_SAMESITE)
    response.delete_cookie(settings.AUTH_COOKIE_REFRESH, path=settings.AUTH_COOKIE_REFRESH_PATH,
                           domain=settings.AUTH_COOKIE_DOMAIN or None,
                           samesite=settings.AUTH_COOKIE_SAMESITE)
    return response
