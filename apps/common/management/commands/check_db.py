from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Check that Django can connect to the database and show a simple result from it.'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_user, version();")
            db_name, db_user, version = cursor.fetchone()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            )
            tables_count = cursor.fetchone()[0]

        self.stdout.write(self.style.SUCCESS('Database connection successful'))
        self.stdout.write(f'Current database: {db_name}')
        self.stdout.write(f'Current user: {db_user}')
        self.stdout.write(f'Tables in public schema: {tables_count}')
        self.stdout.write('PostgreSQL version info:')
        self.stdout.write(version)
