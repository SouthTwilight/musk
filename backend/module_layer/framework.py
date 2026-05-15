"""框架能力暴露 — 模块可通过此接口调用框架服务。"""


class FrameworkAPI:
    """模块可通过 from module_layer import framework 获取框架能力。"""

    @property
    def ai(self):
        from core.ai.adapters import get_adapter
        return get_adapter()

    # 后续扩展: storage, config 等


framework = FrameworkAPI()
