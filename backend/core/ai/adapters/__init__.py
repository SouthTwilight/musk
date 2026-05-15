from core.ai.adapters.openai_compat import OpenAICompatAdapter


def get_adapter(model_name: str = None):
    """获取 AI 适配器实例。默认使用配置中的模型。"""
    from django.conf import settings
    name = model_name or getattr(settings, "AI_DEFAULT_MODEL", "deepseek")
    return OpenAICompatAdapter(model_name=name)
