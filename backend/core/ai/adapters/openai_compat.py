"""OpenAI 兼容适配器 — 支持 DeepSeek 和 GLM。"""

import os
import logging
from typing import Iterator

from core.ai.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)

# 模型配置：name -> (api_key_env, base_url, default_model)
MODEL_CONFIGS = {
    "deepseek": {
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
    },
    "glm": {
        "api_key_env": "GLM_API_KEY",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-flash",
    },
}


class OpenAICompatAdapter(BaseAdapter):
    """通用 OpenAI 兼容 API 适配器。"""

    def __init__(self, model_name: str = "deepseek"):
        config = MODEL_CONFIGS.get(model_name, MODEL_CONFIGS["deepseek"])
        self.api_key = os.environ.get(config["api_key_env"], "")
        self.base_url = config["base_url"]
        self.model = config["default_model"]

    def chat(self, messages: list[dict], stream: bool = False, **kwargs) -> str | Iterator[str]:
        """调用 AI 模型。需要 openai SDK。"""
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai SDK not installed. Run: pip install openai")

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        if stream:
            response = client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=messages,
                stream=True,
            )
            return self._stream_response(response)

        response = client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=messages,
            stream=False,
        )
        return response.choices[0].message.content

    def _stream_response(self, response) -> Iterator[str]:
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def list_models(self) -> list[str]:
        return [self.model]
