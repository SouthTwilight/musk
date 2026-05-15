"""模块注册表 — 存储已发现模块的元信息。"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModuleInfo:
    name: str
    version: str
    display_name: str
    icon: str
    description: str = ""
    menu_order: int = 99
    app_label: str = ""
    db_alias: str = ""
    url_prefix: str = ""
    dependencies: list = field(default_factory=list)
    ai_templates: list = field(default_factory=list)


class ModuleRegistry:
    """全局模块注册表。"""

    def __init__(self):
        self._modules: dict[str, ModuleInfo] = {}

    def register(self, info: ModuleInfo) -> None:
        self._modules[info.name] = info

    def get(self, name: str) -> Optional[ModuleInfo]:
        return self._modules.get(name)

    def all(self) -> list[ModuleInfo]:
        return sorted(self._modules.values(), key=lambda m: m.menu_order)

    def names(self) -> list[str]:
        return [m.name for m in self.all()]

    def clear(self) -> None:
        self._modules.clear()


# 全局单例
registry = ModuleRegistry()
