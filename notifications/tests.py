from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from unittest.mock import patch, Mock
import json

from alerts.models import Alert, Device
from notifications.utils import (
    send_push_notification, send_alert_notification, 
    validate_expo_token, get_device_tokens_for_regions,
    send_test_notification
)

User = get_user_model()


class PushNotificationUtilsTestCase(TestCase):
    """Test cases for push notification utilities."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='STUDENT'
        )
        
        self.device = Device.objects.create(
            user=self.user,
            token='ExponentPushToken[test-token-123]',
            platform='ios',
            device_name='Test iPhone'
        )

    def test_validate_expo_token_valid(self):
        """Test validation of valid Expo tokens."""
        valid_tokens = [
            'ExponentPushToken[test-token-123]',
            'ExponentPushToken[abc123def456]',
            'ExponentPushToken[very-long-token-string-here]'
        ]
        
        for token in valid_tokens:
            self.assertTrue(validate_expo_token(token), f"Token {token} should be valid")

    def test_validate_expo_token_invalid(self):
        """Test validation of invalid Expo tokens."""
        invalid_tokens = [
            '',
            None,
            'short',
            'ExponentPushToken[]',
            'InvalidToken[123]',
            'ExponentPushToken[123]'  # Too short
        ]
        
        for token in invalid_tokens:
            if token is None:
                self.assertFalse(validate_expo_token(token), f"Token {token} should be invalid")
            elif token == 'ExponentPushToken[]':
                self.assertFalse(validate_expo_token(token), f"Token {token} should be invalid")
            elif token == 'ExponentPushToken[123]':
                self.assertFalse(validate_expo_token(token), f"Token {token} should be invalid")
            else:
                self.assertFalse(validate_expo_token(token), f"Token {token} should be invalid")

    def test_get_device_tokens_for_regions(self):
        """Test getting device tokens for regions."""
        # Create another device
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
            role='STUDENT'
        )
        
        device2 = Device.objects.create(
            user=user2,
            token='ExponentPushToken[test-token-456]',
            platform='android',
            device_name='Test Android'
        )
        
        # Test getting tokens
        tokens = get_device_tokens_for_regions(['Mumbai', 'Delhi'])
        
        self.assertEqual(len(tokens), 2)
        self.assertIn(self.device.token, tokens)
        self.assertIn(device2.token, tokens)

    def test_get_device_tokens_for_regions_inactive_devices(self):
        """Test that inactive devices are not included."""
        # Create inactive device
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
            role='STUDENT'
        )
        
        device2 = Device.objects.create(
            user=user2,
            token='ExponentPushToken[test-token-456]',
            platform='android',
            device_name='Test Android',
            is_active=False
        )
        
        tokens = get_device_tokens_for_regions(['Mumbai'])
        
        self.assertEqual(len(tokens), 1)
        self.assertIn(self.device.token, tokens)
        self.assertNotIn(device2.token, tokens)

    @patch('notifications.utils.requests.post')
    def test_send_push_notification_success(self, mock_post):
        """Test successful push notification sending."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'status': 'ok', 'id': 'test-receipt-id'}
            ]
        }
        mock_post.return_value = mock_response
        
        result = send_push_notification(
            tokens=['ExponentPushToken[test-token-123]'],
            title='Test Title',
            body='Test Body',
            data={'test': True}
        )
        
        self.assertTrue(result['success'])
        self.assertIn('result', result)
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], 'https://exp.host/--/api/v2/push/send')
        
        request_data = call_args[1]['json']
        self.assertEqual(request_data['to'], ['ExponentPushToken[test-token-123]'])
        self.assertEqual(request_data['title'], 'Test Title')
        self.assertEqual(request_data['body'], 'Test Body')
        self.assertEqual(request_data['data'], {'test': True})

    @patch('notifications.utils.requests.post')
    def test_send_push_notification_failure(self, mock_post):
        """Test push notification sending failure."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_response.raise_for_status.side_effect = Exception('Bad Request')
        mock_post.return_value = mock_response
        
        result = send_push_notification(
            tokens=['ExponentPushToken[test-token-123]'],
            title='Test Title',
            body='Test Body'
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)

    def test_send_push_notification_no_tokens(self):
        """Test push notification with no tokens."""
        result = send_push_notification(
            tokens=[],
            title='Test Title',
            body='Test Body'
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'No tokens provided')

    def test_send_push_notification_invalid_tokens(self):
        """Test push notification with invalid tokens."""
        result = send_push_notification(
            tokens=['invalid', 'short'],
            title='Test Title',
            body='Test Body'
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'No valid tokens found')

    @patch('notifications.utils.send_push_notification')
    def test_send_alert_notification(self, mock_send):
        """Test sending alert notification."""
        mock_send.return_value = {'success': True, 'result': {}}
        
        result = send_alert_notification(
            alert_id=1,
            title='Earthquake Warning!',
            description='Drop, Cover, Hold — practice safety!',
            severity='CRITICAL',
            region_tags=['Mumbai', 'Delhi'],
            tokens=['ExponentPushToken[test-token-123]']
        )
        
        self.assertTrue(result['success'])
        mock_send.assert_called_once()
        
        # Check call arguments
        call_args = mock_send.call_args
        self.assertEqual(call_args[1]['title'], 'Earthquake Warning!')
        self.assertEqual(call_args[1]['priority'], 'high')
        self.assertEqual(call_args[1]['badge'], 1)
        self.assertEqual(call_args[1]['data']['severity'], 'CRITICAL')

    @patch('notifications.utils.send_push_notification')
    def test_send_test_notification(self, mock_send):
        """Test sending test notification."""
        mock_send.return_value = {'success': True, 'result': {}}
        
        result = send_test_notification(
            token='ExponentPushToken[test-token-123]',
            title='Test Notification',
            body='This is a test'
        )
        
        self.assertTrue(result['success'])
        mock_send.assert_called_once()
        
        # Check call arguments
        call_args = mock_send.call_args
        self.assertEqual(call_args[1]['tokens'], ['ExponentPushToken[test-token-123]'])
        self.assertEqual(call_args[1]['title'], 'Test Notification')
        self.assertEqual(call_args[1]['body'], 'This is a test')
        self.assertEqual(call_args[1]['priority'], 'normal')


class AlertPushNotificationTestCase(TestCase):
    """Test cases for alert push notification integration."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='STUDENT'
        )
        
        self.device = Device.objects.create(
            user=self.user,
            token='ExponentPushToken[test-token-123]',
            platform='ios',
            device_name='Test iPhone'
        )

    @patch('alerts.signals.send_alert_notification')
    def test_alert_creation_triggers_notification(self, mock_send):
        """Test that creating an alert triggers push notifications."""
        mock_send.return_value = {'success': True, 'result': {}}
        
        # Create an alert
        alert = Alert.objects.create(
            title='Test Alert',
            description='This is a test alert',
            severity='HIGH',
            region_tags=['Mumbai'],
            source='NDMA'
        )
        
        # Check that notification was sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        self.assertEqual(call_args[1]['alert_id'], alert.id)
        self.assertEqual(call_args[1]['title'], 'Test Alert')
        self.assertEqual(call_args[1]['severity'], 'HIGH')

    @patch('alerts.signals.send_alert_notification')
    def test_inactive_alert_no_notification(self, mock_send):
        """Test that inactive alerts don't trigger notifications."""
        # Create an inactive alert
        Alert.objects.create(
            title='Test Alert',
            description='This is a test alert',
            severity='HIGH',
            region_tags=['Mumbai'],
            source='NDMA',
            is_active=False
        )
        
        # Check that no notification was sent
        mock_send.assert_not_called()

    @patch('alerts.signals.send_alert_notification')
    def test_alert_update_no_notification(self, mock_send):
        """Test that updating an alert doesn't trigger notifications."""
        # Create an alert
        alert = Alert.objects.create(
            title='Test Alert',
            description='This is a test alert',
            severity='HIGH',
            region_tags=['Mumbai'],
            source='NDMA'
        )
        
        # Reset mock to clear the create call
        mock_send.reset_mock()
        
        # Update the alert
        alert.title = 'Updated Alert'
        alert.save()
        
        # Check that no notification was sent for update
        mock_send.assert_not_called()


