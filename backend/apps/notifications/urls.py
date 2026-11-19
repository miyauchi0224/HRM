from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('webhooks', views.WebhookEndpointViewSet, basename='webhook-endpoint')

urlpatterns = [
    path('',                       views.notification_list,     name='notification-list'),
    path('read-all/',              views.read_all,              name='notification-read-all'),
    path('types/',                 views.notification_types,    name='notification-types'),
    path('personal-webhook/',      views.personal_webhook,      name='personal-webhook'),
    path('personal-webhook/test/', views.personal_webhook_test, name='personal-webhook-test'),
    path('<uuid:pk>/read/',        views.mark_read,             name='notification-read'),
    path('',                       include(router.urls)),
]
