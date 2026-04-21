from rest_framework.routers import DefaultRouter
from .views import LearningCourseViewSet, CourseEnrollmentViewSet, QuizViewSet

router = DefaultRouter()
router.register('courses', LearningCourseViewSet, basename='learning-course')
router.register('enrollments', CourseEnrollmentViewSet, basename='enrollment')
router.register('quizzes', QuizViewSet, basename='quiz')

urlpatterns = router.urls