class DeviceRegistrationTestCase(TestCase):
    """Test cases for device registration."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='STUDENT'
        )

    def test_device_registration(self):
        """Test device registration."""
        device = Device.objects.create(
            user=self.user,
            token='ExponentPushToken[test-token-123]',
            platform='ios',
            device_name='Test iPhone'
        )
        
        self.assertEqual(device.user, self.user)
        self.assertEqual(device.token, 'ExponentPushToken[test-token-123]')
        self.assertEqual(device.platform, 'ios')
        self.assertTrue(device.is_active)

    def test_device_unique_constraint(self):
        """Test device unique constraint."""
        # Create first device
        Device.objects.create(
            user=self.user,
            token='ExponentPushToken[test-token-123]',
            platform='ios',
            device_name='Test iPhone'
        )
        
        # Try to create another device with same token and user
        with self.assertRaises(Exception):  # IntegrityError
            Device.objects.create(
                user=self.user,
                token='ExponentPushToken[test-token-123]',
                platform='android',
                device_name='Test Android'
            )

    def test_device_update_last_used(self):
        """Test device last used update."""
        device = Device.objects.create(
            user=self.user,
            token='ExponentPushToken[test-token-123]',
            platform='ios',
            device_name='Test iPhone'
        )
        
        original_time = device.last_used
        device.update_last_used()
        
        self.assertGreater(device.last_used, original_time)
