from rest_framework import serializers
from .models import DrillScenario, DrillAttempt


class DrillScenarioListSerializer(serializers.ModelSerializer):
    """Serializer for drill scenario list view."""
    
    total_steps = serializers.SerializerMethodField()
    attempts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DrillScenario
        fields = [
            'id', 'title', 'description', 'region_tags', 'difficulty_level',
            'estimated_duration', 'max_score', 'total_steps', 'attempts_count',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_total_steps(self, obj):
        """Get total number of steps in the scenario."""
        return obj.get_total_steps()
    
    def get_attempts_count(self, obj):
        """Get number of attempts for this scenario."""
        return obj.attempts.count()


class DrillScenarioDetailSerializer(serializers.ModelSerializer):
    """Serializer for drill scenario detail view (includes JSON tree)."""
    
    total_steps = serializers.SerializerMethodField()
    
    class Meta:
        model = DrillScenario
        fields = [
            'id', 'title', 'description', 'region_tags', 'json_tree',
            'difficulty_level', 'estimated_duration', 'max_score',
            'total_steps', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_steps(self, obj):
        """Get total number of steps in the scenario."""
        return obj.get_total_steps()


class DrillAttemptSerializer(serializers.ModelSerializer):
    """Serializer for drill attempts."""
    
    scenario_title = serializers.CharField(source='scenario.title', read_only=True)
    percentage_score = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = DrillAttempt
        fields = [
            'id', 'scenario', 'scenario_title', 'score', 'percentage_score',
            'responses', 'completed', 'started_at', 'ended_at', 'duration'
        ]
        read_only_fields = ['id', 'started_at', 'ended_at']
    
    def get_percentage_score(self, obj):
        """Get score as percentage."""
        return obj.get_percentage_score()
    
    def get_duration(self, obj):
        """Get duration of the attempt."""
        return obj.get_duration()


class DrillAttemptCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating drill attempts."""
    
    class Meta:
        model = DrillAttempt
        fields = [
            'id', 'scenario', 'score', 'responses', 'completed',
            'started_at', 'ended_at'
        ]
        read_only_fields = ['id', 'started_at', 'ended_at']
    
    def create(self, validated_data):
        """Create a new drill attempt."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_scenario(self, value):
        """Validate that the scenario is active."""
        if not value.is_active:
            raise serializers.ValidationError("This scenario is not currently active.")
        return value
    
    def validate_score(self, value):
        """Validate score is within scenario limits."""
        scenario = self.initial_data.get('scenario')
        if scenario:
            try:
                scenario_obj = DrillScenario.objects.get(id=scenario)
                if value > scenario_obj.max_score:
                    raise serializers.ValidationError(
                        f"Score cannot exceed {scenario_obj.max_score}"
                    )
            except DrillScenario.DoesNotExist:
                pass
        return value


class DrillAttemptSubmitSerializer(serializers.Serializer):
    """Serializer for submitting drill attempt responses."""
    
    responses = serializers.JSONField(help_text='User responses and path taken')
    completed = serializers.BooleanField(default=True)
    
    def validate_responses(self, value):
        """Validate responses structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Responses must be a dictionary.")
        
        # Basic validation - ensure required fields exist
        required_fields = ['path', 'choices_made']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing required field: {field}")
        
        return value
