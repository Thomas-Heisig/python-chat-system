from __future__ import annotations

import asyncio
import threading
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from app.models.backends.base import ModelBackend
from app.models.loaders.custom.registry import CustomModelLoaderPluginRegistry
from app.models.loaders.custom.runtime import CustomRuntimeAdapter


class CustomPyTorchBackend(ModelBackend):
    def __init__(self) -> None:
        self._loaded = False
        self._model_path: str | None = None
        self._runtime: object | None = None
        self._adapter: CustomRuntimeAdapter | None = None
        self._capabilities: dict[str, Any] = {}
        self._lock = threading.Lock()

    def load(self, model_path: str, config: dict[str, Any]) -> None:
        model_dir = Path(model_path)
        detection = CustomModelLoaderPluginRegistry().detect(name=model_dir.name, model_path=model_dir)
        if detection is None:
            raise RuntimeError("No custom loader plugin matched this model path.")

        metadata_raw = config.get("metadata")
        metadata = metadata_raw if isinstance(metadata_raw, dict) else {}
        if not bool(metadata.get("custom_code_trusted", False)):
            raise RuntimeError("Custom code is not trusted for this model.")

        if not detection.custom_code_entrypoint:
            raise RuntimeError("Custom loader entrypoint is missing for this model.")

        adapter = CustomRuntimeAdapter(entrypoint_path=detection.custom_code_entrypoint)
        runtime = adapter.load_runtime(model_path=model_path, config=config)

        self._adapter = adapter
        self._runtime = runtime
        self._capabilities = {
            "text_generation": True,
            "chat_completion": True,
            "streaming": True,
            "embeddings": False,
            "vision": True,
            "audio": True,
            "tool_calling": False,
            "structured_output": False,
            "backend": "custom_pytorch",
            "custom_loader_id": detection.loader_id,
            **adapter.get_capabilities(runtime),
        }
        self._model_path = model_path
        self._loaded = True

    def unload(self) -> None:
        if self._adapter is not None and self._runtime is not None:
            try:
                self._adapter.unload_runtime(self._runtime)
            except Exception:
                pass
        self._loaded = False
        self._model_path = None
        self._runtime = None
        self._adapter = None
        self._capabilities = {}

    def generate(self, prompt: str, config: dict[str, Any]) -> str:
        if not self._loaded or self._adapter is None or self._runtime is None:
            raise RuntimeError("backend not loaded")
        with self._lock:
            return self._adapter.generate(runtime=self._runtime, prompt=prompt, config=config)

    async def stream(self, prompt: str, config: dict[str, Any]) -> AsyncIterator[str]:
        if not self._loaded or self._adapter is None or self._runtime is None:
            raise RuntimeError("backend not loaded")

        iterator = self._adapter.stream(runtime=self._runtime, prompt=prompt, config=config)
        if iterator is None:
            text = await asyncio.to_thread(self.generate, prompt, config)
            if text:
                yield text
            return

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        def _worker() -> None:
            try:
                for token in iterator:
                    if token:
                        loop.call_soon_threadsafe(queue.put_nowait, str(token))
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        threading.Thread(target=_worker, daemon=True).start()

        while True:
            token = await queue.get()
            if token is None:
                break
            yield token

    def health_check(self) -> bool:
        if not self._loaded or self._adapter is None or self._runtime is None:
            return False
        return self._adapter.health_check(self._runtime)

    def get_capabilities(self) -> dict[str, Any]:
        return dict(self._capabilities)
