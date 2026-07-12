import asyncio
from typing import Any

from app.models.backends.base import ModelBackend


class ModelExecutor:
    async def generate(self, backend: ModelBackend, prompt: str, config: dict[str, Any]) -> str:
        return await asyncio.to_thread(backend.generate, prompt, config)
