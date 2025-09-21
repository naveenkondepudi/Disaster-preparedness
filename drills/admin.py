from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg
from .models import DrillScenario, DrillAttempt


class DrillAttemptInline(admin.TabularInline):
    """Inline admin for drill attempts."""
    model = DrillAttempt
    extra = 0
    readonly_fields = ['started_at', 'ended_at', 'score']
    fields = ['user', 'score', 'completed', 'started_at', 'ended_at']


@admin.register(DrillScenario)
class DrillScenarioAdmin(admin.ModelAdmin):
    """Admin interface for drill scenarios."""
    list_display = ['title', 'difficulty_level', 'estimated_duration', 'max_score', 'attempt_stats', 'is_active', 'created_at']
    list_filter = ['difficulty_level', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [DrillAttemptInline]
    
    def attempt_stats(self, obj):
        """Show attempt statistics for the drill."""
        try:
            from gamification.models import DrillCompletion
            
            attempts = DrillAttempt.objects.filter(scenario=obj)
            completions = DrillCompletion.objects.filter(drill_attempt__scenario=obj)
            
            total_attempts = attempts.count()
            completed_attempts = attempts.filter(completed=True).count()
            avg_score = attempts.aggregate(avg_score=Avg('score'))['avg_score'] or 0
            
            return format_html(
                '<span style="color: #3498db;">Attempts: {}</span><br>'
                '<span style="color: #27ae60;">Completed: {}</span><br>'
                '<span style="color: #f39c12;">Avg Score: {:.1f}</span>',
                total_attempts,
                completed_attempts,
                avg_score
            )
        except ImportError:
            return 'N/A'
    attempt_stats.short_description = 'Attempt Stats'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'difficulty_level')
        }),
        ('Configuration', {
            'fields': ('region_tags', 'estimated_duration', 'max_score', 'is_active')
        }),
        ('Scenario Data', {
            'fields': ('json_tree',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DrillAttempt)
class DrillAttemptAdmin(admin.ModelAdmin):
    """Admin interface for drill attempts."""
    list_display = ['user', 'scenario', 'score', 'completed', 'points_earned', 'started_at', 'ended_at']
    list_filter = ['completed', 'scenario', 'started_at']
    search_fields = ['user__email', 'scenario__title']
    readonly_fields = ['started_at', 'ended_at', 'score', 'percentage_score', 'duration', 'points_earned']
    
    def percentage_score(self, obj):
        """Display percentage score."""
        return f"{obj.get_percentage_score()}%"
    percentage_score.short_description = 'Score %'
    
    def duration(self, obj):
        """Display attempt duration."""
        duration = obj.get_duration()
        return f"{duration} min" if duration else "In progress"
    duration.short_description = 'Duration'
    
    def points_earned(self, obj):
        """Show points earned for this attempt."""
        try:
            from gamification.models import DrillCompletion
            completion = DrillCompletion.objects.filter(drill_attempt=obj).first()
            if completion:
                return format_html(
                    '<span style="color: #27ae60;">{}</span>',
                    completion.points_earned
                )
            return '0'
        except ImportError:
            return 'N/A'
    points_earned.short_description = 'Points Earned'
    
    fieldsets = (
        ('Attempt Information', {
            'fields': ('user', 'scenario', 'score', 'percentage_score', 'completed', 'points_earned')
        }),
        ('Timing', {
            'fields': ('started_at', 'ended_at', 'duration')
        }),
        ('Responses', {
            'fields': ('responses',),
            'classes': ('collapse',)
        }),
    )