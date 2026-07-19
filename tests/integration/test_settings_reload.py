import json
import os
from contextlib import contextmanager
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database.session import get_session_maker
from app.db_models.setting import Setting
from app.db_models.team import Team
from app.db_models.user import User
from app.settings.repair import repair_invalid_settings
from tests.integration.async_utils import run_async


def _run(coro):
	return run_async(coro)


def _extract_error_detail(payload: dict) -> dict:
	detail = payload.get("detail")
	if isinstance(detail, dict):
		return detail

	error = payload.get("error")
	if isinstance(error, dict):
		details = error.get("details")
		if isinstance(details, dict):
			nested_detail = details.get("detail")
			if isinstance(nested_detail, dict):
				return nested_detail

		nested = error.get("detail")
		if isinstance(nested, dict):
			return nested
		if "code" in error or "field_errors" in error:
			return error

	return {}


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


def _promote_user_to_admin(user_id: int) -> None:
	async def promote() -> None:
		session_maker = get_session_maker()
		async with session_maker() as session:
			user = await session.get(User, user_id)
			assert user is not None
			user.is_admin = True
			await session.commit()

	_run(promote())


def _create_team(name: str) -> int:
	async def create() -> int:
		session_maker = get_session_maker()
		async with session_maker() as session:
			team = Team(name=name)
			session.add(team)
			await session.flush()
			team_id = int(team.id)
			await session.commit()
			return team_id

	return _run(create())


@contextmanager
def _client_for_database(db_file: Path):
	previous_database_url = os.environ.get("DATABASE_URL")
	os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file.as_posix()}"

	from app.core.config import get_config
	from app.database import connection as db_connection
	from app.database import session as db_session
	from app.models.manager import model_manager

	def _reset_runtime() -> None:
		backend = model_manager.active_backend
		unload = getattr(backend, "unload", None)
		if callable(unload):
			unload()

		model_manager.active_backend = None
		model_manager.active_model_id = None
		model_manager.active_backend_name = None

		get_config.cache_clear()
		db_connection._engine = None
		db_session._session_maker = None

	_reset_runtime()
	from app.main import app

	with TestClient(app) as client:
		yield client

	_reset_runtime()

	if previous_database_url is None:
		os.environ.pop("DATABASE_URL", None)
	else:
		os.environ["DATABASE_URL"] = previous_database_url


def test_settings_get_returns_default_general_values(app_client):
	user_id, token = _create_user_with_token(app_client, "settings-default-user")
	language_response = app_client.get("/api/settings/system/language", params={"user_id": user_id}, headers=_auth_headers(token))
	theme_response = app_client.get("/api/settings/system/theme", params={"user_id": user_id}, headers=_auth_headers(token))
	timezone_response = app_client.get("/api/settings/system/timezone", params={"user_id": user_id}, headers=_auth_headers(token))

	assert language_response.status_code == 200
	assert theme_response.status_code == 200
	assert timezone_response.status_code == 200

	assert language_response.json()["value"] == "de"
	assert theme_response.json()["value"] == "system"
	assert timezone_response.json()["value"] == "Europe/Berlin"


def test_settings_get_falls_back_for_model_scoped_chat_temperature(app_client):
	user_id, token = _create_user_with_token(app_client, "settings-model-temperature-user")
	response = app_client.get("/api/settings/chat/model_7_temperature", params={"user_id": user_id}, headers=_auth_headers(token))

	assert response.status_code == 200
	assert response.json()["value"] == 0.1


