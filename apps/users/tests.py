from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from apps.users.models import User, RefreshToken
from apps.users.services import create_access_token, create_refresh_token, verify_refresh_token
import jwt
from unittest.mock import patch, MagicMock
from apps.users.services import revoke_refresh_token
from django.utils import timezone


class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(email='test@krok.edu.ua')

    def test_create_access_token(self):
        token = create_access_token(self.user)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        self.assertEqual(payload['email'], self.user.email)

    def test_refresh_token_flow(self):
        raw, rt = create_refresh_token(self.user)
        found = verify_refresh_token(raw)
        self.assertIsNotNone(found)

    def test_login_endpoint_returns_auth_url(self):
        r = self.client.post('/api/v1/auth/login/', {'redirect': 'http://localhost/callback'}, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertIn('auth_url', r.json())

    @patch('apps.users.views.requests.post')
    @patch('apps.users.microsoft.verify_id_token')
    def test_callback_creates_tokens(self, mock_verify, mock_post):
        # mock token exchange
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'id_token': 'fake-id-token'}
        mock_post.return_value = mock_resp
        # mock id_token verification
        mock_verify.return_value = {'email': 'new@krok.edu.ua'}

        r = self.client.post('/api/v1/auth/callback/', {'code': 'abc123'}, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)
        # user created
        self.assertTrue(User.objects.filter(email='new@krok.edu.ua').exists())

    def test_refresh_endpoint(self):
        raw, rt = create_refresh_token(self.user)
        r = self.client.post('/api/v1/auth/refresh/', {'refresh_token': raw}, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertIn('access_token', r.json())

    def test_logout_revokes_token(self):
        raw, rt = create_refresh_token(self.user)
        r = self.client.post('/api/v1/auth/logout/', {'refresh_token': raw}, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        rt.refresh_from_db()
        self.assertTrue(rt.revoked)

    def auth_header(self, user=None):
        user = user or self.user
        token = create_access_token(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {token}'}

    def test_me_get_patch_delete(self):
        # GET
        r = self.client.get('/api/v1/users/me/', **self.auth_header())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json().get('email'), self.user.email)

        # PATCH
        r2 = self.client.patch('/api/v1/users/me/', {'email_verified': True}, content_type='application/json', **self.auth_header())
        self.assertEqual(r2.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

        # DELETE
        r3 = self.client.delete('/api/v1/users/me/', **self.auth_header())
        self.assertEqual(r3.status_code, 204)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())
