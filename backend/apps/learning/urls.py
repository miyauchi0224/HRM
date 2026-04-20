from rest_framework.routers import DefaultRouter
from .views import LearningCourseViewSet, CourseEnrollmentViewSet

router = DefaultRouter()
router.register('courses', LearningCourseViewSet, basename='learning-course')
router.register('enrollments', CourseEnrollmentViewSet, basename='enrollment')

urlpatterns = router.urls
