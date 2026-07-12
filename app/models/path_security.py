from __future__ import annotations

import os
from pathlib import Path, PurePath
import re


_URL_SCHEME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")


def _allowed_base_directories() -> list[str]:
    configured = os.getenv("MODEL_ALLOWED_BASE_DIRS", "").strip()
    if configured:
        entries = [item.strip() for item in configured.split(os.pathsep) if item.strip()]
        return [str(Path(item).expanduser().resolve(strict=False)) for item in entries]
    return [
        str((Path.cwd() / "model-directories").resolve(strict=False)),
        str(Path(r"F:\KI\models").resolve(strict=False)),
    ]


def _is_safe_local_path_input(raw: str) -> bool:
    if not raw or "\x00" in raw:
        return False
    if _URL_SCHEME_PATTERN.match(raw):
        return False
    return True


def normalize_base_directories(raw_directories: object) -> list[str]:
    if not isinstance(raw_directories, list):
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for entry in raw_directories:
        if not isinstance(entry, str):
            continue
        text = entry.strip()
        if not _is_safe_local_path_input(text):
            continue
        if has_path_traversal(text):
            continue
        resolved = str(Path(text).expanduser().resolve(strict=False))
        if resolved in seen:
            continue
        seen.add(resolved)
        normalized.append(resolved)
    return normalized


def has_path_traversal(raw_path: str) -> bool:
    parts = PurePath(raw_path).parts
    return any(part == ".." for part in parts)


def is_within_allowed_bases(path: Path, allowed_base_directories: list[str]) -> bool:
    if not allowed_base_directories:
        return False

    candidate = path.resolve(strict=False)
    for base_raw in allowed_base_directories:
        base = Path(base_raw).expanduser().resolve(strict=False)
        try:
            candidate.relative_to(base)
            return True
        except ValueError:
            continue
    return False


def validate_model_path_against_allowed_bases(model_path: str, allowed_base_directories: list[str]) -> tuple[bool, str | None]:
    raw = str(model_path).strip()
    if not _is_safe_local_path_input(raw):
        return False, "path_empty"

    if has_path_traversal(raw):
        return False, "path_traversal"

    path = Path(raw)
    if not path.exists():
        return False, "path_missing"

    if not is_within_allowed_bases(path, allowed_base_directories):
        return False, "outside_allowed_base_directories"

    return True, None


def validate_runtime_model_paths(
    *,
    model_path: str,
    model_format: str,
    metadata: dict[str, object],
    allowed_base_directories: list[str],
) -> tuple[bool, str | None]:
    if model_format != "peft_adapter":
        return validate_model_path_against_allowed_bases(model_path, allowed_base_directories)

    base_model_path = str(metadata.get("base_model_path") or "").strip()
    adapter_path = str(metadata.get("adapter_path") or model_path or "").strip()
    if not adapter_path or not Path(adapter_path).exists():
        return False, "adapter_path_missing"
    if not base_model_path:
        return False, "base_model_path_missing"
    return validate_model_path_against_allowed_bases(base_model_path, allowed_base_directories)
