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


def test_validate_complete_training_settings():
    assert validate_setting("training", "training_preset", "safe") == "safe"
    assert validate_setting("training", "num_train_epochs", 1.5) == 1.5
    assert validate_setting("training", "learning_rate", 0.0002) == 0.0002
    assert validate_setting("training", "warmup_ratio", 0.05) == 0.05
    assert validate_setting("training", "weight_decay", 0.01) == 0.01
    assert validate_setting("training", "eval_steps", 10) == 10
    assert validate_setting("training", "max_sequence_length", 1024) == 1024
    assert validate_setting("training", "load_best_model_at_end", True) is True
    assert validate_setting("training", "metric_for_best_model", "eval_loss") == "eval_loss"
    assert validate_setting("training", "greater_is_better", False) is False
    assert validate_setting("training", "target_modules", [" q_proj ", "v_proj"]) == ["q_proj", "v_proj"]
    assert validate_setting("training", "continual_model_id", 54) == 54
    assert validate_setting("training", "continual_model_id", None) is None


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("training_preset", "unknown"),
        ("learning_rate", 0),
        ("warmup_ratio", 0.9),
        ("eval_steps", 0),
        ("max_sequence_length", 64),
        ("metric_for_best_model", ""),
        ("target_modules", []),
        ("continual_model_id", 0),
    ],
)
def test_validate_training_settings_reject_invalid_values(key, value):
    with pytest.raises(InvalidSettingError):
        validate_setting("training", key, value)
