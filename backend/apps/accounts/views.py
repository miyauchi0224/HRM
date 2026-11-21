import logging

from django.conf import settings
from django.contrib.auth import authenticate
from django.middleware.csrf import get_token
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from .authentication import enforce_csrf, set_auth_cookies, clear_auth_cookies
from .models import User
from .serializers import ChangePasswordSerializer, UserSerializer

logger = logging.getLogger(__name__)

LOGIN_FAILED_MESSAGE = 'メールアドレスまたはパスワードが正しくありません'
LOGIN_LOCKED_MESSAGE = 'ログインの失敗が続いたため、一定時間ロックされています。しばらくしてから再度お試しください'


def _user_payload(user):
    return {
        'id':        str(user.id),
        'email':     user.email,
        'role':      user.role,
        'full_name': user.employee.full_name if hasattr(user, 'employee') else user.email,
    }


class CsrfView(APIView):
    """GET /api/v1/auth/csrf/ - CSRF トークンを発行（Cookie と本文の両方）"""
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'csrfToken': get_token(request._request)})


class LoginView(APIView):
    """
    POST /api/v1/auth/login/ - ログイン
    トークンは HttpOnly Cookie に設定し、本文にはユーザー情報だけを返す。
    IP ごとの回数制限（throttle）と、アカウントごとの連続失敗ロックを行う。
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        email    = (request.data.get('email') or '').strip()
        password = request.data.get('password') or ''
        if not email or not password:
            return Response({'detail': LOGIN_FAILED_MESSAGE}, status=status.HTTP_401_UNAUTHORIZED)

        target = User.objects.filter(email__iexact=email).first()
        if target and target.is_locked:
            return Response({'detail': LOGIN_LOCKED_MESSAGE, 'code': 'account_locked'},
                            status=status.HTTP_403_FORBIDDEN)

        user = authenticate(request._request, email=target.email if target else email, password=password)
        if user is None or not user.is_active:
            if target:
                locked = target.register_login_failure(settings.LOGIN_MAX_FAILURES, settings.LOGIN_LOCK_MINUTES)
                if locked:
                    logger.warning('アカウントをロックしました: user_id=%s', target.id)
                    return Response({'detail': LOGIN_LOCKED_MESSAGE, 'code': 'account_locked'},
                                    status=status.HTTP_403_FORBIDDEN)
            return Response({'detail': LOGIN_FAILED_MESSAGE}, status=status.HTTP_401_UNAUTHORIZED)

        user.reset_login_failures()
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        refresh = RefreshToken.for_user(user)
        response = Response({'user': _user_payload(user)})
        get_token(request._request)  # CSRF Cookie も発行しておく
        return set_auth_cookies(response, str(refresh.access_token), str(refresh))


class RefreshView(APIView):
    """POST /api/v1/auth/refresh/ - Cookie のリフレッシュトークンでトークンを再発行"""
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        enforce_csrf(request)
        raw = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        if not raw:
            return Response({'detail': 'ログインしてください'}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = TokenRefreshSerializer(data={'refresh': raw})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return clear_auth_cookies(
                Response({'detail': 'ログインの有効期限が切れました'}, status=status.HTTP_401_UNAUTHORIZED))
        data = serializer.validated_data
        return set_auth_cookies(Response({'message': 'ok'}), data['access'], data.get('refresh'))


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ - リフレッシュトークンを無効化し、Cookie を削除"""
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        enforce_csrf(request)
        raw = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH) or request.data.get('refresh_token')
        if raw:
            try:
                RefreshToken(raw).blacklist()
            except TokenError:
                pass
        return clear_auth_cookies(Response({'message': 'ログアウトしました'}))


def revoke_all_refresh_tokens(user):
    """そのユーザーの全リフレッシュトークンを無効化する（全端末のログアウト）"""
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """GET /api/v1/auth/me/ - ログイン中ユーザー情報取得"""
    serializer = UserSerializer(request.user)
    data = serializer.data
    if hasattr(request.user, 'employee'):
        emp = request.user.employee
        data['full_name']  = emp.full_name
        data['department'] = emp.department
        data['employee_number'] = emp.employee_number
    return Response(data)


def _mask_key(key: str, prefix: str) -> str:
    if len(key) > 10:
        return f'{prefix}...{key[-6:]}'
    return '登録済' if key else ''


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_key_view(request):
    """
    GET  /api/v1/auth/api-key/
      → { provider, anthropic_has_key, anthropic_masked, openai_has_key, openai_masked }
    POST /api/v1/auth/api-key/
      body: { provider, api_key }
    """
    user = request.user

    if request.method == 'GET':
        ant_key = user.anthropic_api_key or ''
        oai_key = user.openai_api_key or ''
        return Response({
            'provider':          user.ai_provider,
            'anthropic_has_key': bool(ant_key),
            'anthropic_masked':  _mask_key(ant_key, 'sk-ant-'),
            'openai_has_key':    bool(oai_key),
            'openai_masked':     _mask_key(oai_key, 'sk-'),
        })

    provider = request.data.get('provider', '').strip()
    api_key  = request.data.get('api_key', '').strip()

    if provider not in ('anthropic', 'openai'):
        return Response({'error': 'provider は anthropic または openai を指定してください'},
                        status=status.HTTP_400_BAD_REQUEST)

    # プレフィックスバリデーション（登録・削除どちらも空文字は許可）
    if api_key:
        if provider == 'anthropic' and not api_key.startswith('sk-ant-'):
            return Response({'error': 'Anthropic APIキーは sk-ant- で始まる必要があります'},
                            status=status.HTTP_400_BAD_REQUEST)
        if provider == 'openai' and not api_key.startswith('sk-'):
            return Response({'error': 'OpenAI APIキーは sk- で始まる必要があります'},
                            status=status.HTTP_400_BAD_REQUEST)

    if provider == 'anthropic':
        user.anthropic_api_key = api_key
    else:
        user.openai_api_key = api_key

    user.ai_provider = provider
    user.save(update_fields=['anthropic_api_key', 'openai_api_key', 'ai_provider'])
    return Response({'message': 'APIキーを保存しました', 'provider': provider})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """POST /api/v1/auth/password/change/ - パスワード変更"""
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        # 他の端末のログインをすべて無効にし、この端末には新しいトークンを発行する
        revoke_all_refresh_tokens(user)
        refresh = RefreshToken.for_user(user)
        response = Response({'message': 'パスワードを変更しました'})
        return set_auth_cookies(response, str(refresh.access_token), str(refresh))
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
