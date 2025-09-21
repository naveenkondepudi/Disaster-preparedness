from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for User model."""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'STUDENT',
            'institution': 'Test School'
        }
    
    def test_create_user(self):
        """Test creating a new user."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, 'STUDENT')
        self.assertEqual(user.institution, 'Test School')
        self.assertTrue(user.check_password('testpass123'))
    
    def test_user_str_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(**self.user_data)
        expected = f"{user.email} ({user.get_role_display()})"
        self.assertEqual(str(user), expected)
    
    def test_email_is_username_field(self):
        """Test that email is used as username field."""
        self.assertEqual(User.USERNAME_FIELD, 'email')


class UserAPITest(APITestCase):
    """Test cases for User API endpoints."""
    
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.profile_url = reverse('profile')
        
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'STUDENT',
            'institution': 'Test School'
        }
        
        self.registration_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'STUDENT',
            'institution': 'Test School'
        }
    
    def test_user_registration(self):
        """Test user registration endpoint."""
        response = self.client.post(self.register_url, self.registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check response contains user data and tokens
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        
        # Check user was created
        self.assertTrue(User.objects.filter(email='test@example.com').exists())
    
    def test_user_registration_invalid_data(self):
        """Test user registration with invalid data."""
        invalid_data = self.registration_data.copy()
        invalid_data['password_confirm'] = 'different_password'
        
        response = self.client.post(self.register_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_user_login(self):
        """Test user login endpoint."""
        # Create user first
        user = User.objects.create_user(**self.user_data)
        
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response contains user data and tokens
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
    
    def test_user_login_invalid_credentials(self):
        """Test user login with invalid credentials."""
        login_data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_user_profile_authenticated(self):
        """Test getting user profile when authenticated."""
        # Create and authenticate user
        user = User.objects.create_user(**self.user_data)
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['role'], 'STUDENT')
    
    def test_user_profile_unauthenticated(self):
        """Test getting user profile when not authenticated."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_logout(self):
        """Test user logout with token blacklisting."""
        # Create user and login
        user = User.objects.create_user(**self.user_data)
        login_response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data['tokens']['access']
        refresh_token = login_response.data['tokens']['refresh']
        
        # Logout with refresh token (requires authentication)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}
        logout_response = self.client.post('/api/users/logout/', {
            'refresh': refresh_token
        }, **headers)
        
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertIn('message', logout_response.data)
        self.assertEqual(logout_response.data['message'], 'Successfully logged out')
    
    def test_user_logout_invalid_token(self):
        """Test user logout with invalid token."""
        # Create user and login to get access token
        user = User.objects.create_user(**self.user_data)
        login_response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data['tokens']['access']
        
        # Logout with invalid refresh token
        headers = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}
        logout_response = self.client.post('/api/users/logout/', {
            'refresh': 'invalid_token'
        }, **headers)
        
        self.assertEqual(logout_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', logout_response.data)
    
    def test_user_logout_missing_token(self):
        """Test user logout without refresh token."""
        # Create user and login to get access token
        user = User.objects.create_user(**self.user_data)
        login_response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data['tokens']['access']
        
        # Logout without refresh token
        headers = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}
        logout_response = self.client.post('/api/users/logout/', {}, **headers)
        
        self.assertEqual(logout_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', logout_response.data)
        self.assertEqual(logout_response.data['error'], 'Refresh token is required')
    
    def test_user_logout_all(self):
        """Test logout from all devices."""
        # Create user and login
        user = User.objects.create_user(**self.user_data)
        login_response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data['tokens']['access']
        
        # Logout from all devices (requires authentication)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}
        logout_all_response = self.client.post('/api/users/logout-all/', **headers)
        
        self.assertEqual(logout_all_response.status_code, status.HTTP_200_OK)
        self.assertIn('message', logout_all_response.data)
        self.assertEqual(logout_all_response.data['message'], 'Successfully logged out from all devices')
    
    def test_refresh_token(self):
        """Test token refresh endpoint."""
        # Create user and login
        user = User.objects.create_user(**self.user_data)
        login_response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        refresh_token = login_response.data['tokens']['refresh']
        
        # Refresh token
        refresh_response = self.client.post('/api/users/refresh/', {
            'refresh': refresh_token
        })
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
    
    def test_refresh_token_invalid(self):
        """Test token refresh with invalid token."""
        refresh_response = self.client.post('/api/users/refresh/', {
            'refresh': 'invalid_token'
        })
        
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', refresh_response.data)
    
    def test_duplicate_email_registration(self):
        """Test registration with duplicate email."""
        # Create first user
        User.objects.create_user(**self.user_data)
        
        # Try to create second user with same email
        duplicate_data = self.registration_data.copy()
        duplicate_data['username'] = 'anotheruser'
        
        response = self.client.post(self.register_url, duplicate_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)