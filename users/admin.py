from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model."""
    
    list_display = ('username', 'email', 'role', 'institution', 'gamification_stats', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'institution')
    ordering = ('-date_joined',)
    
    def gamification_stats(self, obj):
        """Show gamification statistics for the user."""
        try:
            from gamification.models import UserPoints, UserBadge
            
            user_points = UserPoints.objects.filter(user=obj).first()
            if user_points:
                badge_count = UserBadge.objects.filter(user=obj).count()
                current_badge = user_points.get_current_badge()
                
                badge_display = ''
                if current_badge:
                    badge_display = format_html(
                        '<br><span style="color: {};">{}</span>',
                        current_badge.color,
                        current_badge.icon
                    )
                
                return format_html(
                    '<span style="color: #3498db;">Points: {}</span><br>'
                    '<span style="color: #27ae60;">Badges: {}</span>{}',
                    user_points.total_points,
                    badge_count,
                    badge_display
                )
            return 'No points'
        except ImportError:
            return 'N/A'
    gamification_stats.short_description = 'Gamification Stats'
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Disaster Prep Info', {
            'fields': ('role', 'phone_number', 'emergency_contact', 'institution', 'grade_class')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Disaster Prep Info', {
            'fields': ('role', 'phone_number', 'emergency_contact', 'institution', 'grade_class')
        }),
    )
