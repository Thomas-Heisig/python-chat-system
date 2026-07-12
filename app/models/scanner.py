from pathlib import Path
from typing import TypedDict

from app.models.metadata import infer_model_capabilities, is_system_directory


class ScannedModel(TypedDict):
    name: str
    model_path: str
    backend: str
    model_format: str
    task_type: str
    model_family: str
    metadata: dict[str, object]


SUPPORTED_HINT_FILES = {
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "generation_config.json",
    "model.safetensors",
    "vqvae.safetensors",
    "pytorch_model.bin",
    "model.bin",
}


class ModelScanner:
    def scan_directories(self, directories: list[str]) -> list[ScannedModel]:
        discovered: list[ScannedModel] = []
        seen: set[str] = set()

        for directory in directories:
            root = Path(directory)
            if not root.exists() or not root.is_dir():
                continue

            for child in root.iterdir():
                if child.is_dir() and is_system_directory(child):
                    continue

                if child.is_file() and child.suffix.lower() == ".gguf":
                    key = str(child.resolve())
                    if key in seen:
                        continue
                    seen.add(key)
                    capabilities = infer_model_capabilities(name=child.stem, model_path=child)
                    metadata = {key: value for key, value in capabilities.items()}
                    discovered.append(
                        {
                            "name": child.stem,
                            "model_path": key,
                            "backend": capabilities["backend"] or "unknown",
                            "model_format": capabilities["model_format"],
                            "task_type": capabilities["task_type"],
                            "model_family": capabilities["model_family"],
                            "metadata": metadata,
                        }
                    )
                    continue

                if not child.is_dir():
                    continue

                hint_match = any((child / hint).exists() for hint in SUPPORTED_HINT_FILES)
                has_nested_onnx = any(child.rglob("*.onnx"))
                has_nested_gguf = any(child.rglob("*.gguf"))
                has_model_index = (child / "model_index.json").exists()
                if not (hint_match or has_nested_onnx or has_nested_gguf or has_model_index):
                    continue

                key = str(child.resolve())
                if key in seen:
                    continue
                seen.add(key)
                capabilities = infer_model_capabilities(name=child.name, model_path=child)
                metadata = {key: value for key, value in capabilities.items()}
                discovered.append(
                    {
                        "name": child.name,
                        "model_path": key,
                        "backend": capabilities["backend"] or "unknown",
                        "model_format": capabilities["model_format"],
                        "task_type": capabilities["task_type"],
                        "model_family": capabilities["model_family"],
                        "metadata": metadata,
                    }
                )

        return discovered
