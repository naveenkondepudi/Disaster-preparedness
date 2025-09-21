from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg
from .models import Module, Lesson, Quiz, Question


class LessonInline(admin.TabularInline):
    """Inline admin for lessons."""
    model = Lesson
    extra = 1
    ordering = ['order']


class QuestionInline(admin.TabularInline):
    """Inline admin for quiz questions."""
    model = Question
    extra = 1
    ordering = ['order']


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    """Admin interface for modules."""
    list_display = ['title', 'disaster_type', 'created_by', 'completion_stats', 'created_at']
    list_filter = ['disaster_type', 'created_at', 'created_by']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [LessonInline]
    
    def completion_stats(self, obj):
        """Show completion statistics for the module."""
        try:
            from gamification.models import LessonCompletion, QuizCompletion
            
            lesson_completions = LessonCompletion.objects.filter(lesson__module=obj).count()
            quiz_completions = QuizCompletion.objects.filter(quiz__module=obj).count()
            
            return format_html(
                '<span style="color: #27ae60;">Lessons: {}</span><br>'
                '<span style="color: #3498db;">Quizzes: {}</span>',
                lesson_completions,
                quiz_completions
            )
        except ImportError:
            return 'N/A'
    completion_stats.short_description = 'Completion Stats'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'disaster_type', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Admin interface for lessons."""
    list_display = ['title', 'module', 'order', 'completion_count', 'created_at']
    list_filter = ['module', 'created_at']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['module', 'order']
    
    def completion_count(self, obj):
        """Show number of completions for this lesson."""
        try:
            from gamification.models import LessonCompletion
            count = LessonCompletion.objects.filter(lesson=obj).count()
            return format_html(
                '<span style="color: #27ae60;">{}</span>',
                count
            )
        except ImportError:
            return 'N/A'
    completion_count.short_description = 'Completions'


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin interface for quizzes."""
    list_display = ['title', 'module', 'completion_stats', 'created_at']
    list_filter = ['created_at', 'module']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [QuestionInline]
    
    def completion_stats(self, obj):
        """Show completion statistics for the quiz."""
        try:
            from gamification.models import QuizCompletion
            
            completions = QuizCompletion.objects.filter(quiz=obj)
            count = completions.count()
            avg_score = completions.aggregate(avg_score=Avg('score'))['avg_score'] or 0
            
            return format_html(
                '<span style="color: #3498db;">Completions: {}</span><br>'
                '<span style="color: #f39c12;">Avg Score: {:.1f}%</span>',
                count,
                avg_score
            )
        except ImportError:
            return 'N/A'
    completion_stats.short_description = 'Completion Stats'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('module', 'title', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin interface for quiz questions."""
    list_display = ['text_short', 'quiz', 'correct_option', 'order']
    list_filter = ['quiz', 'correct_option', 'created_at']
    search_fields = ['text', 'option_a', 'option_b', 'option_c', 'option_d']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['quiz', 'order']
    
    def text_short(self, obj):
        """Return shortened question text for list display."""
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_short.short_description = 'Question Text'
    
    fieldsets = (
        ('Question Information', {
            'fields': ('quiz', 'text', 'order')
        }),
        ('Options', {
            'fields': ('option_a', 'option_b', 'option_c', 'option_d', 'correct_option')
        }),
        ('Additional Information', {
            'fields': ('explanation',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )