from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models import Alert, Device
from .serializers import (
    AlertListSerializer, AlertDetailSerializer, AlertCreateSerializer,
    DeviceSerializer, DeviceRegisterSerializer
)


class IsAdminOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow admins to create/edit alerts."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_authenticated and request.user.role == 'ADMIN'


class AlertViewSet(viewsets.ModelViewSet):
    """ViewSet for managing alerts."""

    queryset = Alert.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return AlertListSerializer
        elif self.action == 'retrieve':
            return AlertDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AlertCreateSerializer
        return AlertDetailSerializer

    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter alerts based on query parameters."""
        queryset = Alert.objects.filter(is_active=True)

        # Filter by region if provided
        region = self.request.query_params.get('region')
        if region:
            queryset = queryset.filter(region_tags__contains=[region])

        # Filter by severity if provided
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)

        # Filter by source if provided
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source__icontains=source)

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            try:
                start_date = timezone.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                queryset = queryset.filter(published_at__gte=start_date)
            except ValueError:
                pass

        if end_date:
            try:
                end_date = timezone.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                queryset = queryset.filter(published_at__lte=end_date)
            except ValueError:
                pass

        # Exclude expired alerts by default
        exclude_expired = self.request.query_params.get('exclude_expired', 'true')
        if exclude_expired.lower() == 'true':
            queryset = queryset.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            )

        return queryset.order_by('-published_at')

    def list(self, request, *args, **kwargs):
        """List all active alerts with optional filtering."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific alert."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Create a new alert (admin only) and send push notifications."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        alert = serializer.save()

        # Send push notifications to all users
        try:
            from notifications.utils import send_alert_notification, get_device_tokens_for_regions

            # Get all active device tokens
            tokens = get_device_tokens_for_regions(alert.region_tags)

            if tokens:
                # Send push notification
                notification_result = send_alert_notification(
                    alert_id=alert.id,
                    title=alert.title,
                    description=alert.description,
                    severity=alert.severity,
                    region_tags=alert.region_tags,
                    tokens=tokens
                )

                # Log the result
                if notification_result.get("success"):
                    print(f"Push notifications sent successfully to {len(tokens)} devices for alert: {alert.title}")
                else:
                    print(f"Failed to send push notifications: {notification_result.get('error')}")
            else:
                print("No active device tokens found for push notifications")

        except Exception as e:
            print(f"Error sending push notifications: {str(e)}")
            # Don't fail the alert creation if notification fails

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all currently active alerts."""
        queryset = self.get_queryset().filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def critical(self, request):
        """Get all critical alerts."""
        queryset = self.get_queryset().filter(severity='CRITICAL')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsAdminOrReadOnly])
    def create_alert(self, request):
        """Create a new alert with push notifications (admin only)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        alert = serializer.save()

        # Send push notifications to all users
        notification_sent = False
        notification_error = None

        try:
            from notifications.utils import send_alert_notification, get_device_tokens_for_regions

            # Get all active device tokens
            tokens = get_device_tokens_for_regions(alert.region_tags)

            if tokens:
                # Send push notification
                notification_result = send_alert_notification(
                    alert_id=alert.id,
                    title=alert.title,
                    description=alert.description,
                    severity=alert.severity,
                    region_tags=alert.region_tags,
                    tokens=tokens
                )

                if notification_result.get("success"):
                    notification_sent = True
                else:
                    notification_error = notification_result.get('error')
            else:
                notification_error = "No active device tokens found"

        except Exception as e:
            notification_error = str(e)

        # Return response with notification status
        response_data = serializer.data.copy()
        response_data['notification_sent'] = notification_sent
        if notification_error:
            response_data['notification_error'] = notification_error

        return Response(
            response_data,
            status=status.HTTP_201_CREATED
        )


class DeviceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user devices."""

    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return devices for the current user."""
        return Device.objects.filter(user=self.request.user).order_by('-last_used')

    def create(self, request, *args, **kwargs):
        """Create a new device registration."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def list(self, request, *args, **kwargs):
        """List user's registered devices."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def register(self, request):
        """Register a device for push notifications."""
        serializer = DeviceRegisterSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            device = serializer.save()
            response_serializer = DeviceSerializer(device)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def test_notification(self, request, pk=None):
        """Send a test notification to the user's devices."""
        from notifications.utils import send_test_notification

        device = self.get_object()

        # Send test notification
        result = send_test_notification(
            token=device.token,
            title="Test Alert",
            body="This is a test notification from the disaster management system."
        )

        if result.get("success"):
            return Response({
                "message": "Test notification sent successfully",
                "result": result
            })
        else:
            return Response({
                "error": "Failed to send test notification",
                "details": result.get("error")
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def update_last_used(self, request, pk=None):
        """Update device last used timestamp."""
        device = self.get_object()
        device.update_last_used()
        serializer = self.get_serializer(device)
        return Response(serializer.data)