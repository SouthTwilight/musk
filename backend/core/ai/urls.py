from django.urls import path
from core.ai.views import (
    ConversationListView,
    ConversationDetailView,
    ChatView,
    PromptTemplateListView,
)

urlpatterns = [
    path("conversations/", ConversationListView.as_view(), name="ai-conversation-list"),
    path("conversations/<int:pk>/", ConversationDetailView.as_view(), name="ai-conversation-detail"),
    path("chat/", ChatView.as_view(), name="ai-chat"),
    path("templates/", PromptTemplateListView.as_view(), name="ai-template-list"),
]
