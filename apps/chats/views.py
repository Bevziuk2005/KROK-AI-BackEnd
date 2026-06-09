from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import filters
from django.shortcuts import get_object_or_404
from apps.chats.models import Chat, Message
from apps.chats.serializers import ChatSerializer, ChatCreateSerializer, MessageSerializer
from apps.chats.services import list_chats_for_user, create_chat, update_chat, soft_delete_chat, user_has_access, create_message
from apps.users.authentication import JWTAuthentication
from apps.users.permissions import IsAuthenticatedCustom
from django.db.models import F


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedCustom]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['last_message_at', 'created_at']
    ordering = ['-last_message_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return ChatCreateSerializer
        return ChatSerializer

    def get_queryset(self):
        user = self.request.user
        qs = list_chats_for_user(user)
        # allow filter by type
        ctype = self.request.query_params.get('type')
        if ctype:
            qs = qs.filter(type=ctype)
        return qs.order_by('-last_message_at')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        owner = request.user
        chat = create_chat(owner=owner, **serializer.validated_data)
        out = ChatSerializer(chat, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        chat = self.get_object()
        if chat.owner_id != request.user.id:
            return Response({'detail': 'Only owner can update chat'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        chat = self.get_object()
        if chat.owner_id != request.user.id:
            return Response({'detail': 'Only owner can delete chat'}, status=status.HTTP_403_FORBIDDEN)
        soft_delete_chat(chat)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages(self, request, pk=None):
        chat = self.get_object()
        if not user_has_access(request.user, chat):
            return Response({'detail': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'GET':
            qs = chat.messages.all().order_by('created_at')
            paginator = StandardPagination()
            page = paginator.paginate_queryset(qs, request)
            serializer = MessageSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # POST: create message
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        msg = create_message(chat=chat, user=request.user, role=serializer.validated_data.get('role'), content=serializer.validated_data.get('content'), token_count=serializer.validated_data.get('token_count', 0))
        return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedCustom]

    def retrieve(self, request, *args, **kwargs):
        msg = self.get_object()
        if not user_has_access(request.user, msg.chat):
            return Response({'detail': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        return super().retrieve(request, *args, **kwargs)
