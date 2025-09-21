from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlertViewSet, DeviceViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'devices', DeviceViewSet, basename='device')

urlpatterns = [
    path('', include(router.urls)),
]
