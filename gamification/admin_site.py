from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render
from django.db.models import Count, Avg
from django.contrib.auth import get_user_model

from gamification.models import UserPoints, UserBadge, LessonCompletion, QuizCompletion, DrillCompletion, Leaderboard
from learning.models import Module, Lesson, Quiz
from drills.models import DrillScenario, DrillAttempt
from alerts.models import Alert

User = get_user_model()


class CustomAdminSite(admin.AdminSite):
    """Custom admin site with enhanced dashboard."""
    
    site_header = "Disaster Preparedness Admin"
    site_title = "DP Admin"
    index_title = "Disaster Preparedness Dashboard"
    
    def get_urls(self):
        """Add custom admin URLs."""
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
            path('user-analytics/', self.admin_view(self.user_analytics_view), name='user_analytics'),
            path('content-analytics/', self.admin_view(self.content_analytics_view), name='content_analytics'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Custom dashboard view."""
        # Get overview statistics
        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'total_modules': Module.objects.count(),
            'total_lessons': Lesson.objects.count(),
            'total_quizzes': Quiz.objects.count(),
            'total_drills': DrillScenario.objects.count(),
            'total_alerts': Alert.objects.count(),
        }
        
        # Get completion statistics
        completion_stats = {
            'lesson_completions': LessonCompletion.objects.count(),
            'quiz_completions': QuizCompletion.objects.count(),
            'drill_completions': DrillCompletion.objects.count(),
        }
        
        # Get top performers
        top_performers = Leaderboard.objects.select_related('user')[:10]
        
        # Get recent activity
        recent_lesson_completions = LessonCompletion.objects.select_related('user', 'lesson').order_by('-completed_at')[:5]
        recent_quiz_completions = QuizCompletion.objects.select_related('user', 'quiz').order_by('-completed_at')[:5]
        recent_drill_completions = DrillCompletion.objects.select_related('user', 'drill_attempt__scenario').order_by('-completed_at')[:5]
        
        context = {
            'title': 'Dashboard Overview',
            'stats': stats,
            'completion_stats': completion_stats,
            'top_performers': top_performers,
            'recent_lesson_completions': recent_lesson_completions,
            'recent_quiz_completions': recent_quiz_completions,
            'recent_drill_completions': recent_drill_completions,
        }
        
        return render(request, 'admin/dashboard.html', context)
    
    def user_analytics_view(self, request):
        """User analytics view."""
        # Get user statistics by role
        user_stats_by_role = User.objects.values('role').annotate(
            count=Count('id'),
            active_count=Count('id', filter=models.Q(is_active=True))
        )
        
        # Get points distribution
        points_distribution = UserPoints.objects.extra(
            select={
                'points_range': "CASE "
                "WHEN total_points < 100 THEN '0-99' "
                "WHEN total_points < 500 THEN '100-499' "
                "WHEN total_points < 1000 THEN '500-999' "
                "ELSE '1000+' END"
            }
        ).values('points_range').annotate(count=Count('id'))
        
        # Get badge distribution
        badge_distribution = UserBadge.objects.values('badge__name').annotate(
            count=Count('user', distinct=True)
        ).order_by('-count')
        
        context = {
            'title': 'User Analytics',
            'user_stats_by_role': user_stats_by_role,
            'points_distribution': points_distribution,
            'badge_distribution': badge_distribution,
        }
        
        return render(request, 'admin/user_analytics.html', context)
    
    def content_analytics_view(self, request):
        """Content analytics view."""
        # Module completion rates
        module_stats = Module.objects.annotate(
            lesson_count=Count('lessons'),
            quiz_count=Count('quiz'),
            lesson_completions=Count('lessons__completions'),
            quiz_completions=Count('quiz__completions'),
        )
        
        # Drill performance
        drill_stats = DrillScenario.objects.annotate(
            attempt_count=Count('attempts'),
            avg_score=Avg('attempts__score'),
        )
        
        context = {
            'title': 'Content Analytics',
            'module_stats': module_stats,
            'drill_stats': drill_stats,
        }
        
        return render(request, 'admin/content_analytics.html', context)
    
    def index(self, request, extra_context=None):
        """Override index to show custom dashboard."""
        extra_context = extra_context or {}
        
        # Add quick stats to index
        extra_context.update({
            'total_users': User.objects.count(),
            'total_modules': Module.objects.count(),
            'total_drills': DrillScenario.objects.count(),
            'total_alerts': Alert.objects.count(),
        })
        
        return super().index(request, extra_context)


# Create custom admin site instance
admin_site = CustomAdminSite(name='custom_admin')

# Register all models with custom admin site
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.admin import UserAdmin
from learning.admin import ModuleAdmin, LessonAdmin, QuizAdmin, QuestionAdmin
from drills.admin import DrillScenarioAdmin, DrillAttemptAdmin
from alerts.admin import AlertAdmin, DeviceAdmin
from gamification.admin import BadgeAdmin, UserPointsAdmin, UserBadgeAdmin, LessonCompletionAdmin, QuizCompletionAdmin, DrillCompletionAdmin, LeaderboardAdmin

admin_site.register(User, UserAdmin)
admin_site.register(Module, ModuleAdmin)
admin_site.register(Lesson, LessonAdmin)
admin_site.register(Quiz, QuizAdmin)
admin_site.register(Question, QuestionAdmin)
admin_site.register(DrillScenario, DrillScenarioAdmin)
admin_site.register(DrillAttempt, DrillAttemptAdmin)
admin_site.register(Alert, AlertAdmin)
admin_site.register(Device, DeviceAdmin)
admin_site.register(Badge, BadgeAdmin)
admin_site.register(UserPoints, UserPointsAdmin)
admin_site.register(UserBadge, UserBadgeAdmin)
admin_site.register(LessonCompletion, LessonCompletionAdmin)
admin_site.register(QuizCompletion, QuizCompletionAdmin)
admin_site.register(DrillCompletion, DrillCompletionAdmin)
admin_site.register(Leaderboard, LeaderboardAdmin)
