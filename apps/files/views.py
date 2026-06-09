from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from apps.files.models import Document, DocumentChunk
from apps.files.serializers import DocumentUploadSerializer, DocumentSerializer, DocumentChunkSerializer, RAGSearchSerializer
from apps.files.services import save_uploaded_file, process_document_background, rag_search
from apps.users.authentication import JWTAuthentication
from apps.users.permissions import IsAuthenticatedCustom


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'


class FileViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedCustom]

    def list(self, request):
        qs = Document.objects.filter(owner=request.user).order_by('-created_at')
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = DocumentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def retrieve(self, request, pk=None):
        doc = get_object_or_404(Document, pk=pk, owner=request.user)
        serializer = DocumentSerializer(doc)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        doc = get_object_or_404(Document, pk=pk, owner=request.user)
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        f = request.FILES.get('file')
        title = serializer.validated_data.get('title', '')
        try:
            doc = save_uploaded_file(request.user, f, title=title)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        out = DocumentSerializer(doc)
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='process')
    def process(self, request, pk=None):
        doc = get_object_or_404(Document, pk=pk, owner=request.user)
        process_document_background(doc.id)
        return Response({'detail': 'Processing started'}, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'], url_path='chunks')
    def chunks(self, request, pk=None):
        doc = get_object_or_404(Document, pk=pk, owner=request.user)
        qs = DocumentChunk.objects.filter(document=doc).order_by('chunk_index')
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = DocumentChunkSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def rag_search_view(request):
    serializer = RAGSearchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    q = serializer.validated_data['query']
    k = serializer.validated_data.get('top_k', 5)
    results = rag_search(request.user, q, top_k=k)
    return Response({'results': results})
