from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('projects',              views.ProjectViewSet,            basename='project')
router.register('project-tasks',         views.ProjectTaskViewSet,        basename='project-task')
router.register('modification-requests', views.AttendanceModRequestViewSet, basename='attendance-mod')
router.register('',                      views.AttendanceViewSet,          basename='attendance')

urlpatterns = [path('', include(router.urls))]