def test_settings_get_ignores_invalid_model_scoped_chat_temperature_and_uses_default(app_client):
	user_id, token = _create_user_with_token(app_client, "settings-invalid-model-temperature-user")

	async def insert_invalid_model_temperature() -> None:
		session_maker = get_session_maker()
		async with session_maker() as session:
			stmt = (
				select(Setting)
				.where(Setting.category == "chat")
				.where(Setting.key == "model_7_temperature")
				.where(Setting.user_id == user_id)
				.where(Setting.team_id.is_(None))
				.limit(1)
			)
			setting = (await session.execute(stmt)).scalar_one_or_none()
			if setting is None:
				setting = Setting(
					category="chat",
					key="model_7_temperature",
					user_id=user_id,
					team_id=None,
					value_json=json.dumps("0.7"),
				)
				session.add(setting)
			else:
				setting.value_json = json.dumps("0.7")
			await session.commit()

	_run(insert_invalid_model_temperature())

	response = app_client.get("/api/settings/chat/model_7_temperature", params={"user_id": user_id}, headers=_auth_headers(token))

	assert response.status_code == 200
	assert response.json()["value"] == 0.1


def test_settings_update_and_get_general_values(app_client):
	user_id, token = _create_user_with_token(app_client, "settings-update-user")
	update_response = app_client.post(
		"/api/settings",
		json={
			"category": "system",
			"key": "timezone",
			"value": "America/New_York",
			"user_id": user_id,
		},
		headers=_auth_headers(token),
	)
	assert update_response.status_code == 200

	get_response = app_client.get("/api/settings/system/timezone", params={"user_id": user_id}, headers=_auth_headers(token))
	assert get_response.status_code == 200
	assert get_response.json()["value"] == "America/New_York"


def test_settings_are_scoped_by_user(app_client):
	user_one_id, user_one_token = _create_user_with_token(app_client, "settings-user-one")
	user_two_id, user_two_token = _create_user_with_token(app_client, "settings-user-two")

	user_one_update = app_client.post(
		"/api/settings",
		json={
			"category": "system",
			"key": "language",
			"value": "en",
			"user_id": user_one_id,
		},
		headers=_auth_headers(user_one_token),
	)
	user_two_update = app_client.post(
		"/api/settings",
		json={
			"category": "system",
			"key": "language",
			"value": "de",
			"user_id": user_two_id,
		},
		headers=_auth_headers(user_two_token),
	)

	assert user_one_update.status_code == 200
	assert user_two_update.status_code == 200

	user_one_get = app_client.get("/api/settings/system/language", params={"user_id": user_one_id}, headers=_auth_headers(user_one_token))
	user_two_get = app_client.get("/api/settings/system/language", params={"user_id": user_two_id}, headers=_auth_headers(user_two_token))

	assert user_one_get.status_code == 200
	assert user_two_get.status_code == 200
	assert user_one_get.json()["value"] == "en"
	assert user_two_get.json()["value"] == "de"


def test_settings_update_rejects_invalid_timezone(app_client):
	user_id, token = _create_user_with_token(app_client, "settings-invalid-timezone-user")
	invalid_response = app_client.post(
		"/api/settings",
		json={
			"category": "system",
			"key": "timezone",
			"value": "Mars/Olympus",
			"user_id": user_id,
		},
		headers=_auth_headers(token),
	)

	assert invalid_response.status_code == 400


def test_settings_get_falls_back_when_persisted_model_base_directories_is_invalid_without_writing(app_client):
	admin_id, admin_token = _create_user_with_token(app_client, "settings-global-model-admin")
	_promote_user_to_admin(admin_id)

	async def insert_invalid_setting() -> None:
		session_maker = get_session_maker()
		async with session_maker() as session:
			stmt = (
				select(Setting)
				.where(Setting.category == "model")
				.where(Setting.key == "base_directories")
				.where(Setting.user_id.is_(None))
				.where(Setting.team_id.is_(None))
				.limit(1)
			)
			setting = (await session.execute(stmt)).scalar_one()
			setting.value_json = json.dumps(["..\\forbidden", "   "])
			await session.commit()

	_run(insert_invalid_setting())

	response = app_client.get("/api/settings/model/base_directories", headers=_auth_headers(admin_token))
	assert response.status_code == 200
	value = response.json()["value"]
	assert isinstance(value, list)
	assert value
	assert all(isinstance(item, str) and item.strip() for item in value)

	async def assert_setting_not_repaired_by_get() -> None:
		session_maker = get_session_maker()
		async with session_maker() as session:
			stmt = (
				select(Setting)
				.where(Setting.category == "model")
				.where(Setting.key == "base_directories")
				.where(Setting.user_id.is_(None))
				.where(Setting.team_id.is_(None))
				.limit(1)
			)
			setting = (await session.execute(stmt)).scalar_one()
			persisted_value = json.loads(setting.value_json)
			assert persisted_value == ["..\\forbidden", "   "]

	_run(assert_setting_not_repaired_by_get())


