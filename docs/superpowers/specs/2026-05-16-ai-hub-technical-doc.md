# AI 中枢技术文档

> 文档日期：2026-05-16
> 版本：Sprint 3 实现

## 1. 架构总览

AI 中枢位于 `backend/core/ai/`，采用**适配器模式**屏蔽不同 AI 供应商的 API 差异，向上提供统一的 `chat()` 接口。

```
┌─────────────────────────────────────────────┐
│              Frontend (Vue 3)                │
│   AiChatView.vue → stores/ai.ts (Pinia)     │
│         ↓ fetch ReadableStream (SSE)         │
├─────────────────────────────────────────────┤
│              Backend (Django)                │
│                                             │
│   views.py (ChatView)                       │
│       ↓                                     │
│   adapters/__init__.py → get_adapter()      │
│       ↓                                     │
│   ┌──────────────────────────┐              │
│   │     BaseAdapter (ABC)     │              │
│   └──────────────────────────┘              │
│       ↑              ↑                      │
│   OpenAICompat   (FutureAdapter)            │
│   (DeepSeek/GLM)                            │
└─────────────────────────────────────────────┘
```

## 2. 适配器层

### 2.1 BaseAdapter（抽象基类）

文件：`backend/core/ai/adapters/base.py`

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional

class BaseAdapter(ABC):
    """AI 模型适配器抽象基类"""

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        **kwargs,
    ) -> ...:
        """发送对话请求"""
        ...

    @abstractmethod
    def list_models(self) -> List[str]:
        """列出可用模型"""
        ...
```

所有适配器必须实现 `chat()` 和 `list_models()` 两个方法。

### 2.2 OpenAICompatAdapter

文件：`backend/core/ai/adapters/openai_compat.py`

使用 `openai` Python SDK，通过不同的 `base_url` 和 `api_key` 支持 DeepSeek 和 GLM 两种模型。

**配置映射：**

| 模型 | base_url | api_key 环境变量 |
|------|----------|------------------|
| DeepSeek | `https://api.deepseek.com` | `DEEPSEEK_API_KEY` |
| GLM | `https://open.bigmodel.cn/api/paas/v4` | `GLM_API_KEY` |

**核心逻辑：**

```python
from openai import OpenAI

class OpenAICompatAdapter(BaseAdapter):
    def __init__(self, provider: str, api_key: str, base_url: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.provider = provider

    def chat(self, messages, model=None, stream=False, **kwargs):
        model = model or f"{self.provider}-chat"
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream,
            **kwargs,
        )
        if stream:
            return response  # 返回 Stream 对象
        return response

    def list_models(self):
        return [f"{self.provider}-chat"]
```

**流式输出原理：**

当 `stream=True` 时，`openai` SDK 返回一个迭代器，每次 `yield` 一个 `ChatCompletionChunk` 对象。后端遍历此迭代器，逐 chunk 以 SSE 格式推送至前端。

### 2.3 适配器工厂

文件：`backend/core/ai/adapters/__init__.py`

```python
from django.conf import settings

_ADAPTERS = {}

def get_adapter(provider: str = None) -> BaseAdapter:
    """获取 AI 模型适配器（带缓存）"""
    provider = provider or getattr(settings, 'AI_DEFAULT_MODEL', 'deepseek')
    if provider not in _ADAPTERS:
        _ADAPTERS[provider] = _create_adapter(provider)
    return _ADAPTERS[provider]

def _create_adapter(provider: str) -> BaseAdapter:
    if provider == 'deepseek':
        return OpenAICompatAdapter(
            provider='deepseek',
            api_key=settings.DEEPSEEK_API_KEY,
            base_url='https://api.deepseek.com',
        )
    elif provider == 'glm':
        return OpenAICompatAdapter(
            provider='glm',
            api_key=settings.GLM_API_KEY,
            base_url='https://open.bigmodel.cn/api/paas/v4',
        )
    raise ValueError(f"Unknown AI provider: {provider}")
```

**缓存机制：** `_ADAPTERS` 字典缓存已创建的适配器实例，避免重复初始化 OpenAI Client。

## 3. 数据模型

文件：`backend/core/ai/models.py`

### 3.1 Conversation（会话）

