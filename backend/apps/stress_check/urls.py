from rest_framework.routers import DefaultRouter
from .views import StressCheckPeriodViewSet, StressCheckResponseViewSet

router = DefaultRouter()
router.register('periods',   StressCheckPeriodViewSet,   basename='stress-check-period')
router.register('responses', StressCheckResponseViewSet, basename='stress-check-response')

urlpatterns = router.urls
