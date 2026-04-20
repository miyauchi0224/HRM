from rest_framework.routers import DefaultRouter
from .views import ApprovalRequestViewSet, ApprovalTemplateViewSet

router = DefaultRouter()
router.register('templates', ApprovalTemplateViewSet, basename='approval-template')
router.register('requests', ApprovalRequestViewSet, basename='approval-request')

urlpatterns = router.urls
