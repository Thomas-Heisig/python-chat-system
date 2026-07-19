from __future__ import annotations

import base64
from typing import Any
from uuid import uuid4

from _pytest.monkeypatch import MonkeyPatch


def _assert_success_or_raise(response: Any) -> dict[str, Any]:
    if response.status_code >= 400:
        raise AssertionError(f"HTTP {response.status_code}: {response.text}")
    payload = response.json()
    if isinstance(payload, dict) and payload.get("detail"):
        detail = payload.get("detail")
        raise AssertionError(f"Unexpected detail payload: {detail}")
    return payload


def _error_code(payload: dict[str, Any]) -> str | None:
    error = payload.get("error")
    if isinstance(error, dict):
        details = error.get("details")
        if isinstance(details, dict):
            nested_detail = details.get("detail")
            if isinstance(nested_detail, dict):
                nested_code = nested_detail.get("code")
                if isinstance(nested_code, str):
                    return nested_code

        nested_detail = error.get("detail")
        if isinstance(nested_detail, dict):
            nested_code = nested_detail.get("code")
            if isinstance(nested_code, str):
                return nested_code

    detail = payload.get("detail")
    if isinstance(detail, dict):
        code = detail.get("code")
        if isinstance(code, str):
            return code
    code = payload.get("code")
    return code if isinstance(code, str) else None


def test_plugins_execute_returns_contract_error_code_for_invalid_input(app_client: Any) -> None:
    response = app_client.post(
        "/api/plugins/execute",
        json={
            "plugin_id": "email",
            "plugin_input": {
                "delivery": "invalid",
                "validate_only": True,
            },
        },
    )

    assert response.status_code == 400
    body = response.json()
    assert _error_code(body) in {"plugin_contract_invalid_input", "plugin_input_schema_invalid"}


def test_plugins_execute_returns_contract_error_code_for_invalid_output(
    app_client: Any,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.tools.executor.CommunicationContractValidator.validate_output",
        lambda self, plugin_id, payload: ["forced-output-contract-error"] if plugin_id == "email" else [],
    )

    response = app_client.post(
        "/api/plugins/execute",
        json={
            "plugin_id": "email",
            "plugin_input": {
                "delivery": {
                    "communication_channel": "both",
                    "to": "kunde@example.de",
                    "subject": "Angebot",
                },
                "content": {
                    "email_text": "Hallo",
                    "email_html": "<p>Hallo</p>",
                },
                "validate_only": True,
            },
        },
    )

    assert response.status_code == 400
    body = response.json()
    assert _error_code(body) == "plugin_contract_invalid_output"


