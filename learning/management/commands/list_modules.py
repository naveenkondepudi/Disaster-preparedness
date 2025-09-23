from django.core.management.base import BaseCommand
from learning.models import Module

class Command(BaseCommand):
    help = 'List all learning modules'

    def handle(self, *args, **options):
        modules = Module.objects.all()

        if not modules.exists():
            self.stdout.write(
                self.style.WARNING('No learning modules found in the database.')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Found {modules.count()} learning modules:')
        )

        for module in modules:
            self.stdout.write(f'- ID: {module.id}')
            self.stdout.write(f'  Title: {module.title}')
            self.stdout.write(f'  Description: {module.description[:100]}...')
            self.stdout.write(f'  Category: {module.category}')
            self.stdout.write(f'  Difficulty: {module.difficulty_level}')
            self.stdout.write(f'  Active: {module.is_active}')
            self.stdout.write(f'  Lessons: {module.lessons.count()}')
            self.stdout.write('')
