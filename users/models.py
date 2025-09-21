from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model for disaster preparedness system."""
    
    ROLE_CHOICES = [
        ('STUDENT', 'Student'),
        ('TEACHER', 'Teacher'),
        ('ADMIN', 'Administrator'),
    ]
    
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='STUDENT',
        help_text='Role of user in the system'
    )
    
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text='Phone number for emergency contacts'
    )
    
    emergency_contact = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text='Emergency contact phone number'
    )
    
    institution = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Educational institution name'
    )
    
    grade_class = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Grade or class level'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
