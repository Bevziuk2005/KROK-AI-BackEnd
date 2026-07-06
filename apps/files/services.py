import hashlib
import logging
import mimetypes
from io import BytesIO
from django.utils import timezone
from django.conf import settings
from django.db.models import Value
from pgvector.django import CosineDistance
from apps.files.models import Document, DocumentChunk, ChunkEmbedding
from apps.files.storage import upload_file
from apps.common.supabase_client import get_supabase_client
from apps.common.openai_client import get_openai, embeddings_create
from apps.users.models import User


ALLOWED_MIME = ['text/plain', 'text/markdown', 'application/pdf']
MAX_FILE_SIZE = int(getattr(settings, 'MAX_FILE_UPLOAD_SIZE', 10 * 1024 * 1024))  # 10MB
SUPABASE_BUCKET = getattr(settings, 'SUPABASE_STORAGE_BUCKET', 'documents')

logger = logging.getLogger(__name__)


def compute_sha256(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def save_uploaded_file(owner: User, file_obj, title: str = '') -> Document:
    # validation
    content_type = file_obj.content_type or mimetypes.guess_type(file_obj.name)[0] or ''
    if content_type not in ALLOWED_MIME:
        if file_obj.name and str(file_obj.name).lower().endswith('.pdf'):
            content_type = 'application/pdf'
        else:
            raise ValueError('Unsupported MIME type')
    file_obj.seek(0)
    data = file_obj.read()
    if len(data) > MAX_FILE_SIZE:
        raise ValueError('File too large')
    checksum = compute_sha256(data)
    # upload to supabase
    key = f"{owner.id}/{timezone.now().strftime('%Y%m%d%H%M%S')}_{file_obj.name}"
    upload_file(SUPABASE_BUCKET, key, data)
    doc = Document.objects.create(owner=owner, title=title or file_obj.name, storage_key=key, checksum_sha256=checksum, status='pending')
    return doc


def _download_from_storage(storage_key: str) -> bytes:
    client = get_supabase_client()
    if not client:
        raise RuntimeError('Supabase client not configured')
    storage = client.storage()
    data = storage.from_(SUPABASE_BUCKET).download(storage_key)
    return data


def _split_text_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50):
    chunks = []
    i = 0
    idx = 0
    L = len(text)
    while i < L:
        part = text[i:i+chunk_size]
        chunks.append((idx, part))
        i += chunk_size - overlap
        idx += 1
    return chunks


def _create_embeddings_for_chunks(chunks, document: Document, owner: User, model_name: str = 'text-embedding-3-small'):
    client = get_openai()
    if not client:
        raise RuntimeError('OpenAI client not configured')
    embeddings = []
    for idx, text in chunks:
        try:
            resp = embeddings_create(client, model_name, text)
            emb = resp.data[0].embedding
            chunk_obj = DocumentChunk.objects.get(document=document, chunk_index=idx)
            ce = ChunkEmbedding.objects.create(chunk=chunk_obj, owner=owner, document=document, model_name=model_name, embedding=emb, token_count=len(text.split()))
            chunk_obj.status = 'embedded'
            chunk_obj.save()
            embeddings.append(ce)
        except Exception as exc:
            logger.exception('Failed to embed chunk %s for document %s', idx, document.id)
            try:
                chunk_obj = DocumentChunk.objects.get(document=document, chunk_index=idx)
                chunk_obj.status = 'failed'
                chunk_obj.save()
            except Exception:
                logger.exception('Failed to update chunk status for doc %s chunk %s', document.id, idx)
    return embeddings


def _extract_text_from_bytes(data: bytes, content_type: str | None = None, file_name: str | None = None) -> str:
    detected_type = content_type or mimetypes.guess_type(file_name or '')[0] or ''
    if detected_type == 'application/pdf' or (file_name and str(file_name).lower().endswith('.pdf')):
        try:
            from pypdf import PdfReader
        except ImportError:
            try:
                import pdfplumber
            except ImportError as exc:
                raise RuntimeError('PDF support requires pypdf or pdfplumber') from exc
            with pdfplumber.open(BytesIO(data)) as pdf:
                pages = [page.extract_text() or '' for page in pdf.pages]
            return '\n'.join(pages)

        reader = PdfReader(BytesIO(data))
        return '\n'.join(page.extract_text() or '' for page in reader.pages)

    try:
        return data.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('Only UTF-8 text files and PDFs are supported') from exc


def _process_document_sync(document_id):
    doc = Document.objects.get(id=document_id)
    doc.status = 'processing'
    doc.save()
    try:
        data = _download_from_storage(doc.storage_key)
    except Exception as exc:
        logger.exception('Failed to download document %s from storage', document_id)
        doc.status = 'failed'
        doc.error_message = str(exc)
        doc.save(update_fields=["status", "error_message"])
        return

    try:
        text = _extract_text_from_bytes(data, file_name=doc.title or doc.storage_key)
    except Exception as exc:
        logger.exception('Failed to extract text from document %s: %s', document_id, exc)
        doc.status = 'failed'
        doc.error_message = str(exc)
        doc.save(update_fields=["status", "error_message"])
        return

    chunks = _split_text_into_chunks(text)
    for idx, chunk_text in chunks:
        DocumentChunk.objects.create(document=doc, owner=doc.owner, chunk_index=idx, chunk_text=chunk_text, status='pending')
    _create_embeddings_for_chunks(chunks, doc, doc.owner)
    doc.status = 'completed'
    doc.updated_at = timezone.now()
    doc.save()


def process_document_background(document_id):
    # Enqueue Celery task for processing documents (preferred) if available
    try:
        from apps.files.celery_tasks import process_document_task

        process_document_task.delay(str(document_id))
        return
    except Exception:
        logger.exception('Celery not available, falling back to synchronous processing')
        _process_document_sync(document_id)


def rag_search(owner: User, query: str, top_k: int = 5, model_name: str = 'text-embedding-3-small'):
    client = get_openai()
    if not client:
        raise RuntimeError('OpenAI client not configured')
    resp = embeddings_create(client, model_name, query)
    q_emb = resp.data[0].embedding

    rows = (
        ChunkEmbedding.objects.filter(owner=owner, model_name=model_name)
        .annotate(distance=CosineDistance('embedding', Value(q_emb)))
        .order_by('distance')[:top_k]
    )

    out = []
    for r in rows:
        similarity = max(1.0 - float(r.distance), 0.0) if r.distance is not None else 0.0
        out.append({
            'similarity': similarity,
            'chunk_id': str(r.chunk.id),
            'chunk_index': r.chunk.chunk_index,
            'chunk_text': r.chunk.chunk_text,
            'document_id': str(r.document.id),
        })
    return out
