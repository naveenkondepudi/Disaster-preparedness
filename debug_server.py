#!/usr/bin/env python
"""
Debug script to test Django server startup and API endpoints.
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path##new comment added
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

try:
    django.setup()
    print("✅ Django setup successful")

    # Test imports
    from users.models import User
    from users.views import register, login
    print("✅ User models and views imported successfully")

    # Test database connection
    user_count = User.objects.count()
    print(f"✅ Database connection successful. Users count: {user_count}")

    # Test API endpoints
    from django.test import RequestFactory
    from django.http import JsonResponse
    import json

    factory = RequestFactory()

    # Test registration endpoint
    print("\n🧪 Testing registration endpoint...")
    register_data = {
        'username': 'testuser123',
        'email': 'testuser123@example.com',
        'password': 'testpass123',
        'password_confirm': 'testpass123',
        'first_name': 'Test',
        'last_name': 'User',
        'role': 'STUDENT'
    }

    request = factory.post('/api/users/register/',
                          data=json.dumps(register_data),
                          content_type='application/json')

    try:
        response = register(request)
        print(f"✅ Registration endpoint working. Status: {response.status_code}")
        if response.status_code == 201:
            print("✅ Registration successful")
        else:
            print(f"❌ Registration failed: {response.data}")
    except Exception as e:
        print(f"❌ Registration endpoint error: {e}")

    # Test login endpoint
    print("\n🧪 Testing login endpoint...")
    login_data = {
        'email': 'testuser123@example.com',
        'password': 'testpass123'
    }

    request = factory.post('/api/users/login/',
                          data=json.dumps(login_data),
                          content_type='application/json')

    try:
        response = login(request)
        print(f"✅ Login endpoint working. Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Login successful")
        else:
            print(f"❌ Login failed: {response.data}")
    except Exception as e:
        print(f"❌ Login endpoint error: {e}")

    print("\n🎯 All tests completed!")

except Exception as e:
    print(f"❌ Error during setup: {e}")
    import traceback
    traceback.print_exc()
