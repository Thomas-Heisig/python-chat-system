from pathlib import Path

from app.models.loaders.custom.base import CustomModelDetection, CustomModelLoaderPlugin
from app.models.loaders.custom.supra_a2a_nano import SupraA2ANanoLoaderPlugin


class CustomModelLoaderPluginRegistry:
    def __init__(self) -> None:
        self._plugins: list[CustomModelLoaderPlugin] = [
            SupraA2ANanoLoaderPlugin(),
        ]

    def detect(self, *, name: str, model_path: Path) -> CustomModelDetection | None:
        for plugin in self._plugins:
            detected = plugin.detect(name=name, model_path=model_path)
            if detected is not None:
                return detected
        return None

    def plugins(self) -> list[CustomModelLoaderPlugin]:
        return list(self._plugins)
