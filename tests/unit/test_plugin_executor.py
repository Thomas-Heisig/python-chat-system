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


def test_plugin_executor_lists_capabilities_and_manifest() -> None:
    executor = PluginExecutor()

    capabilities = executor.list_capabilities()
    manifest = executor.describe_plugin("calculator")
    function = executor.describe_function("calculator", "evaluate")

    assert isinstance(capabilities, list)
    assert any(item.get("plugin_id") == "calculator" for item in capabilities)
    assert isinstance(manifest, dict)
    assert manifest.get("id") == "calculator"
    assert isinstance(manifest.get("functions"), list)
    assert isinstance(function, dict)
    assert function.get("name") == "evaluate"


def test_plugin_executor_search_plugins_returns_candidates() -> None:
    executor = PluginExecutor()

    candidates = executor.search_plugins("rechnung lieferschein", limit=3)

    assert isinstance(candidates, list)
    assert len(candidates) <= 3
    assert all("plugin_id" in item for item in candidates)
    assert all(item.get("decision") in {"direct_manifest", "model_review", "no_auto_selection"} for item in candidates)


def test_plugin_executor_search_plugin_name_only_does_not_auto_select() -> None:
    executor = PluginExecutor()

    candidates = executor.search_plugins("calculator", limit=3)
    calculator_candidate = next((item for item in candidates if item.get("plugin_id") == "calculator"), None)

    assert isinstance(calculator_candidate, dict)
    assert calculator_candidate.get("auto_select") is False


def test_plugin_executor_execute_function_uses_action_name_for_calculator() -> None:
    executor = PluginExecutor()

    result = asyncio.run(executor.execute_function("calculator", "preset_circle_area", {}))

    assert isinstance(result, dict)
    assert result.get("action") == "preset_circle_area"
    assert "result" in result


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
            execution_context={"idempotency_key": "bl-settings-1"},
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

    execution_context = {"idempotency_key": f"harmonized-{plugin_id}"} if plugin_id == "business_letter" else None
    result = asyncio.run(executor.execute(plugin_id, payload, execution_context=execution_context))

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

    assert exc.value.code in {"plugin_contract_invalid_input", "plugin_input_schema_invalid"}


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

    execution_context = {"idempotency_key": f"invalid-contract-{plugin_id}"} if plugin_id == "business_letter" else None

    with pytest.raises(PluginExecutionError) as exc:
        asyncio.run(executor.execute(plugin_id, payload, execution_context=execution_context))

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

    execution_context = {"idempotency_key": "compat-envelope"} if plugin_id == "business_letter" else None
    result = asyncio.run(executor.execute(plugin_id, payload, execution_context=execution_context))

    assert isinstance(result, dict)
    validation = result.get("validation")
    assert isinstance(validation, dict)
    assert isinstance(validation.get("status"), str)
    assert isinstance(validation.get("errors"), list)
    assert isinstance(validation.get("warnings"), list)
    assert isinstance(validation.get("missing_information"), list)


def test_plugin_executor_blocks_mutating_function_without_idempotency_key() -> None:
    executor = PluginExecutor()

    with pytest.raises(PluginExecutionError) as exc:
        asyncio.run(
            executor.execute_function(
                "business_letter",
                "create_document",
                {
                    "letter_type": "allgemein",
                    "subject": "Rueckfrage",
                    "customer_name": "Max Mustermann",
                },
            )
        )

    assert exc.value.code == "plugin_idempotency_key_required"


def test_plugin_executor_allows_duplicate_execution_with_same_idempotency_key() -> None:
    executor = PluginExecutor()
    payload = {
        "letter_type": "allgemein",
        "subject": "Rueckfrage",
        "customer_name": "Max Mustermann",
    }
    context = {"idempotency_key": "idem-duplicate-1"}

    first = asyncio.run(
        executor.execute_function(
            "business_letter",
            "create_document",
            payload,
            execution_context=context,
        )
    )
    assert isinstance(first, dict)

    second = asyncio.run(
        executor.execute_function(
            "business_letter",
            "create_document",
            payload,
            execution_context=context,
        )
    )

    assert isinstance(second, dict)


def test_plugin_executor_rejects_too_short_idempotency_key() -> None:
    executor = PluginExecutor()

    with pytest.raises(PluginExecutionError) as exc:
        asyncio.run(
            executor.execute_function(
                "business_letter",
                "create_document",
                {
                    "letter_type": "allgemein",
                    "subject": "Rueckfrage",
                    "customer_name": "Max Mustermann",
                },
                execution_context={"idempotency_key": "abc"},
            )
        )

    assert exc.value.code == "plugin_idempotency_key_invalid"


def test_plugin_executor_blocks_when_required_permission_missing() -> None:
    executor = PluginExecutor()

    with pytest.raises(PluginExecutionError) as exc:
        asyncio.run(
            executor.execute_function(
                "calculator",
                "evaluate",
                {"expression": "2+2"},
                execution_context={"enforce_permissions": True, "granted_permissions": []},
            )
        )

    assert exc.value.code == "plugin_permission_missing"


def test_plugin_executor_allows_when_required_permission_present() -> None:
    executor = PluginExecutor()

    result = asyncio.run(
        executor.execute_function(
            "calculator",
            "evaluate",
            {"expression": "2+2"},
            execution_context={
                "enforce_permissions": True,
                "granted_permissions": ["calculator.execute"],
            },
        )
    )

    assert result.get("result") == 4
