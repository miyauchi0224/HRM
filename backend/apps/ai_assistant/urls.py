from django.urls import path
from .views import (
    DraftDailyReportView, DraftMBOReportView, DraftMBOGoalView,
    AnalyzeExpenseReceiptView, HRQueryView,
)

urlpatterns = [
    path('draft-daily-report/', DraftDailyReportView.as_view(), name='ai-draft-daily-report'),
    path('draft-mbo-report/',   DraftMBOReportView.as_view(),   name='ai-draft-mbo-report'),
    path('draft-mbo-goal/',     DraftMBOGoalView.as_view(),     name='ai-draft-mbo-goal'),
    path('analyze-receipt/',    AnalyzeExpenseReceiptView.as_view(), name='ai-analyze-receipt'),
    path('hr-query/',           HRQueryView.as_view(),          name='ai-hr-query'),
]
