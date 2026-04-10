from django.urls import path
from . import views

urlpatterns = [
    path('',                views.notification_list, name='notification-list'),
    path('read-all/',       views.read_all,          name='notification-read-all'),
    path('<uuid:pk>/read/', views.mark_read,         name='notification-read'),
]
