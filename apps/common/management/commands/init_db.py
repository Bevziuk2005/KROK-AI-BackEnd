from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connection


class Command(BaseCommand):
    help = 'Initialize Django database with existing Supabase tables (managed=False models). Use --fake-initial to mark initial migrations as applied without running them.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-migrate',
            action='store_true',
            help='Skip actual database migration step (only show commands)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Database Initialization for Existing Tables'))
        self.stdout.write('=' * 60)
        self.stdout.write('')

        skip_migrate = options.get('skip_migrate', False)

        self.stdout.write(self.style.WARNING(
            'This command helps initialize Django with existing Supabase tables.'
        ))
        self.stdout.write('Step 1: Run migrations with --fake-initial')
        self.stdout.write('  This tells Django that initial migrations are already applied.')
        self.stdout.write('')

        if not skip_migrate:
            try:
                call_command('migrate', '--fake-initial', verbosity=1)
                self.stdout.write(self.style.SUCCESS('✓ Migrations applied (marked as fake-initial)'))
            except Exception as e:
                raise CommandError(f'Failed to run migrations: {e}')
        else:
            self.stdout.write('[SKIPPED] Run this command to apply migrations:')
            self.stdout.write('  python manage.py migrate --fake-initial')

        self.stdout.write('')
        self.stdout.write('Step 2: Verify database connection')
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            self.stdout.write(self.style.SUCCESS('✓ Database connection successful'))
        except Exception as e:
            raise CommandError(f'Failed to connect to database: {e}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Database initialization complete!'))
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('1. Create a superuser (if needed):')
        self.stdout.write('   python manage.py createsuperuser')
        self.stdout.write('')
        self.stdout.write('2. Start the development server:')
        self.stdout.write('   python manage.py runserver')
        self.stdout.write('')
