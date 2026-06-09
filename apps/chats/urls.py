from rest_framework.routers import DefaultRouter
from .views import ChatViewSet, MessageViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'chats', ChatViewSet, basename='chat')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('', include(router.urls)),
]
