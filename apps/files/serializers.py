from rest_framework import serializers
from apps.files.models import Document, DocumentChunk, ChunkEmbedding


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    title = serializers.CharField(required=False, allow_blank=True)


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('id', 'owner', 'title', 'storage_key', 'status', 'chat', 'checksum_sha256', 'created_at', 'updated_at')
        read_only_fields = ('id', 'owner', 'status', 'checksum_sha256', 'created_at', 'updated_at')


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = ('id', 'document', 'owner', 'chat', 'chunk_index', 'chunk_text', 'status', 'token_count', 'start_page', 'end_page', 'has_heading', 'heading_text', 'is_table', 'created_at')
        read_only_fields = ('id', 'owner', 'status', 'created_at')


class ChunkEmbeddingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkEmbedding
        fields = ('id', 'chunk', 'owner', 'document', 'model_name', 'embedding', 'token_count', 'created_at')
        read_only_fields = ('id', 'owner', 'created_at')


class RAGSearchSerializer(serializers.Serializer):
    query = serializers.CharField()
    top_k = serializers.IntegerField(default=5)
