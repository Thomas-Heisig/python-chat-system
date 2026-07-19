from __future__ import annotations

from app.db_models.model_config import ModelConfig
from app.speech.service import SpeechService


def _model(name: str, path: str) -> ModelConfig:
    model = ModelConfig(name=name, model_path=path, backend="transformers", model_type="text_to_speech")
    model.id = 123
    return model


def test_kokoro_detection_by_name() -> None:
    service = SpeechService()
    model = _model("Kokoro-82M", "F:/KI/models/Kokoro-82M")

    assert service._is_kokoro_model(model) is True


def test_kokoro_lang_code_from_language_and_speaker() -> None:
    assert SpeechService._kokoro_lang_code("en", "") == "a"
    assert SpeechService._kokoro_lang_code("en-gb", "") == "b"
    assert SpeechService._kokoro_lang_code("ja", "") == "j"
    assert SpeechService._kokoro_lang_code("auto", "bf_emma") == "b"
    assert SpeechService._kokoro_lang_code("unknown", "") == "a"
