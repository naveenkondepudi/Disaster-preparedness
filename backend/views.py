from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.management import call_command
from django.db import transaction
import json

@csrf_exempt
@require_http_methods(["GET", "POST"])
def populate_database(request):
    """
    Endpoint to populate the database with sample data.
    Only populates if database is empty to avoid duplicates.
    """
    try:
        # Check if data already exists
        from learning.models import Module
        from drills.models import DrillScenario
        from alerts.models import Alert
        from gamification.models import Badge

        if (Module.objects.exists() or
            DrillScenario.objects.exists() or
            Alert.objects.exists() or
            Badge.objects.exists()):
            return JsonResponse({
                'success': False,
                'message': 'Database already contains data. Use force=true to repopulate.',
                'data_exists': True
            })

        # Run the populate command
        with transaction.atomic():
            call_command('populate_sample_data')

        return JsonResponse({
            'success': True,
            'message': 'Database populated successfully with sample data!',
            'data': {
                'learning_modules': Module.objects.count(),
                'drill_scenarios': DrillScenario.objects.count(),
                'alerts': Alert.objects.count(),
                'badges': Badge.objects.count()
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error populating database: {str(e)}',
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def force_populate_database(request):
    """
    Endpoint to force populate the database with sample data.
    Clears existing data and repopulates.
    """
    try:
        # Parse request body for POST or query params for GET
        if request.method == 'POST':
            body = json.loads(request.body)
            force = body.get('force', False)
        else:  # GET request
            force = request.GET.get('force', '').lower() == 'true'

        if not force:
            return JsonResponse({
                'success': False,
                'message': 'Force parameter must be set to true to clear existing data. Use ?force=true for GET requests.'
            })

        # Clear existing data
        from learning.models import Module, Lesson, Quiz, Question
        from drills.models import DrillScenario
        from alerts.models import Alert
        from gamification.models import Badge

        with transaction.atomic():
            # Clear all data
            Question.objects.all().delete()
            Quiz.objects.all().delete()
            Lesson.objects.all().delete()
            Module.objects.all().delete()
            DrillScenario.objects.all().delete()
            Alert.objects.all().delete()
            Badge.objects.all().delete()
            # Achievement model doesn't exist, skip deletion

            # Run the populate command
            call_command('populate_sample_data')

        return JsonResponse({
            'success': True,
            'message': 'Database force populated successfully with fresh sample data!',
            'data': {
                'learning_modules': Module.objects.count(),
                'drill_scenarios': DrillScenario.objects.count(),
                'alerts': Alert.objects.count(),
                'badges': Badge.objects.count()
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error force populating database: {str(e)}',
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def database_status(request):
    """
    Endpoint to check database status and data counts.
    """
    try:
        from learning.models import Module
        from drills.models import DrillScenario
        from alerts.models import Alert
        from gamification.models import Badge

        return JsonResponse({
            'success': True,
            'data': {
                'learning_modules': Module.objects.count(),
                'drill_scenarios': DrillScenario.objects.count(),
                'alerts': Alert.objects.count(),
                'badges': Badge.objects.count(),
                'is_populated': any([
                    Module.objects.exists(),
                    DrillScenario.objects.exists(),
                    Alert.objects.exists(),
                    Badge.objects.exists()
                ])
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error checking database status: {str(e)}',
            'error': str(e)
        }, status=500)
