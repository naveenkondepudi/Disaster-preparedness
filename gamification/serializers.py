from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Badge, UserPoints, UserBadge, LessonCompletion, QuizCompletion, DrillCompletion, Leaderboard

User = get_user_model()


class BadgeSerializer(serializers.ModelSerializer):
    """Serializer for Badge model."""
    class Meta:
        model = Badge
        fields = '__all__'


class UserBadgeSerializer(serializers.ModelSerializer):
    """Serializer for UserBadge model."""
    badge = BadgeSerializer(read_only=True)
    
    class Meta:
        model = UserBadge
        fields = ['badge', 'earned_at']


class UserPointsSerializer(serializers.ModelSerializer):
    """Serializer for UserPoints model."""
    current_badge = serializers.SerializerMethodField()
    next_badge = serializers.SerializerMethodField()
    earned_badges = UserBadgeSerializer(many=True, read_only=True)
    
    class Meta:
        model = UserPoints
        fields = [
            'total_points', 'lesson_points', 'quiz_points', 'drill_points',
            'current_badge', 'next_badge', 'earned_badges', 'last_updated'
        ]
    
    def get_current_badge(self, obj):
        badge = obj.get_current_badge()
        if badge:
            return {
                'name': badge.name,
                'description': badge.description,
                'icon': badge.icon,
                'color': badge.color,
                'threshold_points': badge.threshold_points
            }
        return None
    
    def get_next_badge(self, obj):
        badge = obj.get_next_badge()
        if badge:
            return {
                'name': badge.name,
                'description': badge.description,
                'icon': badge.icon,
                'color': badge.color,
                'threshold_points': badge.threshold_points,
                'points_needed': badge.threshold_points - obj.total_points
            }
        return None


class UserStatsSerializer(serializers.ModelSerializer):
    """Serializer for user statistics."""
    user_points = UserPointsSerializer(read_only=True)
    lessons_completed = serializers.SerializerMethodField()
    quizzes_completed = serializers.SerializerMethodField()
    drills_completed = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role',
            'user_points', 'lessons_completed', 'quizzes_completed',
            'drills_completed', 'completion_rate', 'created_at'
        ]
    
    def get_lessons_completed(self, obj):
        return LessonCompletion.objects.filter(user=obj).count()
    
    def get_quizzes_completed(self, obj):
        return QuizCompletion.objects.filter(user=obj).count()
    
    def get_drills_completed(self, obj):
        return DrillCompletion.objects.filter(user=obj).count()
    
    def get_completion_rate(self, obj):
        # Calculate completion rate based on available content
        from learning.models import Lesson, Quiz
        from drills.models import DrillScenario
        
        total_lessons = Lesson.objects.count()
        total_quizzes = Quiz.objects.count()
        total_drills = DrillScenario.objects.count()
        
        if total_lessons + total_quizzes + total_drills == 0:
            return 0
        
        completed_lessons = LessonCompletion.objects.filter(user=obj).count()
        completed_quizzes = QuizCompletion.objects.filter(user=obj).count()
        completed_drills = DrillCompletion.objects.filter(user=obj).count()
        
        total_completed = completed_lessons + completed_quizzes + completed_drills
        total_available = total_lessons + total_quizzes + total_drills
        
        return round((total_completed / total_available) * 100, 2)


class LeaderboardSerializer(serializers.ModelSerializer):
    """Serializer for Leaderboard model."""
    user_email = serializers.ReadOnlyField(source='user.email')
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Leaderboard
        fields = [
            'rank', 'user_email', 'user_name', 'total_points',
            'badge_count', 'lessons_completed', 'quizzes_completed',
            'drills_completed', 'last_updated'
        ]
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


class ModuleStatsSerializer(serializers.Serializer):
    """Serializer for module statistics."""
    module_id = serializers.IntegerField()
    module_title = serializers.CharField()
    total_lessons = serializers.IntegerField()
    total_quizzes = serializers.IntegerField()
    students_enrolled = serializers.IntegerField()
    lessons_completed = serializers.IntegerField()
    quizzes_completed = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    average_score = serializers.FloatField()


class DrillStatsSerializer(serializers.Serializer):
    """Serializer for drill statistics."""
    drill_id = serializers.IntegerField()
    drill_title = serializers.CharField()
    total_attempts = serializers.IntegerField()
    unique_students = serializers.IntegerField()
    average_score = serializers.FloatField()
    completion_rate = serializers.FloatField()
    difficulty_distribution = serializers.DictField()


class LessonCompletionSerializer(serializers.ModelSerializer):
    """Serializer for LessonCompletion model."""
    lesson_title = serializers.ReadOnlyField(source='lesson.title')
    module_title = serializers.ReadOnlyField(source='lesson.module.title')
    
    class Meta:
        model = LessonCompletion
        fields = ['lesson_title', 'module_title', 'points_earned', 'completed_at']


class QuizCompletionSerializer(serializers.ModelSerializer):
    """Serializer for QuizCompletion model."""
    quiz_title = serializers.ReadOnlyField(source='quiz.title')
    module_title = serializers.ReadOnlyField(source='quiz.module.title')
    
    class Meta:
        model = QuizCompletion
        fields = ['quiz_title', 'module_title', 'score', 'points_earned', 'completed_at']


class DrillCompletionSerializer(serializers.ModelSerializer):
    """Serializer for DrillCompletion model."""
    drill_title = serializers.ReadOnlyField(source='drill_attempt.scenario.title')
    
    class Meta:
        model = DrillCompletion
        fields = ['drill_title', 'points_earned', 'completed_at']
