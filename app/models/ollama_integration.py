from __future__ import annotations

import json
import os
from typing import Any, TypedDict, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"


class OllamaScannedModel(TypedDict):
    name: str
    model_path: str
    backend: str
    model_format: str
    task_type: str
    model_family: str
    metadata: dict[str, object]


DEFAULT_OLLAMA_CLOUD_MODELS: tuple[dict[str, object], ...] = (
    {
        "model": "chatgpt-oss:latest",
        "family": "chatgpt",
        "capabilities": ["completion", "tools", "thinking"],
    },
    {
        "model": "llama3.3:latest",
        "family": "llama",
        "capabilities": ["completion", "tools"],
    },
    {
        "model": "phi4:latest",
        "family": "phi4",
        "capabilities": ["completion", "tools", "thinking"],
    },
    {
        "model": "qwen3:latest",
        "family": "qwen",
        "capabilities": ["completion", "tools", "thinking"],
    },
    {
        "model": "qwen2.5-coder:latest",
        "family": "qwen",
        "capabilities": ["completion", "tools"],
    },
    {
        "model": "mistral:latest",
        "family": "mistral",
        "capabilities": ["completion", "tools"],
    },
    {
        "model": "codestral:latest",
        "family": "mistral",
        "capabilities": ["completion", "tools"],
    },
    {
        "model": "gemma4:latest",
        "family": "gemma4",
        "capabilities": ["completion", "tools", "thinking"],
    },
    {
        "model": "gemma3:latest",
        "family": "gemma3",
        "capabilities": ["completion", "tools", "vision"],
    },
    {
        "model": "deepseek-r1:latest",
        "family": "deepseek",
        "capabilities": ["completion", "thinking"],
    },
    {
        "model": "deepseek-v3:latest",
        "family": "deepseek",
        "capabilities": ["completion", "tools"],
    },
    {
        "model": "llava:latest",
        "family": "llava",
        "capabilities": ["completion", "vision"],
    },
    {
        "model": "moondream:latest",
        "family": "moondream",
        "capabilities": ["completion", "vision"],
    },
    {
        "model": "command-r:latest",
        "family": "command-r",
        "capabilities": ["completion", "tools"],
    },
)


def normalize_ollama_host(raw_host: object | None = None) -> str:
    candidate = str(raw_host or os.getenv("OLLAMA_HOST") or DEFAULT_OLLAMA_HOST).strip()
    if not candidate:
        candidate = DEFAULT_OLLAMA_HOST
    if not candidate.startswith(("http://", "https://")):
        candidate = f"http://{candidate}"
    return candidate.rstrip("/")


def ollama_runtime_available() -> tuple[bool, str | None]:
    try:
        payload = get_ollama_tags_payload()
    except RuntimeError as exc:
        return False, str(exc)

    models = payload.get("models")
    if not isinstance(models, list):
        return False, "Ollama-Antwort enthaelt keine gueltige Modellsammlung."
    return True, None


def discover_ollama_models() -> list[OllamaScannedModel]:
    local_models = get_ollama_local_models_payload()
    discovered: list[OllamaScannedModel] = []
    discovered.extend(discover_ollama_local_models(local_models=local_models))
    discovered.extend(discover_ollama_cloud_models(local_models=local_models))
    return discovered


def get_ollama_tags_payload() -> dict[str, Any]:
    return _request_json("GET", "/api/tags")


def get_ollama_local_models_payload() -> list[dict[str, object]]:
    try:
        payload = get_ollama_tags_payload()
    except RuntimeError:
        return []
    models = payload.get("models")
    if not isinstance(models, list):
        return []
    normalized: list[dict[str, object]] = []
    for raw_item in cast(list[object], models):
        if isinstance(raw_item, dict):
            normalized.append(cast(dict[str, object], raw_item))
    return normalized


def is_ollama_model_installed(model_name: str, *, local_models: list[dict[str, object]] | None = None) -> bool:
    normalized_target = _normalize_model_name(model_name).lower()
    models = local_models if local_models is not None else get_ollama_local_models_payload()
    for item in models:
        candidate = _normalize_model_name(item.get("model") or item.get("name")).lower()
        if candidate == normalized_target:
            return True
    return False


