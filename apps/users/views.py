import hashlib
import logging
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

logger = logging.getLogger(__name__)


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

    def get(self, request):
        """Handle Azure GET redirect with code in query params"""
        code = request.query_params.get('code')
        redirect_uri = request.query_params.get('redirect_uri') or settings.MS_REDIRECT_URI
        
        if not code:
            return Response({'detail': 'Missing code'}, status=status.HTTP_400_BAD_REQUEST)

        # Exchange code for id_token
        token_url = f"https://login.microsoftonline.com/{settings.MS_TENANT_ID}/oauth2/v2.0/token"
        data = {
            'client_id': settings.MS_CLIENT_ID,
            'client_secret': settings.MS_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
        }
        
        try:
            r = requests.post(token_url, data=data, timeout=10)
            if r.status_code != 200:
                error_msg = r.text
                logger.error(f'Token exchange failed: {error_msg}')
                # Повертай HTML зі помилкою
                return self._error_html(f'Token exchange failed: {error_msg}')
            
            token_data = r.json()
            id_token = token_data.get('id_token')
            
            # Verify id_token signature and claims
            from .microsoft import verify_id_token
            try:
                claims = verify_id_token(id_token)
            except Exception as exc:
                logger.error(f'Invalid id_token: {exc}')
                return self._error_html(f'Invalid token: {str(exc)}')

            # Validate email domain
            email = claims.get('email') or claims.get('upn')
            if not email or not email.endswith(f"@{settings.KROK_DOMAIN}"):
                logger.warning(f'Email domain not allowed: {email}')
                return self._error_html(f'Email domain not allowed. Use @{settings.KROK_DOMAIN}')

            # Create or update user
            user, created = User.objects.get_or_create(
                email=email, 
                defaults={
                    'created_at': timezone.now(),
                    'first_name': claims.get('given_name', ''),
                    'last_name': claims.get('family_name', ''),
                }
            )
            
            if not created:
                user.first_name = claims.get('given_name', '')
                user.last_name = claims.get('family_name', '')
                user.save()

            # Generate JWT tokens
            access = create_access_token(user)
            raw_refresh, rt = create_refresh_token(user)

            logger.info(f'User {email} authenticated successfully')
            
            # Return HTML that stores tokens and redirects
            return self._success_html(access, raw_refresh)

        except requests.RequestException as e:
            logger.error(f'Request error during token exchange: {e}')
            return self._error_html(f'Request error: {str(e)}')
        except Exception as e:
            logger.exception('Unexpected error in callback')
            return self._error_html(f'Unexpected error: {str(e)}')

    def post(self, request):
        """Handle POST requests (for backward compatibility)"""
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
        
        try:
            r = requests.post(token_url, data=data, timeout=10)
            if r.status_code != 200:
                logger.error(f'Token exchange failed: {r.text}')
                return Response({'detail': 'Token exchange failed', 'error': r.text}, status=status.HTTP_400_BAD_REQUEST)
            
            token_data = r.json()
            id_token = token_data.get('id_token')
            
            from .microsoft import verify_id_token
            try:
                claims = verify_id_token(id_token)
            except Exception as exc:
                logger.error(f'Invalid id_token: {exc}')
                return Response({'detail': 'Invalid id_token', 'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

            email = claims.get('email') or claims.get('upn')
            if not email or not email.endswith(f"@{settings.KROK_DOMAIN}"):
                logger.warning(f'Email domain not allowed: {email}')
                return Response({'detail': 'Email domain not allowed'}, status=status.HTTP_403_FORBIDDEN)

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'created_at': timezone.now(),
                    'first_name': claims.get('given_name', ''),
                    'last_name': claims.get('family_name', ''),
                }
            )
            
            if not created:
                user.first_name = claims.get('given_name', '')
                user.last_name = claims.get('family_name', '')
                user.save()

            access = create_access_token(user)
            raw_refresh, rt = create_refresh_token(user)

            logger.info(f'User {email} authenticated successfully (POST)')
            return Response({'access_token': access, 'refresh_token': raw_refresh})

        except Exception as e:
            logger.exception('Error in POST callback')
            return Response({'detail': 'Authentication failed', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _success_html(self, access_token, refresh_token):
        """Return HTML that stores tokens and redirects to dashboard"""
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Логіну вас...</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .container {{
                    text-align: center;
                    background: white;
                    padding: 2rem;
                    border-radius: 8px;
                    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
                }}
                .spinner {{
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #667eea;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 1rem;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
                h1 {{
                    margin: 1rem 0 0.5rem;
                    color: #333;
                    font-size: 1.5rem;
                }}
                p {{
                    color: #666;
                    margin: 0.5rem 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="spinner"></div>
                <h1>Логіну вас...</h1>
                <p>Одну хвилину</p>
            </div>
            <script>
                // Зберегти токени
                localStorage.setItem('access_token', '{access_token}');
                localStorage.setItem('refresh_token', '{refresh_token}');
                
                // Редірегуй на фронтенд
                // Зміни URL на твій фронтенд домен
                setTimeout(() => {{
                    // ОПЦІЯ 1: Якщо фронтенд на тому ж домені
                    window.location.href = '/dashboard';
                    
                    // ОПЦІЯ 2: Якщо фронтенд на іншому домені
                    // window.location.href = 'https://твій-фронтенд.com/dashboard';
                }}, 1000);
            </script>
        </body>
        </html>
        '''
        return Response(html, content_type='text/html')

    def _error_html(self, error_msg):
        """Return HTML that shows error"""
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Помилка входу</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .container {{
                    text-align: center;
                    background: white;
                    padding: 2rem;
                    border-radius: 8px;
                    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
                    max-width: 500px;
                }}
                .error {{
                    color: #d32f2f;
                    font-size: 3rem;
                    margin-bottom: 1rem;
                }}
                h1 {{
                    margin: 0 0 1rem;
                    color: #333;
                }}
                p {{
                    color: #666;
                    margin: 0.5rem 0;
                    word-break: break-all;
                }}
                .message {{
                    background: #fff3cd;
                    border: 1px solid #ffc107;
                    border-radius: 4px;
                    padding: 1rem;
                    margin: 1rem 0;
                    color: #856404;
                    font-size: 0.9rem;
                }}
                a {{
                    display: inline-block;
                    margin-top: 1rem;
                    padding: 0.75rem 1.5rem;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    transition: background 0.3s;
                }}
                a:hover {{
                    background: #764ba2;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error">⚠️</div>
                <h1>Помилка входу</h1>
                <div class="message">{error_msg}</div>
                <p>На жаль, не вдалося вас авторізувати</p>
                <a href="/login">Спробувати знову</a>
            </div>
        </body>
        </html>
        '''
        return Response(html, content_type='text/html', status=status.HTTP_400_BAD_REQUEST)


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