```python
class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    model = models.CharField(max_length=50, default='deepseek')
    system_prompt = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 3.2 Message（消息）

```python
class Message(models.Model):
    ROLE_CHOICES = [
        ('system', 'System'),
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE,
                                      related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
```

### 3.3 PromptTemplate（Prompt 模板）

```python
class PromptTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    content = models.TextField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

## 4. REST API 端点

文件：`backend/core/ai/urls.py`

### 4.1 会话管理

| 端点 | 方法 | 说明 | 请求体 |
|------|------|------|--------|
| `/api/ai/conversations/` | GET | 获取当前用户的会话列表 | — |
| `/api/ai/conversations/` | POST | 创建新会话 | `{title, model?, system_prompt?}` |
| `/api/ai/conversations/:id/` | GET | 获取会话详情（含消息） | — |
| `/api/ai/conversations/:id/` | DELETE | 删除会话 | — |

### 4.2 AI 对话（核心）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/ai/chat/` | POST | AI 对话（支持 SSE 流式） |

**请求体：**

```json
{
  "conversation_id": "uuid-string",
  "message": "用户输入的文本",
  "model": "deepseek",
  "stream": true
}
```

**响应 — 普通模式（stream=false）：**

```json
{
  "message": {
    "role": "assistant",
    "content": "AI 的完整回复",
    "created_at": "2026-05-16T10:00:00Z"
  }
}
```

**响应 — 流式模式（stream=true）：**

Content-Type: `text/event-stream`

```
data: {"delta": "你"}

data: {"delta": "好"}

data: {"delta": "！"}

data: {"done": true, "message_id": 42}
```

### 4.3 Prompt 模板

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/ai/templates/` | GET | 获取用户的模板列表 |
| `/api/ai/templates/` | POST | 创建模板 | `{name, content, is_default?}` |
| `/api/ai/templates/:id/` | PUT/PATCH | 更新模板 |
| `/api/ai/templates/:id/` | DELETE | 删除模板 |

## 5. SSE 流式输出实现

### 5.1 后端（ChatView）

```python
# backend/core/ai/views.py

class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        conversation = Conversation.objects.get(
            id=serializer.validated_data['conversation_id'],
            user=request.user,
        )

        # 保存用户消息
        Message.objects.create(
            conversation=conversation,
            role='user',
            content=serializer.validated_data['message'],
        )

        # 构建消息历史
        messages = self._build_messages(conversation)

        # 获取适配器
        adapter = get_adapter(serializer.validated_data.get('model'))

        if serializer.validated_data.get('stream'):
            return self._stream_response(adapter, messages, conversation)

        # 非流式
        response = adapter.chat(messages=messages)
        msg = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response.choices[0].message.content,
        )
        return Response({'message': MessageSerializer(msg).data})

    def _stream_response(self, adapter, messages, conversation):
        """SSE 流式响应"""
        def event_stream():
            full_content = []
            stream = adapter.chat(messages=messages, stream=True)
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ''
                if delta:
                    full_content.append(delta)
                    yield f"data: {json.dumps({'delta': delta})}\n\n"
            # 保存完整回复
            msg = Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=''.join(full_content),
            )
            yield f"data: {json.dumps({'done': True, 'message_id': msg.id})}\n\n"

        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'  # Nginx 代理禁用缓冲
        return response
```

### 5.2 前端（ai.ts store）

```typescript
// frontend/src/stores/ai.ts

async sendMessage(content: string) {
  // 1. 保存用户消息到本地
  this.messages.push({ role: 'user', content })

  // 2. 创建 assistant 占位消息
  const assistantMsg = { role: 'assistant', content: '' }
  this.messages.push(assistantMsg)

  // 3. 使用 fetch + ReadableStream 接收 SSE
  const response = await fetch('/api/ai/chat/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      conversation_id: this.currentConversation.id,
      message: content,
      stream: true,
    }),
  })

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const text = decoder.decode(value)
    // 解析 SSE data: 行
    for (const line of text.split('\n')) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6))
        if (data.delta) {
          assistantMsg.content += data.delta  // 逐字追加
        }
        if (data.done) break
      }
    }
  }
}
```

### 5.3 Nginx SSE 代理配置

```nginx
# docker/nginx.conf

