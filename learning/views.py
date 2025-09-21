from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db import models

from .models import Module, Lesson, Quiz, Question
from .serializers import (
    ModuleListSerializer, ModuleDetailSerializer, ModuleCreateSerializer,
    LessonSerializer, LessonCreateSerializer,
    QuizSerializer, QuizCreateSerializer,
    QuestionSerializer, QuestionCreateSerializer
)


class IsTeacherOrAdmin(permissions.BasePermission):
    """Custom permission to only allow teachers and admins to create/edit content."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_authenticated and request.user.role in ['TEACHER', 'ADMIN']


class ModuleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing learning modules."""
    
    queryset = Module.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ModuleListSerializer
        elif self.action == 'retrieve':
            return ModuleDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ModuleCreateSerializer
        return ModuleDetailSerializer
    
    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
        
        return [permission() for permission in permission_classes]
    
    def list(self, request, *args, **kwargs):
        """List all modules with basic information."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific module with lessons and quiz."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create a new module."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsTeacherOrAdmin])
    def add_lesson(self, request, pk=None):
        """Add a lesson to a module."""
        module = self.get_object()
        serializer = LessonCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Check if order is provided, otherwise set to next available order
            if 'order' not in serializer.validated_data:
                max_order = module.lessons.aggregate(
                    max_order=models.Max('order')
                )['max_order'] or 0
                serializer.validated_data['order'] = max_order + 1
            
            lesson = serializer.save(module=module)
            return Response(
                LessonSerializer(lesson).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsTeacherOrAdmin])
    def add_quiz(self, request, pk=None):
        """Add a quiz to a module."""
        module = self.get_object()
        
        # Check if module already has a quiz
        if hasattr(module, 'quiz'):
            return Response(
                {'error': 'Module already has a quiz'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = QuizCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            with transaction.atomic():
                quiz = serializer.save(module=module)
                return Response(
                    QuizSerializer(quiz).data,
                    status=status.HTTP_201_CREATED
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def lessons(self, request, pk=None):
        """Get all lessons for a module."""
        module = self.get_object()
        lessons = module.lessons.all()
        serializer = LessonSerializer(lessons, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def quiz(self, request, pk=None):
        """Get quiz for a module."""
        module = self.get_object()
        
        if not hasattr(module, 'quiz'):
            return Response(
                {'error': 'Module does not have a quiz'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = QuizSerializer(module.quiz)
        return Response(serializer.data)


class LessonViewSet(viewsets.ModelViewSet):
    """ViewSet for managing lessons."""
    
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return LessonCreateSerializer
        return LessonSerializer
    
    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
        
        return [permission() for permission in permission_classes]


class QuizViewSet(viewsets.ModelViewSet):
    """ViewSet for managing quizzes."""
    
    queryset = Quiz.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return QuizCreateSerializer
        return QuizSerializer
    
    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
        
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'], permission_classes=[IsTeacherOrAdmin])
    def add_question(self, request, pk=None):
        """Add a question to a quiz."""
        quiz = self.get_object()
        serializer = QuestionCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Check if order is provided, otherwise set to next available order
            if 'order' not in serializer.validated_data:
                max_order = quiz.questions.aggregate(
                    max_order=models.Max('order')
                )['max_order'] or 0
                serializer.validated_data['order'] = max_order + 1
            
            question = serializer.save(quiz=quiz)
            return Response(
                QuestionSerializer(question).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """Get all questions for a quiz."""
        quiz = self.get_object()
        questions = quiz.questions.all()
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)


class QuestionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing quiz questions."""
    
    queryset = Question.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return QuestionCreateSerializer
        return QuestionSerializer
    
    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
        
        return [permission() for permission in permission_classes]