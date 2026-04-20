from rest_framework.routers import DefaultRouter
from .views import EvaluationPeriodViewSet, EvaluationQuestionViewSet, Evaluation360ViewSet

router = DefaultRouter()
router.register('periods', EvaluationPeriodViewSet, basename='eval-period')
router.register('questions', EvaluationQuestionViewSet, basename='eval-question')
router.register('evaluations', Evaluation360ViewSet, basename='evaluation')

urlpatterns = router.urls
