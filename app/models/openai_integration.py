from __future__ import annotations

import json
import os
from typing import Any, TypedDict, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"


class OpenAiScannedModel(TypedDict):
    name: str
    model_path: str
    backend: str
    model_format: str
    task_type: str
    model_family: str
    metadata: dict[str, object]


DEFAULT_OPENAI_MODELS: tuple[dict[str, object], ...] = (
    {
        "model": "gpt-4.1-mini",
        "family": "chatgpt",
        "capabilities": ["completion", "tools"],
    },
    {
        "model": "gpt-4o-mini",
        "family": "chatgpt",
        "capabilities": ["completion", "tools", "vision"],
    },
    {
        "model": "o4-mini",
        "family": "chatgpt",
        "capabilities": ["completion", "tools", "thinking"],
    },
)


def resolve_openai_api_key(explicit_key: object | None = None) -> str:
    candidate = str(explicit_key or os.getenv("CHATGPT_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    return candidate


def normalize_openai_base_url(raw_url: object | None = None) -> str:
    candidate = str(raw_url or os.getenv("OPENAI_BASE_URL") or DEFAULT_OPENAI_BASE_URL).strip()
    if not candidate:
        candidate = DEFAULT_OPENAI_BASE_URL
    return candidate.rstrip("/")


def openai_runtime_available(api_key: object | None = None) -> tuple[bool, str | None]:
    resolved_key = resolve_openai_api_key(api_key)
    if not resolved_key:
        return False, "ChatGPT/OpenAI API-Key fehlt."
    return True, None


def discover_openai_models(api_key: object | None = None) -> list[OpenAiScannedModel]:
    resolved_key = resolve_openai_api_key(api_key)
    if not resolved_key:
        return []

    discovered: list[OpenAiScannedModel] = []
    for item in DEFAULT_OPENAI_MODELS:
        model_name = str(item.get("model") or "").strip()
        if not model_name:
            continue
        capability_names = _normalize_capability_names(item.get("capabilities"))
        metadata = build_openai_metadata(
            model_name=model_name,
            family=str(item.get("family") or "chatgpt"),
            capability_names=capability_names,
        )
        discovered.append(
            {
                "name": f"{model_name} (ChatGPT API)",
                "model_path": f"openai://{model_name}",
                "backend": "openai",
                "model_format": "openai",
                "task_type": str(metadata.get("task_type") or "text_generation"),
                "model_family": str(metadata.get("model_family") or "chatgpt"),
                "metadata": metadata,
            }
        )
    return discovered


def build_openai_metadata(*, model_name: str, family: str, capability_names: set[str]) -> dict[str, object]:
    supports_vision = "vision" in capability_names
    return {
        "model_format": "openai",
        "model_family": family,
        "task_type": "vision_text_generation" if supports_vision else "text_generation",
        "backend": "openai",
        "loadable": True,
        "supports_inference": True,
        "supports_training": False,
        "supports_peft_training": False,
        "supports_4bit": False,
        "supports_chat": True,
        "supports_embeddings": False,
        "supports_reranking": False,
        "supports_vision": supports_vision,
        "supports_audio": False,
        "reason_unavailable": None,
        "relevance": "relevant",
        "group": "Text / Chat",
        "source_kind": "remote",
        "source_label": "ChatGPT API",
        "provider": "openai",
        "openai_model": model_name,
        "openai_base_url": normalize_openai_base_url(),
        "tool_calling": "tools" in capability_names,
        "structured_output": True,
        "reasoning": "thinking" in capability_names,
        "openai_capabilities": sorted(capability_names),
    }


def extract_openai_runtime_capabilities(metadata: dict[str, object]) -> dict[str, Any]:
    capability_names = _normalize_capability_names(metadata.get("openai_capabilities"))
    return {
        "text_generation": True,
        "chat_completion": True,
        "streaming": True,
        "embeddings": False,
        "vision": "vision" in capability_names,
        "audio": False,
        "tool_calling": "tools" in capability_names,
        "structured_output": True,
        "reasoning": "thinking" in capability_names,
        "provider": "openai",
        "source_label": str(metadata.get("source_label") or "ChatGPT API"),
        "model": str(metadata.get("openai_model") or ""),
    }


def parse_openai_model_ref(model_path: str, metadata: dict[str, object] | None = None) -> str:
    metadata_map = metadata or {}
    model_name = str(metadata_map.get("openai_model") or "").strip()
    if model_name:
        return model_name
    raw = str(model_path or "").strip()
    if raw.startswith("openai://"):
        return raw[len("openai://") :].strip()
    return raw


def request_openai_json(
    method: str,
    path: str,
    *,
    api_key: str,
    payload: dict[str, object] | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    body = None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(
        url=f"{normalize_openai_base_url()}{path}",
        data=body,
        headers=headers,
        method=method.upper(),
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="ignore")
    except HTTPError as exc:
        message = exc.read().decode("utf-8", errors="ignore").strip()
        raise RuntimeError(message or f"OpenAI HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"OpenAI ist nicht erreichbar: {exc.reason}") from exc

    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("OpenAI lieferte kein gueltiges JSON.") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("OpenAI lieferte ein unerwartetes Antwortformat.")
    return cast(dict[str, Any], parsed)


def stream_openai_lines(path: str, payload: dict[str, object], *, api_key: str, timeout: float = 300.0):
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url=f"{normalize_openai_base_url()}{path}",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )
    try:
        response = urlopen(request, timeout=timeout)
    except HTTPError as exc:
        message = exc.read().decode("utf-8", errors="ignore").strip()
        raise RuntimeError(message or f"OpenAI HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"OpenAI ist nicht erreichbar: {exc.reason}") from exc
    return response


def _normalize_capability_names(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item).strip().lower() for item in cast(list[object], value) if str(item).strip()}