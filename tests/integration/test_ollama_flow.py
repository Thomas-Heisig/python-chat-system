from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, cast

from _pytest.monkeypatch import MonkeyPatch

from app.models.ollama_integration import build_ollama_metadata
from app.models.ollama_pull_registry import ollama_pull_registry


def _cloud_scan_entry(model_name: str, *, installed: bool) -> dict[str, object]:
    metadata = build_ollama_metadata(
        model_name=model_name,
        source_kind="ollama_cloud",
        source_label="Ollama Cloud",
        details={"family": "qwen"},
        capability_names={"completion", "tools"},
        installed=installed,
    )
    return {
        "name": f"{model_name} (Ollama Cloud)",
        "model_path": f"ollama-cloud://{model_name}",
        "backend": "ollama",
        "model_format": "ollama",
        "task_type": "text_generation",
        "model_family": "qwen",
        "metadata": metadata,
    }


def _find_cloud_item(items: list[dict[str, Any]], model_name: str) -> dict[str, Any]:
    for item in items:
        if str(item.get("model_path") or "") == f"ollama-cloud://{model_name}":
            return item
    raise AssertionError(f"Cloud model not found: {model_name}")


def test_ollama_scan_select_activate_flow(app_client: Any, monkeypatch: MonkeyPatch) -> None:
    model_name = "qwen3:latest"
    installed_state = {"installed": False}

    monkeypatch.setattr("app.api.routes.models.discover_ollama_models", lambda: [_cloud_scan_entry(model_name, installed=False)])
    monkeypatch.setattr("app.api.routes.models.discover_openai_models", lambda api_key=None: [])
    monkeypatch.setattr("app.api.routes.models.get_ollama_local_models_payload", lambda: [])
    monkeypatch.setattr(
        "app.api.routes.models.is_ollama_model_installed",
        lambda name, local_models=None: bool(installed_state["installed"]),
    )
    monkeypatch.setattr(
        "app.api.routes.models.ModelLoaderRegistry.resolve",
        lambda self, model_format, task_type: SimpleNamespace(
            loader_id="ollama_chat",
            available=True,
            reason_unavailable=None,
        ),
    )

    from app.models.manager import model_manager

    class _HealthyBackend:
        def health_check(self) -> bool:
            return True

        def unload(self) -> None:
            return None

    async def _fake_load_model(*, model_id: int, model_path: str, backend_name: str, config: dict[str, Any]) -> None:
        model_manager.active_model_id = model_id
        model_manager.active_backend = cast(Any, _HealthyBackend())
        model_manager.active_backend_name = backend_name

    monkeypatch.setattr(model_manager, "load_model", _fake_load_model)

    scan_response = app_client.post("/api/models/scan")
    assert scan_response.status_code == 200

    list_before = app_client.get("/api/models")
    assert list_before.status_code == 200
    cloud_item = _find_cloud_item(list_before.json()["items"], model_name)
    assert cloud_item["source_kind"] == "ollama_cloud"
    assert cloud_item["ollama_installed"] is False
    assert "heruntergeladen" in (cloud_item.get("reason_unavailable") or "").lower()

    installed_state["installed"] = True
    activate_response = app_client.post(f"/api/models/{cloud_item['id']}/activate")
    assert activate_response.status_code == 200
    assert activate_response.json()["active_model_id"] == int(cloud_item["id"])

    list_after = app_client.get("/api/models")
    assert list_after.status_code == 200
    cloud_after = _find_cloud_item(list_after.json()["items"], model_name)
    assert cloud_after["is_active"] is True


def test_ollama_cancel_and_retry_flow(app_client: Any, monkeypatch: MonkeyPatch) -> None:
    model_name = "qwen3:latest"

    monkeypatch.setattr("app.api.routes.models.discover_ollama_models", lambda: [_cloud_scan_entry(model_name, installed=False)])
    monkeypatch.setattr("app.api.routes.models.discover_openai_models", lambda api_key=None: [])
    monkeypatch.setattr("app.api.routes.models.get_ollama_local_models_payload", lambda: [])
    monkeypatch.setattr("app.api.routes.models.is_ollama_model_installed", lambda name, local_models=None: False)
    monkeypatch.setattr("app.api.routes.models._run_ollama_pull_task", lambda **kwargs: asyncio.sleep(0))

    scan_response = app_client.post("/api/models/scan")
    assert scan_response.status_code == 200

    listed = app_client.get("/api/models")
    assert listed.status_code == 200
    cloud_item = _find_cloud_item(listed.json()["items"], model_name)
    model_id = int(cloud_item["id"])
    model_path = str(cloud_item["model_path"])

    pull_response = app_client.post(f"/api/models/{model_id}/pull")
    assert pull_response.status_code == 200
    assert pull_response.json()["started"] is True
    assert pull_response.json()["state"] == "queued"

    ollama_pull_registry.begin(model_path, state="pulling", detail="Download laeuft", progress_percent=10)

    cancel_response = app_client.post(f"/api/models/{model_id}/pull/cancel")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["cancelled"] is True
    assert cancel_response.json()["state"] == "cancelling"

    ollama_pull_registry.set(model_path, state="cancelled", detail="Download abgebrochen")

    retry_response = app_client.post(f"/api/models/{model_id}/pull")
    assert retry_response.status_code == 200
    assert retry_response.json()["started"] is True
    assert retry_response.json()["state"] == "queued"

    ollama_pull_registry.set(model_path, state="pulling", detail="Download laeuft", progress_percent=10)
    activate_while_pulling = app_client.post(f"/api/models/{model_id}/activate")
    assert activate_while_pulling.status_code == 409
    body = activate_while_pulling.json()
    assert body["error"]["code"] == "model.pull_in_progress"

    ollama_pull_registry.clear(model_path)
