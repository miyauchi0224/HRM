from rest_framework import serializers
from .models import JobPosting, Candidate, Interview


class InterviewSerializer(serializers.ModelSerializer):
    interviewer_name = serializers.CharField(source='interviewer.full_name', read_only=True)

    class Meta:
        model = Interview
        fields = '__all__'


class CandidateSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job_posting.title', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.full_name', read_only=True)
    interviews = InterviewSerializer(many=True, read_only=True)

    class Meta:
        model = Candidate
        fields = '__all__'


class JobPostingSerializer(serializers.ModelSerializer):
    candidate_count = serializers.SerializerMethodField()

    class Meta:
        model = JobPosting
        fields = '__all__'

    def get_candidate_count(self, obj):
        return obj.candidates.count()
