from django.core.management.base import BaseCommand
from gamification.signals import create_default_badges


class Command(BaseCommand):
    help = 'Create default badges for gamification'

    def handle(self, *args, **options):
        self.stdout.write('Creating default badges...')
        create_default_badges()
        self.stdout.write(
            self.style.SUCCESS('Successfully created default badges')
        )
