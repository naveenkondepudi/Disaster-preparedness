from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Module, Lesson, Quiz, Question

User = get_user_model()


class LearningModelsTestCase(TestCase):
    """Test cases for learning models."""
    
    def setUp(self):
        """Set up test data."""
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher@test.com',
            password='testpass123',
            role='TEACHER'
        )
        
        self.student = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass123',
            role='STUDENT'
        )
        
        self.module = Module.objects.create(
            title='Earthquake Safety',
            description='Learn about earthquake safety measures',
            disaster_type='EARTHQUAKE',
            created_by=self.teacher
        )
        
        self.lesson = Lesson.objects.create(
            module=self.module,
            title='Drop, Cover, Hold',
            content='When an earthquake occurs, drop to the ground, take cover under a sturdy table, and hold on.',
            order=1
        )
        
        self.quiz = Quiz.objects.create(
            module=self.module,
            title='Earthquake Basics Quiz',
            description='Test your knowledge of earthquake safety'
        )
        
        self.question = Question.objects.create(
            quiz=self.quiz,
            text='What should you do first during an earthquake?',
            option_a='Run outside immediately',
            option_b='Drop, cover, and hold on',
            option_c='Stand in a doorway',
            option_d='Call emergency services',
            correct_option='B',
            explanation='Drop, cover, and hold on is the safest immediate action.',
            order=1
        )
    
    def test_module_creation(self):
        """Test module creation and string representation."""
        self.assertEqual(str(self.module), 'Earthquake Safety (Earthquake)')
        self.assertEqual(self.module.disaster_type, 'EARTHQUAKE')
        self.assertEqual(self.module.created_by, self.teacher)
    
    def test_lesson_creation(self):
        """Test lesson creation and string representation."""
        self.assertEqual(str(self.lesson), 'Drop, Cover, Hold (Module: Earthquake Safety)')
        self.assertEqual(self.lesson.module, self.module)
        self.assertEqual(self.lesson.order, 1)
    
    def test_quiz_creation(self):
        """Test quiz creation and string representation."""
        self.assertEqual(str(self.quiz), 'Earthquake Basics Quiz (Module: Earthquake Safety)')
        self.assertEqual(self.quiz.module, self.module)
    
    def test_question_creation(self):
        """Test question creation and string representation."""
        self.assertEqual(str(self.question), 'Q1: What should you do first during an earthquake?... (Quiz: Earthquake Basics Quiz)')
        self.assertEqual(self.question.quiz, self.quiz)
        self.assertEqual(self.question.correct_option, 'B')
    
    def test_question_options_dict(self):
        """Test question options dictionary method."""
        options = self.question.get_options_dict()
        expected = {
            'A': 'Run outside immediately',
            'B': 'Drop, cover, and hold on',
            'C': 'Stand in a doorway',
            'D': 'Call emergency services'
        }
        self.assertEqual(options, expected)


class LearningAPITestCase(APITestCase):
    """Test cases for learning API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create users
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher@test.com',
            password='testpass123',
            role='TEACHER'
        )
        
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
        
        # Create test module
        self.module = Module.objects.create(
            title='Earthquake Safety',
            description='Learn about earthquake safety measures',
            disaster_type='EARTHQUAKE',
            created_by=self.teacher
        )
        
        # Create test lesson
        self.lesson = Lesson.objects.create(
            module=self.module,
            title='Drop, Cover, Hold',
            content='When an earthquake occurs, drop to the ground, take cover under a sturdy table, and hold on.',
            order=1
        )
        
        # Create test quiz
        self.quiz = Quiz.objects.create(
            module=self.module,
            title='Earthquake Basics Quiz',
            description='Test your knowledge of earthquake safety'
        )
        
        # Create test question
        self.question = Question.objects.create(
            quiz=self.quiz,
            text='What should you do first during an earthquake?',
            option_a='Run outside immediately',
            option_b='Drop, cover, and hold on',
            option_c='Stand in a doorway',
            option_d='Call emergency services',
            correct_option='B',
            explanation='Drop, cover, and hold on is the safest immediate action.',
            order=1
        )
    
    def get_auth_headers(self, user):
        """Get authentication headers for a user."""
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
    
    def test_module_list_as_student(self):
        """Test that students can view module list."""
        headers = self.get_auth_headers(self.student)
        url = reverse('module-list')
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Earthquake Safety')
        self.assertEqual(response.data[0]['disaster_type'], 'EARTHQUAKE')
        self.assertTrue('lessons_count' in response.data[0])
        self.assertTrue('has_quiz' in response.data[0])
    
    def test_module_detail_as_student(self):
        """Test that students can view module details."""
        headers = self.get_auth_headers(self.student)
        url = reverse('module-detail', kwargs={'pk': self.module.pk})
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Earthquake Safety')
        self.assertEqual(len(response.data['lessons']), 1)
        self.assertIsNotNone(response.data['quiz'])
        self.assertEqual(len(response.data['quiz']['questions']), 1)
    
    def test_create_module_as_teacher(self):
        """Test that teachers can create modules."""
        headers = self.get_auth_headers(self.teacher)
        url = reverse('module-list')
        data = {
            'title': 'Fire Safety',
            'description': 'Learn about fire safety measures',
            'disaster_type': 'FIRE'
        }
        response = self.client.post(url, data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Fire Safety')
        self.assertEqual(response.data['disaster_type'], 'FIRE')
        self.assertEqual(response.data['created_by_name'], 'teacher@test.com')
    
    def test_create_module_as_student_denied(self):
        """Test that students cannot create modules."""
        headers = self.get_auth_headers(self.student)
        url = reverse('module-list')
        data = {
            'title': 'Fire Safety',
            'description': 'Learn about fire safety measures',
            'disaster_type': 'FIRE'
        }
        response = self.client.post(url, data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access endpoints."""
        url = reverse('module-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_admin_can_create_module(self):
        """Test that admins can create modules."""
        headers = self.get_auth_headers(self.admin)
        url = reverse('module-list')
        data = {
            'title': 'Cyclone Safety',
            'description': 'Learn about cyclone safety measures',
            'disaster_type': 'CYCLONE'
        }
        response = self.client.post(url, data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Cyclone Safety')
        self.assertEqual(response.data['disaster_type'], 'CYCLONE')