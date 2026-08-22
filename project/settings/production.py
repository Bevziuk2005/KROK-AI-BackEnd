from .base import *
import os
from django.core.exceptions import ImproperlyConfigured

DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',') if os.getenv('ALLOWED_HOSTS') else ['*']
IS_PRODUCTION_STRICT = os.getenv('DEBUG_AUTH_ERRORS', 'false').lower() != 'true'
ADMINS = []

LOGGING['loggers']['apps.users'] = {
    'handlers': ['console'],
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'propagate': False,
}

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
MS_REDIRECT_URI = os.getenv('MS_REDIRECT_URI', 'https://krok-ai-back.onrender.com/api/v1/auth/callback/')
KROK_DOMAIN = os.getenv('KROK_DOMAIN', 'krok.edu.ua')
FRONTEND_DEFAULT_REDIRECT = os.getenv('FRONTEND_DEFAULT_REDIRECT', 'https://bevziuk2005.github.io/KROK-AI-FrontEnd/dashboard')
ALLOWED_FRONTEND_REDIRECTS = os.getenv('ALLOWED_FRONTEND_REDIRECTS', 'https://bevziuk2005.github.io').strip()

# JWT settings
JWT_ACCESS_EXPIRATION_MINUTES = int(os.getenv('JWT_ACCESS_EXPIRATION_MINUTES', '15'))
JWT_REFRESH_EXPIRATION_DAYS = int(os.getenv('JWT_REFRESH_EXPIRATION_DAYS', '30'))
