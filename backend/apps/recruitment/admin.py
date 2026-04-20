from django.contrib import admin
from .models import JobPosting, Candidate, Interview
admin.site.register(JobPosting)
admin.site.register(Candidate)
admin.site.register(Interview)
