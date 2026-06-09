import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from apps.users.models import RefreshToken


def create_access_token(user):
    exp = datetime.utcnow() + timedelta(minutes=int(getattr(settings, 'JWT_ACCESS_EXPIRATION_MINUTES', 15)))
    payload = {
        'sub': str(user.id),
        'email': user.email,
        'exp': exp,
        'iat': datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token


def create_refresh_token(user):
    raw = secrets.token_urlsafe(64)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    expires_at = timezone.now() + timedelta(days=int(getattr(settings, 'JWT_REFRESH_EXPIRATION_DAYS', 30)))
    rt = RefreshToken.objects.create(user=user, token_hash=token_hash, expires_at=expires_at)
    return raw, rt


def verify_refresh_token(raw_token):
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    try:
        rt = RefreshToken.objects.get(token_hash=token_hash, revoked=False)
    except RefreshToken.DoesNotExist:
        return None
    if rt.expires_at < timezone.now():
        return None
    return rt


def revoke_refresh_token(rt):
    rt.revoked = True
    rt.save()
