import asyncio
from types import SimpleNamespace

from app.chat.service import ChatService


def _run(coro):
	return asyncio.run(coro)


def test_retrieval_skips_irrelevant_knowledge_for_generic_question() -> None:
	service = ChatService(session=SimpleNamespace())

	async def fake_list_documents(*, user_id: int, limit: int = 200):
		assert user_id == 3
		return [
			{
				"id": 10,
				"file": "naturstein_fugenhandbuch.pdf",
				"position": "Abschnitt 2",
				"relevance": "81%",
				"status": "ready",
				"source": "Upload",
			},
			{
				"id": 11,
				"file": "naturstein_pflege.txt",
				"position": "Abschnitt 1",
				"relevance": "67%",
				"status": "ready",
				"source": "Upload",
			},
		]

	async def fake_get_setting(*, category: str, key: str, user_id: int, request_value=None):
		assert category == "knowledge"
		assert user_id == 3
		if key == "min_score_ratio":
			return 0.5
		if key == "min_absolute_score":
			return 1000
		if key == "min_score_gap":
			return 400
		return None

	service.knowledge_repo = SimpleNamespace(list_documents=fake_list_documents)
	service.settings_service = SimpleNamespace(get=fake_get_setting)

	selected, knowledge_messages, top_k, diagnostics = _run(
		service._select_retrieval_sources(
			user_id=3,
			user_message="Kannst du mir ein Rezept fuer Tomatensuppe geben?",
			model_id=27,
			retrieval_top_k_override=6,
		)
	)

	assert top_k == 6
	assert selected == []
	assert knowledge_messages == ["Keine relevanten externen Quellen gefunden."]
	assert diagnostics
	assert all(item["selected"] is False for item in diagnostics)


def test_retrieval_selects_relevant_chunks_and_records_scores() -> None:
	service = ChatService(session=SimpleNamespace())

	async def fake_list_documents(*, user_id: int, limit: int = 200):
		assert user_id == 3
		return [
			{
				"id": 20,
				"file": "naturstein_verlegung_guide.pdf",
				"position": "Kapitel 4",
				"relevance": "92%",
				"status": "ready",
				"source": "Upload",
			},
			{
				"id": 21,
				"file": "rezepte_tomatensuppe.md",
				"position": "Abschnitt 1",
				"relevance": "88%",
				"status": "ready",
				"source": "Upload",
			},
		]

	async def fake_get_setting(*, category: str, key: str, user_id: int, request_value=None):
		assert category == "knowledge"
		assert user_id == 3
		if key == "min_score_ratio":
			return 0.5
		if key == "min_absolute_score":
			return 1000
		if key == "min_score_gap":
			return 400
		return None

	service.knowledge_repo = SimpleNamespace(list_documents=fake_list_documents)
	service.settings_service = SimpleNamespace(get=fake_get_setting)

	selected, knowledge_messages, _top_k, diagnostics = _run(
		service._select_retrieval_sources(
			user_id=3,
			user_message="Wie verlege ich Naturstein auf der Terrasse?",
			model_id=27,
			retrieval_top_k_override=3,
		)
	)

	assert selected
	assert selected[0]["file"] == "naturstein_verlegung_guide.pdf"
	assert knowledge_messages
	selected_diagnostics = [item for item in diagnostics if item["selected"]]
	assert selected_diagnostics
	assert selected_diagnostics[0]["file"] == "naturstein_verlegung_guide.pdf"
	assert selected_diagnostics[0]["normalized_score"] >= 0.5