def test_settings_startup_repair_repairs_only_user_scope_for_invalid_setting(app_client):
	user_id, user_token = _create_user_with_token(app_client, "settings-heal-scope-user")
	admin_id, admin_token = _create_user_with_token(app_client, "settings-heal-scope-admin")
	_promote_user_to_admin(admin_id)

	global_update = app_client.post(
		"/api/settings",
		json={
			"category": "system",
			"key": "language",
			"value": "de",
		},
		headers=_auth_headers(admin_token),
	)
	assert global_update.status_code == 200

	async def set_invalid_user_language() -> None:
		session_maker = get_session_maker()
		async with session_maker() as session:
			stmt = (
				select(Setting)
				.where(Setting.category == "system")
				.where(Setting.key == "language")
				.where(Setting.user_id == user_id)
				.where(Setting.team_id.is_(None))
				.limit(1)
			)
			setting = (await session.execute(stmt)).scalar_one_or_none()
			if setting is None:
				setting = Setting(
					category="system",
					key="language",
					user_id=user_id,
					team_id=None,
					value_json=json.dumps("zz"),
				)
				session.add(setting)
			else:
				setting.value_json = json.dumps("zz")
			await session.commit()

	_run(set_invalid_user_language())

	async def run_startup_repair_job() -> None:
		session_maker = get_session_maker()
		async with session_maker() as session:
			await repair_invalid_settings(session)
			await session.commit()

	_run(run_startup_repair_job())

	user_response = app_client.get("/api/settings/system/language", params={"user_id": user_id}, headers=_auth_headers(user_token))
	assert user_response.status_code == 200
	assert user_response.json()["value"] == "de"

	global_response = app_client.get("/api/settings/system/language", headers=_auth_headers(admin_token))
	assert global_response.status_code == 200
	assert global_response.json()["value"] == "de"

	async def assert_user_row_was_healed_only() -> None:
		session_maker = get_session_maker()
		async with session_maker() as session:
			user_stmt = (
				select(Setting)
				.where(Setting.category == "system")
				.where(Setting.key == "language")
				.where(Setting.user_id == user_id)
				.where(Setting.team_id.is_(None))
				.limit(1)
			)
			user_setting = (await session.execute(user_stmt)).scalar_one()
			assert json.loads(user_setting.value_json) == "de"

			global_stmt = (
				select(Setting)
				.where(Setting.category == "system")
				.where(Setting.key == "language")
				.where(Setting.user_id.is_(None))
				.where(Setting.team_id.is_(None))
				.limit(1)
			)
			global_setting = (await session.execute(global_stmt)).scalar_one()
			assert json.loads(global_setting.value_json) == "de"

	_run(assert_user_row_was_healed_only())


