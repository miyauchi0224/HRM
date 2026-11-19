from django.urls import path
from . import views

urlpatterns = [
    path('jobs/',                       views.job_list, name='scheduler-jobs'),
    path('jobs/<str:job_name>/run/',    views.run_now,  name='scheduler-run'),
    path('runs/',                       views.run_list, name='scheduler-runs'),
]
