import os
import logging
from openai import OpenAI
from openai.error import OpenAIError, APIError, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

_client = None


def _init_client():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.warning('OPENAI_API_KEY not set; OpenAI client will not be available')
        return None
    client = OpenAI(api_key=api_key)
    return client


def get_openai():
    """Return singleton OpenAI client or None if not configured."""
    global _client
    if _client is None:
        _client = _init_client()
    return _client


@retry(reraise=True, stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), retry=retry_if_exception_type((RateLimitError, APIError, OpenAIError)))
def embeddings_create(client: OpenAI, model: str, input_text):
    """Wrapper to create embeddings with retry and error handling."""
    if client is None:
        raise RuntimeError('OpenAI client not configured')
    try:
        logger.debug('OpenAI embeddings.create call: model=%s, input_len=%d', model, len(input_text) if hasattr(input_text,'__len__') else 0)
        resp = client.embeddings.create(model=model, input=input_text)
        return resp
    except Exception as exc:
        logger.exception('OpenAI embeddings.create failed')
        raise
