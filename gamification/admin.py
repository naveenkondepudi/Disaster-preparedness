from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Badge, UserPoints, UserBadge, LessonCompletion, QuizCompletion, DrillCompletion, Leaderboard


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['icon', 'name', 'threshold_points', 'color_display', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['threshold_points']
    
    def color_display(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            obj.color,
            obj.color
        )
    color_display.short_description = 'Color'


@admin.register(UserPoints)
class UserPointsAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_points', 'lesson_points', 'quiz_points', 'drill_points', 'current_badge', 'last_updated']
    list_filter = ['last_updated', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'last_updated']
    ordering = ['-total_points']
    
    def current_badge(self, obj):
        badge = obj.get_current_badge()
        if badge:
            return format_html(
                '<span style="color: {};">{} {}</span>',
                badge.color,
                badge.icon,
                badge.name
            )
        return '-'
    current_badge.short_description = 'Current Badge'


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge_display', 'earned_at']
    list_filter = ['badge', 'earned_at']
    search_fields = ['user__email', 'badge__name']
    readonly_fields = ['earned_at']
    ordering = ['-earned_at']
    
    def badge_display(self, obj):
        return format_html(
            '<span style="color: {};">{} {}</span>',
            obj.badge.color,
            obj.badge.icon,
            obj.badge.name
        )
    badge_display.short_description = 'Badge'


@admin.register(LessonCompletion)
class LessonCompletionAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'points_earned', 'completed_at']
    list_filter = ['completed_at', 'lesson__module']
    search_fields = ['user__email', 'lesson__title']
    readonly_fields = ['completed_at']
    ordering = ['-completed_at']


@admin.register(QuizCompletion)
class QuizCompletionAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'score', 'points_earned', 'completed_at']
    list_filter = ['completed_at', 'quiz__module']
    search_fields = ['user__email', 'quiz__title']
    readonly_fields = ['completed_at']
    ordering = ['-completed_at']


@admin.register(DrillCompletion)
class DrillCompletionAdmin(admin.ModelAdmin):
    list_display = ['user', 'drill_attempt', 'points_earned', 'completed_at']
    list_filter = ['completed_at']
    search_fields = ['user__email']
    readonly_fields = ['completed_at']
    ordering = ['-completed_at']


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ['rank', 'user', 'total_points', 'badge_count', 'lessons_completed', 'quizzes_completed', 'drills_completed', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['user__email']
    readonly_fields = ['last_updated']
    ordering = ['rank']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False