location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;

    # SSE 关键配置
    proxy_buffering off;           # 禁用缓冲，实时推送
    proxy_cache off;               # 禁用缓存
    proxy_read_timeout 300s;       # 长连接超时 5 分钟
    proxy_http_version 1.1;        # HTTP/1.1 长连接
    proxy_set_header Connection ""; # 清除 Connection 头
}
```

**关键点：** `proxy_buffering off` 是 SSE 在 Nginx 代理下正常工作的必要条件，否则 Nginx 会缓冲整个响应直到完成才发送。

## 6. 环境配置

### 6.1 Django Settings

```python
# backend/musk/settings.py

# AI 配置
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
GLM_API_KEY = os.environ.get('GLM_API_KEY', '')
AI_DEFAULT_MODEL = os.environ.get('AI_DEFAULT_MODEL', 'deepseek')
```

### 6.2 .env 文件

```bash
# .env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxx
GLM_API_KEY=xxxxxxxxxxxx.xxxxxx
AI_DEFAULT_MODEL=deepseek    # 或 glm
```

### 6.3 Docker 环境变量传递

```yaml
# docker-compose.yml
environment:
  - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-}
  - GLM_API_KEY=${GLM_API_KEY:-}
  - AI_DEFAULT_MODEL=${AI_DEFAULT_MODEL:-deepseek}
```

## 7. 模块调用 AI 的方式

模块通过 `module_layer.framework.FrameworkAPI` 访问 AI 能力：

```python
# backend/module_layer/framework.py

class FrameworkAPI:
    """框架能力暴露给模块的接口"""

    @staticmethod
    def get_ai_adapter(provider: str = None) -> BaseAdapter:
        """获取 AI 适配器"""
        from core.ai.adapters import get_adapter
        return get_adapter(provider)
```

模块内使用：

```python
# backend/apps/my_module/views.py
from module_layer.framework import FrameworkAPI

class MyView(APIView):
    def post(self, request):
        adapter = FrameworkAPI.get_ai_adapter('deepseek')
        response = adapter.chat(messages=[
            {"role": "user", "content": "分析这只股票..."}
        ])
        return Response({'result': response.choices[0].message.content})
```

## 8. 扩展新模型

添加新的 AI 供应商只需两步：

### 步骤 1：创建适配器

```python
# backend/core/ai/adapters/qwen_adapter.py
from .base import BaseAdapter

class QwenAdapter(BaseAdapter):
    def __init__(self, api_key: str):
        # 使用 OpenAI 兼容协议或自定义 SDK
        ...

    def chat(self, messages, model=None, stream=False, **kwargs):
        ...

    def list_models(self):
        return ['qwen-turbo', 'qwen-plus', 'qwen-max']
```

### 步骤 2：注册到工厂

```python
# backend/core/ai/adapters/__init__.py
def _create_adapter(provider: str) -> BaseAdapter:
    ...
    elif provider == 'qwen':
        return QwenAdapter(api_key=settings.QWEN_API_KEY)
```

### 步骤 3：添加环境变量

```bash
# .env
QWEN_API_KEY=sk-xxxx
AI_DEFAULT_MODEL=qwen  # 可选设为默认
```

## 9. 数据流完整链路

```
用户输入 → AiChatView.vue
  → stores/ai.ts (sendMessage)
    → fetch('/api/ai/chat/', {stream: true})
      → Nginx proxy (proxy_buffering off)
        → Django ChatView.post()
          → get_adapter('deepseek')
            → OpenAICompatAdapter.chat(stream=True)
              → DeepSeek API (SSE)
                ← chunk by chunk
          → StreamingHttpResponse(event_stream)
            ← SSE: data: {"delta": "..."}
      ← Nginx (透传)
    ← ReadableStream.read()
  → assistantMsg.content += delta
  → Vue reactivity 更新 UI
```

## 10. 测试覆盖

文件：`backend/tests/test_ai.py`（6 个测试）

| 测试 | 说明 |
|------|------|
| `test_get_adapter_deepseek` | DeepSeek 适配器创建 |
| `test_get_adapter_glm` | GLM 适配器创建 |
| `test_get_adapter_unknown` | 未知供应商抛出 ValueError |
| `test_create_conversation` | 创建会话 |
| `test_list_conversations` | 获取会话列表 |
| `test_create_template` | 创建 Prompt 模板 |
