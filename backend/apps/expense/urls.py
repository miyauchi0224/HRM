from rest_framework.routers import DefaultRouter
from .views import AccountItemViewSet, ExpenseRequestViewSet

router = DefaultRouter()
router.register('account-items', AccountItemViewSet, basename='account-item')
router.register('requests',      ExpenseRequestViewSet, basename='expense-request')

urlpatterns = router.urls
