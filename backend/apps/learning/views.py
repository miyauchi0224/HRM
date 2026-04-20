from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.permissions import IsHR, IsNotCustomer

from .models import LearningCourse, CourseContent, CourseEnrollment
from .serializers import LearningCourseSerializer, CourseContentSerializer, CourseEnrollmentSerializer


class LearningCourseViewSet(viewsets.ModelViewSet):
    queryset = LearningCourse.objects.prefetch_related('contents', 'enrollments').all()
    serializer_class = LearningCourseSerializer

    def get_permissions(self):
        if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return [IsHR()]
        return [IsNotCustomer()]

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_hr:
            qs = qs.filter(status=LearningCourse.Status.PUBLISHED)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='enroll')
    def enroll(self, request, pk=None):
        """コースに受講登録"""
        course = self.get_object()
        try:
            emp = request.user.employee
        except Exception:
            return Response({'error': '社員情報が見つかりません'}, status=status.HTTP_403_FORBIDDEN)

        enrollment, created = CourseEnrollment.objects.get_or_create(
            course=course, employee=emp,
            defaults={'status': CourseEnrollment.Status.NOT_STARTED},
        )
        return Response(CourseEnrollmentSerializer(enrollment).data,
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class CourseEnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [IsNotCustomer]

    def get_queryset(self):
        user = self.request.user
        qs = CourseEnrollment.objects.select_related('course', 'employee').all()
        if user.is_hr:
            return qs
        try:
            return qs.filter(employee=user.employee)
        except Exception:
            return qs.none()

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user.employee)

    @action(detail=True, methods=['patch'], url_path='progress')
    def update_progress(self, request, pk=None):
        """進捗率を更新"""
        enrollment = self.get_object()
        pct = request.data.get('progress_pct', 0)
        enrollment.progress_pct = min(100, max(0, int(pct)))
        if enrollment.progress_pct == 100 and enrollment.status != CourseEnrollment.Status.COMPLETED:
            enrollment.status = CourseEnrollment.Status.COMPLETED
            enrollment.completed_at = timezone.now()
        elif enrollment.progress_pct > 0:
            if enrollment.status == CourseEnrollment.Status.NOT_STARTED:
                enrollment.status = CourseEnrollment.Status.IN_PROGRESS
                enrollment.started_at = enrollment.started_at or timezone.now()
        enrollment.save()
        return Response(CourseEnrollmentSerializer(enrollment).data)
