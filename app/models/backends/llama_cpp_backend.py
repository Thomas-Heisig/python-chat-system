import asyncio
import os
from pathlib import Path
import threading
from collections.abc import AsyncIterator
from typing import Any, cast

from app.models.backends.base import ModelBackend


class LlamaCppBackend(ModelBackend):
    def __init__(self) -> None:
        self._loaded = False
        self._model_path: str | None = None
        self._device: str = "cpu"
        self._llm: Any | None = None
        self._lock = threading.Lock()

    def load(self, model_path: str, config: dict[str, Any]) -> None:
        resolved_model_path = self._resolve_model_file(model_path)

        try:
            from llama_cpp import Llama
        except Exception as exc:  # pragma: no cover - depends on local runtime package
            raise RuntimeError(
                "llama-cpp-python is not installed. Install dependencies and restart the backend."
            ) from exc

        requested_device = str(config.get("device", "cpu")).lower()
        self._device = "cuda" if requested_device == "cuda" else "cpu"

        n_ctx = int(config.get("n_ctx", 4096))
        n_threads = int(config.get("n_threads", max(1, (os.cpu_count() or 4) - 1)))

        # CPU mode disables GPU layers; CUDA mode keeps the manager-provided defaults.
        n_gpu_layers_default = 0 if self._device == "cpu" else -1
        n_gpu_layers = int(config.get("n_gpu_layers", n_gpu_layers_default))

        self._llm = Llama(
            model_path=resolved_model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,
            verbose=False,
        )

        self._model_path = resolved_model_path
        self._loaded = True

    def _resolve_model_file(self, model_path: str) -> str:
        candidate = Path(model_path)
        if candidate.is_file():
            return str(candidate)

        if candidate.is_dir():
            gguf_files = [item for item in candidate.rglob("*.gguf") if item.is_file()]
            if gguf_files:
                # Prefer actual model weights over multimodal projector files (for example mmproj*.gguf).
                non_projector_files = [
                    item
                    for item in gguf_files
                    if "mmproj" not in item.name.lower() and "projector" not in item.name.lower()
                ]

                preferred_files = non_projector_files if non_projector_files else gguf_files
                selected = sorted(
                    preferred_files,
                    key=lambda item: (
                        -item.stat().st_size,
                        len(item.relative_to(candidate).parts),
                        item.name.lower(),
                    ),
                )[0]
                return str(selected)

        raise RuntimeError(f"Model file not found: {model_path}")

    def unload(self) -> None:
        self._llm = None
        self._loaded = False
        self._model_path = None
        self._device = "cpu"

    def generate(self, prompt: str, config: dict[str, Any]) -> str:
        if not self._loaded:
            raise RuntimeError("backend not loaded")
        if self._llm is None:
            raise RuntimeError("llama backend is not initialized")
        llm = self._llm

        max_tokens = int(config.get("max_new_tokens", 512))
        temperature = float(config.get("temperature", 0.1))
        top_p = float(config.get("top_p", 0.95))
        top_k = int(config.get("top_k", 6))
        repetition_penalty = float(config.get("repetition_penalty", 1.05))
        stop_sequences = config.get("stop", ["<end_of_turn>", "<eos>"])
        seed = int(config.get("seed", 42))
        do_sample = bool(config.get("do_sample", True))
        chat_messages_raw = config.get("chat_messages")

        if not do_sample:
            temperature = 0.0

        chat_messages: list[dict[str, str]] = []
        if isinstance(chat_messages_raw, list):
            for item in cast(list[object], chat_messages_raw):
                if not isinstance(item, dict):
                    continue
                item_map = cast(dict[str, object], item)
                role = str(item_map.get("role", "")).strip().lower()
                content = str(item_map.get("content", ""))
                if role not in {"system", "user", "assistant"}:
                    continue
                chat_messages.append({"role": role, "content": content})

        with self._lock:
            use_chat_completion = bool(chat_messages and hasattr(llm, "create_chat_completion"))
            result: Any | None = None
            if use_chat_completion:
                try:
                    result = llm.create_chat_completion(
                        messages=chat_messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        top_k=top_k,
                        repeat_penalty=repetition_penalty,
                        stop=stop_sequences,
                        seed=seed,
                        stream=False,
                    )
                except ValueError as exc:
                    if "System role not supported" not in str(exc):
                        raise
                    use_chat_completion = False

            if not use_chat_completion:
                result = llm.create_completion(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    repeat_penalty=repetition_penalty,
                    stop=stop_sequences,
                    seed=seed,
                    echo=False,
                    stream=False,
                )

        if result is None:
            raise RuntimeError("llama generation returned no result")

        text = (
            result.get("choices", [{}])[0].get("message", {}).get("content")
            if use_chat_completion
            else result.get("choices", [{}])[0].get("text")
        )
        return str(text).strip()

    async def stream(self, prompt: str, config: dict[str, Any]) -> AsyncIterator[str]:
        if not self._loaded:
            raise RuntimeError("backend not loaded")
        if self._llm is None:
            raise RuntimeError("llama backend is not initialized")
        llm = self._llm

        max_tokens = int(config.get("max_new_tokens", 512))
        temperature = float(config.get("temperature", 0.1))
        top_p = float(config.get("top_p", 0.95))
        top_k = int(config.get("top_k", 6))
        repetition_penalty = float(config.get("repetition_penalty", 1.05))
        stop_sequences = config.get("stop", ["<end_of_turn>", "<eos>"])
        seed = int(config.get("seed", 42))
        do_sample = bool(config.get("do_sample", True))
        cancel_event_raw = config.get("cancel_event")
        cancel_event = cancel_event_raw if isinstance(cancel_event_raw, threading.Event) else None
        chat_messages_raw = config.get("chat_messages")

        if not do_sample:
            temperature = 0.0

        chat_messages: list[dict[str, str]] = []
        if isinstance(chat_messages_raw, list):
            for item in cast(list[object], chat_messages_raw):
                if not isinstance(item, dict):
                    continue
                item_map = cast(dict[str, object], item)
                role = str(item_map.get("role", "")).strip().lower()
                content = str(item_map.get("content", ""))
                if role not in {"system", "user", "assistant"}:
                    continue
                chat_messages.append({"role": role, "content": content})

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        def _worker() -> None:
            try:
                with self._lock:
                    use_chat_completion = bool(chat_messages and hasattr(llm, "create_chat_completion"))
                    iterator: Any | None = None
                    if use_chat_completion:
                        try:
                            iterator = llm.create_chat_completion(
                                messages=chat_messages,
                                max_tokens=max_tokens,
                                temperature=temperature,
                                top_p=top_p,
                                top_k=top_k,
                                repeat_penalty=repetition_penalty,
                                stop=stop_sequences,
                                seed=seed,
                                stream=True,
                            )
                        except ValueError as exc:
                            if "System role not supported" not in str(exc):
                                raise
                            use_chat_completion = False

                    if not use_chat_completion:
                        iterator = llm.create_completion(
                            prompt=prompt,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            top_p=top_p,
                            top_k=top_k,
                            repeat_penalty=repetition_penalty,
                            stop=stop_sequences,
                            seed=seed,
                            echo=False,
                            stream=True,
                        )
                    if iterator is None:
                        raise RuntimeError("llama stream returned no iterator")
                    for chunk in iterator:
                        if cancel_event is not None and cancel_event.is_set():
                            close_method = getattr(iterator, "close", None)
                            if callable(close_method):
                                try:
                                    close_method()
                                except Exception:
                                    pass
                            break
                        if use_chat_completion:
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            token = str(delta.get("content", ""))
                        else:
                            token = str(chunk.get("choices", [{}])[0].get("text", ""))
                        if token:
                            loop.call_soon_threadsafe(queue.put_nowait, token)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        threading.Thread(target=_worker, daemon=True).start()

        while True:
            token = await queue.get()
            if token is None:
                break
            yield token

    def health_check(self) -> bool:
        return self._loaded and self._llm is not None

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "text_generation": True,
            "chat_completion": True,
            "streaming": True,
            "embeddings": False,
            "vision": False,
            "audio": False,
            "tool_calling": False,
            "structured_output": False,
            "device": self._device,
        }
