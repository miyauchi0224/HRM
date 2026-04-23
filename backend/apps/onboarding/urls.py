from rest_framework.routers import DefaultRouter
from .views import (
    OnboardingTemplateViewSet,
    OnboardingAssignmentViewSet,
    OnboardingTaskItemViewSet,
)

router = DefaultRouter()
router.register('templates',   OnboardingTemplateViewSet,   basename='onboarding-template')
router.register('assignments', OnboardingAssignmentViewSet, basename='onboarding-assignment')
router.register('task-items',  OnboardingTaskItemViewSet,   basename='onboarding-task-item')

urlpatterns = router.urls
