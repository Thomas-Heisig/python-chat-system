from app.settings.validator import validate_setting
from app.core.exceptions import InvalidSettingError
import pytest


def test_validate_chat_limit_hard_cap():
    assert validate_setting("chat", "max_new_tokens", 8000) == 4096


def test_validate_model_scoped_chat_and_prompt_settings():
    assert validate_setting("chat", "model_7_top_k", 6) == 6
    assert validate_setting("chat", "model_7_top_p", 0.9) == 0.9
    assert validate_setting("chat", "model_7_repetition_penalty", 1.1) == 1.1
    assert validate_setting("chat", "model_7_stop_sequences", [" <eos> ", "", "<end_of_turn>"]) == ["<eos>", "<end_of_turn>"]
    assert validate_setting("prompt", "model_7_system_prompt", "  Sei praezise.  ") == "Sei praezise."


def test_validate_general_system_settings():
    assert validate_setting("system", "language", "DE") == "de"
    assert validate_setting("system", "theme", "dark") == "dark"
    assert validate_setting("system", "timezone", "Europe/Berlin") == "Europe/Berlin"


def test_validate_general_system_settings_rejects_invalid_timezone():
    with pytest.raises(InvalidSettingError):
        validate_setting("system", "timezone", "Mars/Olympus")
