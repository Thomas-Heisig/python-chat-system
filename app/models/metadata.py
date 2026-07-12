import json
import re
from pathlib import Path
from typing import Literal, NotRequired, TypedDict, cast

from app.models.loaders.custom.registry import CustomModelLoaderPluginRegistry


SYSTEM_DIRECTORY_NAMES = {"manifests", "_e2e", "_system"}


class ModelCapabilityMetadata(TypedDict):
	model_format: str
	model_family: str
	task_type: str
	backend: str | None
	loadable: bool
	supports_inference: bool
	supports_training: bool
	supports_peft_training: bool
	supports_4bit: bool
	supports_chat: bool
	supports_embeddings: bool
	supports_reranking: bool
	supports_vision: bool
	supports_audio: bool
	reason_unavailable: str | None
	relevance: Literal["active", "favorite", "relevant", "unavailable", "irrelevant"]
	group: str
	requires_custom_code: NotRequired[bool]
	custom_code_trusted: NotRequired[bool]
	custom_code_available: NotRequired[bool]
	custom_loader_id: NotRequired[str]
	custom_code_entrypoint: NotRequired[str | None]


_PIPELINE_TO_TASK: dict[str, str] = {
	"text-generation": "text_generation",
	"text2text-generation": "text_generation",
	"conversational": "text_generation",
	"audio-text-to-text": "audio_text_generation",
	"feature-extraction": "feature_extraction",
	"sentence-similarity": "embedding",
	"text-classification": "classification",
	"token-classification": "classification",
	"text-ranking": "reranking",
	"automatic-speech-recognition": "speech_to_text",
	"text-to-speech": "text_to_speech",
	"image-to-text": "ocr",
	"text-to-image": "text_to_image",
	"image-text-to-text": "vision_text_generation",
}


def is_system_directory(path: Path) -> bool:
	return path.is_dir() and path.name.lower() in SYSTEM_DIRECTORY_NAMES


def infer_model_capabilities(*, name: str, model_path: Path) -> ModelCapabilityMetadata:
	custom_detection = CustomModelLoaderPluginRegistry().detect(name=name, model_path=model_path)
	if custom_detection is not None:
		requires_custom_code = True
		custom_code_trusted = False
		loadable = bool(custom_detection.custom_code_available and custom_code_trusted)
		reason_unavailable = None
		if not custom_detection.custom_code_available:
			reason_unavailable = "Benutzerdefinierter Loader-Code fehlt fuer dieses Modell."
		elif not custom_code_trusted:
			reason_unavailable = "Custom-Code ist nicht als vertrauenswuerdig markiert."

		return {
			"model_format": custom_detection.model_format,
			"model_family": custom_detection.model_family,
			"task_type": custom_detection.task_type,
			"backend": custom_detection.backend,
			"loadable": loadable,
			"supports_inference": loadable,
			"supports_training": False,
			"supports_peft_training": False,
			"supports_4bit": False,
			"supports_chat": True,
			"supports_embeddings": False,
			"supports_reranking": False,
			"supports_vision": True,
			"supports_audio": True,
			"reason_unavailable": reason_unavailable,
			"relevance": "relevant" if loadable else "unavailable",
			"group": "Multimodal",
			"requires_custom_code": requires_custom_code,
			"custom_code_trusted": custom_code_trusted,
			"custom_code_available": bool(custom_detection.custom_code_available),
			"custom_loader_id": custom_detection.loader_id,
			"custom_code_entrypoint": custom_detection.custom_code_entrypoint,
		}

	name_lower = name.lower()
	config_payload = _load_json_if_exists(model_path / "config.json")
	model_index_payload = _load_json_if_exists(model_path / "model_index.json")
	readme_meta = _load_readme_frontmatter(model_path)

	model_format = _infer_model_format(model_path=model_path)
	task_type = _infer_task_type(
		model_path=model_path,
		name_lower=name_lower,
		model_format=model_format,
		config_payload=config_payload,
		model_index_payload=model_index_payload,
		readme_meta=readme_meta,
	)
	model_family = _infer_model_family(name_lower=name_lower, config_payload=config_payload)
	backend = _infer_backend(task_type=task_type, model_format=model_format, name_lower=name_lower)

	supports_chat = task_type == "text_generation"
	supports_embeddings = task_type in {"embedding", "feature_extraction"}
	supports_reranking = task_type == "reranking"
	supports_vision = task_type in {"vision_text_generation", "text_to_image", "ocr"}
	supports_audio = task_type in {"speech_to_text", "text_to_speech", "audio_generation", "voice_activity_detection", "audio_text_generation"}

	supports_training = bool(task_type == "text_generation" and model_format in {"transformers_safetensors", "transformers_pytorch"})
	supports_peft_training = supports_training
	supports_4bit = bool(task_type == "text_generation" and model_format in {"transformers_safetensors", "transformers_pytorch", "gguf"})

	group = _group_for_task(task_type=task_type, model_format=model_format)
	return {
		"model_format": model_format,
		"model_family": model_family,
		"task_type": task_type,
		"backend": backend,
		"loadable": backend is not None,
		"supports_inference": backend is not None,
		"supports_training": supports_training,
		"supports_peft_training": supports_peft_training,
		"supports_4bit": supports_4bit,
		"supports_chat": supports_chat,
		"supports_embeddings": supports_embeddings,
		"supports_reranking": supports_reranking,
		"supports_vision": supports_vision,
		"supports_audio": supports_audio,
		"reason_unavailable": None,
		"relevance": "relevant",
		"group": group,
	}