def test_settings_cleanup_obsolete_chat_keys_endpoint_returns_stats_and_deletes_global_rows(app_client):
	admin_id, admin_token = _create_user_with_token(app_client, "settings-cleanup-admin")
	_promote_user_to_admin(admin_id)

	async def insert_obsolete_global_chat_rows() -> None:
		session_maker = get_session_maker()
		async with session_maker() as session:
			for key, value in [
				("temperature", 0.42),
				("max_new_tokens", 222),
			]:
				stmt = (
					select(Setting)
					.where(Setting.category == "chat")
					.where(Setting.key == key)
					.where(Setting.user_id.is_(None))
					.where(Setting.team_id.is_(None))
					.limit(1)
				)
				row = (await session.execute(stmt)).scalar_one_or_none()
				if row is None:
					row = Setting(
						category="chat",
						key=key,
						user_id=None,
						team_id=None,
						value_json=json.dumps(value),
					)
					session.add(row)
				else:
					row.value_json = json.dumps(value)
			await session.commit()

	_run(insert_obsolete_global_chat_rows())

	preview_response = app_client.post(
		"/api/settings/chat/cleanup-obsolete",
		params={"dry_run": True},
		headers=_auth_headers(admin_token),
	)
	assert preview_response.status_code == 200
	preview_payload = preview_response.json()
	assert preview_payload["dry_run"] is True
	assert preview_payload["category"] == "chat"
	assert preview_payload["matched_count"] >= 2
	assert preview_payload["remaining_count"] >= 2

	cleanup_response = app_client.post(
		"/api/settings/chat/cleanup-obsolete",
		params={"dry_run": False},
		headers=_auth_headers(admin_token),
	)
	assert cleanup_response.status_code == 200
	cleanup_payload = cleanup_response.json()
	assert cleanup_payload["dry_run"] is False
	assert cleanup_payload["deleted"] >= 2
	assert cleanup_payload["remaining_count"] == 0

	async def assert_obsolete_rows_removed() -> None:
		session_maker = get_session_maker()
		async with session_maker() as session:
			for key in ("temperature", "max_new_tokens"):
				stmt = (
					select(Setting)
					.where(Setting.category == "chat")
					.where(Setting.key == key)
					.where(Setting.user_id.is_(None))
					.where(Setting.team_id.is_(None))
					.limit(1)
				)
				row = (await session.execute(stmt)).scalar_one_or_none()
				assert row is None

	_run(assert_obsolete_rows_removed())


def test_plugin_settings_profile_persists_across_full_reload_and_new_session(tmp_path: Path):
	db_file = tmp_path / "settings-plugin-persist.db"
	username = "settings-plugin-persist-user"

	with _client_for_database(db_file) as first_client:
		user_id, token = _create_user_with_token(first_client, username)

		update_response = first_client.post(
			"/api/settings",
			json={
				"category": "plugins",
				"key": "business_letter_profile",
				"value": {
					"default_einvoice_standard": "zugferd",
					"default_einvoice_enabled": True,
					"default_payment_days": 30,
				},
				"user_id": user_id,
			},
				headers=_auth_headers(token),
		)
		assert update_response.status_code == 200

		first_get = first_client.get(
			"/api/settings/plugins/business_letter_profile",
			params={"user_id": user_id},
			headers=_auth_headers(token),
		)
		assert first_get.status_code == 200
		first_value = first_get.json()["value"]
		assert isinstance(first_value, dict)
		assert first_value["default_einvoice_standard"] == "zugferd"
		assert first_value["default_einvoice_enabled"] is True
		assert first_value["default_payment_days"] == 30

	with _client_for_database(db_file) as second_client:
		login_response = second_client.post(
			"/api/auth/login",
			json={"username": username, "password": "Test#2026"},
		)
		assert login_response.status_code == 200
		reloaded_user_id = int(login_response.json()["user"]["id"])

		token = str(login_response.json()["access_token"])
		second_get = second_client.get(
			"/api/settings/plugins/business_letter_profile",
			params={"user_id": reloaded_user_id},
			headers=_auth_headers(token),
		)
		assert second_get.status_code == 200
		second_value = second_get.json()["value"]
		assert isinstance(second_value, dict)
		assert second_value["default_einvoice_standard"] == "zugferd"
		assert second_value["default_einvoice_enabled"] is True
		assert second_value["default_payment_days"] == 30


