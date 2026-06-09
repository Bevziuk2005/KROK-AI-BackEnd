from django.urls import path
from .views import MicrosoftLoginView, MicrosoftCallbackView, LogoutView, MeView, RefreshView

urlpatterns = [
    path('microsoft/login/', MicrosoftLoginView.as_view(), name='ms-login'),
    path('microsoft/callback/', MicrosoftCallbackView.as_view(), name='ms-callback'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('microsoft/refresh/', RefreshView.as_view(), name='ms-refresh'),
]
