from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import logging

from .models import Alert, Device
from notifications.utils import send_alert_notification, get_device_tokens_for_regions

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Alert)
def send_push_notifications(sender, instance, created, **kwargs):
    """Send push notifications when a new alert is created."""
    if not created or not instance.is_active:
        return
    
    try:
        # Get device tokens for affected regions
        tokens = get_device_tokens_for_regions(instance.region_tags)
        
        if not tokens:
            logger.info(f"No active device tokens found for alert {instance.id}")
            return
        
        # Send alert notification
        result = send_alert_notification(
            alert_id=instance.id,
            title=instance.title,
            description=instance.description,
            severity=instance.severity,
            region_tags=instance.region_tags,
            tokens=tokens
        )
        
        if result["success"]:
            logger.info(f"Push notifications sent successfully for alert {instance.id} to {len(tokens)} devices")
        else:
            logger.error(f"Failed to send push notifications for alert {instance.id}: {result.get('error')}")
        
    except Exception as e:
        logger.error(f"Error sending push notifications for alert {instance.id}: {str(e)}")


def send_test_notification(device_token, title="Test Alert", body="This is a test notification"):
    """Send a test notification to a specific device."""
    from notifications.utils import send_test_notification as send_test
    
    return send_test(device_token, title, body)
