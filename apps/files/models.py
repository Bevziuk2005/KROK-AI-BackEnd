from django.db import models
import uuid
from pgvector.django import VectorField
from apps.users.models import User
from apps.chats.models import Chat


class Document(models.Model):
    """Maps public.documents table from Supabase"""
    DOCUMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.TextField(blank=True, null=True)
    storage_key = models.TextField()  # Path in Supabase Storage
    status = models.CharField(max_length=50, choices=DOCUMENT_STATUS_CHOICES, default='pending')
    chat = models.ForeignKey(Chat, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    checksum_sha256 = models.CharField(max_length=64, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'documents'

    def __str__(self):
        return self.title or f"Document {self.id}"


class DocumentChunk(models.Model):
    """Maps public.document_chunks table from Supabase"""
    CHUNK_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('embedded', 'Embedded'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.SET_NULL, null=True, blank=True)
    chunk_index = models.IntegerField()
    chunk_text = models.TextField()
    status = models.CharField(max_length=50, choices=CHUNK_STATUS_CHOICES, default='pending')
    token_count = models.IntegerField(default=0)
    start_page = models.IntegerField(blank=True, null=True)
    end_page = models.IntegerField(blank=True, null=True)
    has_heading = models.BooleanField(default=False)
    heading_text = models.TextField(blank=True, null=True)
    is_table = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'document_chunks'

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.id}"


class ChunkEmbedding(models.Model):
    """Maps public.chunk_embeddings table from Supabase.

    The embedding is stored as a pgvector column for efficient similarity search.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chunk = models.ForeignKey(DocumentChunk, on_delete=models.CASCADE, related_name='embeddings')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.SET_NULL, null=True, blank=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    model_name = models.TextField()  # e.g., 'text-embedding-3-small'
    embedding = VectorField(dimensions=1536, null=True, blank=True)
    token_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'chunk_embeddings'
        unique_together = ('chunk', 'model_name')

    def __str__(self):
        return f"Embedding ({self.model_name}) for chunk {self.chunk.chunk_index}"
