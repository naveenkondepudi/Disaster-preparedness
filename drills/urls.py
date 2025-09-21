from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DrillScenarioViewSet, DrillAttemptViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'scenarios', DrillScenarioViewSet, basename='drillscenario')
router.register(r'attempts', DrillAttemptViewSet, basename='drillattempt')

urlpatterns = [
    path('', include(router.urls)),
]
