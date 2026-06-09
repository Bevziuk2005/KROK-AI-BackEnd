import requests
import time
from django.conf import settings
import jwt
from jwt.algorithms import RSAAlgorithm

_JWKS = None
_JWKS_TS = 0


def get_openid_config():
    tenant = settings.MS_TENANT_ID or 'common'
    return f"https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration"


def fetch_jwks():
    global _JWKS, _JWKS_TS
    if _JWKS and (time.time() - _JWKS_TS) < 3600:
        return _JWKS
    cfg = requests.get(get_openid_config()).json()
    jwks_uri = cfg.get('jwks_uri')
    jwks = requests.get(jwks_uri).json()
    _JWKS = jwks
    _JWKS_TS = time.time()
    return _JWKS


def verify_id_token(id_token):
    jwks = fetch_jwks()
    headers = jwt.get_unverified_header(id_token)
    kid = headers.get('kid')
    key_data = None
    for k in jwks.get('keys', []):
        if k.get('kid') == kid:
            key_data = k
            break
    if not key_data:
        raise Exception('JWKS key not found')
    public_key = RSAAlgorithm.from_jwk(key_data)
    audience = settings.MS_CLIENT_ID
    issuer = f"https://login.microsoftonline.com/{settings.MS_TENANT_ID}/v2.0"
    claims = jwt.decode(id_token, public_key, algorithms=['RS256'], audience=audience, issuer=issuer)
    return claims
