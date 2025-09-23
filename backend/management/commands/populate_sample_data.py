from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from learning.models import Module, Lesson, Quiz, Question
from drills.models import DrillScenario
from alerts.models import Alert
from gamification.models import Badge, Achievement
import random
from datetime import datetime, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with comprehensive sample data for all modules'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database population...'))

        with transaction.atomic():
            # Create admin user if not exists
            admin_user = self.create_admin_user()

            # Populate learning modules
            self.populate_learning_modules(admin_user)

            # Populate drill scenarios
            self.populate_drill_scenarios(admin_user)

            # Populate alerts
            self.populate_alerts(admin_user)

            # Populate gamification data
            self.populate_gamification_data()

        self.stdout.write(self.style.SUCCESS('Database population completed successfully!'))

    def create_admin_user(self):
        """Create admin user if not exists."""
        admin_user, created = User.objects.get_or_create(
            email='admin@disasterprep.com',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True
            }
        )

        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))
        else:
            self.stdout.write(self.style.WARNING('Admin user already exists'))

        return admin_user

    def populate_learning_modules(self, admin_user):
        """Populate learning modules with lessons and quizzes."""
        if Module.objects.exists():
            self.stdout.write(self.style.WARNING('Learning modules already exist, skipping...'))
            return

        modules_data = [
            {
                'title': 'Earthquake Preparedness Fundamentals',
                'description': 'Comprehensive guide to earthquake safety, including preparation, response, and recovery strategies. Learn essential techniques for staying safe during seismic events.',
                'disaster_type': 'EARTHQUAKE',
            },
            {
                'title': 'Flood Safety and Evacuation Procedures',
                'description': 'Master flood preparedness with detailed evacuation plans, safety protocols, and emergency response techniques for various flood scenarios.',
                'disaster_type': 'FLOOD',
            },
            {
                'title': 'Fire Emergency Response and Prevention',
                'description': 'Advanced fire safety training covering prevention strategies, evacuation procedures, and emergency response for different fire types.',
                'disaster_type': 'FIRE',
            },
            {
                'title': 'Cyclone Preparedness and Safety',
                'description': 'Complete cyclone preparedness guide including early warning systems, evacuation procedures, and post-cyclone safety measures.',
                'disaster_type': 'CYCLONE',
            },
            {
                'title': 'Emergency Communication Protocols',
                'description': 'Learn effective communication strategies during emergencies, including radio protocols, emergency signals, and coordination techniques.',
                'disaster_type': 'OTHER',
            },
            {
                'title': 'First Aid and Medical Emergency Response',
                'description': 'Essential first aid skills for emergency situations, including CPR, wound care, and basic medical response procedures.',
                'disaster_type': 'OTHER',
            },
            {
                'title': 'Disaster Recovery and Community Resilience',
                'description': 'Building community resilience and recovery strategies after disasters, including resource management and long-term planning.',
                'disaster_type': 'OTHER',
            },
        ]

        for i, module_data in enumerate(modules_data, 1):
            module = Module.objects.create(
                created_by=admin_user,
                **module_data
            )

            # Create lessons for each module
            lessons_data = [
                {
                    'title': f'{module.title} - Introduction and Overview',
                    'content': f'Welcome to {module.title}. This comprehensive lesson provides an in-depth overview of the key concepts, learning objectives, and practical applications you will master throughout this module.',
                    'order': 1,
                },
                {
                    'title': f'{module.title} - Core Principles and Theory',
                    'content': f'In this lesson, you will learn the fundamental principles and theoretical foundations that underpin {module.title.lower()}. Understanding these concepts is crucial for effective implementation.',
                    'order': 2,
                },
                {
                    'title': f'{module.title} - Practical Applications',
                    'content': f'This hands-on lesson focuses on practical exercises and real-world applications of {module.title.lower()} principles. You will engage in interactive scenarios and case studies.',
                    'order': 3,
                },
                {
                    'title': f'{module.title} - Advanced Techniques',
                    'content': f'Explore advanced techniques and strategies for {module.title.lower()}. This lesson covers complex scenarios and expert-level approaches to emergency preparedness.',
                    'order': 4,
                },
                {
                    'title': f'{module.title} - Assessment and Review',
                    'content': f'Comprehensive review and assessment of {module.title.lower()} concepts. Test your knowledge and reinforce key learning points through interactive exercises.',
                    'order': 5,
                },
            ]

            for lesson_data in lessons_data:
                Lesson.objects.create(module=module, **lesson_data)

            # Create quiz for each module
            quiz = Quiz.objects.create(
                module=module,
                title=f'{module.title} - Knowledge Assessment',
                description=f'Test your understanding of {module.title.lower()} concepts with this comprehensive quiz.'
            )

            # Create questions for each quiz
            questions_data = [
                {
                    'text': f'What is the primary objective of {module.title}?',
                    'option_a': 'Basic safety awareness',
                    'option_b': 'Advanced emergency response',
                    'option_c': 'Comprehensive preparedness',
                    'option_d': 'All of the above',
                    'correct_option': 'D',
                    'explanation': f'{module.title} covers all aspects of safety awareness, emergency response, and comprehensive preparedness.',
                    'order': 1,
                },
                {
                    'text': f'Which disaster type does {module.title} specifically address?',
                    'option_a': 'Earthquake',
                    'option_b': 'Flood',
                    'option_c': 'Fire',
                    'option_d': module.get_disaster_type_display(),
                    'correct_option': 'D',
                    'explanation': f'This module specifically focuses on {module.get_disaster_type_display().lower()} preparedness and response.',
                    'order': 2,
                },
                {
                    'text': f'What is the most important factor in {module.title.lower()}?',
                    'option_a': 'Quick reaction time',
                    'option_b': 'Proper preparation',
                    'option_c': 'Advanced equipment',
                    'option_d': 'Team coordination',
                    'correct_option': 'B',
                    'explanation': 'Proper preparation is the foundation of effective emergency response and disaster preparedness.',
                    'order': 3,
                },
                {
                    'text': f'How many lessons are included in {module.title}?',
                    'option_a': '3',
                    'option_b': '4',
                    'option_c': '5',
                    'option_d': '6',
                    'correct_option': 'C',
                    'explanation': f'{module.title} includes 5 comprehensive lessons covering all aspects of the topic.',
                    'order': 4,
                },
                {
                    'text': f'What should you do after completing {module.title}?',
                    'option_a': 'Forget everything',
                    'option_b': 'Practice regularly',
                    'option_c': 'Share knowledge',
                    'option_d': 'Both B and C',
                    'correct_option': 'D',
                    'explanation': 'Regular practice and sharing knowledge with others are essential for maintaining preparedness skills.',
                    'order': 5,
                },
            ]

            for question_data in questions_data:
                Question.objects.create(quiz=quiz, **question_data)

            self.stdout.write(self.style.SUCCESS(f'Created module: {module.title}'))

    def populate_drill_scenarios(self, admin_user):
        """Populate drill scenarios."""
        if DrillScenario.objects.exists():
            self.stdout.write(self.style.WARNING('Drill scenarios already exist, skipping...'))
            return

        scenarios_data = [
            {
                'title': 'Earthquake Emergency Response Drill',
                'description': 'Simulate a 7.2 magnitude earthquake scenario. Practice evacuation procedures, search and rescue operations, and emergency communication protocols.',
                'region_tags': ['urban', 'residential', 'office'],
                'difficulty_level': 'INTERMEDIATE',
                'estimated_duration': 45,
                'max_score': 100,
                'json_tree': {
                    'start_step': 'earthquake_detected',
                    'steps': {
                        'earthquake_detected': {
                            'question': 'A 7.2 magnitude earthquake has been detected. What is your first action?',
                            'choices': [
                                {'text': 'Sound the alarm immediately', 'points': 10, 'next': 'alarm_sounded'},
                                {'text': 'Check for injuries first', 'points': 5, 'next': 'check_injuries'},
                                {'text': 'Call emergency services', 'points': 8, 'next': 'call_emergency'}
                            ]
                        },
                        'alarm_sounded': {
                            'question': 'Alarm has been sounded. What is your next priority?',
                            'choices': [
                                {'text': 'Evacuate the building', 'points': 15, 'next': 'evacuation'},
                                {'text': 'Check for structural damage', 'points': 10, 'next': 'damage_check'},
                                {'text': 'Account for all personnel', 'points': 12, 'next': 'personnel_count'}
                            ]
                        },
                        'evacuation': {
                            'question': 'During evacuation, you encounter a blocked exit. What do you do?',
                            'choices': [
                                {'text': 'Find alternative route', 'points': 20, 'next': 'alternative_route'},
                                {'text': 'Clear the blockage', 'points': 15, 'next': 'clear_blockage'},
                                {'text': 'Wait for help', 'points': 5, 'next': 'wait_help'}
                            ]
                        }
                    }
                },
                'is_active': True,
            },
            {
                'title': 'Flood Evacuation Coordination',
                'description': 'Manage a flash flood emergency in a residential area. Coordinate evacuation efforts, establish emergency shelters, and manage resources effectively.',
                'region_tags': ['rural', 'residential', 'flood-prone'],
                'difficulty_level': 'ADVANCED',
                'estimated_duration': 60,
                'max_score': 120,
                'json_tree': {'start_step': 'flood_warning', 'steps': {'flood_warning': {'question': 'Flood warning issued. What is your first action?', 'choices': [{'text': 'Evacuate immediately', 'points': 20, 'next': 'evacuation'}, {'text': 'Check water levels', 'points': 10, 'next': 'check_levels'}]}}},
                'is_active': True,
            },
            {
                'title': 'Fire Emergency Response Simulation',
                'description': 'Handle a multi-story building fire emergency. Practice fire suppression, evacuation coordination, and medical response procedures.',
                'region_tags': ['urban', 'commercial', 'high-rise'],
                'difficulty_level': 'ADVANCED',
                'estimated_duration': 90,
                'max_score': 150,
                'json_tree': {'start_step': 'fire_detected', 'steps': {'fire_detected': {'question': 'Fire detected in building. What is your response?', 'choices': [{'text': 'Sound fire alarm', 'points': 15, 'next': 'alarm'}, {'text': 'Call fire department', 'points': 10, 'next': 'call_fire'}]}}},
                'is_active': True,
            },
            {
                'title': 'Cyclone Preparedness Drill',
                'description': 'Prepare for an approaching category 4 cyclone. Implement early warning systems, secure infrastructure, and coordinate community evacuation.',
                'region_tags': ['coastal', 'residential', 'commercial'],
                'difficulty_level': 'INTERMEDIATE',
                'estimated_duration': 75,
                'max_score': 110,
                'json_tree': {'start_step': 'cyclone_alert', 'steps': {'cyclone_alert': {'question': 'Cyclone alert issued. What is your priority?', 'choices': [{'text': 'Secure property', 'points': 12, 'next': 'secure'}, {'text': 'Evacuate to shelter', 'points': 18, 'next': 'evacuate'}]}}},
                'is_active': True,
            },
            {
                'title': 'Medical Emergency Response',
                'description': 'Respond to a mass casualty incident. Practice triage procedures, medical treatment protocols, and resource allocation strategies.',
                'region_tags': ['urban', 'public', 'transportation'],
                'difficulty_level': 'ADVANCED',
                'estimated_duration': 50,
                'max_score': 130,
                'json_tree': {'start_step': 'casualty_incident', 'steps': {'casualty_incident': {'question': 'Mass casualty incident reported. What is your first action?', 'choices': [{'text': 'Establish triage', 'points': 25, 'next': 'triage'}, {'text': 'Call for backup', 'points': 15, 'next': 'backup'}]}}},
                'is_active': True,
            },
            {
                'title': 'Communication System Failure',
                'description': 'Manage emergency response when primary communication systems fail. Establish alternative communication methods and coordinate rescue operations.',
                'region_tags': ['rural', 'remote', 'mountainous'],
                'difficulty_level': 'ADVANCED',
                'estimated_duration': 80,
                'max_score': 140,
                'json_tree': {'start_step': 'comm_failure', 'steps': {'comm_failure': {'question': 'Communication systems down. What do you do?', 'choices': [{'text': 'Use backup radio', 'points': 20, 'next': 'radio'}, {'text': 'Send runner', 'points': 10, 'next': 'runner'}]}}},
                'is_active': True,
            },
            {
                'title': 'Multi-Hazard Emergency Response',
                'description': 'Handle simultaneous multiple disasters including earthquake, fire, and chemical spill. Practice complex coordination and resource management.',
                'region_tags': ['industrial', 'urban', 'hazardous'],
                'difficulty_level': 'ADVANCED',
                'estimated_duration': 120,
                'max_score': 200,
                'json_tree': {'start_step': 'multi_hazard', 'steps': {'multi_hazard': {'question': 'Multiple hazards detected. What is your priority?', 'choices': [{'text': 'Evacuate area', 'points': 30, 'next': 'evacuate'}, {'text': 'Assess each hazard', 'points': 20, 'next': 'assess'}]}}},
                'is_active': True,
            },
        ]

        for scenario_data in scenarios_data:
            DrillScenario.objects.create(**scenario_data)
            self.stdout.write(self.style.SUCCESS(f'Created drill scenario: {scenario_data["title"]}'))

    def populate_alerts(self, admin_user):
        """Populate emergency alerts."""
        if Alert.objects.exists():
            self.stdout.write(self.style.WARNING('Alerts already exist, skipping...'))
            return

        alerts_data = [
            {
                'title': 'Severe Weather Warning - Heavy Rainfall Expected',
                'description': 'The National Weather Service has issued a severe weather warning for heavy rainfall and potential flooding in the region. Residents are advised to avoid low-lying areas and prepare for possible evacuation.',
                'region_tags': ['coastal', 'flood-prone', 'residential'],
                'severity': 'HIGH',
                'source': 'National Weather Service',
                'published_at': datetime.now() - timedelta(hours=2),
                'expires_at': datetime.now() + timedelta(hours=24),
                'is_active': True,
            },
            {
                'title': 'Earthquake Aftershock Alert',
                'description': 'Aftershocks are expected following the 6.8 magnitude earthquake. Residents should remain alert and be prepared for additional seismic activity. Avoid damaged structures.',
                'region_tags': ['urban', 'residential', 'commercial'],
                'severity': 'MEDIUM',
                'source': 'Seismological Center',
                'published_at': datetime.now() - timedelta(hours=1),
                'expires_at': datetime.now() + timedelta(hours=12),
                'is_active': True,
            },
            {
                'title': 'Wildfire Evacuation Order',
                'description': 'Immediate evacuation ordered for areas within 5 miles of the wildfire. High winds are spreading the fire rapidly. Follow designated evacuation routes.',
                'region_tags': ['rural', 'forest', 'residential'],
                'severity': 'CRITICAL',
                'source': 'Fire Department',
                'published_at': datetime.now() - timedelta(minutes=30),
                'expires_at': datetime.now() + timedelta(hours=6),
                'is_active': True,
            },
            {
                'title': 'Chemical Spill Emergency',
                'description': 'Chemical spill reported at industrial facility. Shelter-in-place order issued for 2-mile radius. Avoid outdoor activities and close all windows and doors.',
                'region_tags': ['industrial', 'urban', 'commercial'],
                'severity': 'HIGH',
                'source': 'Emergency Management',
                'published_at': datetime.now() - timedelta(minutes=45),
                'expires_at': datetime.now() + timedelta(hours=8),
                'is_active': True,
            },
            {
                'title': 'Power Grid Failure - Rolling Blackouts',
                'description': 'Power grid experiencing instability. Rolling blackouts will be implemented to prevent complete system failure. Prepare for extended power outages.',
                'region_tags': ['urban', 'residential', 'commercial'],
                'severity': 'MEDIUM',
                'source': 'Power Company',
                'published_at': datetime.now() - timedelta(hours=1),
                'expires_at': datetime.now() + timedelta(hours=18),
                'is_active': True,
            },
            {
                'title': 'Tornado Watch - Severe Thunderstorms',
                'description': 'Tornado watch in effect for the region. Severe thunderstorms with potential for tornado formation. Monitor weather conditions and be prepared to take shelter.',
                'region_tags': ['rural', 'residential', 'agricultural'],
                'severity': 'MEDIUM',
                'source': 'Weather Service',
                'published_at': datetime.now() - timedelta(minutes=15),
                'expires_at': datetime.now() + timedelta(hours=4),
                'is_active': True,
            },
            {
                'title': 'Tsunami Warning - Coastal Evacuation',
                'description': 'Tsunami warning issued following undersea earthquake. Immediate evacuation required for all coastal areas. Move to higher ground immediately.',
                'region_tags': ['coastal', 'beach', 'residential'],
                'severity': 'CRITICAL',
                'source': 'Tsunami Warning Center',
                'published_at': datetime.now() - timedelta(minutes=10),
                'expires_at': datetime.now() + timedelta(hours=3),
                'is_active': True,
            },
        ]

        for alert_data in alerts_data:
            Alert.objects.create(**alert_data)
            self.stdout.write(self.style.SUCCESS(f'Created alert: {alert_data["title"]}'))

    def populate_gamification_data(self):
        """Populate badges and achievements."""
        if Badge.objects.exists():
            self.stdout.write(self.style.WARNING('Gamification data already exists, skipping...'))
            return

        badges_data = [
            {
                'name': 'First Steps',
                'description': 'Complete your first learning module',
                'icon': '🎓',
                'points': 10,
                'category': 'learning',
            },
            {
                'name': 'Knowledge Seeker',
                'description': 'Complete 5 learning modules',
                'icon': '📚',
                'points': 50,
                'category': 'learning',
            },
            {
                'name': 'Master Learner',
                'description': 'Complete all learning modules',
                'icon': '🏆',
                'points': 100,
                'category': 'learning',
            },
            {
                'name': 'Drill Sergeant',
                'description': 'Complete your first drill scenario',
                'icon': '🎯',
                'points': 25,
                'category': 'drills',
            },
            {
                'name': 'Emergency Expert',
                'description': 'Complete 10 drill scenarios',
                'icon': '🚨',
                'points': 150,
                'category': 'drills',
            },
            {
                'name': 'Alert Master',
                'description': 'Respond to 5 emergency alerts',
                'icon': '📢',
                'points': 75,
                'category': 'alerts',
            },
            {
                'name': 'Preparedness Champion',
                'description': 'Achieve 1000 total points',
                'icon': '👑',
                'points': 200,
                'category': 'achievement',
            },
        ]

        for badge_data in badges_data:
            Badge.objects.create(**badge_data)
            self.stdout.write(self.style.SUCCESS(f'Created badge: {badge_data["name"]}'))
