from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

from .models import DrillScenario, DrillAttempt

User = get_user_model()


class DrillModelsTestCase(TestCase):
    """Test cases for drill models."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='STUDENT'
        )
        
        self.scenario_data = {
            'title': 'Earthquake Evacuation Drill',
            'description': 'Practice earthquake evacuation procedures',
            'region_tags': ['Delhi', 'Mumbai'],
            'json_tree': {
                'start_step': 's1',
                'steps': {
                    's1': {
                        'text': 'The ground starts shaking. What do you do?',
                        'choices': [
                            {'id': 'c1', 'text': 'Drop, cover, hold on', 'next': 's2', 'score': 10},
                            {'id': 'c2', 'text': 'Run outside immediately', 'next': 's3', 'score': -5}
                        ]
                    },
                    's2': {
                        'text': 'Good! Now evacuate after shaking stops.',
                        'choices': [
                            {'id': 'c3', 'text': 'Use stairs', 'next': 's4', 'score': 10},
                            {'id': 'c4', 'text': 'Use elevator', 'next': 's5', 'score': -10}
                        ]
                    },
                    's3': {'text': 'You got injured. Seek help.', 'choices': []},
                    's4': {'text': 'You safely evacuated!', 'choices': []},
                    's5': {'text': 'Elevator is dangerous during earthquakes!', 'choices': []}
                }
            },
            'difficulty_level': 'BEGINNER',
            'estimated_duration': 5,
            'max_score': 100
        }
        
        self.scenario = DrillScenario.objects.create(**self.scenario_data)
        
        self.attempt = DrillAttempt.objects.create(
            user=self.user,
            scenario=self.scenario,
            score=20,
            responses={
                'path': ['s1', 's2', 's4'],
                'choices_made': {'s1': 'c1', 's2': 'c3'}
            },
            completed=True
        )
    
    def test_scenario_creation(self):
        """Test scenario creation and string representation."""
        self.assertEqual(str(self.scenario), 'Earthquake Evacuation Drill (Beginner)')
        self.assertEqual(self.scenario.difficulty_level, 'BEGINNER')
        self.assertEqual(self.scenario.region_tags, ['Delhi', 'Mumbai'])
    
    def test_scenario_total_steps(self):
        """Test total steps calculation."""
        total_steps = self.scenario.get_total_steps()
        self.assertEqual(total_steps, 3)  # s1, s2, s4 (only steps with choices)
    
    def test_attempt_creation(self):
        """Test attempt creation and string representation."""
        self.assertEqual(str(self.attempt), f"{self.user.email} - {self.scenario.title} (20 points)")
        self.assertEqual(self.attempt.score, 20)
        self.assertTrue(self.attempt.completed)
    
    def test_attempt_percentage_score(self):
        """Test percentage score calculation."""
        percentage = self.attempt.get_percentage_score()
        self.assertEqual(percentage, 20.0)  # 20/100 * 100
    
    def test_attempt_duration(self):
        """Test duration calculation."""
        # Set end time
        self.attempt.ended_at = timezone.now()
        self.attempt.save()
        
        duration = self.attempt.get_duration()
        self.assertIsNotNone(duration)
        self.assertGreaterEqual(duration, 0)
    
    def test_complete_attempt(self):
        """Test completing an attempt."""
        self.assertIsNone(self.attempt.ended_at)
        self.attempt.complete_attempt()
        
        self.assertTrue(self.attempt.completed)
        self.assertIsNotNone(self.attempt.ended_at)


class DrillAPITestCase(APITestCase):
    """Test cases for drill API endpoints."""
    
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
        
        # Create test scenario
        self.scenario = DrillScenario.objects.create(
            title='Fire Safety Drill',
            description='Practice fire safety procedures',
            region_tags=['Delhi'],
            json_tree={
                'start_step': 's1',
                'steps': {
                    's1': {
                        'text': 'You see smoke. What do you do?',
                        'choices': [
                            {'id': 'c1', 'text': 'Call emergency services', 'next': 's2', 'score': 10},
                            {'id': 'c2', 'text': 'Try to put out the fire', 'next': 's3', 'score': -5}
                        ]
                    },
                    's2': {'text': 'Good! Now evacuate safely.', 'choices': []},
                    's3': {'text': 'Too dangerous! Call for help.', 'choices': []}
                }
            },
            difficulty_level='INTERMEDIATE',
            estimated_duration=3,
            max_score=50
        )
    
    def get_auth_headers(self, user):
        """Get authentication headers for a user."""
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
    
    def test_scenario_list_as_student(self):
        """Test that students can view scenario list."""
        headers = self.get_auth_headers(self.student)
        url = reverse('drillscenario-list')
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Fire Safety Drill')
        self.assertEqual(response.data[0]['difficulty_level'], 'INTERMEDIATE')
        self.assertTrue('total_steps' in response.data[0])
        self.assertTrue('attempts_count' in response.data[0])
    
    def test_scenario_detail_as_student(self):
        """Test that students can view scenario details."""
        headers = self.get_auth_headers(self.student)
        url = reverse('drillscenario-detail', kwargs={'pk': self.scenario.pk})
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Fire Safety Drill')
        self.assertIn('json_tree', response.data)
        self.assertEqual(response.data['json_tree']['start_step'], 's1')
    
    def test_submit_drill_attempt(self):
        """Test submitting a drill attempt."""
        headers = self.get_auth_headers(self.student)
        url = reverse('drillscenario-attempt', kwargs={'pk': self.scenario.pk})
        
        attempt_data = {
            'responses': {
                'path': ['s1', 's2'],
                'choices_made': {'s1': 'c1'}
            },
            'completed': True
        }
        
        response = self.client.post(url, attempt_data, format='json', **headers)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['score'], 10)  # c1 choice score
        self.assertTrue(response.data['completed'])
        self.assertEqual(response.data['scenario'], self.scenario.pk)
    
    def test_create_scenario_as_admin(self):
        """Test that admins can create scenarios."""
        headers = self.get_auth_headers(self.admin)
        url = reverse('drillscenario-list')
        
        scenario_data = {
            'title': 'Flood Safety Drill',
            'description': 'Practice flood safety procedures',
            'region_tags': ['Kerala'],
            'json_tree': {
                'start_step': 's1',
                'steps': {
                    's1': {
                        'text': 'Water level is rising. What do you do?',
                        'choices': [
                            {'id': 'c1', 'text': 'Move to higher ground', 'next': 's2', 'score': 10},
                            {'id': 'c2', 'text': 'Stay in place', 'next': 's3', 'score': -10}
                        ]
                    },
                    's2': {'text': 'Good! You are safe.', 'choices': []},
                    's3': {'text': 'Dangerous! Water is rising.', 'choices': []}
                }
            },
            'difficulty_level': 'ADVANCED',
            'estimated_duration': 7,
            'max_score': 75
        }
        
        response = self.client.post(url, scenario_data, format='json', **headers)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Flood Safety Drill')
        self.assertEqual(response.data['difficulty_level'], 'ADVANCED')
    
    def test_create_scenario_as_student_denied(self):
        """Test that students cannot create scenarios."""
        headers = self.get_auth_headers(self.student)
        url = reverse('drillscenario-list')
        
        scenario_data = {
            'title': 'Unauthorized Scenario',
            'description': 'This should fail',
            'json_tree': {'start_step': 's1', 'steps': {}}
        }
        
        response = self.client.post(url, scenario_data, format='json', **headers)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access endpoints."""
        url = reverse('drillscenario-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)