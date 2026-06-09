from django.db import transaction
from django.utils import timezone
from apps.chats.models import Chat, Message, ChatAccess, ChatMember
from apps.users.models import User


def user_has_access(user: User, chat: Chat) -> bool:
    if chat.owner_id == user.id:
        return True
    return ChatAccess.objects.filter(chat=chat, user=user).exists() or ChatMember.objects.filter(chat=chat, user=user).exists()


def create_chat(owner: User, title: str = '', type: str = 'assistant') -> Chat:
    chat = Chat.objects.create(owner=owner, title=title, type=type)
    # owner is member
    try:
        ChatMember.objects.create(chat=chat, user=owner, role='owner')
    except Exception:
        pass
    return chat


def update_chat(chat: Chat, **kwargs) -> Chat:
    for k, v in kwargs.items():
        setattr(chat, k, v)
    chat.save()
    return chat


def soft_delete_chat(chat: Chat):
    # Soft delete: clear title, zero counts, null last message timestamp
    chat.title = ''
    chat.message_count = 0
    chat.token_count = 0
    chat.last_message_at = None
    chat.last_message_id = None
    chat.save()


def list_chats_for_user(user: User):
    # return chats where user is owner or has access or is member
    owned = Chat.objects.filter(owner=user)
    access = Chat.objects.filter(chataccess__user=user)
    member = Chat.objects.filter(members__user=user)
    qs = (owned | access | member).distinct()
    return qs


def create_message(chat: Chat, user: User, role: str, content: str, token_count: int = 0) -> Message:
    with transaction.atomic():
        msg = Message.objects.create(chat=chat, user=user, role=role, content=content, token_count=token_count)
        chat.message_count = (chat.message_count or 0) + 1
        chat.last_message_at = msg.created_at
        chat.last_message_id = msg.id
        chat.save()
    return msg
