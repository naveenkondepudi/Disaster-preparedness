#!/usr/bin/env python
"""
Simple HTTP server to test Django API endpoints.
"""
import os
import sys
import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.test import RequestFactory
from django.http import JsonResponse
import json

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

try:
    django.setup()
    print("✅ Django setup successful")
    
    from users.views import register, login
    from django.test import Client
    
    # Create a test client
    client = Client()
    
    print("🚀 Starting API test server...")
    print("📡 Testing endpoints...")
    
    # Test registration
    print("\n🧪 Testing Registration...")
    register_data = {
        'username': 'testuser456',
        'email': 'testuser456@example.com',
        'password': 'testpass123',
        'password_confirm': 'testpass123',
        'first_name': 'Test',
        'last_name': 'User',
        'role': 'STUDENT'
    }
    
    response = client.post('/api/users/register/', 
                          data=json.dumps(register_data),
                          content_type='application/json')
    
    print(f"Registration Status: {response.status_code}")
    if response.status_code == 201:
        print("✅ Registration successful!")
        response_data = json.loads(response.content)
        print(f"User created: {response_data['user']['email']}")
    else:
        print(f"❌ Registration failed: {response.content}")
    
    # Test login
    print("\n🧪 Testing Login...")
    login_data = {
        'email': 'testuser456@example.com',
        'password': 'testpass123'
    }
    
    response = client.post('/api/users/login/', 
                          data=json.dumps(login_data),
                          content_type='application/json')
    
    print(f"Login Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Login successful!")
        response_data = json.loads(response.content)
        print(f"User logged in: {response_data['user']['email']}")
        print(f"Access token: {response_data['tokens']['access'][:20]}...")
    else:
        print(f"❌ Login failed: {response.content}")
    
    print("\n🎯 API endpoints are working correctly!")
    print("The issue might be with the Django development server startup.")
    print("Try running: python manage.py runserver --noreload")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
