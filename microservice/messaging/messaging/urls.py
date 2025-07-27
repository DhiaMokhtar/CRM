from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MessageViewSet, ConversationViewSet, UserSearchView, HealthCheckView

router = DefaultRouter()
router.register(r'messages', MessageViewSet)
router.register(r'conversations', ConversationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('search-users/', UserSearchView.as_view(), name='search-users'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
]
