import logging
from celery import shared_task
from apps.files.services import _process_document_sync

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_document_task(self, document_id):
    try:
        _process_document_sync(document_id)
    except Exception as exc:
        logger.exception('process_document_task failed for document %s', document_id)
        # exponential backoff
        try:
            countdown = 60 * (2 ** self.request.retries)
        except Exception:
            countdown = 60
        raise self.retry(exc=exc, countdown=countdown)
