from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from alerts.models import Device
from notifications.utils import send_test_notification, send_alert_notification

User = get_user_model()


class Command(BaseCommand):
    help = 'Send test push notifications to registered devices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--device-id',
            type=int,
            help='Send test notification to specific device ID'
        )
        parser.add_argument(
            '--alert-test',
            action='store_true',
            help='Send a test disaster alert notification'
        )
        parser.add_argument(
            '--all-devices',
            action='store_true',
            help='Send test notification to all active devices'
        )

    def handle(self, *args, **options):
        if options['device_id']:
            self.send_to_device(options['device_id'])
        elif options['alert_test']:
            self.send_alert_test()
        elif options['all_devices']:
            self.send_to_all_devices()
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Please specify --device-id, --alert-test, or --all-devices'
                )
            )

    def send_to_device(self, device_id):
        """Send test notification to a specific device."""
        try:
            device = Device.objects.get(id=device_id)
            
            self.stdout.write(f"Sending test notification to device {device_id}...")
            
            result = send_test_notification(
                token=device.token,
                title="Test Notification",
                body=f"Hello {device.user.first_name}! This is a test notification."
            )
            
            if result.get('success'):
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Test notification sent successfully to {device.user.email}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to send notification: {result.get('error')}"
                    )
                )
                
        except Device.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Device with ID {device_id} not found")
            )

    def send_alert_test(self):
        """Send a test disaster alert notification."""
        devices = Device.objects.filter(is_active=True)
        
        if not devices.exists():
            self.stdout.write(
                self.style.WARNING("No active devices found for alert test")
            )
            return
        
        tokens = [device.token for device in devices]
        
        self.stdout.write(f"Sending test alert to {len(tokens)} devices...")
        
        result = send_alert_notification(
            alert_id=999,  # Test alert ID
            title="🚨 TEST ALERT - Earthquake Warning!",
            description="This is a test disaster alert. Drop, Cover, Hold — practice safety!",
            severity="CRITICAL",
            region_tags=["Test Region"],
            tokens=tokens
        )
        
        if result.get('success'):
            self.stdout.write(
                self.style.SUCCESS(
                    f"Test alert sent successfully to {len(tokens)} devices"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"Failed to send alert: {result.get('error')}"
                )
            )

    def send_to_all_devices(self):
        """Send test notification to all active devices."""
        devices = Device.objects.filter(is_active=True)
        
        if not devices.exists():
            self.stdout.write(
                self.style.WARNING("No active devices found")
            )
            return
        
        self.stdout.write(f"Found {devices.count()} active devices")
        
        for device in devices:
            self.stdout.write(f"Sending to {device.user.email} ({device.platform})...")
            
            result = send_test_notification(
                token=device.token,
                title="Test Notification",
                body=f"Hello {device.user.first_name}! This is a test notification."
            )
            
            if result.get('success'):
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Sent to {device.user.email}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"✗ Failed to send to {device.user.email}: {result.get('error')}")
                )
