import asyncio
import json
import threading
from collections.abc import AsyncIterator
from typing import Any, cast

from app.models.backends.base import ModelBackend
from app.models.openai_integration import (
    extract_openai_runtime_capabilities,
    parse_openai_model_ref,
    request_openai_json,
    resolve_openai_api_key,
    stream_openai_lines,
)


class OpenAiBackend(ModelBackend):
    def __init__(self) -> None:
        self._loaded = False
        self._model_name = ""
        self._api_key = ""
        self._metadata: dict[str, object] = {}
        self._capabilities: dict[str, Any] = {
            "text_generation": True,
            "chat_completion": True,
            "streaming": True,
            "tool_calling": True,
            "structured_output": True,
        }

    def load(self, model_path: str, config: dict[str, Any]) -> None:
        metadata_raw = config.get("metadata")
        metadata = cast(dict[str, object], metadata_raw) if isinstance(metadata_raw, dict) else {}
        model_name = parse_openai_model_ref(model_path, metadata)
        api_key = resolve_openai_api_key(config.get("api_key"))
        if not model_name:
            raise RuntimeError("OpenAI model name is missing")
        if not api_key:
            raise RuntimeError("ChatGPT/OpenAI API-Key fehlt")

        models_payload = request_openai_json("GET", "/models", api_key=api_key, timeout=30.0)
        data = models_payload.get("data")
        if isinstance(data, list):
            available = {
                str(item.get("id") or "").strip()
                for item in cast(list[object], data)
                if isinstance(item, dict)
            }
            if available and model_name not in available:
                raise RuntimeError(f"OpenAI-Modell {model_name} ist fuer diesen API-Key nicht verfuegbar")

        self._loaded = True
        self._model_name = model_name
        self._api_key = api_key
        self._metadata = metadata
        self._capabilities = extract_openai_runtime_capabilities(metadata)

    def unload(self) -> None:
        self._loaded = False
        self._model_name = ""
        self._api_key = ""
        self._metadata = {}

    def generate(self, prompt: str, config: dict[str, Any]) -> str:
        if not self._loaded:
            raise RuntimeError("backend not loaded")
        payload = self._build_payload(prompt=prompt, config=config, stream=False)
        response = request_openai_json("POST", "/chat/completions", api_key=self._api_key, payload=payload, timeout=300.0)
        choices = response.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content.strip()
                    if isinstance(content, list):
                        parts: list[str] = []
                        for item in cast(list[object], content):
                            if isinstance(item, dict):
                                text = item.get("text")
                                if isinstance(text, str) and text:
                                    parts.append(text)
                        if parts:
                            return "".join(parts).strip()
        raise RuntimeError("OpenAI generation returned no text")

    async def stream(self, prompt: str, config: dict[str, Any]) -> AsyncIterator[str]:
        if not self._loaded:
            raise RuntimeError("backend not loaded")

        payload = self._build_payload(prompt=prompt, config=config, stream=True)
        cancel_event_raw = config.get("cancel_event")
        cancel_event = cancel_event_raw if isinstance(cancel_event_raw, threading.Event) else None

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        def _worker() -> None:
            response = None
            try:
                response = stream_openai_lines("/chat/completions", payload, api_key=self._api_key, timeout=900.0)
                for raw_line in response:
                    if cancel_event is not None and cancel_event.is_set():
                        break

                    line = raw_line.decode("utf-8", errors="ignore").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[len("data:") :].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk_raw = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(chunk_raw, dict):
                        continue
                    chunk = cast(dict[str, object], chunk_raw)
                    choices = chunk.get("choices")
                    if not isinstance(choices, list) or not choices:
                        continue
                    first = choices[0]
                    if not isinstance(first, dict):
                        continue
                    delta = first.get("delta")
                    if not isinstance(delta, dict):
                        continue
                    token = str(delta.get("content") or "")
                    if token:
                        loop.call_soon_threadsafe(queue.put_nowait, token)
            finally:
                if response is not None:
                    try:
                        response.close()
                    except Exception:
                        pass
                loop.call_soon_threadsafe(queue.put_nowait, None)

        threading.Thread(target=_worker, daemon=True).start()

        while True:
            token = await queue.get()
            if token is None:
                break
            yield token

    def health_check(self) -> bool:
        return self._loaded and bool(self._model_name) and bool(self._api_key)

    def get_capabilities(self) -> dict[str, Any]:
        return dict(self._capabilities)

    def _build_payload(self, *, prompt: str, config: dict[str, Any], stream: bool) -> dict[str, object]:
        temperature = float(config.get("temperature", 0.1))
        if not bool(config.get("do_sample", True)):
            temperature = 0.0
        payload: dict[str, object] = {
            "model": self._model_name,
            "messages": self._build_messages(prompt=prompt, config=config),
            "stream": stream,
            "temperature": temperature,
            "top_p": float(config.get("top_p", 0.95)),
            "max_tokens": int(config.get("max_new_tokens", 512)),
        }
        return payload

    def _build_messages(self, *, prompt: str, config: dict[str, Any]) -> list[dict[str, str]]:
        chat_messages_raw = config.get("chat_messages")
        if isinstance(chat_messages_raw, list):
            messages: list[dict[str, str]] = []
            for item in cast(list[object], chat_messages_raw):
                if not isinstance(item, dict):
                    continue
                item_map = cast(dict[str, object], item)
                role = str(item_map.get("role") or "").strip().lower()
                content = str(item_map.get("content") or "")
                if role not in {"system", "user", "assistant"}:
                    continue
                messages.append({"role": role, "content": content})
            if messages:
                return messages
        return [{"role": "user", "content": prompt}]