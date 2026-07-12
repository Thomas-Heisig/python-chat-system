from __future__ import annotations

import json


def test_system_diagnostics_contains_core_runtime_fields(app_client):
	response = app_client.get("/api/system/diagnostics")
	assert response.status_code == 200

	payload = response.json()
	assert isinstance(payload.get("generated_at"), str)

	backend_status = payload.get("backend_status")
	assert isinstance(backend_status, dict)
	assert isinstance(backend_status.get("service_name"), str)
	assert "model_loaded" in backend_status

	python_info = payload.get("python")
	assert isinstance(python_info, dict)
	assert isinstance(python_info.get("version"), str)
	assert isinstance(python_info.get("executable"), str)

	cuda_info = payload.get("cuda")
	assert isinstance(cuda_info, dict)
	assert isinstance(cuda_info.get("available"), bool)

	ports_info = payload.get("ports")
	assert isinstance(ports_info, dict)
	assert isinstance(ports_info.get("listening"), list)

	paths_info = payload.get("paths")
	assert isinstance(paths_info, dict)
	assert isinstance(paths_info.get("cwd"), str)
	assert isinstance(paths_info.get("database_url"), str)
	assert "model_base_directories" in paths_info


def test_system_diagnostics_export_returns_downloadable_json(app_client):
	response = app_client.get("/api/system/diagnostics/export")
	assert response.status_code == 200
	assert response.headers.get("cache-control") == "no-store"

	content_disposition = response.headers.get("content-disposition", "")
	assert "attachment;" in content_disposition.lower()
	assert "diagnostics-" in content_disposition.lower()
	assert ".json" in content_disposition.lower()

	payload = json.loads(response.text)
	assert isinstance(payload, dict)
	assert isinstance(payload.get("generated_at"), str)