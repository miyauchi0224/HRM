from rest_framework import serializers
from .models import DEFAULT_QUESTIONS, PulseQuestion, PulseSurvey


class PulseQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PulseQuestion
        fields = ['id', 'order', 'text', 'kind', 'is_required']
        read_only_fields = ['id']


class PulseSurveySerializer(serializers.ModelSerializer):
    questions      = PulseQuestionSerializer(many=True, required=False)
    has_answered   = serializers.SerializerMethodField()
    response_count = serializers.SerializerMethodField()

    class Meta:
        model  = PulseSurvey
        fields = ['id', 'title', 'description', 'start_date', 'end_date', 'is_published',
                  'is_anonymous', 'questions', 'has_answered', 'response_count', 'created_at']
        read_only_fields = ['id', 'is_published', 'created_at']

    def get_has_answered(self, obj):
        request  = self.context.get('request')
        employee = getattr(getattr(request, 'user', None), 'employee', None)
        return bool(employee and obj.participations.filter(employee=employee).exists())

    def get_response_count(self, obj):
        return obj.participations.count()

    def validate(self, data):
        start = data.get('start_date', getattr(self.instance, 'start_date', None))
        end   = data.get('end_date', getattr(self.instance, 'end_date', None))
        if start and end and end < start:
            raise serializers.ValidationError({'end_date': '終了日は開始日以降にしてください'})
        if self.instance is not None and self.instance.is_published:
            if 'questions' in data or 'is_anonymous' in data:
                raise serializers.ValidationError('公開後は質問と匿名設定を変更できません')
        return data

    def _save_questions(self, survey, questions):
        survey.questions.all().delete()
        for i, q in enumerate(questions):
            PulseQuestion.objects.create(
                survey=survey, order=i + 1, text=q['text'], kind=q.get('kind', PulseQuestion.Kind.SCALE5),
                is_required=q.get('is_required', True),
            )

    def create(self, validated_data):
        questions = validated_data.pop('questions', None) or DEFAULT_QUESTIONS
        survey = super().create(validated_data)
        self._save_questions(survey, questions)
        return survey

    def update(self, instance, validated_data):
        questions = validated_data.pop('questions', None)
        survey = super().update(instance, validated_data)
        if questions is not None:
            self._save_questions(survey, questions)
        return survey
