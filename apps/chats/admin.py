from django.contrib import admin
from .models import Chat, ChatMember, ChatAccess, Message


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'type', 'message_count', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('title', 'owner__email')
    readonly_fields = ('id', 'created_at')


@admin.register(ChatMember)
class ChatMemberAdmin(admin.ModelAdmin):
    list_display = ('chat', 'user', 'role')
    list_filter = ('role',)
    search_fields = ('chat__title', 'user__email')


@admin.register(ChatAccess)
class ChatAccessAdmin(admin.ModelAdmin):
    list_display = ('chat', 'user')
    search_fields = ('chat__title', 'user__email')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('chat', 'user', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('chat__title', 'user__email', 'content')
    readonly_fields = ('id', 'created_at')
