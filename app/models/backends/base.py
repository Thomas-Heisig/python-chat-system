from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any


class ModelBackend(ABC):
    @abstractmethod
    def load(self, model_path: str, config: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def unload(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def generate(self, prompt: str, config: dict[str, Any]) -> str:
        raise NotImplementedError

    @abstractmethod
    def stream(self, prompt: str, config: dict[str, Any]) -> AsyncIterator[str]:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_capabilities(self) -> dict[str, Any]:
        raise NotImplementedError
