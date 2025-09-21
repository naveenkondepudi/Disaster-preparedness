import requests
import logging
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Expo Push API endpoint
EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

# Maximum tokens per batch (Expo recommendation)
MAX_TOKENS_PER_BATCH = 100


def send_push_notification(
    tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    sound: str = "default",
    badge: Optional[int] = None,
    priority: str = "high",
    ttl: int = 86400  # 24 hours
) -> Dict[str, Any]:
    """
    Send push notifications to multiple devices using Expo Push API.
    
    Args:
        tokens: List of Expo push tokens
        title: Notification title
        body: Notification body text
        data: Additional data payload (optional)
        sound: Sound to play (default: "default")
        badge: Badge count for iOS (optional)
        priority: Priority level ("default", "normal", "high")
        ttl: Time to live in seconds (default: 86400)
    
    Returns:
        Dict containing the response from Expo Push API
    """
    if not tokens:
        logger.warning("No tokens provided for push notification")
        return {"success": False, "error": "No tokens provided"}
    
    # Validate tokens
    valid_tokens = [token for token in tokens if token and len(token) > 10]
    if not valid_tokens:
        logger.warning("No valid tokens found")
        return {"success": False, "error": "No valid tokens found"}
    
    # Prepare notification payload
    payload = {
        "to": valid_tokens,
        "title": title,
        "body": body,
        "sound": sound,
        "priority": priority,
        "ttl": ttl,
    }
    
    # Add optional fields
    if data:
        payload["data"] = data
    
    if badge is not None:
        payload["badge"] = badge
    
    try:
        # Send notification in batches if needed
        if len(valid_tokens) > MAX_TOKENS_PER_BATCH:
            return _send_batch_notifications(valid_tokens, payload)
        else:
            return _send_single_notification(payload)
    
    except Exception as e:
        logger.error(f"Error sending push notification: {str(e)}")
        return {"success": False, "error": str(e)}


def _send_single_notification(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Send a single notification batch."""
    try:
        response = requests.post(
            EXPO_PUSH_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
            },
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Push notification sent successfully to {len(payload['to'])} devices")
        return {"success": True, "result": result}
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error sending push notification: {str(e)}")
        return {"success": False, "error": f"Request error: {str(e)}"}
    
    except Exception as e:
        logger.error(f"Unexpected error sending push notification: {str(e)}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


def _send_batch_notifications(tokens: List[str], base_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Send notifications in batches when token count exceeds limit."""
    results = []
    errors = []
    
    # Split tokens into batches
    for i in range(0, len(tokens), MAX_TOKENS_PER_BATCH):
        batch_tokens = tokens[i:i + MAX_TOKENS_PER_BATCH]
        batch_payload = base_payload.copy()
        batch_payload["to"] = batch_tokens
        
        result = _send_single_notification(batch_payload)
        
        if result["success"]:
            results.append(result["result"])
        else:
            errors.append(result["error"])
    
    if errors:
        logger.warning(f"Some batches failed: {errors}")
        return {"success": False, "errors": errors, "results": results}
    
    return {"success": True, "results": results}


def send_alert_notification(
    alert_id: int,
    title: str,
    description: str,
    severity: str,
    region_tags: List[str],
    tokens: List[str]
) -> Dict[str, Any]:
    """
    Send a disaster alert notification.
    
    Args:
        alert_id: ID of the alert
        title: Alert title
        description: Alert description
        severity: Alert severity level
        region_tags: List of affected regions
        tokens: List of device tokens to notify
    
    Returns:
        Dict containing the response from Expo Push API
    """
    # Prepare notification data
    data = {
        "alert_id": alert_id,
        "severity": severity,
        "region_tags": region_tags,
        "timestamp": timezone.now().isoformat(),
        "type": "disaster_alert"
    }
    
    # Customize notification based on severity
    sound = "default"
    priority = "high"
    badge = None
    
    if severity == "CRITICAL":
        sound = "default"  # Use default critical sound
        priority = "high"
        badge = 1
    elif severity == "HIGH":
        priority = "high"
        badge = 1
    elif severity == "MEDIUM":
        priority = "normal"
    else:  # LOW
        priority = "normal"
    
    # Truncate description if too long
    max_body_length = 200
    if len(description) > max_body_length:
        description = description[:max_body_length - 3] + "..."
    
    return send_push_notification(
        tokens=tokens,
        title=title,
        body=description,
        data=data,
        sound=sound,
        badge=badge,
        priority=priority,
        ttl=86400  # 24 hours
    )


def validate_expo_token(token: str) -> bool:
    """
    Validate if a token looks like a valid Expo push token.
    
    Args:
        token: Token to validate
    
    Returns:
        True if token appears valid, False otherwise
    """
    if not token or not isinstance(token, str):
        return False
    
    # Basic validation - Expo tokens typically start with ExponentPushToken
    if token.startswith("ExponentPushToken["):
        # Check that there's content inside the brackets and it's long enough
        if len(token) > 25 and token.endswith("]") and len(token.split("[")[1].split("]")[0]) > 5:
            return True
    
    # Also accept Expo push tokens that might not follow the exact format
    if len(token) > 25 and any(char.isalnum() for char in token):
        return True
    
    return False


def get_device_tokens_for_regions(region_tags: List[str]) -> List[str]:
    """
    Get all active device tokens for users in specified regions.
    
    Args:
        region_tags: List of region tags to match
    
    Returns:
        List of valid device tokens
    """
    from alerts.models import Device
    
    # Get all active devices
    devices = Device.objects.filter(is_active=True)
    
    # For now, return all active device tokens
    # In a real implementation, you might want to filter by user location/region
    tokens = [device.token for device in devices if validate_expo_token(device.token)]
    
    logger.info(f"Found {len(tokens)} active device tokens for regions: {region_tags}")
    return tokens


def send_test_notification(token: str, title: str = "Test Notification", body: str = "This is a test notification") -> Dict[str, Any]:
    """
    Send a test notification to verify token works.
    
    Args:
        token: Single device token
        title: Test notification title
        body: Test notification body
    
    Returns:
        Dict containing the response from Expo Push API
    """
    data = {
        "type": "test",
        "timestamp": timezone.now().isoformat()
    }
    
    return send_push_notification(
        tokens=[token],
        title=title,
        body=body,
        data=data,
        sound="default",
        priority="normal",
        ttl=3600  # 1 hour
    )
