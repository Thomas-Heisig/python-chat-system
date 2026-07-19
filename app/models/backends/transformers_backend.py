from __future__ import annotations

import asyncio
import base64
import io
import json
from pathlib import Path
import threading
from collections.abc import AsyncIterator
from typing import Any, cast

from app.models.backends.base import ModelBackend


class TransformersBackend(ModelBackend):
	def __init__(self) -> None:
		self._loaded = False
		self._device: str = "cpu"
		self._task_type: str = "text_generation"
		self._tokenizer: Any | None = None
		self._processor: Any | None = None
		self._model: Any | None = None
		self._lock = threading.Lock()

	def load(self, model_path: str, config: dict[str, Any]) -> None:
		metadata_raw = config.get("metadata")
		metadata: dict[str, Any] = {}
		if isinstance(metadata_raw, dict):
			metadata_map = cast(dict[object, object], metadata_raw)
			for key, value in metadata_map.items():
				metadata[str(key)] = value
		task_type = str(metadata.get("task_type") or "text_generation")
		try:
			import torch
			import transformers
		except Exception as exc:  # pragma: no cover - depends on local runtime package
			raise RuntimeError("transformers backend dependencies are not installed") from exc

		auto_tokenizer = getattr(transformers, "AutoTokenizer", None)
		auto_model_for_causal_lm = getattr(transformers, "AutoModelForCausalLM", None)
		auto_processor = getattr(transformers, "AutoProcessor", None)

		if auto_tokenizer is None or auto_model_for_causal_lm is None:
			raise RuntimeError(
				f"transformers backend is incomplete in version {getattr(transformers, '__version__', 'unknown')}: "
				"AutoTokenizer/AutoModelForCausalLM are missing"
			)

		prefer_gpu = bool(config.get("prefer_gpu", True))
		cuda_available = bool(torch.cuda.is_available())
		self._device = "cuda" if prefer_gpu and cuda_available else "cpu"

		local_files_only = bool(config.get("local_files_only", True))
		if task_type == "vision_text_generation":
			if auto_processor is None:
				raise RuntimeError(
					f"transformers vision loader failed: AutoProcessor is missing "
					f"(transformers={getattr(transformers, '__version__', 'unknown')})"
				)

			processor = auto_processor.from_pretrained(model_path, local_files_only=local_files_only)
			vision_loader_class_names = [
				"AutoModelForVision2Seq",
				"AutoModelForImageTextToText",
				"AutoModel",
			]
			vision_loader_classes: list[Any] = []
			for class_name in vision_loader_class_names:
				loader_cls = getattr(transformers, class_name, None)
				if loader_cls is not None:
					vision_loader_classes.append(loader_cls)

			if not vision_loader_classes:
				raise RuntimeError(
					f"model.vision_loader_failed: no compatible auto-model class found "
					f"(transformers={getattr(transformers, '__version__', 'unknown')})"
				)

			model: Any | None = None
			last_loader_error: Exception | None = None
			for loader_cls in vision_loader_classes:
				try:
					model = loader_cls.from_pretrained(model_path, local_files_only=local_files_only)
					break
				except Exception as exc:
					last_loader_error = exc

			if model is None:
				architectures: list[str] = []
				try:
					config_path = Path(model_path) / "config.json"
					if config_path.exists():
						payload_raw = json.loads(config_path.read_text(encoding="utf-8"))
						if isinstance(payload_raw, dict):
							payload = cast(dict[str, object], payload_raw)
							raw_arch: object = payload.get("architectures")
							if isinstance(raw_arch, list):
								architectures = [str(item) for item in cast(list[object], raw_arch)]
				except Exception:
					architectures = []

				raise RuntimeError(
					"model.vision_loader_failed: recognized vision architecture is not supported by installed transformers "
					f"(transformers={getattr(transformers, '__version__', 'unknown')}, "
					f"architectures={architectures}, last_error={last_loader_error})"
				)
			if model is None:
				raise RuntimeError("model.load_failed")
			loaded_model = model
			if self._device == "cuda":
				loaded_model = loaded_model.to("cuda")
			model = loaded_model
			self._processor = processor
			self._tokenizer = None
		else:
			try:
				tokenizer = auto_tokenizer.from_pretrained(model_path, local_files_only=local_files_only)
			except Exception as exc:
				tokenizer = self._load_tokenizer_fallback(
					model_path=model_path,
					local_files_only=local_files_only,
					original_error=exc,
				)
			text_model = auto_model_for_causal_lm.from_pretrained(model_path, local_files_only=local_files_only)

			if self._device == "cuda":
				text_model = text_model.to("cuda")
			model = text_model

			self._tokenizer = tokenizer
			self._processor = None

		self._task_type = task_type
		self._model = model
		self._loaded = True

	def _load_tokenizer_fallback(self, model_path: str, local_files_only: bool, original_error: Exception) -> Any:
		try:
			from transformers import PreTrainedTokenizerFast

			tokenizer_json_path = Path(model_path) / "tokenizer.json"
			if not tokenizer_json_path.exists():
				raise RuntimeError(str(original_error))

			tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(tokenizer_json_path))
			tokenizer_config_path = Path(model_path) / "tokenizer_config.json"
			if tokenizer_config_path.exists():
				try:
					tokenizer_config_raw = json.loads(tokenizer_config_path.read_text(encoding="utf-8"))
					if isinstance(tokenizer_config_raw, dict):
						tokenizer_config = cast(dict[str, Any], tokenizer_config_raw)
						for token_attr in ("bos_token", "eos_token", "unk_token", "pad_token"):
							token_value = tokenizer_config.get(token_attr)
							if isinstance(token_value, str) and token_value:
								setattr(tokenizer, token_attr, token_value)
				except Exception:
					pass

			return tokenizer
		except Exception as fallback_exc:
			raise RuntimeError(str(original_error)) from fallback_exc

	def unload(self) -> None:
		self._tokenizer = None
		self._processor = None
		self._model = None
		self._loaded = False
		self._device = "cpu"
		self._task_type = "text_generation"

	def _decode_images(self, image_inputs: list[dict[str, Any]]) -> list[Any]:
		try:
			from PIL import Image
		except Exception as exc:
			raise RuntimeError("pillow is required for vision inputs") from exc

		images: list[Any] = []
		for item in image_inputs:
			encoded = str(item.get("data_base64") or "").strip()
			if not encoded:
				continue
			try:
				raw = base64.b64decode(encoded, validate=True)
			except Exception as exc:
				raise RuntimeError("invalid base64 image payload") from exc
			image = Image.open(io.BytesIO(raw)).convert("RGB")
			images.append(image)
		return images

	def generate(self, prompt: str, config: dict[str, Any]) -> str:
		if not self._loaded or self._model is None:
			raise RuntimeError("backend not loaded")

		max_new_tokens = int(config.get("max_new_tokens", 256))
		temperature = float(config.get("temperature", 0.1))
		top_p = float(config.get("top_p", 0.95))
		top_k = int(config.get("top_k", 6))
		repetition_penalty = float(config.get("repetition_penalty", 1.05))
		do_sample = bool(config.get("do_sample", True))

		if self._task_type == "vision_text_generation":
			if self._processor is None:
				raise RuntimeError("vision processor not loaded")

			image_inputs_raw = config.get("image_inputs")
			image_inputs: list[dict[str, Any]] = []
			if isinstance(image_inputs_raw, list):
				for item in cast(list[object], image_inputs_raw):
					if isinstance(item, dict):
						image_inputs.append(cast(dict[str, Any], item))

			images = self._decode_images(image_inputs)
			text_input = prompt.strip() or "Beschreibe den visuellen Inhalt."
			try:
				inputs = cast(dict[str, Any], self._processor(text=text_input, images=images, return_tensors="pt"))
			except ValueError as exc:
				error_text = str(exc)
				if (
					images
					and "number of images in the text" in error_text
					and "<image>" not in text_input
					and "<|image|>" not in text_input
				):
					placeholders = "\n".join(["<image>"] * len(images))
					text_input = f"{placeholders}\n{text_input}".strip()
					inputs = cast(dict[str, Any], self._processor(text=text_input, images=images, return_tensors="pt"))
				else:
					raise
			if self._device == "cuda":
				inputs = {key: value.to("cuda") for key, value in inputs.items()}

			with self._lock:
				outputs = self._model.generate(
					**inputs,
					max_new_tokens=max_new_tokens,
					do_sample=do_sample,
					temperature=temperature,
					top_p=top_p,
					top_k=top_k,
					repetition_penalty=repetition_penalty,
				)

			decoded = self._processor.batch_decode(outputs, skip_special_tokens=True)
			if not decoded:
				return ""
			return str(decoded[0]).strip()

		if self._tokenizer is None:
			raise RuntimeError("tokenizer not loaded")

		chat_messages_raw = config.get("chat_messages")
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

		apply_template = getattr(self._tokenizer, "apply_chat_template", None)
		inputs: dict[str, Any]
		if callable(apply_template) and chat_messages:
			try:
				inputs = cast(
					dict[str, Any],
					apply_template(
					chat_messages,
					add_generation_prompt=True,
					tokenize=True,
					return_dict=True,
					return_tensors="pt",
					),
				)
			except Exception:
				inputs = cast(dict[str, Any], self._tokenizer(prompt, return_tensors="pt"))
		else:
			inputs = cast(dict[str, Any], self._tokenizer(prompt, return_tensors="pt"))
		if self._device == "cuda":
			inputs = {key: value.to("cuda") for key, value in inputs.items()}

		with self._lock:
			outputs = self._model.generate(
				**inputs,
				max_new_tokens=max_new_tokens,
				do_sample=do_sample,
				temperature=temperature,
				top_p=top_p,
				top_k=top_k,
				repetition_penalty=repetition_penalty,
			)

		generated = outputs[0][inputs["input_ids"].shape[-1] :]
		text = self._tokenizer.decode(generated, skip_special_tokens=True)
		return str(text).strip()

	async def stream(self, prompt: str, config: dict[str, Any]) -> AsyncIterator[str]:
		if not self._loaded or self._tokenizer is None or self._model is None:
			raise RuntimeError("backend not loaded")

		loop = asyncio.get_running_loop()
		queue: asyncio.Queue[str | None] = asyncio.Queue()

		def _worker() -> None:
			try:
				text = self.generate(prompt, config)
				if not text:
					return
				for token in text.split():
					loop.call_soon_threadsafe(queue.put_nowait, f"{token} ")
			finally:
				loop.call_soon_threadsafe(queue.put_nowait, None)

		threading.Thread(target=_worker, daemon=True).start()

		while True:
			token = await queue.get()
			if token is None:
				break
			yield token

	def health_check(self) -> bool:
		if not self._loaded or self._model is None:
			return False
		if self._task_type == "vision_text_generation":
			return self._processor is not None
		return self._tokenizer is not None

	def get_capabilities(self) -> dict[str, Any]:
		return {
			"text_generation": True,
			"chat_completion": True,
			"streaming": True,
			"embeddings": False,
			"vision": self._task_type == "vision_text_generation",
			"audio": self._task_type == "audio_text_generation",
			"tool_calling": False,
			"structured_output": False,
			"device": self._device,
			"task_type": self._task_type,
		}
