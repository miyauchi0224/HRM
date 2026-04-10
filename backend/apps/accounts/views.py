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
