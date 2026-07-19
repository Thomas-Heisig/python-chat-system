# 🔌 Plugin-Entwicklung – Vollständige Übersicht (Stand: 2026-06-28)

Dieses Dokument beschreibt die Plugin-Architektur, Entwicklungsrichtlinien und alle verfügbaren Plugins im System.

---

## 📋 Inhaltsverzeichnis

1. [Plugin-Standard & Schablone](#-plugin-standard--schablone)
2. [Verfügbare Plugins](#-verfügbare-plugins)
3. [Entwicklungsrichtlinien](#-entwicklungsrichtlinien)
4. Dynamische Settings
5. [Registrierung & Discovery](#-registrierung--discovery)
6. [Sicherheit & Sandboxing](#-sicherheit--sandboxing)
7. [Monitoring & Metriken](#-monitoring--metriken)
8. [Teams-Kompatibilität](#-teams-kompatibilität)
9. [Mobile-Kompatibilität](#-mobile-kompatibilität)
10. Admin-UI & Konfiguration
11. [Fehlerbehandlung & Debugging](#-fehlerbehandlung--debugging)
12. [Beispiel-Plugins](#-beispiel-plugins)

---

## 📦 Plugin-Standard & Schablone

Alle Plugins werden nach einer **einheitlichen Schablone** gebaut, damit Discovery, Settings-UI und Persistenz ohne Sonderlogik funktionieren.

### Verzeichnis-Struktur

Jedes Plugin bekommt einen eigenen Ordner:

```tree
packages/plugins/<plugin_id>/
├── plugin.py          # Haupt-Plugin-Code (Pflicht)
├── __init__.py        # Python-Paket-Datei
├── README.md          # Plugin-Dokumentation (optional, wird als Hilfe angezeigt)
└── __pycache__/       # Python-Cache (ignorieren)
```

### Pflichtprinzip: Meta-Settings dynamisch, nie hardcoded

- `settingsFields` werden **nur** in `PLUGIN_META` definiert.
- Die UI-Felder werden **dynamisch** aus dem Backend geladen.
- **Keine** hardcoded Feldlisten oder Default-Settings im Frontend.
- Backend-Katalog und Settings-Route sind die **einzige Quelle** für Plugin-Metadaten.

---

## 📄 plugin.py Schablone (verbindlich)

```python
from __future__ import annotations

from typing import Any


PLUGIN_META: dict[str, Any] = {
    "id": "example_plugin",
    "name": "Example Plugin",
    "description": "Kurze Beschreibung, was das Plugin macht.",
    "category": "Tools",
    "apiKeyRequired": False,
    "intentPattern": r"\b(example|demo)\b",
    "status": "implemented",  # planned | implemented
    "settingsFields": [
        {
            "key": "model",
            "label": "Modell",
            "type": "select",         # string | number | boolean | select
            "default": "default-model",
            "group": "Modell",        # optional, sonst "Allgemein"
            "options": [
                {"value": "default-model", "label": "Default"},
                {"value": "fast-model", "label": "Fast"},
            ],
        },
        {
            "key": "temperature",
            "label": "Temperature",
            "type": "number",
            "default": 0.7,
            "group": "Laufzeit",
        },
        {
            "key": "safe_mode",
            "label": "Safe Mode",
            "type": "boolean",
            "default": True,
            "group": "Sicherheit",
        },
    ],
}


class ExamplePlugin:
    name = "example_plugin"
    description = "Kurze Beschreibung, was das Plugin macht."

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Eingabe für das Plugin"},
        },
        "required": ["prompt"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "result": {"type": "string"},
            "error": {"type": "string"},
        },
    }

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        prompt = str(input_data.get("prompt", "")).strip()
        if not prompt:
            return {"error": "prompt ist erforderlich"}
        return {"result": f"ok: {prompt}"}
```

---

## 🔌 Verfügbare Plugins

| Plugin                 | ID                   | Kategorie                 | API-Key | Status |
| ---------------------- | -------------------- | ------------------------- | ------- | ------ |
| **WebSearch**          | `websearch`          | 🌐 Core / Web             | ❌      | ✅     |
| **DuckDuckGo Instant** | `ddg_instant`        | 🌐 Core / Web             | ❌      | ✅     |
| **Google Search**      | `google_search`      | 🌐 Core / Web             | ✅      | ✅     |
| **Bing Search**        | `bing_search`        | 🌐 Core / Web             | ✅      | ✅     |
| **Wikipedia**          | `wikipedia`          | 🌐 Core / Web             | ❌      | ✅     |
| **Calculator**         | `calculator`         | 🧠 NLP & Content          | ❌      | ✅     |
| **Text Analyzer**      | `text_analyzer`      | 🧠 NLP & Content          | ❌      | ✅     |
| **Summarizer**         | `summarizer`         | 🧠 NLP & Content          | ❌      | ✅     |
| **Tone Rewriter**      | `tone_rewriter`      | 🧠 NLP & Content          | ❌      | ✅     |
| **Grammar Checker**    | `grammar_checker`    | 🧠 NLP & Content          | ❌      | ✅     |
| **Translator**         | `translator`         | 🧠 NLP & Content          | ✅      | ✅     |
| **CodeInterpreter**    | `codeinterpreter`    | 🔧 Developer Tools        | ❌      | ✅     |
| **Jupyter Runner**     | `jupyter_runner`     | 🔧 Developer Tools        | ❌      | ✅     |
| **GitHub Search**      | `github_search`      | 🔧 Developer Tools        | ✅      | ✅     |
| **SQL Runner**         | `sql_runner`         | 🔧 Developer Tools        | ✅      | ✅     |
| **API Tester**         | `api_tester`         | 🔧 Developer Tools        | ❌      | ✅     |
| **Price Finder**       | `pricefinder`        | 🛒 E-Commerce & Preis     | ❌      | ✅     |
| **Product Catalog**    | `product_catalog`    | 🛒 E-Commerce & Preis     | ❌      | ✅     |
| **Stock Checker**      | `stock_checker`      | 🛒 E-Commerce & Preis     | ❌      | ✅     |
| **Offer Generator**    | `offer_generator`    | 🛒 E-Commerce & Preis     | ❌      | ✅     |
| **Weather**            | `weather`            | 🌐 Core / Web             | ✅      | ✅     |
| **News**               | `news`               | 📊 Business & Analytics   | ✅      | ✅     |
| **Stock Market**       | `stock_market`       | 📊 Business & Analytics   | ✅      | ✅     |
| **CRM HubSpot**        | `crm_hubspot`        | 📊 Business & Analytics   | ✅      | ✅     |
| **Odoo ERP**           | `erp_odoo`           | 📊 Business & Analytics   | ✅      | ✅     |
| **JTL Suite**          | `jtl_suite`          | 📊 Business & Analytics   | ✅      | ✅     |
| **Currency Converter** | `currency_converter` | 📊 Business & Analytics   | ✅      | ✅     |
| **Email**              | `email`              | 📱 Social & Communication | ✅      | ✅     |
| **WhatsApp**           | `whatsapp`           | 📱 Social & Communication | ✅      | ✅     |
| **Calendar**           | `calendar`           | 📱 Social & Communication | ✅      | ✅     |
| **Lead Capture**       | `lead_capture`       | 📱 Social & Communication | ❌      | ✅     |
| **Care Instructions**  | `care_instructions`  | 🏢 Spezial (Naturstein)   | ❌      | ✅     |
| **Installation Guide** | `installation_guide` | 🏢 Spezial (Naturstein)   | ❌      | ✅     |
| **Stone Colors**       | `stone_colors`       | 🏢 Spezial (Naturstein)   | ❌      | ✅     |
| **Stone Identifier**   | `stone_identifier`   | 🏢 Spezial (Naturstein)   | ❌      | ✅     |
| **OLLAMA API**         | `ollama_api`         | 🔌 Externe APIs           | ❌      | ✅     |
| **OpenAI API**         | `openai_api`         | 🔌 Externe APIs           | ✅      | ✅     |
| **DeepSeek API**       | `deepseek_api`       | 🔌 Externe APIs           | ✅      | ✅     |
| **Replicate API**      | `replicate_api`      | 🔌 Externe APIs           | ✅      | ✅     |
| **Hugging Face API**   | `huggingface_api`    | 🔌 Externe APIs           | ✅      | ✅     |

---

## 📝 Entwicklungsrichtlinien

### Clean-Contract

| Regel                          | Beschreibung                                                 |
| ------------------------------ | ------------------------------------------------------------ |
| **Deterministische Antworten** | Gleiche Eingabe → gleiche Ausgabe (keine Zufälle)            |
| **Strukturierte Fehler**       | `{"error": "...", "code": "...", "details": {...}}`          |
| **Timeouts absichern**         | Alle externen Aufrufe mit Timeout versehen                   |
| **Keine Secrets hardcoden**    | API-Keys aus `.env` oder Settings laden                      |
| **Input-Validierung**          | JSON-Schema validieren (siehe `input_schema`)                |
| **Output-Validierung**         | Antwort gegen `output_schema` prüfen                         |
| **settingsFields**             | Nur über `PLUGIN_META` definieren, nie im Frontend hardcoden |

### Unterstützte Feldtypen für `settingsFields`

| Typ       | Beschreibung     | Beispiel                               |
| --------- | ---------------- | -------------------------------------- |
| `string`  | Text-Eingabe     | `{"type": "string", "default": "..."}` |
| `number`  | Zahlen-Eingabe   | `{"type": "number", "default": 0.7}`   |
| `boolean` | Checkbox/Toggle  | `{"type": "boolean", "default": true}` |
| `select`  | Dropdown-Auswahl | `{"type": "select", "options": [...]}` |

### Beispiel mit Fehlerbehandlung

```python
import httpx
from app.plugins.base import Plugin

class MyExternalPlugin(Plugin):
    name = "myplugin"
    description = "Ruft externe API ab"
    input_schema = {"type": "object", "properties": {"query": {"type": "string"}}}
    output_schema = {"type": "object", "properties": {"result": {"type": "string"}}}
    requires_api_key = True
    timeout_ms = 10000

    async def execute(self, input_data: dict) -> dict:
        api_key = self.get_api_key()  # Aus Settings/DB
        if not api_key:
            return {"error": "API-Key nicht konfiguriert", "code": "MISSING_API_KEY"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout_ms/1000) as client:
                response = await client.get(
                    "https://api.example.com/query",
                    params={"q": input_data["query"]},
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                response.raise_for_status()
                return {"result": response.json()}
        except httpx.TimeoutException:
            return {"error": "Zeitüberschreitung", "code": "TIMEOUT"}
        except httpx.HTTPStatusError as e:
            return {"error": f"API-Fehler: {e.response.status_code}", "code": "API_ERROR"}
        except Exception as e:
            return {"error": str(e), "code": "UNKNOWN_ERROR"}
```

---

## ⚙️ Dynamische Settings (Datenfluss)

1. Plugin liefert `PLUGIN_META.settingsFields` in `packages/plugins/<plugin_id>/plugin.py`.
2. `packages/backend/app/plugins/catalog.py` normalisiert die Felddefinitionen.
3. `packages/backend/app/routes/settings.py` liefert pro Plugin `settingsFields` und `settingsValues`.
4. Frontend rendert Felder dynamisch im Popup (inkl. Gruppen via `group`).
5. Speichern erfolgt per PATCH; Werte werden pro Plugin persistiert.

---

## 🔍 Registrierung & Discovery

- Jeder Plugin-Unterordner mit `plugin.py` und `PLUGIN_META` wird automatisch erkannt.
- Liegt zusätzlich eine `README.md` im Plugin-Ordner, wird sie als Help-Popup im Frontend verfügbar gemacht.
- Das Backend scannt beim Startup `packages/plugins/` und lädt alle Plugins.

**Manuelle Registrierung (optional):**

```python
from app.plugins.registry import PluginRegistry
from my_custom_plugin import MyCustomPlugin

registry = PluginRegistry()
registry.register(MyCustomPlugin())
```

---

## 🔒 Sicherheit & Sandboxing

### Sicherheitsmaßnahmen

| Maßnahme                    | Beschreibung                                                     |
| --------------------------- | ---------------------------------------------------------------- |
| **Input-Validierung**       | JSON-Schema-Validierung vor Ausführung                           |
| **Timeout**                 | Maximale Ausführungszeit pro Plugin                              |
| **Rate-Limiting**           | Max. Aufrufe pro Benutzer/Zeitraum                               |
| **API-Key-Verschlüsselung** | Keys werden verschlüsselt in der DB gespeichert                  |
| **Keine Shell-Aufrufe**     | Plugins dürfen keine Shell-Befehle ausführen                     |
| **Kein Netzwerk**           | Plugins dürfen nur über konfigurierte Proxies/APIs kommunizieren |

---

## 📊 Monitoring & Metriken

### Prometheus-Metriken

| Metrik                    | Typ       | Labels             | Beschreibung                |
| ------------------------- | --------- | ------------------ | --------------------------- |
| `plugin_calls_total`      | Counter   | `plugin`, `status` | Gesamtaufrufe pro Plugin    |
| `plugin_errors_total`     | Counter   | `plugin`, `code`   | Fehler pro Plugin           |
| `plugin_duration_seconds` | Histogram | `plugin`           | Ausführungsdauer pro Plugin |

### Manuelle Instrumentierung

```python
from app.metrics import track_tool_call

class MyPlugin(Plugin):
    async def execute(self, input_data: dict) -> dict:
        import time
        start = time.time()
        try:
            result = await self._do_work(input_data)
            track_tool_call(self.name, time.time() - start, "success")
            return result
        except Exception as e:
            track_tool_call(self.name, time.time() - start, "error")
            raise
```

---

## 👥 Teams-Kompatibilität

| Regel                       | Beschreibung                                                        |
| --------------------------- | ------------------------------------------------------------------- |
| **Kontext respektieren**    | Ergebnisse nur für aktuelles Team/User bereitstellen                |
| **Keine teamfremden Daten** | Keine Daten aus anderen Teams ausgeben                              |
| **Reproduzierbarkeit**      | Gleiche Eingabe → gleiche Ergebnisse (keine teamabhängigen Effekte) |
| **Audit-Logging**           | Team-Zugehörigkeit im Audit-Log mitloggen                           |

---

## 📱 Mobile-Kompatibilität

| Regel                      | Beschreibung                                           |
| -------------------------- | ------------------------------------------------------ |
| **Schlankes Format**       | Ausgabe so kompakt wie möglich halten                  |
| **Markdown-Unterstützung** | Markdown wird in der App gerendert                     |
| **Keine großen Binaries**  | Statt Base64-Bildern → URLs liefern                    |
| **Responsive**             | Ergebnisse müssen auf kleinen Bildschirmen lesbar sein |

---

## 🖥️ Admin-UI & Konfiguration

**Pfad:** `Admin → Plugins`

**Funktionen:**

- Plugin-Liste mit Status (aktiv/inaktiv)
- Aktivieren/Deaktivieren per Toggle
- API-Key-Konfiguration (verschlüsselt)
- Timeout-Einstellung (pro Plugin)
- Test-Button (schnelle Validierung)
- Dynamische Felder aus `settingsFields`

---

## 🐛 Fehlerbehandlung & Debugging

### Fehler-Codes

| Code              | Bedeutung                        | Handlungsempfehlung                     |
| ----------------- | -------------------------------- | --------------------------------------- |
| `TIMEOUT`         | Plugin überschreitet Timeout     | Timeout erhöhen oder Plugin optimieren  |
| `MISSING_API_KEY` | API-Key nicht konfiguriert       | API-Key in Settings hinterlegen         |
| `INVALID_INPUT`   | Input entspricht nicht Schema    | Eingabe prüfen und korrigieren          |
| `API_ERROR`       | Externe API antwortet mit Fehler | API-Status prüfen, ggf. Fallback nutzen |
| `PLUGIN_ERROR`    | Allgemeiner Plugin-Fehler        | Plugin-Logs prüfen                      |

---

## 📂 Beispiel-Plugins

### Beispiel 1: Einfaches Plugin (Stateless)

```python
from app.plugins.base import Plugin

class HelloWorldPlugin(Plugin):
    name = "helloworld"
    description = "Sagt Hallo zur Welt"
    input_schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    output_schema = {"type": "object", "properties": {"greeting": {"type": "string"}}}

    async def execute(self, input_data: dict) -> dict:
        name = input_data.get("name", "Welt")
        return {"greeting": f"Hallo {name}!"}
```

### Beispiel 2: Plugin mit dynamischen Settings

```python
PLUGIN_META = {
    "id": "weather",
    "name": "Weather",
    "settingsFields": [
        {"key": "city", "label": "Standard-Stadt", "type": "string", "default": "Berlin"},
        {"key": "units", "label": "Einheit", "type": "select", "default": "metric", "options": [
            {"value": "metric", "label": "°C"},
            {"value": "imperial", "label": "°F"},
        ]},
    ],
}

class WeatherPlugin(Plugin):
    async def execute(self, input_data: dict) -> dict:
        # Settings aus der DB/Config laden
        city = self.get_setting("city", "Berlin")
        units = self.get_setting("units", "metric")
        # ... Wetterabfrage ...
```

---

## 🚀 Mögliche Erweiterungen (Vorschläge)

### 🏢 Naturstein-spezifische Plugins

| Plugin               | Beschreibung                                               | Priorität  |
| -------------------- | ---------------------------------------------------------- | ---------- |
| Stone Calculator     | Berechnet Gewicht, Volumen und benötigte Menge für Steine  | 🔴 Hoch    |
| Stone Compatibility  | Prüft, ob ein Stein für bestimmte Anwendungen geeignet ist | 🟡 Mittel  |
| Stone Quarry Locator | Findet Steinbrüche für bestimmte Steine (Google Maps API)  | 🟢 Niedrig |
| Stone Sustainability | CO2-Fußabdruck und Nachhaltigkeitszertifikate              | 🟢 Niedrig |

### 📊 Business & Analytics (erweitert)

| Plugin             | Beschreibung                     | Priorität  |
| ------------------ | -------------------------------- | ---------- |
| Slack Integration  | Nachrichten an Slack senden      | 🟡 Mittel  |
| Microsoft Teams    | Nachrichten an Teams senden      | 🟡 Mittel  |
| Google Analytics   | Abfrage von Website-Daten        | 🟢 Niedrig |
| Jira Integration   | Tickets erstellen und abfragen   | 🟢 Niedrig |
| Notion Integration | Daten aus Notion lesen/schreiben | 🟢 Niedrig |

### 🔧 Developer Tools (erweitert)

| Plugin             | Beschreibung                                 | Priorität  |
| ------------------ | -------------------------------------------- | ---------- |
| Docker Runner      | Docker-Container starten/stoppen             | 🟡 Mittel  |
| Kubernetes Manager | Kubernetes-Ressourcen verwalten              | 🟢 Niedrig |
| SSH Executor       | SSH-Befehle auf entfernten Servern ausführen | 🟢 Niedrig |
| Webhook Tester     | Webhooks empfangen und testen                | 🟢 Niedrig |

### 🛒 E-Commerce & Preis (erweitert)

| Plugin              | Beschreibung                          | Priorität |
| ------------------- | ------------------------------------- | --------- |
| Magento Integration | Produkte/Bestellungen aus Magento     | 🟡 Mittel |
| Shopify Integration | Produkte/Bestellungen aus Shopify     | 🟡 Mittel |
| WooCommerce         | Produkte/Bestellungen aus WooCommerce | 🟡 Mittel |

### 📱 Social & Communication (erweitert)

| Plugin       | Beschreibung                | Priorität  |
| ------------ | --------------------------- | ---------- |
| Telegram     | Telegram-Nachrichten senden | 🟡 Mittel  |
| Signal       | Signal-Nachrichten senden   | 🟢 Niedrig |
| Discord      | Discord-Nachrichten senden  | 🟢 Niedrig |
| SMS (Twilio) | SMS senden (via Twilio)     | 🟡 Mittel  |

### 🌐 Core / Web (erweitert)

| Plugin            | Beschreibung                        | Priorität  |
| ----------------- | ----------------------------------- | ---------- |
| RSS Reader        | RSS-Feeds lesen und parsen          | 🟡 Mittel  |
| Web Scraper       | HTML-Seiten scrapen und analysieren | 🟡 Mittel  |
| Sitemap Generator | Sitemap einer Website generieren    | 🟢 Niedrig |
| DNS Lookup        | DNS-Informationen abfragen          | 🟢 Niedrig |

### 🏆 Priorisierte Empfehlung (Top 5)

| Rang | Plugin                      | Begründung                                   |
| ---- | --------------------------- | -------------------------------------------- |
| 1    | Stone Calculator            | Direkter Nutzen für Vertrieb und Kalkulation |
| 2    | Slack Integration           | Team-Kommunikation und Benachrichtigungen    |
| 3    | Magento/Shopify Integration | E-Commerce-Anbindung für Heishg Naturstein   |
| 4    | Web Scraper                 | Wettbewerbsanalyse und Preisrecherche        |
| 5    | Telegram                    | Alternative Kommunikationskanäle             |

### 📋 Checkliste für neue Plugins

Bevor ein neues Plugin erstellt wird:

- Existiert die Funktionalität bereits in einem anderen Plugin?
- Wird ein API-Key benötigt? → `apiKeyRequired: true`
- Welche Intent-Pattern werden benötigt? → `intentPattern` definieren
- Welche Settings-Felder werden benötigt? → `settingsFields` definieren
- Ist die `README.md` vollständig?

---

## ✅ Zusammenfassung

Das Plugin-System ist:

- **Modular** – Plugins können unabhängig voneinander entwickelt werden
- **Sicher** – Eingaben werden validiert, API-Keys verschlüsselt
- **Überwachbar** – Prometheus-Metriken für jedes Plugin
- **Flexibel** – Stateless, Stateful, Streaming, Batch
- **Team-fähig** – Berücksichtigt Team-Zugehörigkeit
- **Mobile-kompatibel** – Optimierte Ausgabe für Mobile-Clients
- **Dynamisch** – Settings werden automatisch aus `PLUGIN_META` generiert

---

**Letzte Aktualisierung:** 2026-06-28
