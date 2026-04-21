from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from apps.accounts.permissions import IsHR, IsNotCustomer

from .models import (
    LearningCourse, CourseContent, CourseEnrollment, CourseAttachment,
    Quiz, QuizQuestion, QuizChoice, QuizAttempt, QuizAnswer,
)
from .serializers import (
    LearningCourseSerializer, CourseContentSerializer, CourseEnrollmentSerializer,
    CourseAttachmentSerializer, QuizSerializer, QuizPublicSerializer,
    QuizQuestionSerializer, QuizChoiceSerializer, QuizAttemptSerializer,
)
from apps.common.mixins import SoftDeleteViewSetMixin


class LearningCourseViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    queryset = LearningCourse.objects.prefetch_related('contents', 'enrollments', 'attachments').all()
    serializer_class = LearningCourseSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

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
        course = serializer.save(created_by=self.request.user)
        self._save_attachments(course, self.request)

    def perform_update(self, serializer):
        course = serializer.save()
        self._save_attachments(course, self.request)

    def _save_attachments(self, course, request):
        files = request.FILES.getlist('files')
        for f in files:
            CourseAttachment.objects.create(
                course=course,
                file=f,
                file_name=f.name,
                file_size=f.size,
                content_type=f.content_type or 'application/octet-stream',
                uploaded_by=request.user,
            )

    @action(detail=True, methods=['delete'], url_path='attachments/(?P<att_id>[^/.]+)')
    def delete_attachment(self, request, pk=None, att_id=None):
        try:
            att = CourseAttachment.objects.get(id=att_id, course_id=pk)
            att.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CourseAttachment.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

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

    @action(detail=True, methods=['get'], url_path='quiz')
    def get_quiz(self, request, pk=None):
        """コースのテストを取得"""
        course = self.get_object()
        if not hasattr(course, 'quiz'):
            return Response({'detail': 'テストが設定されていません'}, status=status.HTTP_404_NOT_FOUND)
        is_hr = getattr(request.user, 'is_hr', False)
        serializer_class = QuizSerializer if is_hr else QuizPublicSerializer
        return Response(serializer_class(course.quiz, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='quiz/create', permission_classes=[IsHR])
    def create_quiz(self, request, pk=None):
        """テストを新規作成（HR専用）"""
        course = self.get_object()
        if hasattr(course, 'quiz'):
            return Response({'detail': 'テストはすでに存在します。編集してください。'}, status=status.HTTP_400_BAD_REQUEST)
        data = request.data
        quiz = Quiz.objects.create(
            course=course,
            title=data.get('title', '理解度確認テスト'),
            description=data.get('description', ''),
            pass_score=data.get('pass_score', 70),
            time_limit_minutes=data.get('time_limit_minutes') or None,
        )
        return Response(QuizSerializer(quiz, context={'request': request}).data, status=status.HTTP_201_CREATED)


class CourseEnrollmentViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
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


class QuizViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    """テスト管理（HR専用）"""
    serializer_class = QuizSerializer

    def get_permissions(self):
        if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return [IsHR()]
        return [IsNotCustomer()]

    def get_queryset(self):
        return Quiz.objects.prefetch_related('questions__choices').all()

    @action(detail=True, methods=['post'], url_path='questions', permission_classes=[IsHR])
    def add_question(self, request, pk=None):
        """問題を追加"""
        quiz = self.get_object()
        data = request.data
        question = QuizQuestion.objects.create(
            quiz=quiz,
            question_text=data['question_text'],
            question_type=data.get('question_type', 'choice'),
            order=data.get('order', quiz.questions.count()),
            explanation=data.get('explanation', ''),
            points=data.get('points', 1),
        )
        # 選択肢を一緒に作成（選択式の場合）
        for i, choice_data in enumerate(data.get('choices', [])):
            QuizChoice.objects.create(
                question=question,
                choice_text=choice_data['choice_text'],
                is_correct=choice_data.get('is_correct', False),
                order=i,
            )
        return Response(QuizQuestionSerializer(question).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put'], url_path='questions/(?P<q_id>[^/.]+)', permission_classes=[IsHR])
    def update_question(self, request, pk=None, q_id=None):
        """問題を更新"""
        try:
            question = QuizQuestion.objects.get(id=q_id, quiz_id=pk)
        except QuizQuestion.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        data = request.data
        question.question_text = data.get('question_text', question.question_text)
        question.question_type = data.get('question_type', question.question_type)
        question.order = data.get('order', question.order)
        question.explanation = data.get('explanation', question.explanation)
        question.points = data.get('points', question.points)
        question.save()
        # 選択肢を再作成
        if 'choices' in data:
            question.choices.all().delete()
            for i, choice_data in enumerate(data['choices']):
                QuizChoice.objects.create(
                    question=question,
                    choice_text=choice_data['choice_text'],
                    is_correct=choice_data.get('is_correct', False),
                    order=i,
                )
        return Response(QuizQuestionSerializer(question).data)

    @action(detail=True, methods=['delete'], url_path='questions/(?P<q_id>[^/.]+)', permission_classes=[IsHR])
    def delete_question(self, request, pk=None, q_id=None):
        """問題を削除"""
        try:
            question = QuizQuestion.objects.get(id=q_id, quiz_id=pk)
            question.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except QuizQuestion.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='start')
    def start_attempt(self, request, pk=None):
        """テスト受験開始"""
        quiz = self.get_object()
        try:
            emp = request.user.employee
        except Exception:
            return Response({'error': '社員情報が見つかりません'}, status=status.HTTP_403_FORBIDDEN)
        attempt = QuizAttempt.objects.create(quiz=quiz, employee=emp)
        return Response(QuizAttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='submit/(?P<attempt_id>[^/.]+)')
    def submit_attempt(self, request, pk=None, attempt_id=None):
        """テスト回答を提出・採点"""
        quiz = self.get_object()
        try:
            emp = request.user.employee
            attempt = QuizAttempt.objects.get(id=attempt_id, quiz=quiz, employee=emp)
        except (QuizAttempt.DoesNotExist, Exception):
            return Response({'error': '受験記録が見つかりません'}, status=status.HTTP_404_NOT_FOUND)

        if attempt.submitted_at:
            return Response({'error': 'すでに提出済みです'}, status=status.HTTP_400_BAD_REQUEST)

        answers_data = request.data.get('answers', [])
        total_points = 0
        earned_points = 0

        for ans_data in answers_data:
            question_id = ans_data.get('question')
            try:
                question = QuizQuestion.objects.get(id=question_id, quiz=quiz)
            except QuizQuestion.DoesNotExist:
                continue

            total_points += question.points
            is_correct = None
            selected_choice = None

            if question.question_type == 'choice':
                choice_id = ans_data.get('selected_choice')
                if choice_id:
                    try:
                        selected_choice = QuizChoice.objects.get(id=choice_id, question=question)
                        is_correct = selected_choice.is_correct
                        if is_correct:
                            earned_points += question.points
                    except QuizChoice.DoesNotExist:
                        pass

            QuizAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    'selected_choice': selected_choice,
                    'free_text_answer': ans_data.get('free_text_answer', ''),
                    'is_correct': is_correct,
                },
            )

        # スコア算出（自由記述は採点対象外）
        choice_questions = quiz.questions.filter(question_type='choice')
        choice_total = sum(q.points for q in choice_questions)
        score_pct = int(earned_points / choice_total * 100) if choice_total > 0 else 0

        attempt.score = score_pct
        attempt.is_passed = score_pct >= quiz.pass_score
        attempt.submitted_at = timezone.now()
        attempt.save()

        # 受講記録のscoreを更新
        try:
            enrollment = CourseEnrollment.objects.get(course=quiz.course, employee=emp)
            enrollment.score = score_pct
            enrollment.save()
        except CourseEnrollment.DoesNotExist:
            pass

        return Response(QuizAttemptSerializer(attempt, context={'request': request}).data)

    @action(detail=True, methods=['get'], url_path='my-attempts')
    def my_attempts(self, request, pk=None):
        """自分の受験履歴"""
        quiz = self.get_object()
        try:
            emp = request.user.employee
        except Exception:
            return Response([])
        attempts = QuizAttempt.objects.filter(quiz=quiz, employee=emp).prefetch_related('answers')
        return Response(QuizAttemptSerializer(attempts, many=True, context={'request': request}).data)
