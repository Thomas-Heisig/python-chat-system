from __future__ import annotations

import asyncio
import threading
from collections.abc import AsyncIterator
from typing import Any, cast

from app.models.backends.base import ModelBackend


class TransformersPeftBackend(ModelBackend):
    def __init__(self) -> None:
        self._loaded = False
        self._device: str = "cpu"
        self._tokenizer: Any | None = None
        self._model: Any | None = None
        self._lock = threading.Lock()
        self._adapter_path: str | None = None
        self._base_model_path: str | None = None

    def load(self, model_path: str, config: dict[str, Any]) -> None:
        metadata = cast(dict[str, Any], config.get("metadata") or {})
        adapter_path = str(metadata.get("adapter_path") or model_path).strip()
        base_model_path = str(metadata.get("base_model_path") or "").strip()
        load_in_4bit = bool(metadata.get("load_in_4bit", True))

        if not adapter_path:
            raise RuntimeError("adapter_path_missing")
        if not base_model_path:
            raise RuntimeError("base_model_path_missing")

        try:
            import torch
            from peft import PeftModel
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        except Exception as exc:
            raise RuntimeError("transformers/peft adapter dependencies are not installed") from exc

        prefer_gpu = bool(config.get("prefer_gpu", True))
        cuda_available = bool(torch.cuda.is_available())
        self._device = "cuda" if prefer_gpu and cuda_available else "cpu"

        tokenizer = AutoTokenizer.from_pretrained(base_model_path, local_files_only=True)
        quant_config = None
        if load_in_4bit and self._device == "cuda":
            quant_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )

        model_load_kwargs: dict[str, object] = {
            "local_files_only": True,
            "device_map": "auto" if self._device == "cuda" else "cpu",
            "quantization_config": quant_config,
            "dtype": torch.float16 if self._device == "cuda" else torch.float32,
        }
        try:
            base_model = AutoModelForCausalLM.from_pretrained(base_model_path, **model_load_kwargs)
        except TypeError:
            model_load_kwargs.pop("dtype", None)
            model_load_kwargs["torch_dtype"] = torch.float16 if self._device == "cuda" else torch.float32
            base_model = AutoModelForCausalLM.from_pretrained(base_model_path, **model_load_kwargs)

        if tokenizer.pad_token is None and tokenizer.eos_token is not None:
            tokenizer.pad_token = tokenizer.eos_token
        if tokenizer.pad_token_id is not None:
            base_model.config.pad_token_id = tokenizer.pad_token_id
            if getattr(base_model, "generation_config", None) is not None:
                base_model.generation_config.pad_token_id = tokenizer.pad_token_id

        model = PeftModel.from_pretrained(base_model, adapter_path, is_trainable=False)
        model.eval()

        self._tokenizer = tokenizer
        self._model = model
        self._loaded = True
        self._adapter_path = adapter_path
        self._base_model_path = base_model_path

    def unload(self) -> None:
        self._tokenizer = None
        self._model = None
        self._loaded = False
        self._device = "cpu"
        self._adapter_path = None
        self._base_model_path = None

    def generate(self, prompt: str, config: dict[str, Any]) -> str:
        if not self._loaded or self._tokenizer is None or self._model is None:
            raise RuntimeError("backend not loaded")

        max_new_tokens = int(config.get("max_new_tokens", 256))
        temperature = float(config.get("temperature", 0.2))
        top_p = float(config.get("top_p", 0.9))
        top_k = int(config.get("top_k", 40))
        repetition_penalty = float(config.get("repetition_penalty", 1.1))
        do_sample = bool(config.get("do_sample", True))
        stop_sequences = config.get("stop", ["<end_of_turn>", "<eos>"])
        seed = int(config.get("seed", 42))
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
                stop_strings=stop_sequences if isinstance(stop_sequences, list) else None,
                tokenizer=self._tokenizer,
                pad_token_id=self._tokenizer.pad_token_id,
            )

        generated = outputs[0][inputs["input_ids"].shape[-1] :]
        text = self._tokenizer.decode(generated, skip_special_tokens=True)
        return str(text).strip()

    async def stream(self, prompt: str, config: dict[str, Any]) -> AsyncIterator[str]:
        if not self._loaded:
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
        return self._loaded and self._tokenizer is not None and self._model is not None

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
            "task_type": "text_generation",
            "adapter_path": self._adapter_path,
            "base_model_path": self._base_model_path,
        }