def test_plugin_settings_profile_rejects_invalid_number_pattern(app_client):
	user_id, token = _create_user_with_token(app_client, "settings-plugin-invalid-pattern")

	response = app_client.post(
		"/api/settings",
		json={
			"category": "plugins",
			"key": "business_letter_profile",
			"value": {
				"document_number_pattern": "{prefix}-{year}",
			},
			"user_id": user_id,
		},
		headers=_auth_headers(token),
	)

	assert response.status_code == 400
	detail = _extract_error_detail(response.json())
	assert detail["code"] == "invalid_plugin_settings"
	assert detail["field_errors"]["document_number_pattern"] == "Pattern must include the token {sequence_text}."


def test_plugin_settings_profile_rejects_invalid_number_width(app_client):
	user_id, token = _create_user_with_token(app_client, "settings-plugin-invalid-width")

	response = app_client.post(
		"/api/settings",
		json={
			"category": "plugins",
			"key": "business_letter_profile",
			"value": {
				"document_number_width": 0,
			},
			"user_id": user_id,
		},
		headers=_auth_headers(token),
	)

	assert response.status_code == 400
	detail = _extract_error_detail(response.json())
	assert detail["code"] == "invalid_plugin_settings"
	assert detail["field_errors"]["document_number_width"] == "Expected an integer value between 1 and 12."


def test_plugin_settings_profile_rejects_invalid_number_start_value(app_client):
	user_id, token = _create_user_with_token(app_client, "settings-plugin-invalid-start-value")

	response = app_client.post(
		"/api/settings",
		json={
			"category": "plugins",
			"key": "business_letter_profile",
			"value": {
				"document_number_start_value": 0,
			},
			"user_id": user_id,
		},
		headers=_auth_headers(token),
	)

	assert response.status_code == 400
	detail = _extract_error_detail(response.json())
	assert detail["code"] == "invalid_plugin_settings"
	assert detail["field_errors"]["document_number_start_value"] == "Expected an integer start value greater than or equal to 1."


def test_plugin_settings_profile_rejects_conflicting_sequence_kinds(app_client):
	user_id, token = _create_user_with_token(app_client, "settings-plugin-sequence-conflict")

	response = app_client.post(
		"/api/settings",
		json={
			"category": "plugins",
			"key": "business_letter_profile",
			"value": {
				"rechnung_document_number_sequence_kind": "business_letter:shared",
				"gutschrift_document_number_sequence_kind": "business_letter:shared",
			},
			"user_id": user_id,
		},
		headers=_auth_headers(token),
	)

	assert response.status_code == 400
	detail = _extract_error_detail(response.json())
	assert detail["code"] == "invalid_plugin_settings"
	assert "rechnung_document_number_sequence_kind" in detail["field_errors"]
	assert "gutschrift_document_number_sequence_kind" in detail["field_errors"]


def test_plugin_settings_profile_rejects_unsafe_guest_database_path(app_client):
	user_id, token = _create_user_with_token(app_client, "settings-plugin-invalid-path")

	response = app_client.post(
		"/api/settings",
		json={
			"category": "plugins",
			"key": "business_letter_profile",
			"value": {
				"guest_system_database_path": "../outside/chat_system.db",
			},
			"user_id": user_id,
		},
		headers=_auth_headers(token),
	)

	assert response.status_code == 400
	detail = _extract_error_detail(response.json())
	assert detail["code"] == "invalid_plugin_settings"
	assert detail["field_errors"]["guest_system_database_path"] == "Path traversal segments are not allowed."