def _infer_model_format(*, model_path: Path) -> str:
	if model_path.is_file() and model_path.suffix.lower() == ".gguf":
		return "gguf"

	if (model_path / "model_index.json").exists():
		return "diffusers"

	if (model_path / "config.json").exists() and _has_file_match(model_path, "*.safetensors"):
		return "transformers_safetensors"

	if (model_path / "config.json").exists() and _has_file_match(model_path, "pytorch_model*.bin"):
		return "transformers_pytorch"

	if _has_file_match(model_path, "*.gguf"):
		return "gguf"

	if _has_file_match(model_path, "*.onnx"):
		return "onnx"

	if _has_file_match(model_path, "*.pt") or _has_file_match(model_path, "*.pth"):
		return "pytorch"

	if (model_path / "config.json").exists():
		return "transformers"

	return "unknown"


def _infer_task_type(
	*,
	model_path: Path,
	name_lower: str,
	model_format: str,
	config_payload: dict[str, object],
	model_index_payload: dict[str, object],
	readme_meta: dict[str, object],
) -> str:
	tags = {str(tag).strip().lower() for tag in _read_list(readme_meta.get("tags"))}
	pipeline_tag = str(readme_meta.get("pipeline_tag") or "").strip().lower()

	# Strong semantic hints override generic pipeline labels.
	if "reranker" in name_lower or "cross-encoder" in name_lower:
		return "reranking"
	if "embedding" in name_lower:
		return "embedding"

	if "reranker" in tags or "cross-encoder" in tags or "text-ranking" in tags:
		return "reranking"
	if "embedding" in tags or "sentence-transformers" in tags:
		return "embedding"
	if "automatic-speech-recognition" in tags or "asr" in tags:
		return "speech_to_text"
	if "audio-text-to-text" in tags or "ultravox" in tags:
		return "audio_text_generation"
	if "text-to-speech" in tags or "tts" in tags:
		return "text_to_speech"

	if pipeline_tag in _PIPELINE_TO_TASK:
		pipeline_task = _PIPELINE_TO_TASK[pipeline_tag]
		if pipeline_task == "vision_text_generation":
			# Keep common instruct chat models in text mode unless clearly multimodal-focused.
			if "ultravox" in name_lower:
				return "audio_text_generation"
			if "vlm" in name_lower or "vision" in name_lower:
				return "vision_text_generation"
			if (model_path / "processor_config.json").exists() or (model_path / "image_processor_config.json").exists():
				return "vision_text_generation"
			return "text_generation"
		return pipeline_task

	model_type = str(config_payload.get("model_type") or "").strip().lower()
	architectures = {str(item).strip().lower() for item in _read_list(config_payload.get("architectures"))}

	if model_format == "diffusers":
		return "text_to_image"
	if model_format == "onnx" and ("voxtral" in name_lower or "whisper" in name_lower or "moonshine" in name_lower):
		return "speech_to_text"

	if "whisper" in name_lower or "moonshine" in name_lower or "voxtral" in name_lower or "asr" in name_lower:
		return "speech_to_text"
	if "ultravox" in name_lower:
		return "audio_text_generation"
	if "tts" in name_lower or "kokoro" in name_lower or "mms" in name_lower or "kitten" in name_lower:
		return "text_to_speech"
	if "musicgen" in name_lower:
		return "audio_generation"
	if "vad" in name_lower:
		return "voice_activity_detection"
	if "trocr" in name_lower or "ocr" in name_lower:
		return "ocr"
	if "vlm" in name_lower or "vision" in name_lower:
		return "vision_text_generation"
	if "stable-diffusion" in str(model_index_payload.get("_class_name") or "").lower():
		return "text_to_image"
	if model_type in {"bert", "roberta", "xlm-roberta", "deberta", "albert", "electra"}:
		if "sentence-transformers" in tags or "embedding" in tags or "embedding" in name_lower:
			return "embedding"
		return "feature_extraction"
	if "causallm" in " ".join(architectures) or model_type in {"llama", "qwen2", "qwen3", "gemma", "mistral", "phi3"}:
		return "text_generation"

	return "text_generation"


