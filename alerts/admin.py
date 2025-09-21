from django.contrib import admin
from .models import Alert, Device


class DeviceInline(admin.TabularInline):
    """Inline admin for user devices."""
    model = Device
    extra = 0
    readonly_fields = ['last_used', 'created_at']
    fields = ['token', 'platform', 'device_name', 'is_active', 'last_used']


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    """Admin interface for alerts."""
    list_display = ['title', 'severity', 'source', 'is_active', 'published_at', 'expires_at']
    list_filter = ['severity', 'source', 'is_active', 'published_at']
    search_fields = ['title', 'description', 'region_tags']
    readonly_fields = ['created_at', 'updated_at', 'is_expired']
    date_hierarchy = 'published_at'
    
    def is_expired(self, obj):
        """Display if alert is expired."""
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('title', 'description', 'severity', 'source')
        }),
        ('Targeting', {
            'fields': ('region_tags', 'geometry')
        }),
        ('Status & Timing', {
            'fields': ('is_active', 'published_at', 'expires_at', 'is_expired')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Override save to trigger push notifications."""
        super().save_model(request, obj, form, change)
        # Push notifications will be sent via the post_save signal


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """Admin interface for user devices."""
    list_display = ['user', 'platform', 'device_name', 'is_active', 'last_used', 'created_at']
    list_filter = ['platform', 'is_active', 'created_at']
    search_fields = ['user__email', 'device_name', 'token']
    readonly_fields = ['last_used', 'created_at']
    
    fieldsets = (
        ('Device Information', {
            'fields': ('user', 'token', 'platform', 'device_name')
        }),
        ('Status', {
            'fields': ('is_active', 'last_used', 'created_at')
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')