import os
from django.test import TestCase
from unittest.mock import MagicMock

from apps.common import openai_client


class OpenAIClientTests(TestCase):
    def tearDown(self):
        # reset singleton
        try:
            openai_client._client = None
        except Exception:
            pass

    def test_get_openai_no_key(self):
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        openai_client._client = None
        c = openai_client.get_openai()
        self.assertIsNone(c)

    def test_get_openai_with_key(self):
        os.environ['OPENAI_API_KEY'] = 'sk-test'
        mock_client = MagicMock()
        # patch the OpenAI constructor used in module
        openai_client._client = None
        openai_client.OpenAI = lambda api_key: mock_client
        c = openai_client.get_openai()
        self.assertIs(c, mock_client)

    def test_embeddings_create_wrapper_calls_client(self):
        os.environ['OPENAI_API_KEY'] = 'sk-test'
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = {'data': [{'embedding': [0.1, 0.2]}]}
        openai_client._client = None
        openai_client.OpenAI = lambda api_key: mock_client
        client = openai_client.get_openai()
        resp = openai_client.embeddings_create(client, 'text-embedding-3-small', 'hello')
        self.assertIn('data', resp)
        mock_client.embeddings.create.assert_called_once()
