import json
from sqlalchemy import select

from app.database.session import get_session_maker
from app.db_models.setting import Setting
from app.settings.repair import repair_invalid_settings
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


def test_settings_get_returns_default_general_values(app_client):
	user_id = _create_user(app_client, "settings-default-user")
	language_response = app_client.get("/api/settings/system/language", params={"user_id": user_id})
	theme_response = app_client.get("/api/settings/system/theme", params={"user_id": user_id})
	timezone_response = app_client.get("/api/settings/system/timezone", params={"user_id": user_id})

	assert language_response.status_code == 200
	assert theme_response.status_code == 200
	assert timezone_response.status_code == 200

	assert language_response.json()["value"] == "de"
	assert theme_response.json()["value"] == "system"
	assert timezone_response.json()["value"] == "Europe/Berlin"


def test_settings_update_and_get_general_values(app_client):
	user_id = _create_user(app_client, "settings-update-user")
	update_response = app_client.post(
		"/api/settings",
		json={
			"category": "system",
			"key": "timezone",
			"value": "America/New_York",
			"user_id": user_id,
		},
	)
	assert update_response.status_code == 200

	get_response = app_client.get("/api/settings/system/timezone", params={"user_id": user_id})
	assert get_response.status_code == 200
	assert get_response.json()["value"] == "America/New_York"


def test_settings_are_scoped_by_user(app_client):
	user_one_id = _create_user(app_client, "settings-user-one")
	user_two_id = _create_user(app_client, "settings-user-two")

	user_one_update = app_client.post(
		"/api/settings",
		json={
			"category": "system",
			"key": "language",
			"value": "en",
			"user_id": user_one_id,
		},
	)
	user_two_update = app_client.post(
		"/api/settings",
		json={
			"category": "system",
			"key": "language",
			"value": "de",
			"user_id": user_two_id,
		},
	)

	assert user_one_update.status_code == 200
	assert user_two_update.status_code == 200

	user_one_get = app_client.get("/api/settings/system/language", params={"user_id": user_one_id})
	user_two_get = app_client.get("/api/settings/system/language", params={"user_id": user_two_id})

	assert user_one_get.status_code == 200
	assert user_two_get.status_code == 200
	assert user_one_get.json()["value"] == "en"
	assert user_two_get.json()["value"] == "de"


def test_settings_update_rejects_invalid_timezone(app_client):
	user_id = _create_user(app_client, "settings-invalid-timezone-user")
	invalid_response = app_client.post(
		"/api/settings",
		json={
			"category": "system",
			"key": "timezone",
			"value": "Mars/Olympus",
			"user_id": user_id,
		},
	)

	assert invalid_response.status_code == 400


def test_settings_get_falls_back_when_persisted_model_base_directories_is_invalid_without_writing(app_client):
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

	response = app_client.get("/api/settings/model/base_directories")
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
	user_id = _create_user(app_client, "settings-heal-scope-user")

	global_update = app_client.post(
		"/api/settings",
		json={
			"category": "system",
			"key": "language",
			"value": "de",
		},
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

	user_response = app_client.get("/api/settings/system/language", params={"user_id": user_id})
	assert user_response.status_code == 200
	assert user_response.json()["value"] == "de"

	global_response = app_client.get("/api/settings/system/language")
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
