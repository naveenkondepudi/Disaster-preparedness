from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class DrillScenario(models.Model):
    """Virtual drill scenario with decision tree structure."""
    
    title = models.CharField(max_length=200, help_text='Scenario title')
    description = models.TextField(help_text='Scenario description')
    region_tags = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text='Regions where this scenario is relevant'
    )
    json_tree = models.JSONField(
        help_text='Decision tree structure in JSON format'
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('BEGINNER', 'Beginner'),
            ('INTERMEDIATE', 'Intermediate'),
            ('ADVANCED', 'Advanced'),
        ],
        default='BEGINNER',
        help_text='Difficulty level of the scenario'
    )
    estimated_duration = models.PositiveIntegerField(
        default=5,
        help_text='Estimated duration in minutes'
    )
    max_score = models.PositiveIntegerField(
        default=100,
        help_text='Maximum possible score for this scenario'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this scenario is available for attempts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'drill_scenarios'
        verbose_name = 'Drill Scenario'
        verbose_name_plural = 'Drill Scenarios'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_difficulty_level_display()})"
    
    def get_total_steps(self):
        """Calculate total number of steps in the decision tree."""
        def count_steps(node):
            if not isinstance(node, dict):
                return 0
            
            count = 1
            if 'choices' in node:
                for choice in node['choices']:
                    if 'next' in choice:
                        count += count_steps(node.get('steps', {}).get(choice['next'], {}))
            return count
        
        return count_steps(self.json_tree.get('steps', {}).get(self.json_tree.get('start_step', ''), {}))


class DrillAttempt(models.Model):
    """User's attempt at a drill scenario."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='drill_attempts',
        help_text='User who attempted the drill'
    )
    scenario = models.ForeignKey(
        DrillScenario,
        on_delete=models.CASCADE,
        related_name='attempts',
        help_text='Scenario that was attempted'
    )
    score = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Score achieved in this attempt'
    )
    responses = models.JSONField(
        default=dict,
        help_text='User responses and path taken through the scenario'
    )
    completed = models.BooleanField(
        default=False,
        help_text='Whether the attempt was completed'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'drill_attempts'
        verbose_name = 'Drill Attempt'
        verbose_name_plural = 'Drill Attempts'
        ordering = ['-started_at']
        unique_together = ['user', 'scenario', 'started_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.scenario.title} ({self.score} points)"
    
    def get_percentage_score(self):
        """Get score as percentage of maximum possible score."""
        if self.scenario.max_score == 0:
            return 0
        return round((self.score / self.scenario.max_score) * 100, 2)
    
    def get_duration(self):
        """Get duration of the attempt in minutes."""
        if not self.ended_at:
            return None
        
        duration = self.ended_at - self.started_at
        return round(duration.total_seconds() / 60, 2)
    
    def complete_attempt(self):
        """Mark attempt as completed and set end time."""
        from django.utils import timezone
        self.completed = True
        self.ended_at = timezone.now()
        self.save()