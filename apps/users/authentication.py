import jwt
from django.conf import settings
from rest_framework import authentication, exceptions
from django.utils import timezone
from apps.users.models import User


class JWTAuthentication(authentication.BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        auth = authentication.get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None
        if len(auth) == 1:
            raise exceptions.AuthenticationFailed('Invalid token header. No credentials provided.')
        try:
            token = auth[1].decode()
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token expired')
        except Exception:
            raise exceptions.AuthenticationFailed('Invalid token')

        user_id = payload.get('sub')
        if not user_id:
            raise exceptions.AuthenticationFailed('Invalid token payload')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')

        return (user, None)
