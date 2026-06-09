import hashlib
import requests
from urllib.parse import urlencode
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.users.serializers import MicrosoftLoginSerializer, RefreshSerializer, UserSerializer, MeUpdateSerializer
from apps.users.services import create_access_token, create_refresh_token, verify_refresh_token, revoke_refresh_token
from apps.users.models import User
from django.utils import timezone
from .permissions import IsAuthenticatedCustom


class MicrosoftLoginView(APIView):
    """Return Microsoft OAuth2 authorize URL for frontend to redirect to."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = MicrosoftLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        redirect_uri = serializer.validated_data.get('redirect') or settings.MS_REDIRECT_URI
        params = {
            'client_id': settings.MS_CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'response_mode': 'query',
            'scope': 'openid email profile',
            'state': 'state',
        }
        auth_url = f"https://login.microsoftonline.com/{settings.MS_TENANT_ID}/oauth2/v2.0/authorize?{urlencode(params)}"
        return Response({'auth_url': auth_url})


class MicrosoftCallbackView(APIView):
    """Exchange code for id_token, validate domain and return JWTs."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # accept code in body or query params
        code = request.data.get('code') or request.query_params.get('code')
        redirect_uri = request.data.get('redirect') or settings.MS_REDIRECT_URI
        if not code:
            return Response({'detail': 'Missing code'}, status=status.HTTP_400_BAD_REQUEST)

        token_url = f"https://login.microsoftonline.com/{settings.MS_TENANT_ID}/oauth2/v2.0/token"
        data = {
            'client_id': settings.MS_CLIENT_ID,
            'client_secret': settings.MS_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
        }
        r = requests.post(token_url, data=data)
        if r.status_code != 200:
            return Response({'detail': 'Token exchange failed', 'error': r.text}, status=status.HTTP_400_BAD_REQUEST)
        token_data = r.json()
        id_token = token_data.get('id_token')
        # verify id_token signature and claims using Microsoft's JWKS
        from .microsoft import verify_id_token
        try:
            claims = verify_id_token(id_token)
        except Exception as exc:
            return Response({'detail': 'Invalid id_token', 'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        email = claims.get('email') or claims.get('upn')
        if not email or not email.endswith(f"@{settings.KROK_DOMAIN}"):
            return Response({'detail': 'Email domain not allowed'}, status=status.HTTP_403_FORBIDDEN)

        # create or update user
        user, _ = User.objects.get_or_create(email=email, defaults={'created_at': timezone.now()})

        access = create_access_token(user)
        raw_refresh, rt = create_refresh_token(user)

        return Response({'access_token': access, 'refresh_token': raw_refresh})


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        raw = serializer.validated_data['refresh_token']
        rt = verify_refresh_token(raw)
        if not rt:
            return Response({'detail': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)
        user = rt.user
        access = create_access_token(user)
        return Response({'access_token': access})


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get('refresh_token')
        if token:
            rt = verify_refresh_token(token)
            if rt:
                revoke_refresh_token(rt)
        return Response({'detail': 'Logged out'})


class MeView(APIView):
    """Get, update or delete current user account."""
    permission_classes = [IsAuthenticatedCustom]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        serializer = MeUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(user).data)

    def delete(self, request):
        user = request.user
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
