from django.db import models
import uuid
from apps.users.models import User


class Chat(models.Model):
    """Maps public.chats table from Supabase"""
    CHAT_TYPE_CHOICES = [
        ('assistant', 'Assistant'),
        ('group', 'Group'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')
    title = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=50, choices=CHAT_TYPE_CHOICES, default='assistant')
    message_count = models.IntegerField(default=0)
    token_count = models.IntegerField(default=0)
    last_message_id = models.UUIDField(blank=True, null=True)
    last_message_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'chats'

    def __str__(self):
        return self.title or f"Chat {self.id}"


class ChatMember(models.Model):
    """Maps public.chat_members table from Supabase"""
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('admin', 'Admin'),
        ('owner', 'Owner'),
    ]
    
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='member')

    class Meta:
        managed = False
        db_table = 'chat_members'
        unique_together = ('chat', 'user')

    def __str__(self):
        return f"{self.user.email} in {self.chat.title or self.chat.id}"


class ChatAccess(models.Model):
    """Maps public.chat_access table from Supabase"""
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'chat_access'
        unique_together = ('chat', 'user')

    def __str__(self):
        return f"Access: {self.user.email} -> {self.chat.id}"


class Message(models.Model):
    """Maps public.messages table from Supabase"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    content = models.TextField()
    token_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'messages'

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"
