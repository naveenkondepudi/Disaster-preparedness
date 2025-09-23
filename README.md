# Disaster Preparedness Backend

Django REST API backend for the Disaster Preparedness & Response Education System.

## Setup Instructions

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your database credentials
   # Or create .env file with:
   # SECRET_KEY=your-secret-key-here
   # DEBUG=True
   # ALLOWED_HOSTS=localhost,127.0.0.1
   # DB_NAME=dprep_db
   # DB_USER=postgres
   # DB_PASSWORD=your-password
   # DB_HOST=localhost
   # DB_PORT=5432
   ```

3. **Set up PostgreSQL database:**
   - Create a database named `dprep_db`
   - Update the database credentials in `.env`

4. **Run migrations:**
   ```bash
   python manage.py makemigrations users
   python manage.py migrate
   ```

5. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000/`

## Authentication System

The backend uses **JWT (JSON Web Tokens)** with **Session Authentication** for secure user authentication and logout functionality.

### Authentication Features:
- **JWT Access Tokens**: Short-lived (60 minutes) for API access
- **JWT Refresh Tokens**: Long-lived (7 days) for token renewal
- **Token Blacklisting**: Secure logout by blacklisting refresh tokens
- **Session Authentication**: Maintained for logout functionality
- **Token Rotation**: Refresh tokens are rotated on each use for security

### JWT Configuration:
- Access Token Lifetime: 60 minutes
- Refresh Token Lifetime: 7 days
- Token Rotation: Enabled
- Blacklist After Rotation: Enabled
- Algorithm: HS256

## API Endpoints

### Authentication Endpoints:
- `POST /api/users/register/` - User registration
- `POST /api/users/login/` - User login (returns JWT tokens)
- `POST /api/users/logout/` - Logout (blacklists refresh token)
- `POST /api/users/logout-all/` - Logout from all devices
- `POST /api/users/refresh/` - Refresh access token
- `GET /api/users/me/` - Get user profile (requires authentication)

### Learning Module Endpoints:
- `GET /api/learning/modules/` - List all learning modules
- `GET /api/learning/modules/{id}/` - Get module details with lessons and quizzes
- `POST /api/learning/modules/` - Create new module (TEACHER/ADMIN only)
- `POST /api/learning/modules/{id}/lessons/` - Add lessons to module (TEACHER/ADMIN only)
- `POST /api/learning/modules/{id}/quiz/` - Add quiz to module (TEACHER/ADMIN only)

### Virtual Drills Endpoints:
- `GET /api/drills/scenarios/` - List all available drill scenarios
- `GET /api/drills/scenarios/{id}/` - Get scenario with JSON decision tree
- `POST /api/drills/scenarios/{id}/attempt/` - Submit drill attempt with responses
- `GET /api/drills/scenarios/{id}/attempts/` - Get user's attempts for a scenario
- `POST /api/drills/scenarios/` - Create new scenario (ADMIN only)

### Emergency Alerts Endpoints:
- `GET /api/alerts/alerts/` - List all active alerts (with filtering)
- `GET /api/alerts/alerts/{id}/` - Get alert details
- `POST /api/alerts/alerts/` - Create new alert (ADMIN only)
- `POST /api/alerts/devices/register/` - Register device for push notifications
- `GET /api/alerts/devices/` - List user's registered devices
- `GET /api/alerts/alerts/active/` - Get currently active alerts
- `GET /api/alerts/alerts/critical/` - Get critical alerts only

### System Endpoints:
- `GET /health/` - Health check endpoint

## Project Structure

```
dprep-backend/
├── backend/           # Django project settings
├── users/            # Users app with custom User model
├── manage.py         # Django management script
├── requirements.txt  # Python dependencies
└── env.example       # Environment variables template
```


API Endpoints:
POST /api/populate/ - Populate database (only if empty)
POST /api/force-populate/ - Force populate (clears existing data)
GET /api/database-status/ - Check database status
