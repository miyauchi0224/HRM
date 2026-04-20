from django.urls import path
from .views import DraftDailyReportView, DraftMBOReportView, AnalyzeExpenseReceiptView

urlpatterns = [
    path('draft-daily-report/', DraftDailyReportView.as_view(), name='ai-draft-daily-report'),
    path('draft-mbo-report/', DraftMBOReportView.as_view(), name='ai-draft-mbo-report'),
    path('analyze-receipt/', AnalyzeExpenseReceiptView.as_view(), name='ai-analyze-receipt'),
]
