from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
from django.contrib.auth import get_user_model

from .models import Badge, UserPoints, UserBadge, LessonCompletion, QuizCompletion, DrillCompletion, Leaderboard
from .serializers import (
    BadgeSerializer, UserStatsSerializer, LeaderboardSerializer,
    ModuleStatsSerializer, DrillStatsSerializer, LessonCompletionSerializer,
    QuizCompletionSerializer, DrillCompletionSerializer
)
from learning.models import Module, Lesson, Quiz
from drills.models import DrillScenario, DrillAttempt
from users.permissions import IsAdminOrTeacher

User = get_user_model()


class BadgeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for badges."""
    queryset = Badge.objects.filter(is_active=True)
    serializer_class = BadgeSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user statistics."""
    queryset = User.objects.all()
    serializer_class = UserStatsSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrTeacher]
    
    def get_queryset(self):
        """Filter users based on role and other criteria."""
        queryset = super().get_queryset()
        
        # Filter by role if specified
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role.upper())
        
        # Filter by region if specified (assuming user has region field)
        region = self.request.query_params.get('region')
        if region:
            # This would need to be implemented based on your user model
            pass
        
        return queryset.prefetch_related('earned_badges__badge')
    
    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """Get leaderboard data."""
        limit = int(request.query_params.get('limit', 10))
        leaderboard = Leaderboard.objects.select_related('user')[:limit]
        serializer = LeaderboardSerializer(leaderboard, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def completions(self, request, pk=None):
        """Get user's completion history."""
        user = self.get_object()
        
        lesson_completions = LessonCompletion.objects.filter(user=user).select_related('lesson__module')
        quiz_completions = QuizCompletion.objects.filter(user=user).select_related('quiz__module')
        drill_completions = DrillCompletion.objects.filter(user=user).select_related('drill_attempt__scenario')
        
        data = {
            'lesson_completions': LessonCompletionSerializer(lesson_completions, many=True).data,
            'quiz_completions': QuizCompletionSerializer(quiz_completions, many=True).data,
            'drill_completions': DrillCompletionSerializer(drill_completions, many=True).data,
        }
        
        return Response(data)


class AdminStatsViewSet(viewsets.ViewSet):
    """ViewSet for admin statistics."""
    permission_classes = [permissions.IsAuthenticated, IsAdminOrTeacher]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get overview statistics."""
        total_users = User.objects.count()
        total_modules = Module.objects.count()
        total_drills = DrillScenario.objects.count()
        total_alerts = Alert.objects.count() if hasattr(self, 'Alert') else 0
        
        # User engagement stats
        active_users = User.objects.filter(
            Q(lesson_completions__isnull=False) |
            Q(quiz_completions__isnull=False) |
            Q(drill_completions__isnull=False)
        ).distinct().count()
        
        # Completion stats
        total_lesson_completions = LessonCompletion.objects.count()
        total_quiz_completions = QuizCompletion.objects.count()
        total_drill_completions = DrillCompletion.objects.count()
        
        data = {
            'total_users': total_users,
            'active_users': active_users,
            'total_modules': total_modules,
            'total_drills': total_drills,
            'total_alerts': total_alerts,
            'total_lesson_completions': total_lesson_completions,
            'total_quiz_completions': total_quiz_completions,
            'total_drill_completions': total_drill_completions,
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def module_stats(self, request):
        """Get module statistics."""
        modules = Module.objects.annotate(
            total_lessons=Count('lessons'),
            total_quizzes=Count('quiz'),
            students_enrolled=Count('lessons__completions__user', distinct=True),
            lessons_completed=Count('lessons__completions'),
            quizzes_completed=Count('quiz__completions'),
        )
        
        stats = []
        for module in modules:
            completion_rate = 0
            if module.total_lessons + module.total_quizzes > 0:
                completion_rate = ((module.lessons_completed + module.quizzes_completed) / 
                                (module.total_lessons + module.total_quizzes)) * 100
            
            # Calculate average score for quizzes
            quiz_scores = QuizCompletion.objects.filter(
                quiz__module=module
            ).values_list('score', flat=True)
            average_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
            
            stats.append({
                'module_id': module.id,
                'module_title': module.title,
                'total_lessons': module.total_lessons,
                'total_quizzes': module.total_quizzes,
                'students_enrolled': module.students_enrolled,
                'lessons_completed': module.lessons_completed,
                'quizzes_completed': module.quizzes_completed,
                'completion_rate': round(completion_rate, 2),
                'average_score': round(average_score, 2),
            })
        
        serializer = ModuleStatsSerializer(stats, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def module_detail_stats(self, request, pk=None):
        """Get detailed statistics for a specific module."""
        try:
            module = Module.objects.get(pk=pk)
        except Module.DoesNotExist:
            return Response({'error': 'Module not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get detailed stats
        lessons = module.lessons.all()
        quiz = getattr(module, 'quiz', None)
        
        lesson_stats = []
        for lesson in lessons:
            completions = LessonCompletion.objects.filter(lesson=lesson)
            lesson_stats.append({
                'lesson_id': lesson.id,
                'lesson_title': lesson.title,
                'completions_count': completions.count(),
                'completion_rate': (completions.count() / User.objects.count()) * 100 if User.objects.count() > 0 else 0,
            })
        
        quiz_stats = None
        if quiz:
            quiz_completions = QuizCompletion.objects.filter(quiz=quiz)
            quiz_stats = {
                'quiz_id': quiz.id,
                'quiz_title': quiz.title,
                'completions_count': quiz_completions.count(),
                'average_score': quiz_completions.aggregate(avg_score=Avg('score'))['avg_score'] or 0,
                'completion_rate': (quiz_completions.count() / User.objects.count()) * 100 if User.objects.count() > 0 else 0,
            }
        
        data = {
            'module': {
                'id': module.id,
                'title': module.title,
                'description': module.description,
            },
            'lesson_stats': lesson_stats,
            'quiz_stats': quiz_stats,
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def drill_stats(self, request):
        """Get drill statistics."""
        drills = DrillScenario.objects.annotate(
            total_attempts=Count('attempts'),
            unique_students=Count('attempts__user', distinct=True),
        )
        
        stats = []
        for drill in drills:
            attempts = DrillAttempt.objects.filter(scenario=drill)
            
            if attempts.exists():
                average_score = attempts.aggregate(avg_score=Avg('score'))['avg_score'] or 0
                completion_rate = (attempts.filter(completed=True).count() / attempts.count()) * 100
            else:
                average_score = 0
                completion_rate = 0
            
            # Difficulty distribution
            difficulty_distribution = {
                'beginner': attempts.filter(scenario__difficulty_level='BEGINNER').count(),
                'intermediate': attempts.filter(scenario__difficulty_level='INTERMEDIATE').count(),
                'advanced': attempts.filter(scenario__difficulty_level='ADVANCED').count(),
            }
            
            stats.append({
                'drill_id': drill.id,
                'drill_title': drill.title,
                'total_attempts': drill.total_attempts,
                'unique_students': drill.unique_students,
                'average_score': round(average_score, 2),
                'completion_rate': round(completion_rate, 2),
                'difficulty_distribution': difficulty_distribution,
            })
        
        serializer = DrillStatsSerializer(stats, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def drill_detail_stats(self, request, pk=None):
        """Get detailed statistics for a specific drill."""
        try:
            drill = DrillScenario.objects.get(pk=pk)
        except DrillScenario.DoesNotExist:
            return Response({'error': 'Drill not found'}, status=status.HTTP_404_NOT_FOUND)
        
        attempts = DrillAttempt.objects.filter(scenario=drill).select_related('user')
        
        # Calculate statistics
        total_attempts = attempts.count()
        completed_attempts = attempts.filter(completed=True).count()
        average_score = attempts.aggregate(avg_score=Avg('score'))['avg_score'] or 0
        
        # Score distribution
        score_ranges = {
            '0-25': attempts.filter(score__gte=0, score__lte=25).count(),
            '26-50': attempts.filter(score__gte=26, score__lte=50).count(),
            '51-75': attempts.filter(score__gte=51, score__lte=75).count(),
            '76-100': attempts.filter(score__gte=76, score__lte=100).count(),
        }
        
        # Recent attempts
        recent_attempts = attempts.order_by('-started_at')[:10]
        
        data = {
            'drill': {
                'id': drill.id,
                'title': drill.title,
                'description': drill.description,
                'difficulty_level': drill.difficulty_level,
                'max_score': drill.max_score,
            },
            'statistics': {
                'total_attempts': total_attempts,
                'completed_attempts': completed_attempts,
                'completion_rate': (completed_attempts / total_attempts) * 100 if total_attempts > 0 else 0,
                'average_score': round(average_score, 2),
                'score_distribution': score_ranges,
            },
            'recent_attempts': [
                {
                    'user_email': attempt.user.email,
                    'score': attempt.score,
                    'completed': attempt.completed,
                    'started_at': attempt.started_at,
                    'ended_at': attempt.ended_at,
                }
                for attempt in recent_attempts
            ],
        }
        
        return Response(data)