from django.test import TestCase, Client
from apps.users.models import User
from apps.chats.models import Chat, Message
from apps.users.services import create_access_token
from django.utils import timezone
import uuid


class ChatsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(email='owner@krok.edu.ua')
        self.other = User.objects.create(email='other@krok.edu.ua')
        self.chat = Chat.objects.create(owner=self.user, title='Test Chat')

    def auth_headers(self, user=None):
        user = user or self.user
        token = create_access_token(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {token}'}

    def test_list_chats(self):
        r = self.client.get('/api/v1/chats/', **self.auth_headers())
        self.assertEqual(r.status_code, 200)

    def test_create_chat(self):
        r = self.client.post('/api/v1/chats/', {'title': 'New Chat', 'type': 'assistant'}, content_type='application/json', **self.auth_headers())
        self.assertEqual(r.status_code, 201)
        self.assertIn('id', r.json())

    def test_retrieve_chat(self):
        r = self.client.get(f'/api/v1/chats/{self.chat.id}/', **self.auth_headers())
        self.assertEqual(r.status_code, 200)

    def test_update_chat_by_owner(self):
        r = self.client.patch(f'/api/v1/chats/{self.chat.id}/', {'title': 'Updated'}, content_type='application/json', **self.auth_headers())
        self.assertEqual(r.status_code, 200)

    def test_update_chat_forbidden(self):
        r = self.client.patch(f'/api/v1/chats/{self.chat.id}/', {'title': 'Bad'}, content_type='application/json', **self.auth_headers(self.other))
        self.assertEqual(r.status_code, 403)

    def test_delete_soft(self):
        r = self.client.delete(f'/api/v1/chats/{self.chat.id}/', **self.auth_headers())
        self.assertEqual(r.status_code, 204)
        self.chat.refresh_from_db()
        self.assertEqual(self.chat.title, '')

    def test_messages_list_and_create(self):
        # list
        r = self.client.get(f'/api/v1/chats/{self.chat.id}/messages/', **self.auth_headers())
        self.assertEqual(r.status_code, 200)
        # create
        r2 = self.client.post(f'/api/v1/chats/{self.chat.id}/messages/', {'role': 'user', 'content': 'Hello', 'token_count': 2}, content_type='application/json', **self.auth_headers())
        self.assertEqual(r2.status_code, 201)
        self.assertIn('id', r2.json())

    def test_message_retrieve(self):
        msg = Message.objects.create(chat=self.chat, user=self.user, role='user', content='Hi')
        r = self.client.get(f'/api/v1/messages/{msg.id}/', **self.auth_headers())
        self.assertEqual(r.status_code, 200)
