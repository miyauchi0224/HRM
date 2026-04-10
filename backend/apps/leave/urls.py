from rest_framework.routers import DefaultRouter
from .views import LeaveBalanceViewSet, LeaveRequestViewSet

router = DefaultRouter()
router.register('balances', LeaveBalanceViewSet, basename='leave-balance')
router.register('requests', LeaveRequestViewSet, basename='leave-request')

urlpatterns = router.urls
