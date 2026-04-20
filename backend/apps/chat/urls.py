from rest_framework.routers import DefaultRouter
from .views import ChatRoomViewSet, ChatMessageViewSet

router = DefaultRouter()
router.register('rooms', ChatRoomViewSet, basename='chat-room')
router.register('messages', ChatMessageViewSet, basename='chat-message')

urlpatterns = router.urls
