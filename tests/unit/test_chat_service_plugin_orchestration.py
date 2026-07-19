from __future__ import annotations

import asyncio

from app.chat.service import ChatService
from app.tools.executor import PluginExecutionError


class _FakeSettingsService:
    async def get(self, category: str, key: str, user_id: int | None = None, team_id: int | None = None, request_value: object | None = None) -> object:
        if category == "chat" and key == "plugin_orchestration_enabled":
            return True
        return None


class _FakePluginExecutor:
    def __init__(self) -> None:
        self.executed = False
        self.search_calls: list[tuple[str, int]] = []
        self.last_execution_context: dict[str, object] | None = None
        self.last_input_data: dict[str, object] | None = None

    def parse_markup(self, assistant_output: str) -> tuple[str, dict[str, object]]:
        if "<plugin_call>" not in assistant_output:
            raise PluginExecutionError("plugin_call_missing", "No plugin call found")
        return "calculator", {"expression": "2 + 2"}

    def search_plugins(self, query: str, *, limit: int = 3) -> list[dict[str, object]]:
        self.search_calls.append((query, limit))
        return [
            {
                "plugin_id": "business_letter",
                "score": 0.9,
                "decision": "direct_manifest",
                "auto_select": True,
                "reason": "Matched terms: dokumentanfrage",
                "summary": "Erstellt Geschaeftsdokumente.",
                "capabilities": ["document.invoice.create"],
            }
        ]

    async def execute(
        self,
        plugin_id: str,
        input_data: dict[str, object],
        plugin_settings: dict[str, object] | None = None,
        execution_context: dict[str, object] | None = None,
    ) -> dict[str, object]:
        self.executed = True
        self.last_execution_context = execution_context
        self.last_input_data = input_data
        return {"result": 4, "plugin_id": plugin_id, "input": input_data}


class _BusinessLetterFallbackPluginExecutor(_FakePluginExecutor):
    async def execute(
        self,
        plugin_id: str,
        input_data: dict[str, object],
        plugin_settings: dict[str, object] | None = None,
        execution_context: dict[str, object] | None = None,
    ) -> dict[str, object]:
        self.executed = True
        self.last_execution_context = execution_context
        self.last_input_data = input_data
        return {
            "success": True,
            "document_id": "doc_123",
            "document_type": "angebot",
            "status": "needs_review",
            "artifacts": [{"file_name": "Angebot-2026-0001.pdf"}],
            "validation": {"missing_information": []},
            "database": {
                "persisted": {
                    "tenant_id": "user:1",
                    "plugin_storage": {
                        "artifacts": [
                            {"artifact_kind": "pdf"},
                            {"artifact_kind": "json"},
                        ]
                    }
                }
            },
            "plugin_id": plugin_id,
            "input": input_data,
        }


class _PriceFinderAwarePluginExecutor(_BusinessLetterFallbackPluginExecutor):
    async def execute(
        self,
        plugin_id: str,
        input_data: dict[str, object],
        plugin_settings: dict[str, object] | None = None,
        execution_context: dict[str, object] | None = None,
    ) -> dict[str, object]:
        self.executed = True
        self.last_execution_context = execution_context
        self.last_input_data = input_data
        if plugin_id == "pricefinder":
            return {
                "success": True,
                "source": "internet",
                "currency": "EUR",
                "unit": "qm",
                "prices": {"min": 210.0, "avg": 240.0, "max": 275.0, "count": 5},
            }
        return await super().execute(plugin_id, input_data, plugin_settings, execution_context)


class _FakeExecutor:
    def __init__(self) -> None:
        self.calls: list[list[dict[str, str]]] = []

    async def generate(self, backend, prompt: str, config: dict[str, object]) -> str:
        chat_messages = config.get("chat_messages")
        if isinstance(chat_messages, list):
            self.calls.append([dict(item) for item in chat_messages if isinstance(item, dict)])

        if len(self.calls) == 1:
            return "<plugin_call>calculator</plugin_call><plugin_input>{\"expression\":\"2 + 2\"}</plugin_input>"
        return "Antwort: 4"


class _FallbackExecutor:
    def __init__(self) -> None:
        self.calls: list[list[dict[str, str]]] = []

    async def generate(self, backend, prompt: str, config: dict[str, object]) -> str:
        chat_messages = config.get("chat_messages")
        if isinstance(chat_messages, list):
            self.calls.append([dict(item) for item in chat_messages if isinstance(item, dict)])

        if len(self.calls) == 1:
            return "Bitte teile mir mehr Details mit."
        if len(self.calls) == 2:
            return "<plugin_call>calculator</plugin_call><plugin_input>{\"expression\":\"2 + 2\"}</plugin_input>"
        return "Antwort: 4"


class _DirectDocumentFallbackExecutor:
    def __init__(self) -> None:
        self.calls: list[list[dict[str, str]]] = []

    async def generate(self, backend, prompt: str, config: dict[str, object]) -> str:
        chat_messages = config.get("chat_messages")
        if isinstance(chat_messages, list):
            self.calls.append([dict(item) for item in chat_messages if isinstance(item, dict)])
        return "Hier ist ein Beispiel fuer ein Angebot."


def test_chat_service_orchestrates_plugin_calls_into_final_answer() -> None:
    service = ChatService.__new__(ChatService)
    service.executor = _FakeExecutor()
    service.plugin_executor = _FakePluginExecutor()
    service.settings_service = _FakeSettingsService()
    service._postprocess_model_output = lambda text: text.strip()

    result = asyncio.run(
        service._generate_with_optional_plugin_orchestration(
            user_id=1,
            backend=object(),
            prompt="ignored",
            config={"chat_messages": [{"role": "system", "content": "Du bist hilfreich."}]},
            user_message="Rechne 2 + 2",
        )
    )

    assert result == "Antwort: 4"
    assert service.plugin_executor.executed is True
    assert len(service.executor.calls) == 2
    assert service.executor.calls[1][-1]["content"].startswith("<plugin_response>")


