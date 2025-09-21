from django.core.management.base import BaseCommand
from gamification.signals import update_leaderboard


class Command(BaseCommand):
    help = 'Update leaderboard with current user rankings'

    def handle(self, *args, **options):
        self.stdout.write('Updating leaderboard...')
        update_leaderboard()
        self.stdout.write(
            self.style.SUCCESS('Successfully updated leaderboard')
        )
