from django.urls import path
from .views import (AttendanceTrendView, LeaveUsageView,
                    HeadcountView, ExpenseSummaryView, OvertimeRankingView)

urlpatterns = [
    path('attendance-trend/', AttendanceTrendView.as_view(), name='analytics-attendance-trend'),
    path('leave-usage/', LeaveUsageView.as_view(), name='analytics-leave-usage'),
    path('headcount/', HeadcountView.as_view(), name='analytics-headcount'),
    path('expense-summary/', ExpenseSummaryView.as_view(), name='analytics-expense-summary'),
    path('overtime-ranking/', OvertimeRankingView.as_view(), name='analytics-overtime-ranking'),
]
