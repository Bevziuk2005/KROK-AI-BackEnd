from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', include('apps.common.urls')),
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/users/', include('apps.users.user_urls')),
    path('api/v1/', include('apps.chats.urls')),
    path('api/v1/', include('apps.files.urls')),
]
