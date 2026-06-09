from django.urls import path
from .views import MicrosoftLoginView, MicrosoftCallbackView, LogoutView, RefreshView

urlpatterns = [
    path('login/', MicrosoftLoginView.as_view(), name='auth-login'),
    path('callback/', MicrosoftCallbackView.as_view(), name='auth-callback'),
    path('refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
]
