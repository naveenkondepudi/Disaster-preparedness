from django.core.management.base import BaseCommand
from learning.models import Module, Lesson, Quiz, Question

class Command(BaseCommand):
    help = 'Create sample learning modules for testing'

    def handle(self, *args, **options):
        # Get or create a user to be the creator
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Try to get an existing user, or create a default one
        try:
            creator = User.objects.filter(role='ADMIN').first()
            if not creator:
                creator = User.objects.first()
            if not creator:
                # Create a default admin user
                creator = User.objects.create_user(
                    email='admin@disasterprep.com',
                    password='admin123',
                    first_name='Admin',
                    last_name='User',
                    role='ADMIN'
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error getting/creating user: {e}')
            )
            return

        # Create sample modules
        modules_data = [
            {
                'title': 'Earthquake Preparedness Basics',
                'description': 'Learn the fundamental principles of earthquake safety and preparedness. This module covers essential knowledge for staying safe during seismic events.',
                'disaster_type': 'EARTHQUAKE',
                'created_by': creator,
            },
            {
                'title': 'Flood Safety and Evacuation',
                'description': 'Comprehensive guide to flood preparedness, including evacuation procedures, safety measures, and emergency response protocols.',
                'disaster_type': 'FLOOD',
                'created_by': creator,
            },
            {
                'title': 'Fire Emergency Response',
                'description': 'Advanced training on fire safety, evacuation procedures, and emergency response techniques for various fire scenarios.',
                'disaster_type': 'FIRE',
                'created_by': creator,
            },
            {
                'title': 'Cyclone Preparedness',
                'description': 'Learn how to prepare for and respond to cyclone emergencies, including evacuation procedures and safety measures.',
                'disaster_type': 'CYCLONE',
                'created_by': creator,
            },
            {
                'title': 'General Emergency Response',
                'description': 'Essential skills for various emergency situations, including communication protocols, first aid basics, and coordination techniques.',
                'disaster_type': 'OTHER',
                'created_by': creator,
            },
        ]

        created_modules = []

        for module_data in modules_data:
            module, created = Module.objects.get_or_create(
                title=module_data['title'],
                defaults=module_data
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created module: {module.title}')
                )

                # Add some sample lessons
                lessons_data = [
                    {
                        'title': f'{module.title} - Introduction',
                        'content': f'Welcome to {module.title}. This lesson provides an overview of the key concepts and learning objectives.',
                        'order': 1,
                    },
                    {
                        'title': f'{module.title} - Core Concepts',
                        'content': f'In this lesson, you will learn the fundamental principles and techniques related to {module.title.lower()}.',
                        'order': 2,
                    },
                    {
                        'title': f'{module.title} - Practical Application',
                        'content': f'This lesson focuses on practical exercises and real-world applications of {module.title.lower()} principles.',
                        'order': 3,
                    },
                ]

                for lesson_data in lessons_data:
                    Lesson.objects.create(
                        module=module,
                        **lesson_data
                    )

                # Add a sample quiz
                quiz = Quiz.objects.create(
                    module=module,
                    title=f'{module.title} - Assessment',
                    description=f'Test your knowledge of {module.title.lower()} concepts.'
                )

                # Add sample questions
                questions_data = [
                    {
                        'text': f'What is the primary focus of {module.title}?',
                        'option_a': 'Basic safety principles',
                        'option_b': 'Advanced techniques',
                        'option_c': 'Emergency response',
                        'option_d': 'All of the above',
                        'correct_option': 'D',
                        'explanation': f'{module.title} covers all aspects of safety and emergency response.',
                        'order': 1,
                    },
                    {
                        'text': f'Which disaster type does {module.title} cover?',
                        'option_a': 'Earthquake',
                        'option_b': 'Flood',
                        'option_c': 'Fire',
                        'option_d': module.get_disaster_type_display(),
                        'correct_option': 'D',
                        'explanation': f'This module specifically covers {module.get_disaster_type_display().lower()} preparedness.',
                        'order': 2,
                    },
                ]

                for question_data in questions_data:
                    Question.objects.create(
                        quiz=quiz,
                        **question_data
                    )

                created_modules.append(module)
            else:
                self.stdout.write(
                    self.style.WARNING(f'Module already exists: {module.title}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed {len(created_modules)} modules')
        )
