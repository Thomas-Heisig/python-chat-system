from __future__ import annotations

from app.api.routes.speech import TtsRequest


def test_tts_request_accepts_camel_case_and_null_optional_values() -> None:
    payload = {
        "modelId": 7,
        "text": "  Hallo Welt  ",
        "language": None,
        "speaker": None,
        "speed": "",
        "device": None,
    }

    request = TtsRequest.model_validate(payload)

    assert request.model_id == 7
    assert request.text == "Hallo Welt"
    assert request.language == "auto"
    assert request.speaker == ""
    assert request.speed == 1.0
    assert request.device == "auto"


def test_tts_request_coerces_invalid_device_and_speed() -> None:
    payload = {
        "model_id": 9,
        "text": "Test",
        "speed": "not-a-number",
        "device": "tpu",
    }

    request = TtsRequest.model_validate(payload)

    assert request.speed == 1.0
    assert request.device == "auto"
