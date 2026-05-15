from abc import ABC, abstractmethod
from typing import Iterator


class BaseAdapter(ABC):
    """AI 模型适配器基类。"""

    @abstractmethod
    def chat(self, messages: list[dict], stream: bool = False, **kwargs) -> str | Iterator[str]:
        ...

    @abstractmethod
    def list_models(self) -> list[str]:
        ...
