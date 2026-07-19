import asyncio
import json
import threading
from collections.abc import AsyncIterator
from typing import Any, cast

from app.models.backends.base import ModelBackend
from app.models.ollama_integration import (
	extract_ollama_runtime_capabilities,
	parse_ollama_model_ref,
	request_ollama_json,
	stream_ollama_lines,
)


class OllamaBackend(ModelBackend):
	def __init__(self) -> None:
		self._loaded = False
		self._model_name = ""
		self._metadata: dict[str, object] = {}
		self._capabilities: dict[str, Any] = {
			"text_generation": True,
			"chat_completion": True,
			"streaming": True,
			"embeddings": False,
			"vision": False,
			"audio": False,
			"tool_calling": False,
			"structured_output": False,
			"source_label": "Ollama",
		}

	def load(self, model_path: str, config: dict[str, Any]) -> None:
		metadata_raw = config.get("metadata")
		metadata = cast(dict[str, object], metadata_raw) if isinstance(metadata_raw, dict) else {}
		model_name, source_kind = parse_ollama_model_ref(model_path, metadata)
		if not model_name:
			raise RuntimeError("Ollama model name is missing")

		if source_kind == "ollama_cloud":
			request_ollama_json("POST", "/api/pull", {"model": model_name, "stream": False}, timeout=900.0)

		show_payload = request_ollama_json("POST", "/api/show", {"model": model_name}, timeout=60.0)

		capability_names = show_payload.get("capabilities")
		if isinstance(capability_names, list):
			metadata["ollama_capabilities"] = capability_names
		details = show_payload.get("details")
		if isinstance(details, dict):
			for key, value in cast(dict[str, object], details).items():
				if key in {"context_length", "embedding_length", "parameter_size", "quantization_level", "family", "families"}:
					metadata[key] = value

		metadata.setdefault("ollama_model", model_name)
		metadata.setdefault("source_kind", source_kind)
		metadata.setdefault("source_label", "Ollama Cloud" if source_kind == "ollama_cloud" else "Ollama Local")

		self._metadata = metadata
		self._model_name = model_name
		self._capabilities = extract_ollama_runtime_capabilities(metadata)
		self._loaded = True

	def unload(self) -> None:
		self._loaded = False
		self._model_name = ""
		self._metadata = {}

	def generate(self, prompt: str, config: dict[str, Any]) -> str:
		if not self._loaded:
			raise RuntimeError("backend not loaded")

		payload = self._build_payload(prompt=prompt, config=config, stream=False)
		response = request_ollama_json("POST", "/api/chat", payload, timeout=300.0)
		message = response.get("message")
		if isinstance(message, dict):
			content = str(cast(dict[str, object], message).get("content") or "")
			if content:
				return content.strip()
		return str(response.get("response") or "").strip()

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
				response = stream_ollama_lines("/api/chat", payload, timeout=900.0)
				for raw_line in response:
					if cancel_event is not None and cancel_event.is_set():
						break

					line = raw_line.decode("utf-8", errors="ignore").strip()
					if not line:
						continue

					try:
						chunk_raw = json.loads(line)
					except json.JSONDecodeError:
						continue
					if not isinstance(chunk_raw, dict):
						continue
					chunk = cast(dict[str, object], chunk_raw)

					message = chunk.get("message")
					token = ""
					if isinstance(message, dict):
						token = str(cast(dict[str, object], message).get("content") or "")
					if not token:
						token = str(chunk.get("response") or "")
					if token:
						loop.call_soon_threadsafe(queue.put_nowait, token)

					if bool(chunk.get("done")):
						break
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
		if not self._loaded or not self._model_name:
			return False
		try:
			request_ollama_json("POST", "/api/show", {"model": self._model_name}, timeout=10.0)
		except Exception:
			return False
		return True

	def get_capabilities(self) -> dict[str, Any]:
		return dict(self._capabilities)

	def _build_payload(self, *, prompt: str, config: dict[str, Any], stream: bool) -> dict[str, object]:
		messages = self._build_messages(prompt=prompt, config=config)
		temperature = float(config.get("temperature", 0.1))
		if not bool(config.get("do_sample", True)):
			temperature = 0.0

		options: dict[str, object] = {
			"num_predict": int(config.get("max_new_tokens", 512)),
			"temperature": temperature,
			"top_k": int(config.get("top_k", 6)),
			"top_p": float(config.get("top_p", 0.95)),
			"repeat_penalty": float(config.get("repetition_penalty", 1.05)),
			"seed": int(config.get("seed", 42)),
		}

		stop_sequences = config.get("stop") or config.get("stop_sequences")
		if isinstance(stop_sequences, list):
			normalized_stop = [
				str(item).strip()
				for item in cast(list[object], stop_sequences)
				if str(item).strip()
			]
			if normalized_stop:
				options["stop"] = normalized_stop

		context_length = self._metadata.get("context_length")
		if isinstance(context_length, int) and context_length > 0:
			options["num_ctx"] = context_length

		return {
			"model": self._model_name,
			"messages": messages,
			"stream": stream,
			"options": options,
		}

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
				if role not in {"system", "user", "assistant", "tool"}:
					continue
				messages.append({"role": role, "content": content})
			if messages:
				return messages
		return [{"role": "user", "content": prompt}]
