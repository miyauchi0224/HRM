from rest_framework import serializers
from .models import LearningCourse, CourseContent, CourseEnrollment


class CourseContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseContent
        fields = '__all__'


class LearningCourseSerializer(serializers.ModelSerializer):
    contents = CourseContentSerializer(many=True, read_only=True)
    enrollment_count = serializers.SerializerMethodField()
    my_enrollment = serializers.SerializerMethodField()

    class Meta:
        model = LearningCourse
        fields = '__all__'

    def get_enrollment_count(self, obj):
        return obj.enrollments.count()

    def get_my_enrollment(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        try:
            emp = request.user.employee
            enrollment = obj.enrollments.filter(employee=emp).first()
            if enrollment:
                return CourseEnrollmentSerializer(enrollment).data
        except Exception:
            pass
        return None


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = '__all__'
        read_only_fields = ['employee']
