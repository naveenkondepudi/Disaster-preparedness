from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from unittest.mock import patch

from .models import Alert, Device

User = get_user_model()


class AlertModelsTestCase(TestCase):
    """Test cases for alert models."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='STUDENT'
        )
        
        self.alert = Alert.objects.create(
            title='Earthquake Warning',
            description='Strong earthquake expected in Delhi region',
            region_tags=['Delhi', 'NCR'],
            severity='HIGH',
            source='NDMA',
            geometry={
                'type': 'Point',
                'coordinates': [77.2090, 28.6139]
            }
        )
        
        self.device = Device.objects.create(
            user=self.user,
            token='ExponentPushToken[test-token-123]',
            platform='ios',
            device_name='iPhone 12'
        )
    
    def test_alert_creation(self):
        """Test alert creation and string representation."""
        self.assertEqual(str(self.alert), 'Earthquake Warning (High)')
        self.assertEqual(self.alert.severity, 'HIGH')
        self.assertEqual(self.alert.region_tags, ['Delhi', 'NCR'])
    
    def test_alert_is_expired(self):
        """Test alert expiration check."""
        # Alert without expiry should not be expired
        self.assertFalse(self.alert.is_expired())
        
        # Alert with future expiry should not be expired
        self.alert.expires_at = timezone.now() + timezone.timedelta(hours=1)
        self.alert.save()
        self.assertFalse(self.alert.is_expired())
        
        # Alert with past expiry should be expired
        self.alert.expires_at = timezone.now() - timezone.timedelta(hours=1)
        self.alert.save()
        self.assertTrue(self.alert.is_expired())
    
    def test_alert_affected_regions(self):
        """Test getting affected regions."""
        regions = self.alert.get_affected_regions()
        self.assertEqual(regions, ['Delhi', 'NCR'])
        
        # Test with no region tags
        self.alert.region_tags = []
        self.alert.save()
        regions = self.alert.get_affected_regions()
        self.assertEqual(regions, ['All Regions'])
    
    def test_device_creation(self):
        """Test device creation and string representation."""
        self.assertEqual(str(self.device), f"{self.user.email} - iOS (iPhone 12)")
        self.assertEqual(self.device.platform, 'ios')
        self.assertEqual(self.device.token, 'ExponentPushToken[test-token-123]')
    
    def test_device_update_last_used(self):
        """Test updating device last used timestamp."""
        original_time = self.device.last_used
        self.device.update_last_used()
        self.assertGreater(self.device.last_used, original_time)


class AlertAPITestCase(APITestCase):
    """Test cases for alert API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create users
        self.student = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass123',
            role='STUDENT'
        )
        
        self.admin = User.objects.create_user(
            username='admin1',
            email='admin@test.com',
            password='testpass123',
            role='ADMIN'
        )
        
        # Create test alert
        self.alert = Alert.objects.create(
            title='Flood Warning',
            description='Heavy rainfall expected in Mumbai',
            region_tags=['Mumbai', 'Maharashtra'],
            severity='CRITICAL',
            source='IMD',
            geometry={
                'type': 'Polygon',
                'coordinates': [[[72.8, 19.0], [72.9, 19.0], [72.9, 19.1], [72.8, 19.1], [72.8, 19.0]]]
            }
        )
        
        # Create test device
        self.device = Device.objects.create(
            user=self.student,
            token='ExponentPushToken[test-device-token]',
            platform='android',
            device_name='Samsung Galaxy'
        )
    
    def get_auth_headers(self, user):
        """Get authentication headers for a user."""
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
    
    def test_alert_list_as_student(self):
        """Test that students can view alert list."""
        headers = self.get_auth_headers(self.student)
        url = reverse('alert-list')
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Flood Warning')
        self.assertEqual(response.data[0]['severity'], 'CRITICAL')
        self.assertTrue('is_expired' in response.data[0])
        self.assertTrue('affected_regions' in response.data[0])
    
    def test_alert_detail_as_student(self):
        """Test that students can view alert details."""
        headers = self.get_auth_headers(self.student)
        url = reverse('alert-detail', kwargs={'pk': self.alert.pk})
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Flood Warning')
        self.assertIn('geometry', response.data)
        self.assertEqual(response.data['geometry']['type'], 'Polygon')
    
    def test_alert_filter_by_region(self):
        """Test filtering alerts by region."""
        headers = self.get_auth_headers(self.student)
        url = reverse('alert-list')
        response = self.client.get(url, {'region': 'Mumbai'}, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test with non-matching region
        response = self.client.get(url, {'region': 'Delhi'}, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_alert_filter_by_severity(self):
        """Test filtering alerts by severity."""
        headers = self.get_auth_headers(self.student)
        url = reverse('alert-list')
        response = self.client.get(url, {'severity': 'CRITICAL'}, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test with non-matching severity
        response = self.client.get(url, {'severity': 'LOW'}, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_alert_active_endpoint(self):
        """Test active alerts endpoint."""
        headers = self.get_auth_headers(self.student)
        url = reverse('alert-active')
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_alert_critical_endpoint(self):
        """Test critical alerts endpoint."""
        headers = self.get_auth_headers(self.student)
        url = reverse('alert-critical')
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['severity'], 'CRITICAL')
    
    def test_create_alert_as_admin(self):
        """Test that admins can create alerts."""
        headers = self.get_auth_headers(self.admin)
        url = reverse('alert-list')
        
        alert_data = {
            'title': 'Cyclone Warning',
            'description': 'Cyclone approaching Odisha coast',
            'region_tags': ['Odisha', 'West Bengal'],
            'severity': 'HIGH',
            'source': 'IMD',
            'geometry': {
                'type': 'Point',
                'coordinates': [85.8245, 20.2961]
            }
        }
        
        response = self.client.post(url, alert_data, format='json', **headers)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Cyclone Warning')
        self.assertEqual(response.data['severity'], 'HIGH')
    
    def test_create_alert_as_student_denied(self):
        """Test that students cannot create alerts."""
        headers = self.get_auth_headers(self.student)
        url = reverse('alert-list')
        
        alert_data = {
            'title': 'Unauthorized Alert',
            'description': 'This should fail',
            'severity': 'LOW'
        }
        
        response = self.client.post(url, alert_data, format='json', **headers)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_device_registration(self):
        """Test device registration for push notifications."""
        headers = self.get_auth_headers(self.student)
        url = reverse('device-register')
        
        device_data = {
            'token': 'ExponentPushToken[new-device-token]',
            'platform': 'ios',
            'device_name': 'iPhone 13'
        }
        
        response = self.client.post(url, device_data, format='json', **headers)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['token'], 'ExponentPushToken[new-device-token]')
        self.assertEqual(response.data['platform'], 'ios')
    
    def test_device_list(self):
        """Test listing user's devices."""
        headers = self.get_auth_headers(self.student)
        url = reverse('device-list')
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['device_name'], 'Samsung Galaxy')
    
    def test_device_update_last_used(self):
        """Test updating device last used timestamp."""
        headers = self.get_auth_headers(self.student)
        url = reverse('device-update-last-used', kwargs={'pk': self.device.pk})
        response = self.client.post(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['last_used'])
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access endpoints."""
        url = reverse('alert-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)