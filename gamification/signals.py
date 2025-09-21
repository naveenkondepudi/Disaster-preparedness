from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import UserPoints, UserBadge, LessonCompletion, QuizCompletion, DrillCompletion, Leaderboard
from learning.models import Lesson, Quiz
from drills.models import DrillAttempt

User = get_user_model()


@receiver(post_save, sender=LessonCompletion)
def update_points_on_lesson_completion(sender, instance, created, **kwargs):
    """Update user points when a lesson is completed."""
    if created:
        user_points, _ = UserPoints.objects.get_or_create(user=instance.user)
        user_points.add_points(instance.points_earned, 'lesson')
        
        # Check for new badges
        check_and_assign_badges(instance.user)


@receiver(post_save, sender=QuizCompletion)
def update_points_on_quiz_completion(sender, instance, created, **kwargs):
    """Update user points when a quiz is completed."""
    if created:
        user_points, _ = UserPoints.objects.get_or_create(user=instance.user)
        user_points.add_points(instance.points_earned, 'quiz')
        
        # Check for new badges
        check_and_assign_badges(instance.user)


@receiver(post_save, sender=DrillCompletion)
def update_points_on_drill_completion(sender, instance, created, **kwargs):
    """Update user points when a drill is completed."""
    if created:
        user_points, _ = UserPoints.objects.get_or_create(user=instance.user)
        user_points.add_points(instance.points_earned, 'drill')
        
        # Check for new badges
        check_and_assign_badges(instance.user)


def check_and_assign_badges(user):
    """Check if user has earned any new badges and assign them."""
    try:
        user_points = UserPoints.objects.get(user=user)
    except UserPoints.DoesNotExist:
        return
    
    from .models import Badge
    
    # Get all badges the user hasn't earned yet
    earned_badges = UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
    available_badges = Badge.objects.filter(
        threshold_points__lte=user_points.total_points,
        is_active=True
    ).exclude(id__in=earned_badges)
    
    # Assign new badges
    for badge in available_badges:
        UserBadge.objects.create(user=user, badge=badge)
    
    # Update leaderboard
    update_leaderboard()


def update_leaderboard():
    """Update the leaderboard with current user rankings."""
    # Clear existing leaderboard
    Leaderboard.objects.all().delete()
    
    # Get all users with points, ordered by total points
    users_with_points = UserPoints.objects.select_related('user').order_by('-total_points')
    
    # Create leaderboard entries
    for rank, user_points in enumerate(users_with_points, 1):
        # Count completions
        lessons_completed = LessonCompletion.objects.filter(user=user_points.user).count()
        quizzes_completed = QuizCompletion.objects.filter(user=user_points.user).count()
        drills_completed = DrillCompletion.objects.filter(user=user_points.user).count()
        badge_count = UserBadge.objects.filter(user=user_points.user).count()
        
        Leaderboard.objects.create(
            user=user_points.user,
            rank=rank,
            total_points=user_points.total_points,
            badge_count=badge_count,
            lessons_completed=lessons_completed,
            quizzes_completed=quizzes_completed,
            drills_completed=drills_completed
        )


def create_default_badges():
    """Create default badges if they don't exist."""
    from .models import Badge
    
    default_badges = [
        {
            'name': 'Beginner',
            'description': 'Completed your first learning module',
            'threshold_points': 50,
            'icon': '🌱',
            'color': '#27ae60'
        },
        {
            'name': 'Learner',
            'description': 'Completed 5 lessons',
            'threshold_points': 100,
            'icon': '📚',
            'color': '#3498db'
        },
        {
            'name': 'Quiz Master',
            'description': 'Scored 80% or higher on 3 quizzes',
            'threshold_points': 200,
            'icon': '🧠',
            'color': '#9b59b6'
        },
        {
            'name': 'Drill Expert',
            'description': 'Completed 5 drill scenarios',
            'threshold_points': 300,
            'icon': '🏃‍♂️',
            'color': '#e67e22'
        },
        {
            'name': 'Intermediate',
            'description': 'Earned 500 points',
            'threshold_points': 500,
            'icon': '⭐',
            'color': '#f39c12'
        },
        {
            'name': 'Advanced',
            'description': 'Earned 1000 points',
            'threshold_points': 1000,
            'icon': '🔥',
            'color': '#e74c3c'
        },
        {
            'name': 'Expert',
            'description': 'Earned 2000 points',
            'threshold_points': 2000,
            'icon': '💎',
            'color': '#8e44ad'
        },
        {
            'name': 'Disaster Hero',
            'description': 'Earned 5000 points - The ultimate disaster preparedness champion!',
            'threshold_points': 5000,
            'icon': '🦸‍♂️',
            'color': '#2c3e50'
        }
    ]
    
    for badge_data in default_badges:
        Badge.objects.get_or_create(
            name=badge_data['name'],
            defaults=badge_data
        )
