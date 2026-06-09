from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from apps.users.models import User, RefreshToken
from apps.users.services import create_access_token, create_refresh_token, verify_refresh_token
import jwt


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
