from __future__ import annotations

import json
import os
from pathlib import Path

from app.database.session import get_session_maker
from app.db_models.model_config import ModelConfig
from tests.integration.async_utils import run_async


def _run(coro):
	return run_async(coro)


def _create_user(app_client, username: str) -> int:
	response = app_client.post(
		"/api/auth/register",
		json={"username": username, "password": "Test#2026"},
	)
	assert response.status_code == 200
	return int(response.json()["user"]["id"])


def _create_user_with_token(app_client, username: str) -> tuple[int, str]:
	response = app_client.post(
		"/api/auth/register",
		json={"username": username, "password": "Test#2026"},
	)
	assert response.status_code == 200
	payload = response.json()
	return int(payload["user"]["id"]), str(payload["access_token"])


def _auth_headers(token: str) -> dict[str, str]:
	return {"Authorization": f"Bearer {token}"}


def _create_model(model_name: str, model_path: str) -> int:
	async def _insert_model() -> int:
		session_maker = get_session_maker()
		async with session_maker() as session:
			model = ModelConfig(
				name=model_name,
				model_path=model_path,
				backend="transformers",
				model_type="text_generation",
				model_format="transformers_safetensors",
				is_available=True,
				is_active=False,
				load_status="unloaded",
			)
			session.add(model)
			await session.flush()
			await session.commit()
			return int(model.id)

	return _run(_insert_model())


def test_post_user_only_message_persists_and_is_listed(app_client):
	user_id = _create_user(app_client, "chat-api-user-only")
	create_response = app_client.post(
		"/api/messages/user-only",
		json={"user_id": user_id, "message": "Hallo Team"},
	)
	assert create_response.status_code == 200

	payload = create_response.json()
	conversation_id = payload["conversation_id"]
	assert isinstance(conversation_id, int)

	list_response = app_client.get(
		"/api/messages",
		params={"conversation_id": conversation_id, "user_id": user_id, "limit": 10},
	)
	assert list_response.status_code == 200

	items = list_response.json()["items"]
	assert len(items) >= 1
	assert items[-1]["role"] == "user"
	assert items[-1]["content"] == "Hallo Team"


def test_chat_stream_returns_standardized_error_envelope_for_missing_conversation(app_client):
	user_id = _create_user(app_client, "chat-api-stream-error")
	from app.models.manager import model_manager

	class _HealthyBackend:
		def health_check(self) -> bool:
			return True

		def unload(self) -> None:
			return None

	model_manager.active_backend = _HealthyBackend()
	model_manager.active_model_id = 999

	with app_client.stream(
		"POST",
		"/api/chat/generate",
		json={
			"user_id": user_id,
			"conversation_id": 999999,
			"message": "test",
			"stream": True,
		},
	) as response:
		assert response.status_code == 200
		stream_text = ""
		for chunk in response.iter_text():
			stream_text += chunk

	assert "event: error" in stream_text

	data_index = stream_text.find("data:")
	assert data_index != -1, stream_text
	data_payload_raw = stream_text[data_index + len("data:") :].strip()
	data_payload, _ = json.JSONDecoder().raw_decode(data_payload_raw)

	assert data_payload["error"]["code"] == "conversation.not_found"
	assert data_payload["error"]["message"] == "Conversation not found"
	assert data_payload["error"]["retry"]["retryable"] is False
	assert isinstance(data_payload["error"]["details"], dict)


def test_chat_context_usage_returns_server_computed_breakdown(app_client):
	user_id = _create_user(app_client, "chat-api-context-usage")
	seed_response = app_client.get("/api/workspace/sources", params={"user_id": user_id})
	assert seed_response.status_code == 200

	response = app_client.get("/api/chat/context-usage", params={"user_id": user_id})
	assert response.status_code == 200

	payload = response.json()
	assert isinstance(payload.get("context_limit_tokens"), int)
	assert isinstance(payload.get("used_context_tokens"), int)
	assert isinstance(payload.get("usage_ratio"), float)

	breakdown = payload.get("breakdown")
	assert isinstance(breakdown, dict)
	for key in [
		"system_prompt_tokens",
		"chat_history_tokens",
		"external_data_tokens",
		"files_tokens",
		"output_reserve_tokens",
		"safety_margin_tokens",
	]:
		assert isinstance(breakdown.get(key), int)

	assert breakdown["external_data_tokens"] >= 0
	assert breakdown["files_tokens"] >= 0

	external_data = payload.get("external_data")
	assert isinstance(external_data, dict)
	assert isinstance(external_data.get("integrated"), bool)
	assert isinstance(external_data.get("sources_count"), int)
	assert isinstance(external_data.get("selected_count"), int)
	assert isinstance(external_data.get("selected_sources"), list)
	assert external_data["selected_count"] >= 0


