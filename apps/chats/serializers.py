from rest_framework import serializers
from apps.chats.models import Chat, Message


class MessageSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField(read_only=True)
    chat = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'chat', 'user', 'user_email', 'role', 'content', 'token_count', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None


class ChatSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ('id', 'owner', 'title', 'type', 'message_count', 'token_count', 'last_message_id', 'last_message_at', 'created_at', 'messages')
        read_only_fields = ('id', 'message_count', 'token_count', 'last_message_id', 'last_message_at', 'created_at')


class ChatCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ('title', 'type')
