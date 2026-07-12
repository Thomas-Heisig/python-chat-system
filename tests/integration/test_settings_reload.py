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