def discover_ollama_local_models(*, local_models: list[dict[str, object]] | None = None) -> list[OllamaScannedModel]:
    models = local_models if local_models is not None else get_ollama_local_models_payload()

    discovered: list[OllamaScannedModel] = []
    for item in models:
        model_name = _normalize_model_name(item.get("model") or item.get("name"))
        if not model_name:
            continue

        details = _normalize_mapping(item.get("details"))
        capability_names = _normalize_capability_names(item.get("capabilities"))
        metadata = build_ollama_metadata(
            model_name=model_name,
            source_kind="ollama_local",
            source_label="Ollama Local",
            details=details,
            capability_names=capability_names,
            installed=True,
        )
        if not bool(metadata.get("supports_chat")):
            continue

        discovered.append(
            {
                "name": f"{model_name} (Ollama Local)",
                "model_path": f"ollama-local://{model_name}",
                "backend": "ollama",
                "model_format": "ollama",
                "task_type": str(metadata.get("task_type") or "text_generation"),
                "model_family": str(metadata.get("model_family") or "unknown"),
                "metadata": metadata,
            }
        )

    return discovered


def discover_ollama_cloud_models(*, local_models: list[dict[str, object]] | None = None) -> list[OllamaScannedModel]:
    discovered: list[OllamaScannedModel] = []
    installed_names = {
        _normalize_model_name(item.get("model") or item.get("name")).lower()
        for item in (local_models if local_models is not None else get_ollama_local_models_payload())
    }
    for item in DEFAULT_OLLAMA_CLOUD_MODELS:
        model_name = _normalize_model_name(item.get("model"))
        if not model_name:
            continue

        details = {
            "family": item.get("family"),
            "families": [item.get("family")] if item.get("family") else [],
        }
        capability_names = _normalize_capability_names(item.get("capabilities"))
        metadata = build_ollama_metadata(
            model_name=model_name,
            source_kind="ollama_cloud",
            source_label="Ollama Cloud",
            details=details,
            capability_names=capability_names,
            installed=model_name.lower() in installed_names,
        )
        if not bool(metadata.get("supports_chat")):
            continue

        discovered.append(
            {
                "name": f"{model_name} (Ollama Cloud)",
                "model_path": f"ollama-cloud://{model_name}",
                "backend": "ollama",
                "model_format": "ollama",
                "task_type": str(metadata.get("task_type") or "text_generation"),
                "model_family": str(metadata.get("model_family") or "unknown"),
                "metadata": metadata,
            }
        )
    return discovered


def build_ollama_metadata(
    *,
    model_name: str,
    source_kind: str,
    source_label: str,
    details: dict[str, object],
    capability_names: set[str],
    installed: bool,
) -> dict[str, object]:
    task_type = _infer_task_type(model_name=model_name, capability_names=capability_names)
    supports_chat = task_type in {"text_generation", "vision_text_generation"}
    supports_embeddings = task_type in {"embedding", "feature_extraction"}
    supports_vision = task_type == "vision_text_generation"
    model_family = _infer_family(model_name=model_name, details=details)

    metadata: dict[str, object] = {
        "model_format": "ollama",
        "model_family": model_family,
        "task_type": task_type,
        "backend": "ollama",
        "loadable": True,
        "supports_inference": supports_chat,
        "supports_training": False,
        "supports_peft_training": False,
        "supports_4bit": False,
        "supports_chat": supports_chat,
        "supports_embeddings": supports_embeddings,
        "supports_reranking": False,
        "supports_vision": supports_vision,
        "supports_audio": False,
        "reason_unavailable": None,
        "relevance": "relevant",
        "group": _group_for_task(task_type),
        "source_kind": source_kind,
        "source_label": source_label,
        "ollama_host": normalize_ollama_host(),
        "ollama_model": model_name,
        "ollama_installed": installed,
        "ollama_capabilities": sorted(capability_names),
        "tool_calling": "tools" in capability_names,
        "structured_output": "json" in capability_names or "structured" in capability_names,
        "reasoning": "thinking" in capability_names,
    }

    context_length = details.get("context_length")
    if isinstance(context_length, int):
        metadata["context_length"] = context_length

    embedding_length = details.get("embedding_length")
    if isinstance(embedding_length, int):
        metadata["embedding_length"] = embedding_length

    parameter_size = details.get("parameter_size")
    if isinstance(parameter_size, str) and parameter_size.strip():
        metadata["parameter_size"] = parameter_size.strip()

    quantization = details.get("quantization_level")
    if isinstance(quantization, str) and quantization.strip():
        metadata["quantization_level"] = quantization.strip()

    return metadata


