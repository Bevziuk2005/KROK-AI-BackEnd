from django.contrib import admin
from .models import Document, DocumentChunk, ChunkEmbedding


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'owner__email', 'storage_key')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('document', 'chunk_index', 'owner', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('document__title', 'owner__email', 'chunk_text')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(ChunkEmbedding)
class ChunkEmbeddingAdmin(admin.ModelAdmin):
    list_display = ('chunk', 'model_name', 'owner', 'created_at')
    list_filter = ('model_name', 'created_at')
    search_fields = ('chunk__document__title', 'owner__email', 'model_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
