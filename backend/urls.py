"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from . import views

def health_check(request):
    """Health check endpoint for testing."""
    return JsonResponse({
        'status': 'healthy',
        'message': 'Disaster Preparedness Backend API is running',
        'version': '1.0.0'
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health'),
    path('api/users/', include('users.urls')),
    path('api/learning/', include('learning.urls')),
    path('api/drills/', include('drills.urls')),
    path('api/alerts/', include('alerts.urls')),
    path('api/gamification/', include('gamification.urls')),
    # Database population endpoints
    path('api/populate/', views.populate_database, name='populate_database'),
    path('api/force-populate/', views.force_populate_database, name='force_populate_database'),
    path('api/database-status/', views.database_status, name='database_status'),
]
