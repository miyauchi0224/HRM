from django.urls import path
from . import views

urlpatterns = [
    path('csrf/',             views.CsrfView.as_view(),           name='auth-csrf'),
    path('login/',            views.LoginView.as_view(),          name='auth-login'),
    path('logout/',           views.LogoutView.as_view(),         name='auth-logout'),
    path('refresh/',          views.RefreshView.as_view(),        name='auth-refresh'),
    path('me/',               views.me_view,                      name='auth-me'),
    path('password/change/',  views.change_password_view,         name='auth-password-change'),
    path('api-key/',          views.api_key_view,                 name='auth-api-key'),
]
