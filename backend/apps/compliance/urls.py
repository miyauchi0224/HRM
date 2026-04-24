from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ComplianceChecklistViewSet

router = DefaultRouter()
router.register(r'checklists', ComplianceChecklistViewSet, basename='compliance-checklist')

urlpatterns = [
    path('', include(router.urls)),
]
