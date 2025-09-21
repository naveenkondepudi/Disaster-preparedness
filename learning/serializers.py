from rest_framework import serializers
from .models import Module, Lesson, Quiz, Question


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for quiz questions."""
    
    options = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = [
            'id', 'text', 'options', 'order', 'explanation'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_options(self, obj):
        """Return options as a dictionary."""
        return obj.get_options_dict()


class QuestionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating quiz questions (includes correct answer)."""
    
    class Meta:
        model = Question
        fields = [
            'id', 'text', 'option_a', 'option_b', 'option_c', 'option_d',
            'correct_option', 'explanation', 'order'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class QuizSerializer(serializers.ModelSerializer):
    """Serializer for quizzes."""
    
    questions = QuestionSerializer(many=True, read_only=True)
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'questions', 'questions_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_questions_count(self, obj):
        """Return the number of questions in the quiz."""
        return obj.questions.count()


class QuizCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating quizzes."""
    
    questions = QuestionCreateSerializer(many=True, required=False)
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'questions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create quiz with questions."""
        questions_data = validated_data.pop('questions', [])
        quiz = Quiz.objects.create(**validated_data)
        
        for question_data in questions_data:
            Question.objects.create(quiz=quiz, **question_data)
        
        return quiz


class LessonSerializer(serializers.ModelSerializer):
    """Serializer for lessons."""
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'content', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModuleListSerializer(serializers.ModelSerializer):
    """Serializer for module list view (minimal data)."""
    
    lessons_count = serializers.SerializerMethodField()
    has_quiz = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = [
            'id', 'title', 'description', 'disaster_type', 'lessons_count',
            'has_quiz', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_lessons_count(self, obj):
        """Return the number of lessons in the module."""
        return obj.lessons.count()
    
    def get_has_quiz(self, obj):
        """Return whether the module has a quiz."""
        return hasattr(obj, 'quiz')
    
    def get_created_by_name(self, obj):
        """Return the name of the user who created the module."""
        return obj.created_by.email


class ModuleDetailSerializer(serializers.ModelSerializer):
    """Serializer for module detail view (includes lessons and quiz)."""
    
    lessons = LessonSerializer(many=True, read_only=True)
    quiz = QuizSerializer(read_only=True)
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = [
            'id', 'title', 'description', 'disaster_type', 'lessons', 'quiz',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        """Return the name of the user who created the module."""
        return obj.created_by.email


class ModuleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating modules."""
    
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = [
            'id', 'title', 'description', 'disaster_type', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        """Return the name of the user who created the module."""
        return obj.created_by.email
    
    def create(self, validated_data):
        """Create module with the current user as creator."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class LessonCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating lessons."""
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'content', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
