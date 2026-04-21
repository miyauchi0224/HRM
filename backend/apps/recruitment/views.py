from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.accounts.permissions import IsHR

from .models import JobPosting, Candidate, Interview
from .serializers import JobPostingSerializer, CandidateSerializer, InterviewSerializer
from apps.common.mixins import SoftDeleteViewSetMixin


class JobPostingViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    queryset = JobPosting.objects.all()
    serializer_class = JobPostingSerializer

    def get_permissions(self):
        if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return [IsHR()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CandidateViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    queryset = Candidate.objects.select_related('job_posting', 'assigned_to').prefetch_related('interviews').all()
    serializer_class = CandidateSerializer
    permission_classes = [IsHR]

    def get_queryset(self):
        qs = super().get_queryset()
        job_id = self.request.query_params.get('job')
        if job_id:
            qs = qs.filter(job_posting_id=job_id)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class InterviewViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    queryset = Interview.objects.select_related('candidate', 'interviewer').all()
    serializer_class = InterviewSerializer
    permission_classes = [IsHR]

    def get_queryset(self):
        qs = super().get_queryset()
        candidate_id = self.request.query_params.get('candidate')
        if candidate_id:
            qs = qs.filter(candidate_id=candidate_id)
        return qs
