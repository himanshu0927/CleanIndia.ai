from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand
from django.db import transaction

from complaints.models import Complaint


DELETED_ACCOUNT_NAME = '[deleted account]'


class Command(BaseCommand):
    help = 'Remove all citizen, authority and admin accounts and sessions.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Delete accounts. Omit this flag to preview counts.',
        )

    def handle(self, *args, **options):
        users = get_user_model().objects.all()
        user_count = users.count()
        session_count = Session.objects.count()
        self.stdout.write(f'Accounts: {user_count}; sessions: {session_count}.')
        if not options['confirm']:
            self.stdout.write('Preview only. Run with --confirm to reset accounts.')
            return

        with transaction.atomic():
            usernames = list(users.values_list('username', flat=True))
            anonymized = Complaint.objects.filter(name__in=usernames).update(
                name=DELETED_ACCOUNT_NAME
            )
            Session.objects.all().delete()
            users.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Removed {user_count} accounts and {session_count} sessions; '
                f'anonymized {anonymized} complaints. Signup pages remain available.'
            )
        )
