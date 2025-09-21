from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Module(models.Model):
    """Learning module for disaster preparedness content."""
    
    DISASTER_TYPE_CHOICES = [
        ('EARTHQUAKE', 'Earthquake'),
        ('FLOOD', 'Flood'),
        ('FIRE', 'Fire'),
        ('CYCLONE', 'Cyclone'),
        ('OTHER', 'Other'),
    ]
    
    title = models.CharField(max_length=200, help_text='Module title')
    description = models.TextField(help_text='Module description')
    disaster_type = models.CharField(
        max_length=20,
        choices=DISASTER_TYPE_CHOICES,
        help_text='Type of disaster this module covers'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_modules',
        help_text='User who created this module'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learning_modules'
        verbose_name = 'Learning Module'
        verbose_name_plural = 'Learning Modules'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_disaster_type_display()})"


class Lesson(models.Model):
    """Individual lesson within a module."""
    
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='lessons',
        help_text='Module this lesson belongs to'
    )
    title = models.CharField(max_length=200, help_text='Lesson title')
    content = models.TextField(help_text='Lesson content (Markdown supported)')
    order = models.PositiveIntegerField(
        default=0,
        help_text='Order of lesson within module'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learning_lessons'
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        ordering = ['order', 'created_at']
        unique_together = ['module', 'order']
    
    def __str__(self):
        return f"{self.title} (Module: {self.module.title})"


class Quiz(models.Model):
    """Quiz associated with a module."""
    
    module = models.OneToOneField(
        Module,
        on_delete=models.CASCADE,
        related_name='quiz',
        help_text='Module this quiz belongs to'
    )
    title = models.CharField(max_length=200, help_text='Quiz title')
    description = models.TextField(
        blank=True,
        null=True,
        help_text='Quiz description'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learning_quizzes'
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} (Module: {self.module.title})"


class Question(models.Model):
    """Individual question within a quiz."""
    
    OPTION_CHOICES = [
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    ]
    
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
        help_text='Quiz this question belongs to'
    )
    text = models.TextField(help_text='Question text')
    option_a = models.CharField(max_length=500, help_text='Option A')
    option_b = models.CharField(max_length=500, help_text='Option B')
    option_c = models.CharField(max_length=500, help_text='Option C')
    option_d = models.CharField(max_length=500, help_text='Option D')
    correct_option = models.CharField(
        max_length=1,
        choices=OPTION_CHOICES,
        help_text='Correct answer option'
    )
    explanation = models.TextField(
        blank=True,
        null=True,
        help_text='Explanation for the correct answer'
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text='Order of question within quiz'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learning_questions'
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['order', 'created_at']
        unique_together = ['quiz', 'order']
    
    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}... (Quiz: {self.quiz.title})"
    
    def get_options_dict(self):
        """Return options as a dictionary for easy API consumption."""
        return {
            'A': self.option_a,
            'B': self.option_b,
            'C': self.option_c,
            'D': self.option_d,
        }