def test_append_general_settings_self_knowledge_includes_user_values() -> None:
	service = ChatService(session=SimpleNamespace())
	calls: list[tuple[object | None, object | None, object | None]] = []

	async def fake_get_setting(*args, **kwargs):
		category = kwargs.get("category") if "category" in kwargs else (args[0] if len(args) > 0 else None)
		key = kwargs.get("key") if "key" in kwargs else (args[1] if len(args) > 1 else None)
		user_id = kwargs.get("user_id") if "user_id" in kwargs else (args[2] if len(args) > 2 else None)
		calls.append((category, key, user_id))
		key_text = str(key).lower()
		if "language" in key_text:
			return "en"
		if "theme" in key_text:
			return "dark"
		if "timezone" in key_text:
			return "America/New_York"
		return None

	service.settings_service = SimpleNamespace(get=fake_get_setting)

	result = _run(service._append_general_settings_self_knowledge(base_prompt="Du bist hilfreich.", user_id=7))

	assert calls
	assert all(category == "system" for category, _key, _user_id in calls)
	assert all(user_id == 7 for _category, _key, user_id in calls)
	assert any("language" in str(key).lower() for _category, key, _user_id in calls)
	assert any("theme" in str(key).lower() for _category, key, _user_id in calls)
	assert any("timezone" in str(key).lower() for _category, key, _user_id in calls)
	assert "Selbstwissen (Benutzer-Einstellungen):" in result
	assert "- Sprache: en" in result
	assert "- Theme: dark" in result
	assert "- Zeitzone: America/New_York" in result
	assert "- Lokale Zeit:" in result


def test_append_general_settings_self_knowledge_uses_fallback_on_settings_error() -> None:
	service = ChatService(session=SimpleNamespace())

	async def failing_get_setting(*, category: str, key: str, user_id: int, request_value=None):
		raise RuntimeError("settings unavailable")

	service.settings_service = SimpleNamespace(get=failing_get_setting)

	result = _run(service._append_general_settings_self_knowledge(base_prompt="Du bist hilfreich.", user_id=3))

	assert "- Sprache: de" in result
	assert "- Theme: system" in result
	assert "- Zeitzone: Europe/Berlin" in result


def test_retrieval_respects_conversation_project_hierarchy_scope() -> None:
	service = ChatService(session=SimpleNamespace())
	captured_scope: dict[str, object] = {}

	async def fake_list_documents_for_scope(*, user_id: int, project_ids: list[int], include_unassigned: bool, limit: int = 200):
		assert user_id == 3
		captured_scope["project_ids"] = list(project_ids)
		captured_scope["include_unassigned"] = include_unassigned
		return [
			{
				"id": 30,
				"file": "fussball_trainingsplan.md",
				"position": "Abschnitt 1",
				"relevance": "93%",
				"status": "ready",
				"source": "Upload",
				"project_id": 2,
			},
			{
				"id": 31,
				"file": "sportverein_satzung.pdf",
				"position": "Seite 2",
				"relevance": "76%",
				"status": "ready",
				"source": "Upload",
				"project_id": 1,
			},
		]

	async def fake_get_setting(*, category: str, key: str, user_id: int, request_value=None):
		assert user_id == 3
		if category == "knowledge":
			if key == "min_score_ratio":
				return 0.0
			if key == "min_absolute_score":
				return 0
			if key == "min_score_gap":
				return 99999
			return None
		if category == "chat" and key == "conversation_project_map":
			return {"55": 2}
		if category == "workspace" and key == "project_meta_map":
			return {
				"1": {"project_id": 1, "parent_project_id": None},
				"2": {"project_id": 2, "parent_project_id": 1},
				"3": {"project_id": 3, "parent_project_id": None},
			}
		return None

	service.knowledge_repo = SimpleNamespace(list_documents_for_scope=fake_list_documents_for_scope)
	service.settings_service = SimpleNamespace(get=fake_get_setting)

	selected, knowledge_messages, _top_k, diagnostics = _run(
		service._select_retrieval_sources(
			user_id=3,
			conversation_id=55,
			user_message="Bitte gib mir den Fussball Trainingsplan.",
			model_id=27,
			retrieval_top_k_override=3,
		)
	)

	assert captured_scope["project_ids"] == [1, 2]
	assert captured_scope["include_unassigned"] is False
	assert selected
	assert selected[0]["file"] == "fussball_trainingsplan.md"
	assert selected[0]["project_id"] == 2
	assert selected[0]["scope_depth"] == 1
	assert knowledge_messages
	assert diagnostics
	selected_diagnostics = [item for item in diagnostics if item["selected"]]
	assert selected_diagnostics
	assert selected_diagnostics[0]["project_id"] in {1, 2}
