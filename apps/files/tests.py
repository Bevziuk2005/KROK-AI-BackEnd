from django.test import TestCase, Client
from apps.users.models import User
from apps.files.models import Document, DocumentChunk, ChunkEmbedding
from apps.users.services import create_access_token
from unittest.mock import patch, MagicMock
from io import BytesIO


class FilesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(email='u@krok.edu.ua')
        self.auth = {'HTTP_AUTHORIZATION': f'Bearer {create_access_token(self.user)}'}

    @patch('apps.files.services.upload_file')
    def test_upload_text_file(self, mock_upload):
        mock_upload.return_value = True
        f = BytesIO(b'Hello world. This is a test document.' )
        f.name = 'doc.txt'
        f.content_type = 'text/plain'
        r = self.client.post('/api/v1/files/upload/', {'file': f}, **self.auth)
        self.assertEqual(r.status_code, 201)
        self.assertIn('id', r.json())

    @patch('apps.files.services._download_from_storage')
    @patch('apps.files.services.get_openai')
    def test_process_document(self, mock_openai, mock_download):
        # create document
        doc = Document.objects.create(owner=self.user, title='t', storage_key='k', status='pending')
        mock_download.return_value = b"A long text. "*100
        # mock embedding
        mock_client = MagicMock()
        mock_client.Embedding.create.return_value = {'data':[{'embedding':[0.1,0.2,0.3]}]}
        mock_openai.return_value = mock_client
        r = self.client.post(f'/api/v1/files/{doc.id}/process/', **self.auth)
        self.assertEqual(r.status_code, 202)

    @patch('apps.files.services.get_openai')
    def test_rag_search(self, mock_openai):
        mock_client = MagicMock()
        mock_client.Embedding.create.return_value = {'data':[{'embedding':[0.1,0.2,0.3]}]}
        mock_openai.return_value = mock_client
        r = self.client.post('/api/v1/rag/search/', {'query':'hello', 'top_k':1}, content_type='application/json', **self.auth)
        self.assertEqual(r.status_code, 200)
