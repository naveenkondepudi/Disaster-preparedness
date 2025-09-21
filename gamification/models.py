from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Badge(models.Model):
    """Badge model for gamification."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    threshold_points = models.IntegerField(help_text="Minimum points required to earn this badge")
    icon = models.CharField(max_length=50, default="🏆", help_text="Emoji or icon for the badge")
    color = models.CharField(max_length=20, default="#f39c12", help_text="Hex color code for the badge")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['threshold_points']
    
    def __str__(self):
        return f"{self.icon} {self.name} ({self.threshold_points} pts)"


class UserPoints(models.Model):
    """Track user points and badges."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='points')
    total_points = models.IntegerField(default=0)
    lesson_points = models.IntegerField(default=0)
    quiz_points = models.IntegerField(default=0)
    drill_points = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-total_points']
    
    def __str__(self):
        return f"{self.user.email} - {self.total_points} points"
    
    def get_current_badge(self):
        """Get the highest badge the user has earned."""
        badges = Badge.objects.filter(
            threshold_points__lte=self.total_points,
            is_active=True
        ).order_by('-threshold_points')
        return badges.first() if badges.exists() else None
    
    def get_next_badge(self):
        """Get the next badge the user can earn."""
        badges = Badge.objects.filter(
            threshold_points__gt=self.total_points,
            is_active=True
        ).order_by('threshold_points')
        return badges.first() if badges.exists() else None
    
    def add_points(self, points, category='general'):
        """Add points to user's total."""
        self.total_points += points
        
        if category == 'lesson':
            self.lesson_points += points
        elif category == 'quiz':
            self.quiz_points += points
        elif category == 'drill':
            self.drill_points += points
        
        self.save()
        return self


class UserBadge(models.Model):
    """Track which badges users have earned."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='users')
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'badge')
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.email} earned {self.badge.name}"


class LessonCompletion(models.Model):
    """Track lesson completions for points."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_completions')
    lesson = models.ForeignKey('learning.Lesson', on_delete=models.CASCADE, related_name='completions')
    completed_at = models.DateTimeField(auto_now_add=True)
    points_earned = models.IntegerField(default=10)
    
    class Meta:
        unique_together = ('user', 'lesson')
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.user.email} completed {self.lesson.title}"


class QuizCompletion(models.Model):
    """Track quiz completions for points."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_completions')
    quiz = models.ForeignKey('learning.Quiz', on_delete=models.CASCADE, related_name='completions')
    score = models.IntegerField()
    points_earned = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.user.email} completed {self.quiz.title} ({self.score}%)"


class DrillCompletion(models.Model):
    """Track drill completions for points."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='drill_completions')
    drill_attempt = models.ForeignKey('drills.DrillAttempt', on_delete=models.CASCADE, related_name='completion')
    points_earned = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.user.email} completed drill ({self.points_earned} pts)"


class Leaderboard(models.Model):
    """Store leaderboard data for caching."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaderboard_entry')
    rank = models.IntegerField()
    total_points = models.IntegerField()
    badge_count = models.IntegerField()
    lessons_completed = models.IntegerField()
    quizzes_completed = models.IntegerField()
    drills_completed = models.IntegerField()
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['rank']
    
    def __str__(self):
        return f"#{self.rank} {self.user.email} - {self.total_points} pts"