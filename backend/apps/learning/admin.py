from django.contrib import admin
from .models import LearningCourse, CourseContent, CourseEnrollment
admin.site.register(LearningCourse)
admin.site.register(CourseContent)
admin.site.register(CourseEnrollment)
