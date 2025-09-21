from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Badge, UserPoints, UserBadge, LessonCompletion, QuizCompletion, DrillCompletion
from .signals import check_and_assign_badges, create_default_badges
from learning.models import Module, Lesson, Quiz
from drills.models import DrillScenario, DrillAttempt

User = get_user_model()


class GamificationModelsTestCase(TestCase):
    """Test cases for gamification models."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='STUDENT'
        )
        
        self.badge = Badge.objects.create(
            name='Test Badge',
            description='A test badge',
            threshold_points=100,
            icon='🏆',
            color='#f39c12'
        )
    
    def test_user_points_creation(self):
        """Test UserPoints model creation."""
        user_points = UserPoints.objects.create(user=self.user)
        self.assertEqual(user_points.total_points, 0)
        self.assertEqual(user_points.lesson_points, 0)
        self.assertEqual(user_points.quiz_points, 0)
        self.assertEqual(user_points.drill_points, 0)
    
    def test_user_points_add_points(self):
        """Test adding points to user."""
        user_points = UserPoints.objects.create(user=self.user)
        user_points.add_points(50, 'lesson')
        
        self.assertEqual(user_points.total_points, 50)
        self.assertEqual(user_points.lesson_points, 50)
        self.assertEqual(user_points.quiz_points, 0)
        self.assertEqual(user_points.drill_points, 0)
    
    def test_user_points_get_current_badge(self):
        """Test getting current badge."""
        user_points = UserPoints.objects.create(user=self.user)
        user_points.add_points(150)  # Above threshold
        
        current_badge = user_points.get_current_badge()
        self.assertEqual(current_badge, self.badge)
    
    def test_user_points_get_next_badge(self):
        """Test getting next badge."""
        user_points = UserPoints.objects.create(user=self.user)
        user_points.add_points(50)  # Below threshold
        
        next_badge = user_points.get_next_badge()
        self.assertEqual(next_badge, self.badge)
    
    def test_user_badge_creation(self):
        """Test UserBadge model creation."""
        user_badge = UserBadge.objects.create(user=self.user, badge=self.badge)
        self.assertEqual(user_badge.user, self.user)
        self.assertEqual(user_badge.badge, self.badge)


class GamificationSignalsTestCase(TestCase):
    """Test cases for gamification signals."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='STUDENT'
        )
        
        self.badge = Badge.objects.create(
            name='Test Badge',
            description='A test badge',
            threshold_points=100,
            icon='🏆',
            color='#f39c12'
        )
        
        # Create a module and lesson for testing
        self.module = Module.objects.create(
            title='Test Module',
            description='A test module',
            disaster_type='EARTHQUAKE',
            created_by=self.user
        )
        
        self.lesson = Lesson.objects.create(
            title='Test Lesson',
            content='Test content',
            order=1,
            module=self.module
        )
        
        self.quiz = Quiz.objects.create(
            title='Test Quiz',
            module=self.module
        )
        
        self.drill_scenario = DrillScenario.objects.create(
            title='Test Drill',
            description='A test drill',
            difficulty_level='BEGINNER',
            estimated_duration=15,
            max_score=100,
            json_tree={'root': {'question': 'Test question', 'options': []}}
        )
    
    def test_lesson_completion_signal(self):
        """Test lesson completion signal."""
        # Create lesson completion
        lesson_completion = LessonCompletion.objects.create(
            user=self.user,
            lesson=self.lesson,
            points_earned=10
        )
        
        # Check if points were added
        user_points = UserPoints.objects.get(user=self.user)
        self.assertEqual(user_points.total_points, 10)
        self.assertEqual(user_points.lesson_points, 10)
    
    def test_quiz_completion_signal(self):
        """Test quiz completion signal."""
        # Create quiz completion
        quiz_completion = QuizCompletion.objects.create(
            user=self.user,
            quiz=self.quiz,
            score=80,
            points_earned=80
        )
        
        # Check if points were added
        user_points = UserPoints.objects.get(user=self.user)
        self.assertEqual(user_points.total_points, 80)
        self.assertEqual(user_points.quiz_points, 80)
    
    def test_drill_completion_signal(self):
        """Test drill completion signal."""
        # Create drill attempt first
        drill_attempt = DrillAttempt.objects.create(
            user=self.user,
            scenario=self.drill_scenario,
            score=75,
            responses={'test': 'data'},
            completed=True
        )
        
        # Create drill completion
        drill_completion = DrillCompletion.objects.create(
            user=self.user,
            drill_attempt=drill_attempt,
            points_earned=75
        )
        
        # Check if points were added
        user_points = UserPoints.objects.get(user=self.user)
        self.assertEqual(user_points.total_points, 75)
        self.assertEqual(user_points.drill_points, 75)
    
    def test_badge_assignment(self):
        """Test automatic badge assignment."""
        # Add enough points to earn badge
        user_points = UserPoints.objects.create(user=self.user)
        user_points.add_points(150)  # Above threshold
        
        # Manually trigger badge assignment
        check_and_assign_badges(self.user)
        
        # Check if badge was assigned
        user_badges = UserBadge.objects.filter(user=self.user)
        self.assertEqual(user_badges.count(), 1)
        self.assertEqual(user_badges.first().badge, self.badge)
    
    def test_create_default_badges(self):
        """Test creation of default badges."""
        # Clear existing badges
        Badge.objects.all().delete()
        
        # Create default badges
        create_default_badges()
        
        # Check if badges were created
        badges = Badge.objects.all()
        self.assertGreater(badges.count(), 0)
        
        # Check specific badges
        beginner_badge = Badge.objects.get(name='Beginner')
        self.assertEqual(beginner_badge.threshold_points, 50)
        
        disaster_hero_badge = Badge.objects.get(name='Disaster Hero')
        self.assertEqual(disaster_hero_badge.threshold_points, 5000)


