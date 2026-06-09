from django.contrib import admin
from .models import User, RefreshToken


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'auth_provider', 'email_verified', 'created_at')
    list_filter = ('auth_provider', 'email_verified', 'created_at')
    search_fields = ('email',)
    readonly_fields = ('id', 'created_at')


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'revoked', 'created_at', 'expires_at')
    list_filter = ('revoked', 'created_at')
    search_fields = ('user__email', 'token_hash')
    readonly_fields = ('id', 'created_at', 'token_hash')
