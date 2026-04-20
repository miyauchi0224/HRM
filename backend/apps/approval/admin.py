from django.contrib import admin
from .models import ApprovalRequest, ApprovalStep, ApprovalTemplate

admin.site.register(ApprovalTemplate)
admin.site.register(ApprovalRequest)
admin.site.register(ApprovalStep)
