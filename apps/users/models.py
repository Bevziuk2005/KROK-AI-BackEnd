from django.db import models
import uuid


class User(models.Model):
    """Maps public.users table from Supabase"""
    AUTH_PROVIDER_CHOICES = [
        ('email', 'Email'),
        ('google', 'Google'),
        ('github', 'GitHub'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    auth_provider = models.CharField(max_length=50, choices=AUTH_PROVIDER_CHOICES, default='email')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'users'

    def __str__(self):
        return self.email


class RefreshToken(models.Model):
    """Server-side stored refresh tokens for issued JWTs."""
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='refresh_tokens')
    token_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'django_refresh_tokens'

    def __str__(self):
        return f"RefreshToken(user={self.user.email}, revoked={self.revoked})"
