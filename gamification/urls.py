from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BadgeViewSet, UserStatsViewSet, AdminStatsViewSet

router = DefaultRouter()
router.register(r'badges', BadgeViewSet, basename='badge')
router.register(r'user-stats', UserStatsViewSet, basename='userstats')
router.register(r'admin-stats', AdminStatsViewSet, basename='adminstats')

urlpatterns = [
    path('', include(router.urls)),
]
