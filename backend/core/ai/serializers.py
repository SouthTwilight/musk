from rest_framework import serializers
from core.ai.models import Conversation, Message, PromptTemplate


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ("id", "role", "content", "created_at")
        read_only_fields = ("id", "created_at")


class ConversationSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "title", "model_name", "message_count", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def get_message_count(self, obj):
        return obj.messages.count()


class ConversationDetailSerializer(ConversationSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ("messages",)


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
    model = serializers.CharField(required=False, default="deepseek")


class PromptTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptTemplate
        fields = ("id", "name", "prompt", "variables", "category", "module", "created_at")
        read_only_fields = ("id", "created_at")
