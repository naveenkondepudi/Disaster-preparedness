from rest_framework import serializers
from .models import Alert, Device


class AlertListSerializer(serializers.ModelSerializer):
    """Serializer for alert list view."""
    
    is_expired = serializers.SerializerMethodField()
    affected_regions = serializers.SerializerMethodField()
    
    class Meta:
        model = Alert
        fields = [
            'id', 'title', 'description', 'region_tags', 'severity',
            'source', 'is_active', 'is_expired', 'affected_regions',
            'published_at', 'expires_at'
        ]
        read_only_fields = ['id', 'published_at']
    
    def get_is_expired(self, obj):
        """Check if alert is expired."""
        return obj.is_expired()
    
    def get_affected_regions(self, obj):
        """Get affected regions."""
        return obj.get_affected_regions()


class AlertDetailSerializer(serializers.ModelSerializer):
    """Serializer for alert detail view."""
    
    is_expired = serializers.SerializerMethodField()
    affected_regions = serializers.SerializerMethodField()
    
    class Meta:
        model = Alert
        fields = [
            'id', 'title', 'description', 'region_tags', 'severity',
            'source', 'geometry', 'is_active', 'is_expired',
            'affected_regions', 'published_at', 'expires_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'published_at', 'created_at', 'updated_at']
    
    def get_is_expired(self, obj):
        """Check if alert is expired."""
        return obj.is_expired()
    
    def get_affected_regions(self, obj):
        """Get affected regions."""
        return obj.get_affected_regions()


class AlertCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating alerts (admin only)."""
    
    class Meta:
        model = Alert
        fields = [
            'id', 'title', 'description', 'region_tags', 'severity',
            'source', 'geometry', 'is_active', 'expires_at'
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        """Create a new alert."""
        return super().create(validated_data)


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for user devices."""
    
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    
    class Meta:
        model = Device
        fields = [
            'id', 'token', 'platform', 'platform_display', 'device_name',
            'is_active', 'last_used', 'created_at'
        ]
        read_only_fields = ['id', 'last_used', 'created_at']
    
    def create(self, validated_data):
        """Create a new device registration."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_token(self, value):
        """Validate Expo push token format."""
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid push token format.")
        return value


class DeviceRegisterSerializer(serializers.Serializer):
    """Serializer for device registration."""
    
    token = serializers.CharField(max_length=255, help_text='Expo push notification token')
    platform = serializers.ChoiceField(choices=Device.PLATFORM_CHOICES, help_text='Device platform')
    device_name = serializers.CharField(max_length=100, required=False, help_text='Device name')
    
    def validate_token(self, value):
        """Validate Expo push token format."""
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid push token format.")
        return value
    
    def create(self, validated_data):
        """Create or update device registration."""
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            raise serializers.ValidationError("User context is required")
            
        user = request.user
        token = validated_data['token']
        
        # Update existing device or create new one
        device, created = Device.objects.update_or_create(
            user=user,
            token=token,
            defaults={
                'platform': validated_data['platform'],
                'device_name': validated_data.get('device_name', ''),
                'is_active': True
            }
        )
        
        return device
