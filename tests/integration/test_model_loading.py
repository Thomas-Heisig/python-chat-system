from __future__ import annotations


def test_model_capabilities_endpoint_returns_supported_backends_and_runtime(app_client):
	response = app_client.get("/api/models/capabilities")
	assert response.status_code == 200

	payload = response.json()
	assert payload["required_chat_capabilities"] == ["text_generation", "chat_completion"]
	assert isinstance(payload["runtime"]["gpu_available"], bool)

	backends = payload["backends"]
	assert isinstance(backends, list)
	assert any(item["backend"] == "llama_cpp" for item in backends)

	llama = next(item for item in backends if item["backend"] == "llama_cpp")
	assert isinstance(llama["capabilities"], dict)
	assert llama["capabilities"].get("text_generation") is True
	assert llama["capabilities"].get("chat_completion") is True

	active = payload["active"]
	assert active["loaded"] is False
	assert active["model_id"] is None
	assert active["backend"] is None


def test_meta_capabilities_advertise_model_capabilities_feature(app_client):
	response = app_client.get("/api/meta/capabilities")
	assert response.status_code == 200

	payload = response.json()
	assert payload["features"].get("models.capabilities") is True