def test_chat_generate_applies_model_scoped_prompt_and_generation_settings(app_client, tmp_path: Path):
	user_id, token = _create_user_with_token(app_client, "chat-api-model-scoped")
	from app.models.manager import model_manager
	model_id = _create_model("chat-api-model", str((tmp_path / "chat-api-model.safetensors").resolve(strict=False)))

	class _CapturingBackend:
		def __init__(self):
			self.last_prompt = ""
			self.last_config: dict[str, object] = {}

		def health_check(self) -> bool:
			return True

		def unload(self) -> None:
			return None

		def generate(self, prompt: str, config: dict[str, object]) -> str:
			self.last_prompt = prompt
			self.last_config = config
			return "ok"

	backend = _CapturingBackend()
	model_manager.active_backend = backend
	model_manager.active_model_id = model_id

	for category, key, value in [
		("prompt", f"model_{model_id}_system_prompt", "Antwort nur in JSON."),
		("chat", f"model_{model_id}_temperature", 0.0),
		("chat", f"model_{model_id}_max_new_tokens", 1234),
		("chat", f"model_{model_id}_top_k", 6),
		("chat", f"model_{model_id}_top_p", 0.85),
		("chat", f"model_{model_id}_repetition_penalty", 1.1),
		("chat", f"model_{model_id}_do_sample", False),
		("chat", f"model_{model_id}_seed", 99),
		("chat", f"model_{model_id}_stop_sequences", ["<end_of_turn>", "<eos>"]),
	]:
		update_response = app_client.post(
			"/api/settings",
			json={
				"category": category,
				"key": key,
				"value": value,
				"user_id": user_id,
			},
			headers=_auth_headers(token),
		)
		assert update_response.status_code == 200

	response = app_client.post(
		"/api/chat/generate",
		json={
			"user_id": user_id,
			"message": "Bitte Status liefern",
			"model_id": model_id,
			"stream": False,
		},
	)
	assert response.status_code == 200

	assert backend.last_prompt.startswith("System: Antwort nur in JSON.")
	assert backend.last_config["max_new_tokens"] == 1234
	assert backend.last_config["temperature"] == 0.0
	assert backend.last_config["top_k"] == 6
	assert backend.last_config["top_p"] == 0.85
	assert backend.last_config["repetition_penalty"] == 1.1
	assert backend.last_config["do_sample"] is False
	assert backend.last_config["seed"] == 99
	assert backend.last_config["stop"] == ["<end_of_turn>", "<eos>"]


def test_prompt_diagnostics_endpoint_is_disabled_by_default(app_client):
	response = app_client.get("/api/chat/diagnostics/prompts")
	assert response.status_code == 404


def test_prompt_diagnostics_endpoint_returns_recent_entries_in_local_mode(app_client):
	user_id = _create_user(app_client, "chat-api-diagnostics")
	from app.models.manager import model_manager

	class _CapturingBackend:
		def health_check(self) -> bool:
			return True

		def unload(self) -> None:
			return None

		def generate(self, prompt: str, config: dict[str, object]) -> str:
			return "ok"

	backend = _CapturingBackend()
	model_manager.active_backend = backend
	model_manager.active_model_id = 27
	model_manager.active_backend_name = "transformers"

	previous = os.environ.get("LOCAL_PROMPT_DIAGNOSTICS")
	os.environ["LOCAL_PROMPT_DIAGNOSTICS"] = "1"
	try:
		generate_response = app_client.post(
			"/api/chat/generate",
			json={
				"user_id": user_id,
				"message": "Bitte antworte kurz.",
				"stream": False,
			},
		)
		assert generate_response.status_code == 200

		diagnostics_response = app_client.get("/api/chat/diagnostics/prompts", params={"user_id": user_id, "limit": 5})
		assert diagnostics_response.status_code == 200

		payload = diagnostics_response.json()
		assert payload["enabled"] is True
		assert isinstance(payload.get("items"), list)
		assert payload["items"]
		entry = payload["items"][-1]
		assert entry.get("user_id") == user_id
		assert entry.get("chat_template_source") == "tokenizer_config"
		assert isinstance(payload.get("dependencies"), dict)
		assert "onnxruntime_installed" in payload["dependencies"]
	finally:
		if previous is None:
			os.environ.pop("LOCAL_PROMPT_DIAGNOSTICS", None)
		else:
			os.environ["LOCAL_PROMPT_DIAGNOSTICS"] = previous

