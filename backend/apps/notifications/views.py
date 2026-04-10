from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
    qs = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({
        'unread_count': unread_count,
        'results': NotificationSerializer(qs, many=True).data,
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_read(request, pk):
    notif = Notification.objects.filter(pk=pk, user=request.user).first()
    if notif:
        notif.is_read = True
        notif.save()
    return Response({'status': 'ok'})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def read_all(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({'status': 'ok'})
