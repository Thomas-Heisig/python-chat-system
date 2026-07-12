from __future__ import annotations

from collections.abc import Iterable
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any, cast


class CustomRuntimeAdapter:
    def __init__(self, *, entrypoint_path: str) -> None:
        self._entrypoint_path = Path(entrypoint_path)
        self._module: ModuleType | None = None

    def load_runtime(self, *, model_path: str, config: dict[str, Any]) -> object:
        module = self._load_module()
        loader = getattr(module, "load_model", None)
        if not callable(loader):
            raise RuntimeError("Custom loader module must provide load_model(model_path, config).")
        return cast(object, loader(model_path, config))

    def unload_runtime(self, runtime: object) -> None:
        module = self._ensure_module_loaded()
        unload = getattr(module, "unload", None)
        if callable(unload):
            unload(runtime)

    def generate(self, *, runtime: object, prompt: str, config: dict[str, Any]) -> str:
        module = self._ensure_module_loaded()
        generate = getattr(module, "generate", None)
        if not callable(generate):
            raise RuntimeError("Custom loader module must provide generate(runtime, prompt, config).")
        result = generate(runtime, prompt, config)
        return str(result or "")

    def stream(self, *, runtime: object, prompt: str, config: dict[str, Any]) -> Iterable[str] | None:
        module = self._ensure_module_loaded()
        stream = getattr(module, "stream", None)
        if not callable(stream):
            return None
        result = stream(runtime, prompt, config)
        if isinstance(result, Iterable):
            return cast(Iterable[str], result)
        return None

    def health_check(self, runtime: object) -> bool:
        module = self._ensure_module_loaded()
        check = getattr(module, "health_check", None)
        if callable(check):
            return bool(check(runtime))
        return True

    def get_capabilities(self, runtime: object) -> dict[str, Any]:
        module = self._ensure_module_loaded()
        get_caps = getattr(module, "get_capabilities", None)
        if callable(get_caps):
            payload = get_caps(runtime)
            if isinstance(payload, dict):
                return cast(dict[str, Any], payload)
        return {}

    def _load_module(self) -> ModuleType:
        if self._module is not None:
            return self._module
        if not self._entrypoint_path.exists() or not self._entrypoint_path.is_file():
            raise RuntimeError(f"Custom loader entrypoint not found: {self._entrypoint_path}")

        module_name = f"custom_loader_{abs(hash(str(self._entrypoint_path.resolve(strict=False))))}"
        spec = importlib.util.spec_from_file_location(module_name, str(self._entrypoint_path))
        if spec is None or spec.loader is None:
            raise RuntimeError("Custom loader module could not be imported.")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self._module = module
        return module

    def _ensure_module_loaded(self) -> ModuleType:
        return self._load_module()