def _infer_model_family(*, name_lower: str, config_payload: dict[str, object]) -> str:
	if "qwen" in name_lower:
		return "qwen"
	if "gemma" in name_lower:
		return "gemma"
	if "mistral" in name_lower:
		return "mistral"
	if "phi" in name_lower:
		return "phi"
	if "smollm" in name_lower:
		return "smollm"
	if "whisper" in name_lower:
		return "whisper"
	if "moonshine" in name_lower:
		return "moonshine"
	model_type = str(config_payload.get("model_type") or "").strip().lower()
	if model_type:
		return model_type
	return "unknown"


def _infer_backend(*, task_type: str, model_format: str, name_lower: str) -> str | None:
	if model_format == "gguf" and task_type in {"text_generation", "embedding", "reranking"}:
		return "llama_cpp"
	if task_type == "speech_to_text" and "whisper" in name_lower:
		return "whisper"
	if task_type == "voice_activity_detection":
		if model_format == "onnx":
			return "onnxruntime"
		if model_format in {"pytorch", "transformers", "transformers_safetensors", "transformers_pytorch"}:
			return "torch"
	if model_format in {"transformers", "transformers_safetensors", "transformers_pytorch"} and task_type in {
		"text_generation",
		"embedding",
		"feature_extraction",
		"reranking",
		"speech_to_text",
		"text_to_speech",
		"audio_text_generation",
		"ocr",
		"vision_text_generation",
	}:
		return "transformers"
	if model_format == "onnx":
		return "onnxruntime"
	if model_format == "diffusers":
		return "diffusers"
	return None


def _group_for_task(*, task_type: str, model_format: str) -> str:
	if task_type == "text_generation" and model_format == "gguf":
		return "GGUF - Text / Chat"
	if task_type == "text_generation":
		return "Text / Chat"
	if task_type == "vision_text_generation":
		return "Multimodal"
	if task_type in {"embedding", "feature_extraction"}:
		return "Embeddings"
	if task_type == "reranking":
		return "Reranker"
	if task_type == "speech_to_text":
		return "Speech-to-Text"
	if task_type == "text_to_speech":
		return "Text-to-Speech"
	if task_type in {"text_to_image"}:
		return "Bild"
	if task_type in {"audio_generation", "voice_activity_detection"}:
		return "Audio / Musik"
	if task_type == "audio_text_generation":
		return "Multimodal"
	if task_type == "ocr":
		return "OCR"
	return "Hilfsmodelle"


def _load_json_if_exists(path: Path) -> dict[str, object]:
	if not path.exists() or not path.is_file():
		return {}
	try:
		parsed = json.loads(path.read_text(encoding="utf-8"))
	except Exception:
		return {}
	if not isinstance(parsed, dict):
		return {}
	normalized: dict[str, object] = {}
	for key, value in cast(dict[object, object], parsed).items():
		normalized[str(key)] = value
	return normalized


def _load_readme_frontmatter(model_path: Path) -> dict[str, object]:
	for candidate in (model_path / "README.md", model_path / "README.MD"):
		if not candidate.exists() or not candidate.is_file():
			continue
		try:
			text = candidate.read_text(encoding="utf-8")
		except Exception:
			continue
		if not text.startswith("---"):
			return {}
		parts = text.split("---", 2)
		if len(parts) < 3:
			return {}
		return _parse_simple_yaml(parts[1])
	return {}


def _parse_simple_yaml(raw: str) -> dict[str, object]:
	result: dict[str, object] = {}
	current_list_key: str | None = None
	for line in raw.splitlines():
		stripped = line.strip()
		if not stripped or stripped.startswith("#"):
			continue
		if stripped.startswith("- ") and current_list_key is not None:
			existing = result.get(current_list_key)
			if not isinstance(existing, list):
				existing = []
				result[current_list_key] = existing
			cast(list[object], existing).append(stripped[2:].strip())
			continue
		match = re.match(r"^([A-Za-z0-9_\-]+)\s*:\s*(.*)$", stripped)
		if not match:
			current_list_key = None
			continue
		key = match.group(1)
		value = match.group(2).strip()
		if value == "":
			result[key] = []
			current_list_key = key
			continue
		current_list_key = None
		if value.startswith("[") and value.endswith("]"):
			items = [item.strip().strip('"\'') for item in value[1:-1].split(",") if item.strip()]
			result[key] = items
			continue
		result[key] = value.strip('"\'')
	return result


def _read_list(value: object) -> list[object]:
	if isinstance(value, list):
		return cast(list[object], value)
	return []


def _has_file_match(model_path: Path, pattern: str) -> bool:
	if not model_path.exists():
		return False
	if model_path.is_file():
		return model_path.match(pattern)
	return any(model_path.rglob(pattern))
