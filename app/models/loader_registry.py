from dataclasses import dataclass
import importlib
import importlib.util
import sys

from app.models.loaders.custom.registry import CustomModelLoaderPluginRegistry
from app.models.openai_integration import openai_runtime_available
from app.models.ollama_integration import ollama_runtime_available


@dataclass(frozen=True, slots=True)
class LoaderDescriptor:
    loader_id: str
    name: str
    supported_formats: set[str]
    supported_tasks: set[str]
    available: bool
    reason_unavailable: str | None = None


@dataclass(frozen=True, slots=True)
class DependencyCheck:
    available: bool
    interpreter: str
    error: str | None = None


class ModelLoaderRegistry:
    def __init__(self) -> None:
        transformers_check = check_python_module("transformers")
        llama_cpp_check = check_python_module("llama_cpp")
        sentence_transformers_check = check_python_module("sentence_transformers")
        onnx_check = check_python_module("onnxruntime")
        diffusers_check = check_python_module("diffusers")
        torch_check = check_python_module("torch")
        pillow_check = check_python_module("PIL")
        openai_available, openai_reason = openai_runtime_available()
        ollama_available, ollama_reason = ollama_runtime_available()

        transformers_available = transformers_check.available
        llama_cpp_available = llama_cpp_check.available
        sentence_transformers_available = sentence_transformers_check.available
        onnx_available = onnx_check.available
        pillow_available = pillow_check.available
        diffusers_available = diffusers_check.available and torch_check.available

        llama_cpp_reason = (
            None
            if llama_cpp_available
            else (
                "llama-cpp-python ist im Backend-Python nicht verfuegbar. "
                f"Interpreter: {llama_cpp_check.interpreter}. "
                f"Details: {llama_cpp_check.error or 'unbekannt'}"
            )
        )

        self._loaders = [
            LoaderDescriptor(
                loader_id="transformers_causal_lm",
                name="Transformers CausalLM",
                supported_formats={"transformers", "transformers_safetensors", "transformers_pytorch"},
                supported_tasks={"text_generation"},
                available=transformers_available,
                reason_unavailable=None if transformers_available else "Transformers ist nicht installiert.",
            ),
            LoaderDescriptor(
                loader_id="transformers_vision",
                name="Transformers Vision",
                supported_formats={"transformers", "transformers_safetensors", "transformers_pytorch"},
                supported_tasks={"vision_text_generation"},
                available=transformers_available and pillow_available,
                reason_unavailable=(
                    None
                    if transformers_available and pillow_available
                    else "transformers und pillow werden fuer Vision-Modelle benoetigt."
                ),
            ),
            LoaderDescriptor(
                loader_id="transformers_audio_text",
                name="Transformers Audio-Text",
                supported_formats={"transformers", "transformers_safetensors", "transformers_pytorch"},
                supported_tasks={"audio_text_generation"},
                available=transformers_available,
                reason_unavailable=None if transformers_available else "Transformers ist nicht installiert.",
            ),
            LoaderDescriptor(
                loader_id="transformers_peft_adapter",
                name="Transformers PEFT Adapter",
                supported_formats={"peft_adapter"},
                supported_tasks={"text_generation"},
                available=transformers_available and torch_check.available and check_python_module("peft").available,
                reason_unavailable=(
                    None
                    if transformers_available and torch_check.available and check_python_module("peft").available
                    else "transformers, torch und peft werden fuer PEFT-Adapter benoetigt."
                ),
            ),
            LoaderDescriptor(
                loader_id="llama_cpp",
                name="llama.cpp",
                supported_formats={"gguf"},
                supported_tasks={"text_generation"},
                available=llama_cpp_available,
                reason_unavailable=llama_cpp_reason,
            ),
            LoaderDescriptor(
                loader_id="llama_cpp_embedding",
                name="llama.cpp Embedding",
                supported_formats={"gguf"},
                supported_tasks={"embedding", "feature_extraction"},
                available=llama_cpp_available,
                reason_unavailable=llama_cpp_reason,
            ),
            LoaderDescriptor(
                loader_id="llama_cpp_reranker",
                name="llama.cpp Reranker",
                supported_formats={"gguf"},
                supported_tasks={"reranking"},
                available=llama_cpp_available,
                reason_unavailable=llama_cpp_reason,
            ),
            LoaderDescriptor(
                loader_id="openai_chat",
                name="ChatGPT API",
                supported_formats={"openai"},
                supported_tasks={"text_generation", "vision_text_generation"},
                available=openai_available,
                reason_unavailable=openai_reason,
            ),
            LoaderDescriptor(
                loader_id="ollama_chat",
                name="Ollama Chat",
                supported_formats={"ollama"},
                supported_tasks={"text_generation", "vision_text_generation"},
                available=ollama_available,
                reason_unavailable=ollama_reason,
            ),
            LoaderDescriptor(
                loader_id="ollama_embedding",
                name="Ollama Embedding",
                supported_formats={"ollama"},
                supported_tasks={"embedding", "feature_extraction"},
                available=ollama_available,
                reason_unavailable=ollama_reason,
            ),
            LoaderDescriptor(
                loader_id="transformers_embedding",
                name="Transformers Embedding",
                supported_formats={"transformers", "transformers_safetensors", "transformers_pytorch"},
                supported_tasks={"embedding", "feature_extraction"},
                available=transformers_available,
                reason_unavailable=None if transformers_available else "Transformers ist nicht installiert.",
            ),
            LoaderDescriptor(
                loader_id="cross_encoder_reranker",
                name="CrossEncoder Reranker",
                supported_formats={"transformers", "transformers_safetensors", "transformers_pytorch", "gguf"},
                supported_tasks={"reranking"},
                available=transformers_available or sentence_transformers_available,
                reason_unavailable=(
                    None
                    if transformers_available or sentence_transformers_available
                    else "Weder transformers noch sentence-transformers sind installiert."
                ),
            ),
            LoaderDescriptor(
                loader_id="speech_loader",
                name="Speech Loader",
                supported_formats={"transformers", "transformers_safetensors", "transformers_pytorch", "onnx"},
                supported_tasks={"speech_to_text", "text_to_speech"},
                available=transformers_available or onnx_available,
                reason_unavailable=None if transformers_available or onnx_available else "Weder transformers noch onnxruntime sind installiert.",
            ),
            LoaderDescriptor(
                loader_id="vad_loader",
                name="Voice Activity Detection",
                supported_formats={"onnx", "pytorch", "transformers", "transformers_safetensors", "transformers_pytorch"},
                supported_tasks={"voice_activity_detection"},
                available=onnx_available or torch_check.available,
                reason_unavailable=None if onnx_available or torch_check.available else "Fuer VAD wird onnxruntime oder torch benoetigt.",
            ),
            LoaderDescriptor(
                loader_id="onnx_runtime",
                name="ONNX Runtime",
                supported_formats={"onnx"},
                supported_tasks={"text_generation", "speech_to_text", "embedding", "feature_extraction", "reranking"},
                available=onnx_available,
                reason_unavailable=None if onnx_available else "onnxruntime ist nicht installiert.",
            ),
            LoaderDescriptor(
                loader_id="diffusers",
                name="Diffusers",
                supported_formats={"diffusers"},
                supported_tasks={"text_to_image"},
                available=diffusers_available,
                reason_unavailable=None if diffusers_available else "diffusers und torch werden fuer diesen Loader benoetigt.",
            ),
            LoaderDescriptor(
                loader_id="ocr_loader",
                name="OCR Loader",
                supported_formats={"transformers", "transformers_safetensors", "transformers_pytorch", "onnx"},
                supported_tasks={"ocr"},
                available=transformers_available and pillow_available,
                reason_unavailable=(
                    None
                    if transformers_available and pillow_available
                    else "transformers und pillow werden fuer OCR benoetigt."
                ),
            ),
        ]

        custom_plugins = CustomModelLoaderPluginRegistry().plugins()
        for plugin in custom_plugins:
            available, reason_unavailable = plugin.runtime_available()
            self._loaders.append(
                LoaderDescriptor(
                    loader_id=plugin.loader_id,
                    name=plugin.display_name,
                    supported_formats=set(plugin.supported_formats),
                    supported_tasks=set(plugin.supported_tasks),
                    available=available,
                    reason_unavailable=reason_unavailable,
                )
            )

    def resolve(self, *, model_format: str, task_type: str) -> LoaderDescriptor | None:
        for loader in self._loaders:
            if model_format in loader.supported_formats and task_type in loader.supported_tasks:
                return loader
        return None


def check_python_module(module_name: str) -> DependencyCheck:
    interpreter = sys.executable
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return DependencyCheck(
                available=False,
                interpreter=interpreter,
                error=f"Modul {module_name!r} wurde in dieser Python-Umgebung nicht gefunden.",
            )

        importlib.import_module(module_name)
        return DependencyCheck(available=True, interpreter=interpreter)
    except Exception as exc:
        return DependencyCheck(
            available=False,
            interpreter=interpreter,
            error=f"{type(exc).__name__}: {exc}",
        )
