from rest_framework.routers import DefaultRouter
from .views import LeaveBalanceViewSet, LeaveGrantViewSet, LeaveRequestViewSet

router = DefaultRouter()
router.register('balances', LeaveBalanceViewSet, basename='leave-balance')
router.register('requests', LeaveRequestViewSet, basename='leave-request')
router.register('grants',   LeaveGrantViewSet,   basename='leave-grant')

urlpatterns = router.urls
