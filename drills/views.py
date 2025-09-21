from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone

from .models import DrillScenario, DrillAttempt
from .serializers import (
    DrillScenarioListSerializer, DrillScenarioDetailSerializer,
    DrillAttemptSerializer, DrillAttemptCreateSerializer, DrillAttemptSubmitSerializer
)


class IsAdminOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow admins to create/edit scenarios."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_authenticated and request.user.role == 'ADMIN'


class DrillScenarioViewSet(viewsets.ModelViewSet):
    """ViewSet for managing drill scenarios."""
    
    queryset = DrillScenario.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return DrillScenarioListSerializer
        elif self.action == 'retrieve':
            return DrillScenarioDetailSerializer
        return DrillScenarioDetailSerializer
    
    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action in ['list', 'retrieve', 'attempt', 'attempts']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
        
        return [permission() for permission in permission_classes]
    
    def list(self, request, *args, **kwargs):
        """List all active drill scenarios."""
        queryset = self.get_queryset()
        
        # Filter by region if provided
        region = request.query_params.get('region')
        if region:
            queryset = queryset.filter(region_tags__contains=[region])
        
        # Filter by difficulty if provided
        difficulty = request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific drill scenario with JSON tree."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def attempt(self, request, pk=None):
        """Submit a drill attempt."""
        scenario = self.get_object()
        serializer = DrillAttemptSubmitSerializer(data=request.data)
        
        if serializer.is_valid():
            with transaction.atomic():
                # Create or update attempt
                attempt, created = DrillAttempt.objects.get_or_create(
                    user=request.user,
                    scenario=scenario,
                    started_at__date=timezone.now().date(),
                    defaults={
                        'responses': serializer.validated_data['responses'],
                        'completed': serializer.validated_data['completed'],
                        'score': self._calculate_score(scenario, serializer.validated_data['responses'])
                    }
                )
                
                if not created:
                    # Update existing attempt
                    attempt.responses = serializer.validated_data['responses']
                    attempt.completed = serializer.validated_data['completed']
                    attempt.score = self._calculate_score(scenario, serializer.validated_data['responses'])
                    attempt.complete_attempt()
                
                response_serializer = DrillAttemptSerializer(attempt)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _calculate_score(self, scenario, responses):
        """Calculate score based on user responses."""
        try:
            path = responses.get('path', [])
            choices_made = responses.get('choices_made', {})
            
            total_score = 0
            scenario_tree = scenario.json_tree
            
            # Navigate through the path and sum up scores
            current_step = scenario_tree.get('start_step')
            steps = scenario_tree.get('steps', {})
            
            for step_id in path:
                if step_id in steps:
                    step = steps[step_id]
                    if 'choices' in step:
                        choice_id = choices_made.get(step_id)
                        if choice_id:
                            for choice in step['choices']:
                                if choice.get('id') == choice_id:
                                    total_score += choice.get('score', 0)
                                    break
            
            return min(total_score, scenario.max_score)
        except Exception:
            return 0
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def attempts(self, request, pk=None):
        """Get user's attempts for this scenario."""
        scenario = self.get_object()
        attempts = DrillAttempt.objects.filter(
            user=request.user,
            scenario=scenario
        ).order_by('-started_at')
        
        serializer = DrillAttemptSerializer(attempts, many=True)
        return Response(serializer.data)


class DrillAttemptViewSet(viewsets.ModelViewSet):
    """ViewSet for managing drill attempts."""
    
    serializer_class = DrillAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return attempts for the current user."""
        return DrillAttempt.objects.filter(user=self.request.user).order_by('-started_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return DrillAttemptCreateSerializer
        return DrillAttemptSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new drill attempt."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def list(self, request, *args, **kwargs):
        """List user's drill attempts."""
        queryset = self.get_queryset()
        
        # Filter by scenario if provided
        scenario_id = request.query_params.get('scenario')
        if scenario_id:
            queryset = queryset.filter(scenario_id=scenario_id)
        
        # Filter by completion status if provided
        completed = request.query_params.get('completed')
        if completed is not None:
            queryset = queryset.filter(completed=completed.lower() == 'true')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)