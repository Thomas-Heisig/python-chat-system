from pathlib import Path
import importlib.util

from app.models.loaders.custom.base import CustomModelDetection, CustomModelLoaderPlugin


class SupraA2ANanoLoaderPlugin(CustomModelLoaderPlugin):
    loader_id = "supra_a2a_nano"
    display_name = "Supra A2A Nano Loader"
    supported_formats = {"custom_safetensors", "custom_pytorch"}
    supported_tasks = {"any_to_any"}

    _required_artifacts = ("vqvae.safetensors", "tokenizer.json")
    _weight_artifacts = {
        "custom_safetensors": ("model.safetensors",),
        "custom_pytorch": ("pytorch_model.bin", "model.bin"),
    }
    _code_candidates = (
        "modeling_supra.py",
        "supra_a2a_model.py",
        "loader_supra.py",
        "custom_loader.py",
    )

    def detect(self, *, name: str, model_path: Path) -> CustomModelDetection | None:
        if not model_path.is_dir():
            return None
        if not all(self._find_file(model_path, artifact) is not None for artifact in self._required_artifacts):
            return None

        matched_format = self._detect_format(model_path)
        if matched_format is None:
            return None

        custom_code_entrypoint = self._find_custom_code_entrypoint(model_path)
        model_family = "supra_a2a_nano" if ("supra" in name.lower() or "a2a" in name.lower()) else "custom_any_to_any"
        return CustomModelDetection(
            loader_id=self.loader_id,
            model_format=matched_format,
            task_type="any_to_any",
            model_family=model_family,
            backend="custom_pytorch",
            custom_code_available=custom_code_entrypoint is not None,
            custom_code_entrypoint=custom_code_entrypoint,
        )

    def runtime_available(self) -> tuple[bool, str | None]:
        has_torch = importlib.util.find_spec("torch") is not None
        if not has_torch:
            return False, "torch ist fuer benutzerdefinierte Supra-Loader nicht installiert."
        return True, None

    def _detect_format(self, model_path: Path) -> str | None:
        for model_format, candidates in self._weight_artifacts.items():
            if any(self._find_file(model_path, candidate) is not None for candidate in candidates):
                return model_format
        return None

    def _find_custom_code_entrypoint(self, model_path: Path) -> str | None:
        for candidate in self._code_candidates:
            path = self._find_file(model_path, candidate)
            if path is not None and path.is_file():
                return str(path)
        return None

    def _find_file(self, model_path: Path, name: str) -> Path | None:
        direct = model_path / name
        if direct.exists() and direct.is_file():
            return direct
        return next((path for path in model_path.rglob(name) if path.is_file()), None)
