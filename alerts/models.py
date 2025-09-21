from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone

User = get_user_model()


class Alert(models.Model):
    """Emergency alert/disaster warning."""
    
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    title = models.CharField(max_length=200, help_text='Alert title')
    description = models.TextField(help_text='Detailed alert description')
    region_tags = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text='Regions affected by this alert'
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='MEDIUM',
        help_text='Severity level of the alert'
    )
    source = models.CharField(
        max_length=100,
        default='NDMA',
        help_text='Source of the alert (NDMA, IMD, etc.)'
    )
    geometry = models.JSONField(
        null=True,
        blank=True,
        help_text='GeoJSON geometry for mapping'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this alert is currently active'
    )
    published_at = models.DateTimeField(
        default=timezone.now,
        help_text='When the alert was published'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the alert expires (optional)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'alerts'
        verbose_name = 'Alert'
        verbose_name_plural = 'Alerts'
        ordering = ['-published_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_severity_display()})"
    
    def is_expired(self):
        """Check if the alert has expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def get_affected_regions(self):
        """Get list of affected regions."""
        return self.region_tags if self.region_tags else ['All Regions']


class Device(models.Model):
    """User device for push notifications."""
    
    PLATFORM_CHOICES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='devices',
        help_text='User who owns this device'
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        help_text='Expo push notification token'
    )
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        help_text='Device platform'
    )
    device_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='User-friendly device name'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this device is active for notifications'
    )
    last_used = models.DateTimeField(
        auto_now=True,
        help_text='Last time this device was used'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'devices'
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'
        ordering = ['-last_used']
        unique_together = ['user', 'token']
    
    def __str__(self):
        return f"{self.user.email} - {self.get_platform_display()} ({self.device_name or 'Unknown'})"
    
    def update_last_used(self):
        """Update the last used timestamp."""
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])