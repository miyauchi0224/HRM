from rest_framework.routers import DefaultRouter
from .views import MBOGoalViewSet, MBOReportViewSet, DailyReportViewSet

router = DefaultRouter()
router.register('goals',    MBOGoalViewSet,    basename='mbo-goal')
router.register('reports',  MBOReportViewSet,  basename='mbo-report')
router.register('daily',    DailyReportViewSet, basename='daily-report')

urlpatterns = router.urls
