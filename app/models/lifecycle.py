import gc
import asyncio
from typing import Any

from app.core.exceptions import ModelLoadError
from app.models.backends.base import ModelBackend


class ModelLifecycleManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    async def switch_model(
        self,
        old_backend: ModelBackend | None,
        new_backend: ModelBackend,
        model_path: str,
        config: dict[str, Any],
    ) -> ModelBackend:
        async with self._lock:
            if old_backend is not None:
                old_backend.unload()
                self._cleanup_memory()

            try:
                new_backend.load(model_path=model_path, config=config)
                if not new_backend.health_check():
                    raise ModelLoadError("health_check_failed")
                return new_backend
            except Exception as exc:
                new_backend.unload()
                self._cleanup_memory()
                raise ModelLoadError(str(exc)) from exc

    def _cleanup_memory(self) -> None:
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            return
