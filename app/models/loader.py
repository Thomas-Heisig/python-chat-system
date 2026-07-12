from app.models.backends.base import ModelBackend
from app.models.backends.custom_pytorch_backend import CustomPyTorchBackend
from app.models.backends.llama_cpp_backend import LlamaCppBackend
from app.models.backends.transformers_peft_backend import TransformersPeftBackend
from app.models.backends.transformers_backend import TransformersBackend


SUPPORTED_BACKENDS: dict[str, type[ModelBackend]] = {
    "custom_pytorch": CustomPyTorchBackend,
    "llama_cpp": LlamaCppBackend,
    "transformers": TransformersBackend,
    "transformers_peft": TransformersPeftBackend,
}


def list_supported_backends() -> list[str]:
    return sorted(SUPPORTED_BACKENDS.keys())


def create_backend(backend_name: str) -> ModelBackend:
    backend_cls = SUPPORTED_BACKENDS.get(backend_name)
    if backend_cls is not None:
        return backend_cls()
    raise ValueError(f"Unsupported backend: {backend_name}")