def test_plugins_execute_returns_skip_reason_for_unsupported_channel(app_client: Any) -> None:
    response = app_client.post(
        "/api/plugins/execute",
        json={
            "plugin_id": "email",
            "plugin_input": {
                "communication_channel": "letter",
                "subject": "Test",
                "body": "Nur Briefkanal.",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    plugin_response = payload["plugin_response"]

    assert plugin_response["success"] is True
    assert plugin_response["status"] == "skipped"
    assert plugin_response["reason"] == "unsupported_channel"


def test_plugins_capabilities_endpoint_returns_items(app_client: Any) -> None:
    response = app_client.get("/api/plugins/capabilities")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("items"), list)


def test_plugins_manifest_endpoint_returns_plugin_manifest(app_client: Any) -> None:
    response = app_client.get("/api/plugins/calculator/manifest")

    assert response.status_code == 200
    payload = response.json()
    assert payload.get("id") == "calculator"
    assert isinstance(payload.get("functions"), list)


def test_business_letter_artifact_download_returns_pdf_payload(app_client: Any) -> None:
    from plugins.business_letter.services.persistence import BusinessLetterPersistence

    register_response = app_client.post(
        "/api/auth/register",
        json={"username": f"artifact-user-{uuid4().hex[:8]}", "password": "Test#2026"},
    )
    assert register_response.status_code == 200
    register_payload = register_response.json()
    user_id = int(register_payload["user"]["id"])
    token = str(register_payload["access_token"])

    persistence = BusinessLetterPersistence()
    document_id = f"doc_test_artifact_{uuid4().hex[:12]}"
    persistence.persist_bundle_transactional(
        tenant_id=f"user:{user_id}",
        document_id=document_id,
        document_number="ANG-2026-0001",
        numbering=None,
        template_profile="default",
        status="draft",
        data_snapshot={"document": {}, "template": {}, "email": {}, "commercial_document": {}},
        document_kind="angebot",
        snapshot_json={"document": {}, "template": {}, "commercial_document": {}, "email": {}},
        created_by="test",
        approved_by="",
        sent_at=None,
        revision_number=1,
        reason="test",
        artifacts=[
            {
                "artifact_kind": "pdf",
                "storage_key": "business_letter/ANG-2026-0001.pdf",
                "mime_type": "application/pdf",
                "payload_text": base64.b64encode(b"%PDF-test-payload").decode("ascii"),
                "metadata": {"artifact": {"file_name": "ANG-2026-0001.pdf"}},
            }
        ],
        retention_days=30,
        immutable_after_release=False,
        verify_hashes=False,
    )

    response = app_client.get(
        f"/api/plugins/business-letter/documents/{document_id}/artifacts/pdf",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content == b"%PDF-test-payload"

    events = persistence.list_document_events_for_document(tenant_id=f"user:{user_id}", document_id=document_id)
    assert any(
        str(item.get("event_type") or "") == "artifact_downloaded"
        and isinstance(item.get("event_payload"), dict)
        and int(item["event_payload"].get("actor_user_id") or 0) == user_id
        for item in events
    )


def test_business_letter_artifact_download_allows_shared_scope_for_authenticated_user(app_client: Any) -> None:
    from plugins.business_letter.services.persistence import BusinessLetterPersistence

    register_response = app_client.post(
        "/api/auth/register",
        json={"username": f"shared-artifact-user-{uuid4().hex[:8]}", "password": "Test#2026"},
    )
    assert register_response.status_code == 200
    register_payload = register_response.json()
    token = str(register_payload["access_token"])

    persistence = BusinessLetterPersistence()
    document_id = f"doc_shared_artifact_{uuid4().hex[:12]}"
    persistence.persist_bundle_transactional(
        tenant_id="shared",
        document_id=document_id,
        document_number="ANG-SHARED-0001",
        numbering=None,
        template_profile="default",
        status="draft",
        data_snapshot={"document": {}, "template": {}, "email": {}, "commercial_document": {}},
        document_kind="angebot",
        snapshot_json={"document": {}, "template": {}, "commercial_document": {}, "email": {}},
        created_by="test",
        approved_by="",
        sent_at=None,
        revision_number=1,
        reason="test",
        artifacts=[
            {
                "artifact_kind": "json",
                "storage_key": "business_letter/ANG-SHARED-0001.json",
                "mime_type": "application/json",
                "payload_text": '{"ok":true}',
                "metadata": {"artifact": {"file_name": "ANG-SHARED-0001.json"}},
            }
        ],
        retention_days=30,
        immutable_after_release=False,
        verify_hashes=False,
    )

    response = app_client.get(
        f"/api/plugins/business-letter/documents/{document_id}/artifacts/json?tenant_id=shared",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.content == b'{"ok":true}'


def test_plugins_execute_function_endpoint_executes_action(app_client: Any) -> None:
    response = app_client.post(
        "/api/plugins/execute-function",
        json={
            "plugin_id": "calculator",
            "function_name": "preset_percentage",
            "function_input": {},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    plugin_response = payload.get("plugin_response")
    assert isinstance(plugin_response, dict)
    assert plugin_response.get("action") == "preset_percentage"


def test_plugins_execute_function_accepts_frontend_contract_for_business_letter(app_client: Any) -> None:
    response = app_client.post(
        "/api/plugins/execute-function",
        json={
            "plugin_id": "business_letter",
            "function_name": "create_document",
            "function_input": {
                "letter_type": "allgemein",
                "document_kind": "allgemein",
                "subject": "Frontend Vertragstest",
                "customer_name": "Muster GmbH",
            },
            "idempotency_key": "frontend-contract-001",
            "confirmed": False,
            "user_id": 17,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload.get("plugin_id") == "business_letter"
    assert payload.get("function_name") == "create_document"
    assert isinstance(payload.get("function_input"), dict)
    assert payload["function_input"].get("subject") == "Frontend Vertragstest"
    assert "plugin_input" not in payload
    assert payload.get("idempotency", {}).get("status") in {"completed", "replayed"}


def test_plugins_execute_function_returns_pending_confirmation_and_confirm_executes(
    app_client: Any,
    monkeypatch: MonkeyPatch,
) -> None:
    from app.tools.executor import PluginExecutor

    original = PluginExecutor.resolve_execution_target

    def _patched(self, plugin_id: str, input_data: dict[str, Any], *, function_name: str | None = None):
        definition, function_meta, payload, resolved_function_name = original(
            self,
            plugin_id,
            input_data,
            function_name=function_name,
        )
        if plugin_id == "calculator" and resolved_function_name == "evaluate":
            patched_meta = dict(function_meta)
            patched_meta["requires_confirmation"] = True
            return definition, patched_meta, payload, resolved_function_name
        return definition, function_meta, payload, resolved_function_name

    monkeypatch.setattr("app.tools.executor.PluginExecutor.resolve_execution_target", _patched)

    pending_response = app_client.post(
        "/api/plugins/execute-function",
        json={
            "plugin_id": "calculator",
            "function_name": "evaluate",
            "function_input": {"expression": "2+2"},
            "user_id": 7,
        },
    )

    assert pending_response.status_code == 200
    pending_body = _assert_success_or_raise(pending_response)
    assert pending_body.get("status") == "pending_confirmation"
    confirmation = pending_body.get("confirmation")
    assert isinstance(confirmation, dict)
    confirmation_id = confirmation.get("confirmation_id")
    assert isinstance(confirmation_id, str)

    confirm_response = app_client.post(
        f"/api/plugins/confirmations/{confirmation_id}/confirm",
        json={"user_id": 7},
    )

    assert confirm_response.status_code == 200
    confirm_body = _assert_success_or_raise(confirm_response)
    assert confirm_body.get("status") == "executed"
    plugin_response = confirm_body.get("plugin_response")
    assert isinstance(plugin_response, dict)
    assert plugin_response.get("result") == 4


def test_plugins_confirmation_reject_marks_pending_call_rejected(
    app_client: Any,
    monkeypatch: MonkeyPatch,
) -> None:
    from app.tools.executor import PluginExecutor

    original = PluginExecutor.resolve_execution_target

    def _patched(self, plugin_id: str, input_data: dict[str, Any], *, function_name: str | None = None):
        definition, function_meta, payload, resolved_function_name = original(
            self,
            plugin_id,
            input_data,
            function_name=function_name,
        )
        if plugin_id == "calculator" and resolved_function_name == "evaluate":
            patched_meta = dict(function_meta)
            patched_meta["requires_confirmation"] = True
            return definition, patched_meta, payload, resolved_function_name
        return definition, function_meta, payload, resolved_function_name

    monkeypatch.setattr("app.tools.executor.PluginExecutor.resolve_execution_target", _patched)

    pending_response = app_client.post(
        "/api/plugins/execute-function",
        json={
            "plugin_id": "calculator",
            "function_name": "evaluate",
            "function_input": {"expression": "8/2"},
            "user_id": 11,
        },
    )

    assert pending_response.status_code == 200
    pending_body = _assert_success_or_raise(pending_response)
    confirmation = pending_body.get("confirmation")
    assert isinstance(confirmation, dict)
    confirmation_id = confirmation.get("confirmation_id")
    assert isinstance(confirmation_id, str)

    reject_response = app_client.post(
        f"/api/plugins/confirmations/{confirmation_id}/reject",
        json={"user_id": 11},
    )

    assert reject_response.status_code == 200
    reject_body = _assert_success_or_raise(reject_response)
    assert reject_body.get("status") == "rejected"


def test_plugins_confirmation_confirm_rejects_team_mismatch(
    app_client: Any,
    monkeypatch: MonkeyPatch,
) -> None:
    from app.tools.executor import PluginExecutor

    original = PluginExecutor.resolve_execution_target

    def _patched(self, plugin_id: str, input_data: dict[str, Any], *, function_name: str | None = None):
        definition, function_meta, payload, resolved_function_name = original(
            self,
            plugin_id,
            input_data,
            function_name=function_name,
        )
        if plugin_id == "calculator" and resolved_function_name == "evaluate":
            patched_meta = dict(function_meta)
            patched_meta["requires_confirmation"] = True
            return definition, patched_meta, payload, resolved_function_name
        return definition, function_meta, payload, resolved_function_name

    monkeypatch.setattr("app.tools.executor.PluginExecutor.resolve_execution_target", _patched)

    pending_response = app_client.post(
        "/api/plugins/execute-function",
        json={
            "plugin_id": "calculator",
            "function_name": "evaluate",
            "function_input": {"expression": "3*3"},
            "user_id": 14,
            "team_id": 100,
        },
    )

    assert pending_response.status_code == 200
    pending_body = _assert_success_or_raise(pending_response)
    confirmation = pending_body.get("confirmation")
    assert isinstance(confirmation, dict)
    confirmation_id = confirmation.get("confirmation_id")
    assert isinstance(confirmation_id, str)

    mismatch_response = app_client.post(
        f"/api/plugins/confirmations/{confirmation_id}/confirm",
        json={"user_id": 14, "team_id": 101},
    )

    assert mismatch_response.status_code == 403
    body = mismatch_response.json()
    assert _error_code(body) == "plugin_confirmation_team_mismatch"


def test_plugins_confirmation_confirm_can_only_be_claimed_once(
    app_client: Any,
    monkeypatch: MonkeyPatch,
) -> None:
    from app.tools.executor import PluginExecutor

    original = PluginExecutor.resolve_execution_target

    def _patched(self, plugin_id: str, input_data: dict[str, Any], *, function_name: str | None = None):
        definition, function_meta, payload, resolved_function_name = original(
            self,
            plugin_id,
            input_data,
            function_name=function_name,
        )
        if plugin_id == "calculator" and resolved_function_name == "evaluate":
            patched_meta = dict(function_meta)
            patched_meta["requires_confirmation"] = True
            return definition, patched_meta, payload, resolved_function_name
        return definition, function_meta, payload, resolved_function_name

    monkeypatch.setattr("app.tools.executor.PluginExecutor.resolve_execution_target", _patched)

    pending_response = app_client.post(
        "/api/plugins/execute-function",
        json={
            "plugin_id": "calculator",
            "function_name": "evaluate",
            "function_input": {"expression": "9/3"},
            "user_id": 15,
        },
    )

    assert pending_response.status_code == 200
    pending_body = _assert_success_or_raise(pending_response)
    confirmation = pending_body.get("confirmation")
    assert isinstance(confirmation, dict)
    confirmation_id = confirmation.get("confirmation_id")
    assert isinstance(confirmation_id, str)

    first_confirm = app_client.post(
        f"/api/plugins/confirmations/{confirmation_id}/confirm",
        json={"user_id": 15},
    )
    assert first_confirm.status_code == 200

    second_confirm = app_client.post(
        f"/api/plugins/confirmations/{confirmation_id}/confirm",
        json={"user_id": 15},
    )
    assert second_confirm.status_code == 409
    second_body = second_confirm.json()
    assert _error_code(second_body) == "plugin_confirmation_not_pending"


def test_plugins_execute_function_idempotency_replays_completed_result(app_client: Any) -> None:
    payload = {
        "plugin_id": "business_letter",
        "function_name": "create_document",
        "function_input": {
            "letter_type": "allgemein",
            "customer_name": "Max Mustermann",
            "subject": "Rueckfrage",
        },
        "idempotency_key": "idem-bl-001",
        "user_id": 3,
    }

    first_response = app_client.post("/api/plugins/execute-function", json=payload)
    assert first_response.status_code == 200
    first_body = _assert_success_or_raise(first_response)
    first_plugin_response = first_body.get("plugin_response")
    assert isinstance(first_plugin_response, dict)

    second_response = app_client.post("/api/plugins/execute-function", json=payload)
    assert second_response.status_code == 200
    second_body = _assert_success_or_raise(second_response)
    second_plugin_response = second_body.get("plugin_response")
    assert second_body.get("idempotency", {}).get("status") == "replayed"
    assert second_plugin_response == first_plugin_response


def test_plugins_execute_function_idempotency_conflict_for_different_arguments(app_client: Any) -> None:
    first = app_client.post(
        "/api/plugins/execute-function",
        json={
            "plugin_id": "business_letter",
            "function_name": "create_document",
            "function_input": {
                "letter_type": "allgemein",
                "customer_name": "Max Mustermann",
                "subject": "Erste Version",
            },
            "idempotency_key": "idem-bl-002",
            "user_id": 4,
        },
    )
    assert first.status_code == 200

    conflict = app_client.post(
        "/api/plugins/execute-function",
        json={
            "plugin_id": "business_letter",
            "function_name": "create_document",
            "function_input": {
                "letter_type": "allgemein",
                "customer_name": "Max Mustermann",
                "subject": "Andere Version",
            },
            "idempotency_key": "idem-bl-002",
            "user_id": 4,
        },
    )

    assert conflict.status_code == 400
    body = conflict.json()
    assert _error_code(body) == "plugin_idempotency_conflict"


def test_plugins_execute_function_idempotency_lease_timeout_allows_retry(app_client: Any) -> None:
    import sqlite3
    from datetime import datetime, timedelta, timezone

    from app.core.config import get_config

    payload = {
        "plugin_id": "business_letter",
        "function_name": "create_document",
        "function_input": {
            "letter_type": "allgemein",
            "customer_name": "Max Mustermann",
            "subject": "Lease Test",
        },
        "idempotency_key": "idem-bl-lease-001",
        "user_id": 22,
        "team_id": 5,
    }

    first_response = app_client.post("/api/plugins/execute-function", json=payload)
    assert first_response.status_code == 200

    database_url = get_config().database_url
    sqlite_path = database_url.replace("sqlite+aiosqlite:///", "", 1)
    now = datetime.now(timezone.utc)

    with sqlite3.connect(sqlite_path) as connection:
        connection.execute(
            """
            UPDATE plugin_idempotency_records
            SET status = ?, response_json = ?, lease_expires_at = ?
            WHERE plugin_id = ? AND function_name = ? AND idempotency_key = ?
            """,
            (
                "in_progress",
                None,
                (now + timedelta(minutes=10)).isoformat(),
                "business_letter",
                "create_document",
                "idem-bl-lease-001",
            ),
        )
        connection.commit()

    blocked_response = app_client.post("/api/plugins/execute-function", json=payload)
    assert blocked_response.status_code == 400
    blocked_body = blocked_response.json()
    assert _error_code(blocked_body) == "plugin_idempotency_in_progress"

    with sqlite3.connect(sqlite_path) as connection:
        connection.execute(
            """
            UPDATE plugin_idempotency_records
            SET lease_expires_at = ?
            WHERE plugin_id = ? AND function_name = ? AND idempotency_key = ?
            """,
            (
                (now - timedelta(minutes=10)).isoformat(),
                "business_letter",
                "create_document",
                "idem-bl-lease-001",
            ),
        )
        connection.commit()

    retry_response = app_client.post("/api/plugins/execute-function", json=payload)
    assert retry_response.status_code == 200
    retry_body = _assert_success_or_raise(retry_response)
    assert retry_body.get("idempotency", {}).get("status") == "completed"
