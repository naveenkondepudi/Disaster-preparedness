#!/usr/bin/env python
"""
Simple script to start Django server and test endpoints.
"""
import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

try:
    django.setup()
    print("✅ Django setup successful")
    
    # Start the server
    print("🚀 Starting Django development server...")
    print("📡 Server will be available at: http://localhost:8000")
    print("🔗 API endpoints:")
    print("   - Registration: POST http://localhost:8000/api/users/register/")
    print("   - Login: POST http://localhost:8000/api/users/login/")
    print("   - Health check: GET http://localhost:8000/health/")
    print("\n⏹️  Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Start the server
    execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000'])
    
except KeyboardInterrupt:
    print("\n\n🛑 Server stopped by user")
except Exception as e:
    print(f"❌ Error starting server: {e}")
    import traceback
    traceback.print_exc()
