from rest_framework.routers import DefaultRouter
from .views import TodoItemViewSet, DailyReportViewSet

router = DefaultRouter()
router.register('items',         TodoItemViewSet,    basename='todo-item')
router.register('daily-reports', DailyReportViewSet, basename='daily-report')

urlpatterns = router.urls