def test_chat_service_injects_auto_discovery_for_document_requests() -> None:
    service = ChatService.__new__(ChatService)
    service.executor = _FallbackExecutor()
    service.plugin_executor = _FakePluginExecutor()
    service.settings_service = _FakeSettingsService()
    service._postprocess_model_output = lambda text: text.strip()

    result = asyncio.run(
        service._generate_with_optional_plugin_orchestration(
            user_id=1,
            backend=object(),
            prompt="ignored",
            config={"chat_messages": [{"role": "system", "content": "Du bist hilfreich."}]},
            user_message="Ich brauche eine Dokumentanfrage fuer eine Rechnung.",
        )
    )

    assert result
    assert service.plugin_executor.search_calls
    assert len(service.executor.calls) == 3
    assert service.executor.calls[1][-1]["content"].startswith("<plugin_search_response>")
    assert service.plugin_executor.executed is True


def test_chat_service_executes_direct_document_fallback_after_discovery() -> None:
    service = ChatService.__new__(ChatService)
    service.executor = _DirectDocumentFallbackExecutor()
    service.plugin_executor = _BusinessLetterFallbackPluginExecutor()
    service.settings_service = _FakeSettingsService()
    service._postprocess_model_output = lambda text: text.strip()
    service._load_plugin_settings = _FakeLoadPluginSettings()  # type: ignore[method-assign]

    result = asyncio.run(
        service._generate_with_optional_plugin_orchestration(
            user_id=1,
            backend=object(),
            prompt="ignored",
            config={"chat_messages": [{"role": "system", "content": "Du bist hilfreich."}]},
            user_message=(
                "Erstelle mir ein Angebot als PDF. Kunde ist Max Mustermann, "
                "Projekt Musterkueche 2026, Position: 1 Stueck Arbeitsplatte Nero Assoluto, "
                "Preis 2450 Euro netto, Lieferzeit 3 Wochen."
            ),
        )
    )

    assert "business_letter verarbeitet" in result
    assert "Angebot-2026-0001.pdf" in result
    assert "[[business_letter_result:" in result
    assert '"tenantId":"user:1"' in result
    assert service.plugin_executor.executed is True
    assert len(service.executor.calls) == 2


def test_chat_service_routes_document_request_before_model_generation() -> None:
    service = ChatService.__new__(ChatService)
    service.plugin_executor = _BusinessLetterFallbackPluginExecutor()
    service.settings_service = _FakeSettingsService()
    service._load_plugin_settings = _FakeLoadPluginSettings()  # type: ignore[method-assign]

    result = asyncio.run(
        service._try_direct_document_request_response(
            user_id=1,
            user_message=(
                "Bitte erstelle ein Angebot als PDF. Kunde: Max Mustermann, Firma: Mustermann Bau, "
                "Projekt: Eingangsbereich Naturstein, Positionen: Jura Kalkstein 12 qm à 85 Euro."
            ),
        )
    )

    assert result is not None
    assert "business_letter verarbeitet" in result
    assert "Angebot-2026-0001.pdf" in result
    assert "[[business_letter_result:" in result
    assert '"tenantId":"user:1"' in result
    assert service.plugin_executor.last_execution_context is not None
    assert str(service.plugin_executor.last_execution_context.get("idempotency_key") or "").startswith("chat-doc-1-")
    assert service.plugin_executor.last_input_data is not None
    assert "content" not in service.plugin_executor.last_input_data
    assert service.plugin_executor.last_input_data.get("tenant_id") == "user:1"


def test_chat_service_direct_document_route_can_enrich_prices_and_parse_freeform_recipient() -> None:
    service = ChatService.__new__(ChatService)
    service.plugin_executor = _PriceFinderAwarePluginExecutor()
    service.settings_service = _FakeSettingsService()
    service._load_plugin_settings = _FakeLoadPluginSettings()  # type: ignore[method-assign]

    result = asyncio.run(
        service._try_direct_document_request_response(
            user_id=1,
            user_message=(
                "erstelle ein angebot , ermittel die preie im durschschnitt im internet.\n\n"
                "Fensterbank Nero assoluto 3 cm Pol. 2,50 m * 0,30 m\n\n"
                "für Thomas Heisig\n"
                "wolfsheid e10 27777 Ganderkesee t_heisig@gmx.de"
            ),
        )
    )

    assert result is not None
    assert "angebot erstellt" in result
    assert service.plugin_executor.last_input_data is not None
    assert service.plugin_executor.last_input_data.get("customer_name") == "Thomas Heisig"
    assert service.plugin_executor.last_input_data.get("customer_street") == "wolfsheid e10"
    assert service.plugin_executor.last_input_data.get("customer_zip") == "27777"
    assert service.plugin_executor.last_input_data.get("customer_city") == "Ganderkesee"
    assert service.plugin_executor.last_input_data.get("recipient_email") == "t_heisig@gmx.de"
    positions = service.plugin_executor.last_input_data.get("positions")
    assert isinstance(positions, list) and positions
    first = positions[0]
    assert isinstance(first, dict)
    assert first.get("unit_code") == "MTK"
    assert first.get("price_net") == 240.0


class _FakeLoadPluginSettings:
    async def __call__(self, *, plugin_id: str, user_id: int) -> dict[str, object]:
        return {}
