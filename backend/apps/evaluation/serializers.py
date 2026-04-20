from rest_framework import serializers
from .models import EvaluationPeriod, EvaluationQuestion, Evaluation360, EvaluationScore


class EvaluationPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationPeriod
        fields = '__all__'


class EvaluationQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationQuestion
        fields = '__all__'


class EvaluationScoreSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)

    class Meta:
        model = EvaluationScore
        fields = ['id', 'question', 'question_text', 'score', 'comment']


class Evaluation360Serializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.full_name', read_only=True)
    evaluator_name = serializers.CharField(source='evaluator.full_name', read_only=True)
    scores = EvaluationScoreSerializer(many=True, required=False)

    class Meta:
        model = Evaluation360
        fields = [
            'id', 'period', 'subject', 'subject_name', 'evaluator', 'evaluator_name',
            'evaluator_type', 'is_submitted', 'submitted_at', 'overall_comment',
            'created_at', 'scores',
        ]
        read_only_fields = ['evaluator', 'is_submitted', 'submitted_at']

    def create(self, validated_data):
        scores_data = validated_data.pop('scores', [])
        evaluation = super().create(validated_data)
        for score_data in scores_data:
            EvaluationScore.objects.create(evaluation=evaluation, **score_data)
        return evaluation

    def update(self, instance, validated_data):
        scores_data = validated_data.pop('scores', [])
        evaluation = super().update(instance, validated_data)
        for score_data in scores_data:
            EvaluationScore.objects.update_or_create(
                evaluation=evaluation,
                question=score_data['question'],
                defaults={'score': score_data['score'], 'comment': score_data.get('comment', '')},
            )
        return evaluation
