from typing import Any

from app.models.backends.base import ModelBackend
from app.models.lifecycle import ModelLifecycleManager
from app.models.loader import create_backend


class ModelManager:
    def __init__(self) -> None:
        self.active_model_id: int | None = None
        self.active_backend_name: str | None = None
        self.active_backend: ModelBackend | None = None
        self.lifecycle = ModelLifecycleManager()

    async def load_model(
        self,
        model_id: int,
        model_path: str,
        backend_name: str,
        config: dict[str, Any] | None,
    ) -> None:
        runtime_config = self._build_runtime_config(config)
        new_backend = create_backend(backend_name)
        try:
            active = await self.lifecycle.switch_model(self.active_backend, new_backend, model_path, runtime_config)
        except Exception as exc:
            # Retry on CPU if CUDA load failed because of OOM.
            if not self._is_cuda_oom(exc) or str(runtime_config.get("device", "")).lower() != "cuda":
                raise

            cpu_backend = create_backend(backend_name)
            cpu_config = dict(runtime_config)
            cpu_config["prefer_gpu"] = False
            cpu_config["device"] = "cpu"
            cpu_config["n_gpu_layers"] = 0
            active = await self.lifecycle.switch_model(self.active_backend, cpu_backend, model_path, cpu_config)

        self.active_backend = active
        self.active_model_id = model_id
        self.active_backend_name = backend_name

    async def unload(self) -> None:
        if self.active_backend is not None:
            self.active_backend.unload()
        self.active_backend = None
        self.active_model_id = None
        self.active_backend_name = None

    def _build_runtime_config(self, config: dict[str, Any] | None) -> dict[str, Any]:
        runtime_config: dict[str, Any] = dict(config or {})

        # Default policy: always try GPU first, then fall back to CPU.
        prefer_gpu = bool(runtime_config.get("prefer_gpu", True))
        runtime_config["prefer_gpu"] = prefer_gpu

        if prefer_gpu and self._gpu_available():
            runtime_config.setdefault("device", "cuda")
            runtime_config.setdefault("n_gpu_layers", -1)
            runtime_config.setdefault("offload_kqv", True)
        else:
            runtime_config["device"] = "cpu"
            runtime_config.setdefault("n_gpu_layers", 0)

        return runtime_config

    def _gpu_available(self) -> bool:
        try:
            import torch

            return bool(torch.cuda.is_available())
        except Exception:
            return False

    def _is_cuda_oom(self, exc: Exception) -> bool:
        text = str(exc).lower()
        return "cuda out of memory" in text or "cublas_status_alloc_failed" in text


model_manager = ModelManager()
