from rest_framework.routers import DefaultRouter
from .views import OneOnOneMeetingViewSet

router = DefaultRouter()
router.register('meetings', OneOnOneMeetingViewSet, basename='one-on-one-meeting')

urlpatterns = router.urls