def test_plugin_settings_scope_matrix_global_team_user_resolution(app_client):
	user_id, user_token = _create_user_with_token(app_client, "settings-plugin-scope-matrix")
	admin_id, admin_token = _create_user_with_token(app_client, "settings-plugin-scope-admin")
	_promote_user_to_admin(admin_id)
	team_id = _create_team("settings-team-scope-matrix")

	global_update = app_client.post(
		"/api/settings",
		json={
			"category": "plugins",
			"key": "business_letter_profile",
			"value": {"default_payment_days": 10},
		},
		headers=_auth_headers(admin_token),
	)
	assert global_update.status_code == 200

	team_update = app_client.post(
		"/api/settings",
		json={
			"category": "plugins",
			"key": "business_letter_profile",
			"value": {"default_payment_days": 20},
			"team_id": team_id,
		},
		headers=_auth_headers(admin_token),
	)
	assert team_update.status_code == 200

	user_update = app_client.post(
		"/api/settings",
		json={
			"category": "plugins",
			"key": "business_letter_profile",
			"value": {"default_payment_days": 30},
			"user_id": user_id,
			"team_id": team_id,
		},
		headers=_auth_headers(user_token),
	)
	assert user_update.status_code == 200

	global_get = app_client.get("/api/settings/plugins/business_letter_profile", headers=_auth_headers(admin_token))
	assert global_get.status_code == 200
	assert global_get.json()["value"]["default_payment_days"] == 10

	team_get = app_client.get(
		"/api/settings/plugins/business_letter_profile",
		params={"team_id": team_id},
		headers=_auth_headers(admin_token),
	)
	assert team_get.status_code == 200
	assert team_get.json()["value"]["default_payment_days"] == 20

	user_team_get = app_client.get(
		"/api/settings/plugins/business_letter_profile",
		params={"user_id": user_id, "team_id": team_id},
		headers=_auth_headers(user_token),
	)
	assert user_team_get.status_code == 200
	assert user_team_get.json()["value"]["default_payment_days"] == 30

	user_without_team_get = app_client.get(
		"/api/settings/plugins/business_letter_profile",
		params={"user_id": user_id},
		headers=_auth_headers(user_token),
	)
	assert user_without_team_get.status_code == 200
	assert user_without_team_get.json()["value"]["default_payment_days"] == 10


def test_global_settings_are_admin_only(app_client):
	user_id, user_token = _create_user_with_token(app_client, "settings-global-non-admin")
	response = app_client.get("/api/settings/system/language", headers=_auth_headers(user_token))
	assert response.status_code == 403

	admin_id, admin_token = _create_user_with_token(app_client, "settings-global-admin")
	_promote_user_to_admin(admin_id)
	admin_response = app_client.get("/api/settings/system/language", headers=_auth_headers(admin_token))
	assert admin_response.status_code == 200


def test_team_settings_are_admin_only_without_team_membership_model(app_client):
	user_id, user_token = _create_user_with_token(app_client, "settings-team-non-admin")
	team_id = _create_team("settings-team-authz")
	response = app_client.get(
		"/api/settings/plugins/business_letter_profile",
		params={"team_id": team_id},
		headers=_auth_headers(user_token),
	)
	assert response.status_code == 403


def test_users_can_only_access_their_own_settings(app_client):
	owner_id, owner_token = _create_user_with_token(app_client, "settings-owner-user")
	other_id, other_token = _create_user_with_token(app_client, "settings-other-user")

	update_response = app_client.post(
		"/api/settings",
		json={
			"category": "system",
			"key": "language",
			"value": "en",
			"user_id": owner_id,
		},
		headers=_auth_headers(owner_token),
	)
	assert update_response.status_code == 200

	forbidden = app_client.get(
		"/api/settings/system/language",
		params={"user_id": owner_id},
		headers=_auth_headers(other_token),
	)
	assert forbidden.status_code == 403


def test_secret_settings_are_masked_by_default(app_client):
	admin_id, admin_token = _create_user_with_token(app_client, "settings-secret-admin")
	_promote_user_to_admin(admin_id)

	update_response = app_client.post(
		"/api/settings",
		json={
			"category": "integrations",
			"key": "chatgpt_api_key",
			"value": "sk-secret-123",
		},
		headers=_auth_headers(admin_token),
	)
	assert update_response.status_code == 200

	masked = app_client.get(
		"/api/settings/integrations/chatgpt_api_key",
		headers=_auth_headers(admin_token),
	)
	assert masked.status_code == 200
	assert masked.json()["value"] == "********"
