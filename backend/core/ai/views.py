import json
import logging
from django.http import StreamingHttpResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.ai.models import Conversation, Message, PromptTemplate
from core.ai.serializers import (
    ConversationSerializer,
    ConversationDetailSerializer,
    ChatRequestSerializer,
    PromptTemplateSerializer,
)

logger = logging.getLogger(__name__)


class ConversationListView(generics.ListCreateAPIView):
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ConversationDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ConversationDetailSerializer

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)


class ChatView(APIView):
    """AI 对话 — 支持普通响应和 SSE 流式响应。"""

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_message = serializer.validated_data["message"]
        conversation_id = serializer.validated_data.get("conversation_id")
        model_name = serializer.validated_data.get("model", "deepseek")

        # 获取或创建会话
        if conversation_id:
            try:
                conv = Conversation.objects.get(id=conversation_id, user=request.user)
            except Conversation.DoesNotExist:
                return Response({"detail": "会话不存在"}, status=status.HTTP_404_NOT_FOUND)
        else:
            conv = Conversation.objects.create(
                user=request.user,
                title=user_message[:50],
                model_name=model_name,
            )

        # 保存用户消息
        Message.objects.create(conversation=conv, role="user", content=user_message)

        # 构建消息历史
        history = [
            {"role": m.role, "content": m.content}
            for m in conv.messages.all().order_by("created_at")
        ]

        # 调用 AI
        try:
            from core.ai.adapters import get_adapter
            adapter = get_adapter(model_name)
            stream = request.query_params.get("stream", "false").lower() == "true"

            if stream:
                response_iter = adapter.chat(history, stream=True)
                return self._stream_response(response_iter, conv)

            reply = adapter.chat(history, stream=False)
            Message.objects.create(conversation=conv, role="assistant", content=reply)
            return Response({
                "conversation_id": conv.id,
                "message": {"role": "assistant", "content": reply},
            })

        except Exception as e:
            logger.error("AI chat error: %s", e)
            return Response(
                {"detail": f"AI 调用失败: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def _stream_response(self, response_iter, conv):
        """SSE 流式响应。"""
        def event_stream():
            full_content = []
            try:
                for chunk in response_iter:
                    full_content.append(chunk)
                    data = json.dumps({"content": chunk}, ensure_ascii=False)
                    yield f"data: {data}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            finally:
                # 流式结束后保存完整回复
                content = "".join(full_content)
                if content:
                    Message.objects.create(conversation=conv, role="assistant", content=content)
                yield f"data: {json.dumps({'done': True, 'conversation_id': conv.id}, ensure_ascii=False)}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class PromptTemplateListView(generics.ListCreateAPIView):
    serializer_class = PromptTemplateSerializer

    def get_queryset(self):
        return PromptTemplate.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
