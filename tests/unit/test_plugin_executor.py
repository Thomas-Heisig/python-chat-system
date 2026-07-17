from __future__ import annotations

import asyncio
import pytest

from app.tools.executor import PluginExecutionError, PluginExecutor


def test_plugin_executor_executes_calculator_plugin() -> None:
    executor = PluginExecutor()

    result = asyncio.run(executor.execute("calculator", {"expression": "2+3*4"}))

    assert isinstance(result, dict)
    assert "result" in result


def test_plugin_executor_executes_from_markup() -> None:
    executor = PluginExecutor()
    assistant_output = (
        "<plugin_call>calculator</plugin_call>"
        "<plugin_input>{\"expression\":\"10-4\"}</plugin_input>"
    )

    result = asyncio.run(executor.execute_from_markup(assistant_output))

    assert result["plugin_id"] == "calculator"
    assert result["plugin_input"] == {"expression": "10-4"}
    assert "plugin_response" in result
    assert "plugin_response_markup" in result


def test_plugin_executor_parse_markup_fails_without_plugin_call() -> None:
    executor = PluginExecutor()

    with pytest.raises(PluginExecutionError) as exc:
        executor.parse_markup("<plugin_input>{\"x\":1}</plugin_input>")

    assert exc.value.code == "plugin_call_missing"


def test_plugin_executor_passes_plugin_settings_to_business_letter() -> None:
    executor = PluginExecutor()

    result = asyncio.run(
        executor.execute(
            "business_letter",
            {
                "letter_type": "allgemein",
                "customer_name": "Max Mustermann",
                "subject": "Abstimmung",
            },
            {
                "base_closing_text": "Mit besten Gruessen",
                "default_signatory_name": "Projekt Admin",
            },
        )
    )

    assert isinstance(result, dict)
    assert "letter" in result
    assert "Mit besten Gruessen" in result["letter"]
    assert "Projekt Admin" in result["letter"]


@pytest.mark.parametrize(
    ("plugin_id", "payload"),
    [
        (
            "email",
            {
                "delivery": {"channel": "both", "recipient": "kunde@example.de", "subject": "Angebot"},
                "content": {"email_text": "Hallo", "email_html": "<p>Hallo</p>"},
                "metadata": {"request_id": "req-1", "validate_only": True},
                "validate_only": True,
            },
        ),
        (
            "whatsapp",
            {
                "delivery": {"channel": "both", "recipient": "+491701234567", "communication_channel": "whatsapp"},
                "content": {"message": "Statusupdate"},
                "metadata": {"request_id": "req-2", "validate_only": True},
                "validate_only": True,
            },
        ),
        (
            "translator",
            {
                "content": {"email_text": "Guten Tag", "target_lang": "en"},
                "metadata": {"request_id": "req-3", "validate_only": True},
                "validate_only": True,
            },
        ),
        (
            "business_letter",
            {
                "letter_type": "allgemein",
                "subject": "Rueckfrage zur Lieferung",
                "customer_name": "Max Mustermann",
                "metadata": {"request_id": "req-4"},
            },
        ),
    ],
)
def test_plugin_executor_validates_contract_for_harmonized_plugins(
    plugin_id: str,
    payload: dict[str, object],
) -> None:
    executor = PluginExecutor()

    result = asyncio.run(executor.execute(plugin_id, payload))

    assert isinstance(result, dict)
    assert "error" not in result


def test_plugin_executor_rejects_invalid_communication_contract_input() -> None:
    executor = PluginExecutor()

    with pytest.raises(PluginExecutionError) as exc:
        asyncio.run(
            executor.execute(
                "email",
                {
                    "delivery": "invalid",
                    "validate_only": True,
                },
            )
        )

    assert exc.value.code == "plugin_contract_invalid_input"


@pytest.mark.parametrize(
    ("plugin_id", "payload"),
    [
        (
            "email",
            {
                "delivery": {"cc": "team@example.de"},
                "validate_only": True,
            },
        ),
        (
            "whatsapp",
            {
                "content": {"message": 42},
                "validate_only": True,
            },
        ),
        (
            "translator",
            {
                "content": {"target_lang": 123},
                "validate_only": True,
            },
        ),
        (
            "business_letter",
            {
                "letter_type": "allgemein",
                "subject": "Rueckfrage",
                "metadata": {"request_id": 101},
            },
        ),
    ],
)
def test_plugin_executor_rejects_invalid_communication_contract_input_for_all_supported_plugins(
    plugin_id: str,
    payload: dict[str, object],
) -> None:
    executor = PluginExecutor()

    with pytest.raises(PluginExecutionError) as exc:
        asyncio.run(executor.execute(plugin_id, payload))

    assert exc.value.code == "plugin_contract_invalid_input"


@pytest.mark.parametrize(
    ("plugin_id", "payload"),
    [
        (
            "email",
            {
                "delivery": {"channel": "both", "recipient": "kunde@example.de", "subject": "Angebot"},
                "content": {"email_text": "Hallo", "email_html": "<p>Hallo</p>"},
                "validate_only": True,
            },
        ),
        (
            "whatsapp",
            {
                "delivery": {"channel": "both", "recipient": "+491701234567", "communication_channel": "whatsapp"},
                "content": {"message": "Statusupdate"},
                "validate_only": True,
            },
        ),
        (
            "translator",
            {
                "content": {"email_text": "Guten Tag", "target_lang": "en"},
                "validate_only": True,
            },
        ),
        (
            "business_letter",
            {
                "letter_type": "allgemein",
                "subject": "Rueckfrage zur Lieferung",
                "customer_name": "Max Mustermann",
                "metadata": {"request_id": "req-4"},
            },
        ),
    ],
)
def test_plugin_executor_returns_schema_compatible_validation_envelope_for_supported_plugins(
    plugin_id: str,
    payload: dict[str, object],
) -> None:
    executor = PluginExecutor()

    result = asyncio.run(executor.execute(plugin_id, payload))

    assert isinstance(result, dict)
    validation = result.get("validation")
    assert isinstance(validation, dict)
    assert isinstance(validation.get("status"), str)
    assert isinstance(validation.get("errors"), list)
    assert isinstance(validation.get("warnings"), list)
    assert isinstance(validation.get("missing_information"), list)
