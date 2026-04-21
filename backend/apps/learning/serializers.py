from rest_framework import serializers
from .models import (
    LearningCourse, CourseContent, CourseEnrollment, CourseAttachment,
    Quiz, QuizQuestion, QuizChoice, QuizAttempt, QuizAnswer,
)


class CourseAttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = CourseAttachment
        fields = ['id', 'file_name', 'file_size', 'content_type', 'is_image', 'url', 'created_at']

    def get_url(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return ''


class CourseContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseContent
        fields = '__all__'


class QuizChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizChoice
        fields = ['id', 'choice_text', 'is_correct', 'order']


class QuizChoicePublicSerializer(serializers.ModelSerializer):
    """受講者向け（正解フラグを隠す）"""
    class Meta:
        model = QuizChoice
        fields = ['id', 'choice_text', 'order']


class QuizQuestionSerializer(serializers.ModelSerializer):
    choices = QuizChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = QuizQuestion
        fields = ['id', 'question_text', 'question_type', 'order', 'explanation', 'points', 'choices']


class QuizQuestionPublicSerializer(serializers.ModelSerializer):
    """受講者向け（解説・正解を隠す）"""
    choices = QuizChoicePublicSerializer(many=True, read_only=True)

    class Meta:
        model = QuizQuestion
        fields = ['id', 'question_text', 'question_type', 'order', 'points', 'choices']


class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'course', 'title', 'description', 'pass_score',
                  'time_limit_minutes', 'question_count', 'questions', 'created_at']

    def get_question_count(self, obj):
        return obj.questions.count()


class QuizPublicSerializer(serializers.ModelSerializer):
    """受講者向け（解説なし）"""
    questions = QuizQuestionPublicSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'pass_score',
                  'time_limit_minutes', 'question_count', 'questions']

    def get_question_count(self, obj):
        return obj.questions.count()


class QuizAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAnswer
        fields = ['question', 'selected_choice', 'free_text_answer', 'is_correct']


class QuizAttemptSerializer(serializers.ModelSerializer):
    answers = QuizAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'score', 'is_passed', 'started_at', 'submitted_at', 'answers']


class LearningCourseSerializer(serializers.ModelSerializer):
    contents = CourseContentSerializer(many=True, read_only=True)
    attachments = CourseAttachmentSerializer(many=True, read_only=True)
    enrollment_count = serializers.SerializerMethodField()
    my_enrollment = serializers.SerializerMethodField()
    has_quiz = serializers.SerializerMethodField()

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

    def get_has_quiz(self, obj):
        return hasattr(obj, 'quiz')


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = '__all__'
        read_only_fields = ['employee']
