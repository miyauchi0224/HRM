from rest_framework.routers import DefaultRouter
from .views import ApprovalRequestViewSet, ApprovalTemplateViewSet, ApprovalDelegationViewSet

router = DefaultRouter()
router.register('templates', ApprovalTemplateViewSet, basename='approval-template')
router.register('requests', ApprovalRequestViewSet, basename='approval-request')
router.register('delegations', ApprovalDelegationViewSet, basename='approval-delegation')

urlpatterns = router.urls
