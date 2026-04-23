from rest_framework.routers import DefaultRouter
from .views import DocumentCategoryViewSet, DocumentViewSet

router = DefaultRouter()
router.register('categories', DocumentCategoryViewSet, basename='document-category')
router.register('',           DocumentViewSet,          basename='document')

urlpatterns = router.urls
