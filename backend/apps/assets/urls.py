from rest_framework.routers import DefaultRouter
from .views import AssetViewSet, AssetCategoryViewSet

router = DefaultRouter()
router.register('categories', AssetCategoryViewSet, basename='asset-category')
router.register('items', AssetViewSet, basename='asset')

urlpatterns = router.urls
