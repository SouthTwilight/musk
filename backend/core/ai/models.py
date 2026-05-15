from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """AI 对话会话。"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_conversations")
    title = models.CharField(max_length=255, default="新对话")
    model_name = models.CharField(max_length=50, default="deepseek")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_conversation"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.username}: {self.title}"


class Message(models.Model):
    """对话消息。"""
    ROLE_CHOICES = [
        ("system", "System"),
        ("user", "User"),
        ("assistant", "Assistant"),
    ]
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_message"
        ordering = ["created_at"]


class PromptTemplate(models.Model):
    """Prompt 模板。"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="prompt_templates", null=True, blank=True)
    name = models.CharField(max_length=255)
    prompt = models.TextField(help_text="支持 {变量名} 格式的占位符")
    variables = models.JSONField(default=list, help_text='变量名列表，如 ["语言", "关注点"]')
    category = models.CharField(max_length=50, default="general")
    module = models.CharField(max_length=50, default="framework", help_text="所属模块")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_prompt_template"
        ordering = ["category", "name"]

    def render(self, **kwargs) -> str:
        """渲染模板，替换变量。"""
        result = self.prompt
        for key, value in kwargs.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result
