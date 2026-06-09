from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FileViewSet, rag_search_view

router = DefaultRouter()
router.register(r'files', FileViewSet, basename='files')

urlpatterns = [
    path('', include(router.urls)),
    path('rag/search/', rag_search_view, name='rag-search'),
]
