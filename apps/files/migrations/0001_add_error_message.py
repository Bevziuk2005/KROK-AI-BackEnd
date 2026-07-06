from django.db import migrations

class Migration(migrations.Migration):

    initial = False

    dependencies = [
        ('files', '0002_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE documents
            ADD COLUMN IF NOT EXISTS error_message text;
            """,
            reverse_sql="""
            ALTER TABLE documents
            DROP COLUMN IF EXISTS error_message;
            """,
        ),
    ]