class GamificationAPITestCase(TestCase):
    """Test cases for gamification API endpoints."""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            role='ADMIN'
        )
        
        self.teacher_user = User.objects.create_user(
            username='teacheruser',
            email='teacher@example.com',
            password='teacherpass123',
            first_name='Teacher',
            last_name='User',
            role='TEACHER'
        )
        
        self.student_user = User.objects.create_user(
            username='studentuser',
            email='student@example.com',
            password='studentpass123',
            first_name='Student',
            last_name='User',
            role='STUDENT'
        )
        
        self.badge = Badge.objects.create(
            name='Test Badge',
            description='A test badge',
            threshold_points=100,
            icon='🏆',
            color='#f39c12'
        )
    
    def test_badge_list_api(self):
        """Test badge list API endpoint."""
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        
        client = APIClient()
        token = RefreshToken.for_user(self.student_user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        
        response = client.get('/api/gamification/badges/')
        self.assertEqual(response.status_code, 200)
        # Check that we have badges in the results
        self.assertGreater(len(response.data['results']), 0)
        # Check that the first badge has a name
        self.assertIn('name', response.data['results'][0])
    
    def test_user_stats_api_permission(self):
        """Test user stats API permission."""
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        
        client = APIClient()
        
        # Test with student (should be denied)
        token = RefreshToken.for_user(self.student_user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        
        response = client.get('/api/gamification/user-stats/')
        self.assertEqual(response.status_code, 403)
        
        # Test with admin (should be allowed)
        token = RefreshToken.for_user(self.admin_user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        
        response = client.get('/api/gamification/user-stats/')
        self.assertEqual(response.status_code, 200)
    
    def test_admin_stats_api_permission(self):
        """Test admin stats API permission."""
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        
        client = APIClient()
        
        # Test with student (should be denied)
        token = RefreshToken.for_user(self.student_user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        
        response = client.get('/api/gamification/admin-stats/overview/')
        self.assertEqual(response.status_code, 403)
        
        # Test with admin (should be allowed)
        token = RefreshToken.for_user(self.admin_user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        
        response = client.get('/api/gamification/admin-stats/overview/')
        self.assertEqual(response.status_code, 200)
    
    def test_leaderboard_api(self):
        """Test leaderboard API endpoint."""
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        
        client = APIClient()
        token = RefreshToken.for_user(self.admin_user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        
        response = client.get('/api/gamification/user-stats/leaderboard/')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)