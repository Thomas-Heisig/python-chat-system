from pathlib import Path
from collections.abc import Mapping

from app.models.path_security import validate_model_path_against_allowed_bases


class ModelRegistry:
    def validate_entry(
        self,
        model: Mapping[str, object],
        allowed_base_directories: list[str] | None = None,
    ) -> tuple[bool, str | None]:
        model_path = str(model.get("model_path", ""))
        if model.get("model_format") in {"ollama", "openai"}:
            return True, None

        if allowed_base_directories is not None:
            valid, reason = validate_model_path_against_allowed_bases(model_path, allowed_base_directories)
            if not valid:
                return False, reason

        path = Path(model_path)
        if model.get("model_format") == "gguf":
            if path.is_file() and path.suffix.lower() == ".gguf":
                return True, None
            if path.is_dir() and any(path.rglob("*.gguf")):
                return True, None
            return False, "invalid_gguf_path"
        return True, None
