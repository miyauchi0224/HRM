from rest_framework.routers import DefaultRouter
from .views import TodoItemViewSet

router = DefaultRouter()
router.register('items', TodoItemViewSet, basename='todo-item')

urlpatterns = router.urls
