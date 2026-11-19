from rest_framework.routers import DefaultRouter
from .views import PulseSurveyViewSet

router = DefaultRouter()
router.register('surveys', PulseSurveyViewSet, basename='pulse-survey')

urlpatterns = router.urls
