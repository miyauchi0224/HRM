from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer, ChangePasswordSerializer, UserSerializer


class LoginView(TokenObtainPairView):
    """POST /api/v1/auth/login/ - ログイン"""
    serializer_class = LoginSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """POST /api/v1/auth/logout/ - ログアウト（リフレッシュトークン無効化）"""
    try:
        refresh_token = request.data.get('refresh_token')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'ログアウトしました'})
    except Exception:
        return Response({'error': 'トークンが無効です'}, status=status.HTTP_400_BAD_REQUEST)


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
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': 'パスワードを変更しました'})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
