from __future__ import annotations

import asyncio
from pathlib import Path

from app.models.backends.custom_pytorch_backend import CustomPyTorchBackend


def test_custom_pytorch_backend_load_generate_and_stream(tmp_path: Path) -> None:
    model_dir = tmp_path / "Supra-A2A-Nano-Exp"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "model.safetensors").write_text("stub", encoding="utf-8")
    (model_dir / "vqvae.safetensors").write_text("stub", encoding="utf-8")
    (model_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
    entrypoint = model_dir / "modeling_supra.py"
    entrypoint.write_text(
        "def load_model(model_path, config):\n"
        "    return {'ok': True, 'path': model_path}\n\n"
        "def generate(runtime, prompt, config):\n"
        "    return f'response:{prompt}'\n\n"
        "def stream(runtime, prompt, config):\n"
        "    for token in ['response:', prompt]:\n"
        "        yield token\n\n"
        "def health_check(runtime):\n"
        "    return bool(runtime.get('ok'))\n\n"
        "def get_capabilities(runtime):\n"
        "    return {'vision': True, 'audio': True}\n",
        encoding="utf-8",
    )

    backend = CustomPyTorchBackend()
    backend.load(
        str(model_dir),
        {
            "metadata": {
                "custom_code_trusted": True,
            }
        },
    )

    assert backend.health_check() is True
    assert backend.generate("hello", {}) == "response:hello"

    async def _collect() -> list[str]:
        items: list[str] = []
        async for token in backend.stream("hello", {}):
            items.append(token)
        return items

    chunks = asyncio.run(_collect())
    assert chunks == ["response:", "hello"]

    caps = backend.get_capabilities()
    assert caps.get("backend") == "custom_pytorch"
    assert caps.get("vision") is True
    assert caps.get("audio") is True

    backend.unload()
    assert backend.health_check() is False


def test_custom_pytorch_backend_requires_trust(tmp_path: Path) -> None:
    model_dir = tmp_path / "Supra-A2A-Nano-Exp"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "model.safetensors").write_text("stub", encoding="utf-8")
    (model_dir / "vqvae.safetensors").write_text("stub", encoding="utf-8")
    (model_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
    (model_dir / "modeling_supra.py").write_text("def load_model(model_path, config):\n    return {}\n", encoding="utf-8")

    backend = CustomPyTorchBackend()
    try:
        backend.load(str(model_dir), {"metadata": {"custom_code_trusted": False}})
    except RuntimeError as exc:
        assert "not trusted" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when custom code is not trusted")
