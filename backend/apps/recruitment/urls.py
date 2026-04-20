from rest_framework.routers import DefaultRouter
from .views import JobPostingViewSet, CandidateViewSet, InterviewViewSet

router = DefaultRouter()
router.register('jobs', JobPostingViewSet, basename='job-posting')
router.register('candidates', CandidateViewSet, basename='candidate')
router.register('interviews', InterviewViewSet, basename='interview')

urlpatterns = router.urls
