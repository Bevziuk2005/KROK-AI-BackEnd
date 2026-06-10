from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0002_user'),
        ('chats', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.TextField(blank=True, null=True)),
                ('storage_key', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=50)),
                ('checksum_sha256', models.CharField(blank=True, max_length=64, null=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='documents', to='chats.chat')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='users.user')),
            ],
            options={
                'db_table': 'documents',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DocumentChunk',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('chunk_index', models.IntegerField()),
                ('chunk_text', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('embedded', 'Embedded'), ('failed', 'Failed')], default='pending', max_length=50)),
                ('token_count', models.IntegerField(default=0)),
                ('start_page', models.IntegerField(blank=True, null=True)),
                ('end_page', models.IntegerField(blank=True, null=True)),
                ('has_heading', models.BooleanField(default=False)),
                ('heading_text', models.TextField(blank=True, null=True)),
                ('is_table', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='chats.chat')),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chunks', to='files.document')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
            options={
                'db_table': 'document_chunks',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='ChunkEmbedding',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('model_name', models.TextField()),
                ('embedding', models.JSONField()),
                ('token_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='chats.chat')),
                ('chunk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='embeddings', to='files.documentchunk')),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='files.document')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
            options={
                'db_table': 'chunk_embeddings',
                'managed': False,
                'unique_together': {('chunk', 'model_name')},
            },
        ),
    ]
