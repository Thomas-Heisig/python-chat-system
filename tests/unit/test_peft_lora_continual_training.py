from __future__ import annotations

from pathlib import Path

import pytest

from app.training.trainers.peft_lora import _attach_trainable_adapter


class _PeftModel:
    calls: list[tuple[object, str, bool]] = []

    @classmethod
    def from_pretrained(cls, model: object, path: str, *, is_trainable: bool) -> object:
        cls.calls.append((model, path, is_trainable))
        return "continued-model"


def test_existing_adapter_is_loaded_trainable(tmp_path: Path) -> None:
    adapter = tmp_path / "adapter"
    adapter.mkdir()
    (adapter / "adapter_config.json").write_text("{}", encoding="utf-8")
    (adapter / "adapter_model.safetensors").write_bytes(b"weights")
    _PeftModel.calls.clear()

    result = _attach_trainable_adapter(
        "base-model",
        resume_adapter_path=str(adapter),
        lora_config="new-config",
        peft_model_class=_PeftModel,
        get_peft_model_fn=lambda _model, _config: "new-model",
    )

    assert result == "continued-model"
    assert _PeftModel.calls == [("base-model", str(adapter.resolve()), True)]


def test_missing_previous_adapter_fails_instead_of_silently_starting_over(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="continual_adapter_invalid"):
        _attach_trainable_adapter(
            "base-model",
            resume_adapter_path=str(tmp_path / "missing"),
            lora_config="new-config",
            peft_model_class=_PeftModel,
            get_peft_model_fn=lambda _model, _config: "new-model",
        )


def test_first_run_creates_adapter() -> None:
    result = _attach_trainable_adapter(
        "base-model",
        resume_adapter_path="",
        lora_config="new-config",
        peft_model_class=_PeftModel,
        get_peft_model_fn=lambda model, config: (model, config),
    )

    assert result == ("base-model", "new-config")
