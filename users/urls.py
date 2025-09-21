from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('logout-all/', views.logout_all, name='logout_all'),
    path('refresh/', views.refresh_token, name='refresh_token'),
    path('me/', views.profile, name='profile'),
]
