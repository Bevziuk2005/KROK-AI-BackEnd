from .base import *
import os

DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',') if os.getenv('ALLOWED_HOSTS') else ['*']

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# OpenAI and Supabase env variables must be present in production environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Microsoft / Auth settings (required for Microsoft Entra integration)
MS_CLIENT_ID = os.getenv('MS_CLIENT_ID')
MS_CLIENT_SECRET = os.getenv('MS_CLIENT_SECRET')
MS_TENANT_ID = os.getenv('MS_TENANT_ID', 'common')
MS_REDIRECT_URI = os.getenv('MS_REDIRECT_URI', '')
KROK_DOMAIN = os.getenv('KROK_DOMAIN', 'krok.edu.ua')

# JWT settings
JWT_ACCESS_EXPIRATION_MINUTES = int(os.getenv('JWT_ACCESS_EXPIRATION_MINUTES', '15'))
JWT_REFRESH_EXPIRATION_DAYS = int(os.getenv('JWT_REFRESH_EXPIRATION_DAYS', '30'))
