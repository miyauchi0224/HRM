from django.urls import path
from .views import (
    DraftDailyReportView, DraftMBOReportView, DraftMBOGoalView,
    AnalyzeExpenseReceiptView, HRQueryView,
    DraftIntraArticleView, DraftJobPostingView, DraftNextMonthIssueView,
)

urlpatterns = [
    path('draft-daily-report/',     DraftDailyReportView.as_view(),     name='ai-draft-daily-report'),
    path('draft-mbo-report/',       DraftMBOReportView.as_view(),       name='ai-draft-mbo-report'),
    path('draft-mbo-goal/',         DraftMBOGoalView.as_view(),         name='ai-draft-mbo-goal'),
    path('analyze-receipt/',        AnalyzeExpenseReceiptView.as_view(), name='ai-analyze-receipt'),
    path('hr-query/',               HRQueryView.as_view(),               name='ai-hr-query'),
    path('draft-intra-article/',    DraftIntraArticleView.as_view(),     name='ai-draft-intra-article'),
    path('draft-job-posting/',      DraftJobPostingView.as_view(),       name='ai-draft-job-posting'),
    path('draft-next-month-issue/', DraftNextMonthIssueView.as_view(),   name='ai-draft-next-month-issue'),
]
