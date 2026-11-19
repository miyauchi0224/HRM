from rest_framework.routers import DefaultRouter
from .views import HealthCheckupViewSet

router = DefaultRouter()
router.register('', HealthCheckupViewSet, basename='health-checkup')

urlpatterns = router.urls