def extract_ollama_runtime_capabilities(metadata: dict[str, object]) -> dict[str, Any]:
    capability_names = _normalize_capability_names(metadata.get("ollama_capabilities"))
    task_type = str(metadata.get("task_type") or "text_generation")
    return {
        "text_generation": task_type in {"text_generation", "vision_text_generation"},
        "chat_completion": task_type in {"text_generation", "vision_text_generation"},
        "streaming": True,
        "embeddings": task_type in {"embedding", "feature_extraction"},
        "vision": task_type == "vision_text_generation" or "vision" in capability_names,
        "audio": False,
        "tool_calling": "tools" in capability_names,
        "structured_output": "json" in capability_names or "structured" in capability_names,
        "reasoning": "thinking" in capability_names,
        "host": str(metadata.get("ollama_host") or normalize_ollama_host()),
        "source_kind": str(metadata.get("source_kind") or "ollama_local"),
        "source_label": str(metadata.get("source_label") or "Ollama"),
        "model": str(metadata.get("ollama_model") or ""),
        "context_length": metadata.get("context_length"),
        "parameter_size": metadata.get("parameter_size"),
        "quantization_level": metadata.get("quantization_level"),
        "ollama_installed": bool(metadata.get("ollama_installed")),
        "ollama_capabilities": sorted(capability_names),
    }


def parse_ollama_model_ref(model_path: str, metadata: dict[str, object] | None = None) -> tuple[str, str]:
    metadata_map = metadata or {}
    model_name = _normalize_model_name(metadata_map.get("ollama_model"))
    source_kind = str(metadata_map.get("source_kind") or "").strip() or _source_kind_from_path(model_path)
    if model_name:
        return model_name, source_kind or "ollama_local"

    raw = str(model_path or "").strip()
    if raw.startswith("ollama-local://"):
        return raw[len("ollama-local://") :].strip(), "ollama_local"
    if raw.startswith("ollama-cloud://"):
        return raw[len("ollama-cloud://") :].strip(), "ollama_cloud"
    return raw, source_kind or "ollama_local"


def request_ollama_json(method: str, path: str, payload: dict[str, object] | None = None, *, timeout: float = 30.0) -> dict[str, Any]:
    return _request_json(method, path, payload=payload, timeout=timeout)


def stream_ollama_lines(path: str, payload: dict[str, object], *, timeout: float = 300.0):
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url=f"{normalize_ollama_host()}{path}",
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/x-ndjson"},
        method="POST",
    )

    try:
        response = urlopen(request, timeout=timeout)
    except HTTPError as exc:
        message = exc.read().decode("utf-8", errors="ignore").strip()
        raise RuntimeError(message or f"Ollama HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"Ollama ist nicht erreichbar: {exc.reason}") from exc

    return response


def _request_json(method: str, path: str, payload: dict[str, object] | None = None, timeout: float = 15.0) -> dict[str, Any]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(
        url=f"{normalize_ollama_host()}{path}",
        data=body,
        headers=headers,
        method=method.upper(),
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="ignore")
    except HTTPError as exc:
        message = exc.read().decode("utf-8", errors="ignore").strip()
        raise RuntimeError(message or f"Ollama HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"Ollama ist nicht erreichbar: {exc.reason}") from exc

    if not raw.strip():
        return {}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Ollama lieferte kein gueltiges JSON.") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("Ollama lieferte ein unerwartetes Antwortformat.")
    return cast(dict[str, Any], parsed)


def _normalize_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in cast(dict[object, object], value).items()}


def _normalize_capability_names(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item).strip().lower() for item in cast(list[object], value) if str(item).strip()}


def _normalize_model_name(value: object) -> str:
    return str(value or "").strip()


def _infer_task_type(*, model_name: str, capability_names: set[str]) -> str:
    lowered = model_name.lower()
    if "embedding" in capability_names or "embed" in lowered:
        return "embedding"
    if "vision" in capability_names or any(marker in lowered for marker in ("vision", "vl", "llava")):
        return "vision_text_generation"
    return "text_generation"


def _infer_family(*, model_name: str, details: dict[str, object]) -> str:
    family = str(details.get("family") or "").strip().lower()
    if family:
        return family

    families = details.get("families")
    if isinstance(families, list):
        for item in cast(list[object], families):
            candidate = str(item).strip().lower()
            if candidate:
                return candidate

    lowered = model_name.lower()
    for marker in ("llama", "qwen", "mistral", "gemma", "phi"):
        if marker in lowered:
            return marker
    return "unknown"


def _group_for_task(task_type: str) -> str:
    if task_type == "vision_text_generation":
        return "Multimodal"
    if task_type in {"embedding", "feature_extraction"}:
        return "Embeddings"
    return "Text / Chat"


def _source_kind_from_path(model_path: str) -> str:
    raw = str(model_path or "").strip().lower()
    if raw.startswith("ollama-cloud://"):
        return "ollama_cloud"
    if raw.startswith("ollama-local://"):
        return "ollama_local"
    return "ollama_local"