from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, upload_image

router = DefaultRouter()
router.register('articles', ArticleViewSet, basename='intra-article')

urlpatterns = router.urls + [
    path('upload/', upload_image, name='intra-upload'),
]
