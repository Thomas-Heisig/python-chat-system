# Changelog

## 0.1.41 - 2026-07-17

- Kommunikations-Contract in der Runtime operationalisiert: `app/tools/communication_contract.py` validiert fuer `business_letter`, `email`, `whatsapp`, `translator` jetzt direkt gegen `app/plugins/contracts/communication.schema.json` (Draft 2020-12).
- Runtime-Dependency ergaenzt: `jsonschema` als Projektabhaengigkeit in `requirements.txt` aufgenommen.
- Contract-Regressionen fuer alle betroffenen Plugins erweitert: `tests/unit/test_plugin_executor.py` prueft jetzt pluginuebergreifend schema-konforme Validierungs-Envelopes sowie gezielte schema-seitige Invalid-Faelle.
- WhatsApp-Validate-Only-Pfad an den gemeinsamen Contract angepasst: Top-Level-`status` nutzt jetzt `ready` statt `validated`, inklusive angepasstem Runtime-Test in `tests/unit/test_whatsapp_plugin_runtime.py`.

## 0.1.41 - 2026-07-17

- Zentrale Contract-Validierung in den gemeinsamen Execute-Pfad integriert: `app/tools/executor.py` prueft fuer `business_letter`, `email`, `whatsapp`, `translator` den Kommunikations-Envelope vor dem Plugin-Call (`plugin_contract_invalid_input`) und das Plugin-Ergebnis danach (`plugin_contract_invalid_output`).
- Shared Helper eingefuehrt: `app/tools/communication_contract.py` validiert die kanonischen Boundary-Felder (`delivery`, `content`, `metadata`, `validate_only`, `validation`, `status`, `reason`) auf Basis des zentralen Contracts.
- Plugin-Ausgaben auf den gemeinsamen `validation`-Vertrag harmonisiert: nicht-kanonische Zusatzfelder im `validation`-Objekt bei `email`, `whatsapp`, `translator` entfernt.
- Executor-Regression erweitert: `tests/unit/test_plugin_executor.py` deckt jetzt alle vier harmonisierten Plugins im zentralen Execute-Pfad plus einen Negativfall fuer ungueltige Contract-Eingaben ab.

## 0.1.40 - 2026-07-17

- Zentrale Boundary-Contract-Dokumentation fuer Kommunikations-Plugins eingefuehrt: `docs/plugins/communication-contract.md` beschreibt verbindlich den gemeinsamen Envelope (`delivery`, `content`, `metadata`), `validation`-Format, `validate_only`, Skip-Verhalten und Autonomiegrenzen.
- Maschinenlesbare Contract-Definition hinzugefuegt: `app/plugins/contracts/communication.schema.json` als wiederverwendbare Basis fuer spaetere Typen, Validierung, Frontend-Formulare und Tests.
- Bestehende Kommunikations-Konventionen verknuepft: `docs/plugins/communication.md` referenziert jetzt den kanonischen Contract und das Schema.

- Serverseitige Feldvalidierung fuer Plugin-Profile in `POST /api/settings/{category}/{key}` eingefuehrt: fuer `plugins/*_profile` werden jetzt Pflichtfelder, Feldtypen und Select-Optionen anhand der Registry-`settings_fields` geprueft.
- Fehlervertrag fuer Plugin-Validierung gehaertet: bei ungueltigen Profilwerten liefert die API strukturierte Details mit `code`, `message`, `plugin_id` und `field_errors` pro Feld.
- Plugin-Settings im Frontend konsequent auf dynamische Steuerung umgestellt: `WorkspacePage` rendert konfigurierbare Plugins ausschliesslich ueber `settings_fields` (inkl. Gruppen) und unterstuetzt `string`, `text`, `boolean`, `number`, `select`, `password`.
- UI-Fehlerrueckmeldung pro Plugin/Feld umgesetzt: Validierungsfehler aus dem Backend werden plugin- und feldspezifisch angezeigt, statt nur als allgemeiner Speichern-Fehler.
- Save-Flow je Plugin vereinheitlicht: Plugin-spezifischer Pending-Status (`savingPluginId`) und generische Draft-Verwaltung ueber `pluginSettingsDrafts`/`onPluginSettingChange`.
- Plugins ohne konfigurierbare `settings_fields` werden im Plugin-Settings-Bereich nicht mehr als leere Konfigurationsbloecke gerendert.
- Frontend-Build verifiziert: `npm run build` (Vite) laeuft nach der Umstellung erfolgreich durch.

## 0.1.39 - 2026-07-17

- Kommunikations-Plugin-Gleichklang erweitert: `whatsapp` und `translator` akzeptieren jetzt auch harmonisierte Eingabestrukturen aus fachuebergreifenden Payloads (`delivery`/`content`) ohne Verlust ihrer provider-spezifischen Autonomie.
- `whatsapp` gehaertet: kanalbewusster Skip fuer fachfremde Kanaele (`letter`/`email`), `validate_only`-Pfad sowie strukturierte Validierung mit `status`, `errors`, `warnings`, `missing_information`.
- `translator` gehaertet: harmonisierte Text-Normalisierung aus `content`, `validate_only`-Pfad und strukturierte Validierung in der Plugin-Antwort.
- Runtime-Regressionen ergaenzt: neue Unit-Tests fuer WhatsApp und Translator (`tests/unit/test_whatsapp_plugin_runtime.py`, `tests/unit/test_translator_plugin_runtime.py`) inklusive Envelope-Kompatibilitaet und Validierungsfaellen.
- Kommunikations-Plugin-Dokumentation synchronisiert: READMEs von `whatsapp` und `translator` auf neue Eingabe-/Ausgabevertraege erweitert.

## 0.1.38 - 2026-07-17

- business_letter Plugin-Dokumentation synchronisiert: README an den aktuellen Runtime-Stand angepasst (Alias-Mapping, Tonalitaeten, Input-Regeln, Statuslogik und erweiterte Validierungsregeln).
- Zentrale Plugin-System-Dokumentation eingefuehrt: neue Leitdokumente unter `docs/architecture/plugin-system.md` und `docs/plugins/` (`settings.md`, `standards.md`, `validation.md`, `communication.md`, `plugin-development.md`) fuer systemweite Regeln statt plugin-spezifischer Ablage.
- Navigationsseite fuer Plugin-Dokumente hinzugefuegt: `docs/plugins/index.md` mit empfohlener Lesereihenfolge und zielorientierter Schnellnavigation fuer neue Entwickler.
- Chat-Retrieval auf Projekt-Hierarchie umgestellt: Quellen werden im Chat jetzt konversationsbezogen ueber `conversation_project_map` und `workspace.project_meta_map` aufgeloest statt userweit gemischt.
- Scope-Regel durchgesetzt: bei zugewiesenem Konversationsprojekt werden nur Quellen aus der eigenen Projektlinie (Vorfahren + aktueller Knoten) beruecksichtigt; fachfremde Parallelprojekte (z. B. `Heisig Naturstein` vs. `Fussball`) werden nicht mehr vermischt.
- Hierarchie-Richtung gehaertet: Quellen wandern nur von oben nach unten entlang der Parent-Kette; untergeordnete Projektdaten werden nicht nach oben geerbt.
- Retrieval-Metadaten erweitert: ausgewaehlte Quellen und Diagnostik enthalten jetzt zusaetzlich `project_id` und `scope_depth` fuer nachvollziehbare Scope-Transparenz.
- Knowledge-Repository erweitert: neuer Scope-Query-Pfad fuer kontextbezogenes Laden (`list_documents_for_scope`) inklusive optionalem Unassigned-Fallback.
- Regressionstest hinzugefuegt (`tests/unit/test_chat_service.py`): validiert die konversationsgebundene Hierarchie-Auswahl und verhindert Quell-Leakage zwischen Projektbaeumen.

## 0.1.37 - 2026-07-17

- Plugin-Settings im Frontend von statisch auf generisch umgestellt: der Bereich `Einstellungen -> Plugins` rendert jetzt dynamisch alle Plugins anhand von `GET /api/plugins` und deren `settings_fields`.
- Neue Frontend-API-Verdrahtung fuer Plugin-Metadaten umgesetzt: `getPlugins()` liefert Plugin-Katalog inkl. normalisierter Felddefinitionen (`type`, `group`, `default`, `options`) fuer die UI.
- Persistenzpfad verallgemeinert: Profile werden fuer jedes Plugin unter `plugins.<plugin_id>_profile` geladen und gespeichert, statt nur `business_letter_profile` statisch zu behandeln.
- Feldtypen produktiv abgedeckt: dynamisches Rendern/Speichern fuer `string`, `number`, `boolean` und `select` inkl. gruppierter Darstellung je Plugin.
- Frontend-Build validiert: `vite build` laeuft nach der Mehr-Plugin-Umstellung erfolgreich durch (bestehende Chunk-Groessenwarnung unveraendert, nicht blockierend).

## 0.1.36 - 2026-07-17

- Chat-Settings entruempelt: redundante Generierungs-Standardwerte fuer Antwortstil/Sampling (`temperature`, `max_new_tokens`, `top_p`, `top_k`, `repetition_penalty`, `do_sample`, `seed`, `stop_sequences`) wurden aus den globalen `chat`-Defaults entfernt.
- Aufloesung im Chat-Flow praezisiert: Generierungsparameter werden jetzt fuer die Antworterzeugung nur noch modell-spezifisch (`model_<id>_*`) gelesen; globale Chat-Werte dienen dafuer nicht mehr als Fallback.
- Settings-UI `Chat` neu ausgerichtet: statt Antwortstil-Parametern werden jetzt chattypische Voreinstellungen gepflegt (`plugin_orchestration_enabled`, `auto_specialist_enabled`, `context_limit_tokens`, `context_safety_margin_tokens`).
- Startup-Cleanup aktiviert: verbliebene alte globale `chat`-Eintraege fuer Antwortstil-/Sampling-Keys werden beim Runtime-Start kontrolliert entfernt (nur globaler Scope `user_id=null`, `team_id=null`).
- On-Demand-Cleanup fuer Alt-Keys ergaenzt: neuer Endpoint `POST /api/settings/chat/cleanup-obsolete` unterstuetzt `dry_run`-Statistiken und die manuelle Ausfuehrung der Bereinigung.
- Zugriffsschutz nachgezogen: `POST /api/settings/chat/cleanup-obsolete` verlangt jetzt explizit einen gueltigen Bearer-Token mit Admin-Rechten; fuer fehlende/ungueltige Tokens bzw. fehlende Admin-Rolle werden sichtbare `401/403`-Antworten geliefert.
- Settings-UI erweitert: im Bereich `Einstellungen -> Chat` kann die Legacy-Bereinigung jetzt manuell angestossen werden; die letzte Cleanup-Statistik (gefunden/entfernt/verbleibend) wird direkt angezeigt.
- Security-Dokumentation zentralisiert: neue Struktur unter `docs/security/` mit `authentication.md`, `authorization.md`, `admin-actions.md` und `audit-logging.md` als verbindlicher Referenzrahmen fuer geschuetzte Admin-Aktionen.
- Verbindliche Guard-Konvention dokumentiert: administrative Endpunkte sollen zentralisierte Auth-Guards/Dependencies (z. B. `require_admin_user`) verwenden statt verteilter ad-hoc-Rollenpruefung.
- Security-Uebersicht ergaenzt: `docs/security/README.md` verlinkt die vier Kern-Dokumente und legt die empfohlene Reihenfolge fuer Implementierung und Reviews fest.

## 0.1.35 - 2026-07-17

- `business_letter` als vollstaendigeres Kommunikationsmodul erweitert: Brief- und E-Mail-Ausgabe werden jetzt getrennt erzeugt (`letter`, `email`, `content`) und um `validation`, `delivery` sowie `metadata` ergaenzt.
- Plugin-Schema deutlich ausgebaut: neue Eingabefelder fuer Kommunikationskanal (`letter`/`email`/`both`), Empfaengerdetails, E-Mail-Header (`to`/`cc`/`bcc`/`reply_to`), Referenzen, Fristen, Verlaufskontext und strukturierte Anlagenobjekte.
- Briefarten fuer den Betriebsalltag erweitert (u. a. `angebotserinnerung`, `terminbestaetigung`, `lieferankuendigung`, `rechnung_begleitschreiben`, `mahnung_1`, `mahnung_2`, `dokumentenanforderung`).
- Anrede-Logik sprachlich gehaertet: die pauschale Form `Sehr geehrte/r` wurde entfernt und durch eine strukturierte Anrede auf Basis von `customer_salutation`/`customer_title`/`customer_last_name` ersetzt.
- Versandvalidierung professionalisiert: getrennte `errors`, `warnings` und `missing_information`, kanalabhaengige Pflichtpruefungen, Plausibilitaetschecks fuer Mahnungen/Angebote, Anlage-Checks und Platzhalter-Blocker vor Versandfreigabe.
- Rechts- und Stammdaten in Plugin-Settings erweitert: u. a. Land/Postfach/Mobil/Fax, Reply-To/BCC, strukturierte Registerangaben, strukturierte Bankdaten, Kommunikationsvorgaben und fachliche Hinweisbausteine.
- Legacy-Kompatibilitaet erhalten: `company_registry` und `company_bank` werden weiterhin als Fallback gelesen, intern aber in strukturierte Felder ueberfuehrt.
- Instabile Referenzbildung mit Python-`hash()` entfernt: Dokumentnummern werden nun stabil ueber explizite Felder bzw. UUID-basierte IDs erzeugt.
- Trainings-/Eval-Schema (`app/training/evaluation/business_letter_schema.py`) auf das neue erweiterte Ausgabeformat angepasst (kompatibel fuer altes und neues JSON-Layout).
- Unit-Tests fuer das Business-Letter-Schema aktualisiert und um erweiterte Statusfaelle (`queued` etc.) ergaenzt.
- Runtime-Tests fuer `BusinessLetterPlugin.execute()` hinzugefuegt (`tests/unit/test_business_letter_runtime.py`) mit sechs Kernfaellen: vollstaendige E-Mail, unvollstaendiger Brief, fehlende Pflichtanlage, Platzhalter-Firmendaten, Kanal `both`, Mahnung ohne Rechnungs-/Faelligkeitsangaben.

## 0.1.34 - 2026-07-17

- Plugin-Einstellungen im Settings-Bereich sichtbar vervollstaendigt: das `Geschaeftsbrief`-Profil zeigt jetzt neben Basisfeldern auch erweiterte Unternehmensdaten (u. a. Webseite, Steuer-/USt-ID, Register, Geschaeftsfuehrung, Kammer, Bank, AGB/Datenschutz).
- Persistenzpfad fuer `plugins.business_letter_profile` erweitert: neue Felder werden in `AppShell` vollstaendig geladen, bearbeitet und gespeichert.
- Frontend-Validierung erfolgreich: `vite build` laeuft nach dem Ausbau ohne neue Fehler in den geaenderten Settings-Komponenten.

## 0.1.33 - 2026-07-17

- Workspace-Hierarchie serverseitig gehaertet: `POST /api/workspace/projects` validiert `parent_project_id` jetzt strikt und liefert bei ungueltigem Parent den klaren Fehler `project_parent_not_found`.
- Reparenting-Schutz erweitert: `PATCH /api/workspace/projects/{project_id}/hierarchy` blockiert nun indirekte Kreisbeziehungen mit `project_parent_cycle`.
- Projektloeschung verbessert: beim Entfernen eines Hierarchieknotens werden direkte Kinder auf den Parent des geloeschten Knotens umgehaengt, statt auf `null` zu fallen.
- End-to-End validiert: Hierarchietiefe, effektive Quellenvererbung und Kontexttrennung zwischen getrennten Projektbaeumen wurden gegen die Live-API erfolgreich geprueft.

## 0.1.32 - 2026-07-17

- Integrationen-UI erweitert: neue Sammelaktion `Alle Keys testen` fuehrt die sechs Kernprovider-Checks (`OpenWeather`, `WeatherAPI`, `Tomorrow.io`, `Exa`, `Brave Search`, `Bing Search`) in einem Lauf aus.
- Re-Validation-Ausgabe ergaenzt: pro Key wird jetzt ein klares Ergebnis `OK`, `Fehler` oder `uebersprungen` in einer kompakten Ergebnisliste angezeigt.
- Einzelfeld- und Sammeltest vereinheitlicht: dieselbe Testlogik wird fuer `Key testen` und `Alle Keys testen` verwendet, inklusive Skip-Verhalten fuer leere Felder.

- Projektbegriff im Workspace erweitert: Projekte tragen jetzt zusaetzliche Hierarchie-Metadaten (`parent_project_id`, `scope_kind`, `area_key`, `tenant_key`, `owner_user_id`) und koennen als Knoten in einer variabel tiefen Struktur genutzt werden.
- Persistente Hierarchiespeicherung eingefuehrt: die neue Struktur wird ueber `workspace.project_meta_map` in den Settings gespeichert und beim Laden wiederhergestellt.
- Quellenzuordnung pro Hierarchieebene aktiviert: Bibliotheksquellen koennen jetzt explizit einer Projektebene zugewiesen oder von ihr geloest werden (`PATCH /api/workspace/sources/{source_id}/project`).
- Effektive Quellenvererbung umgesetzt: neuer Endpoint `GET /api/workspace/projects/{project_id}/sources/effective` liefert Quellen entlang der Parent-Kette fuer tiefenbasierte Nutzung.
- Projekte-UI erweitert: beim Erstellen und Bearbeiten sind nun Typ (`Mandant`, `Benutzer`, `Bereich`, `Projekt`), Parent-Ebene sowie Mandant-/Bereichskennungen konfigurierbar und direkt speicherbar.
- Bibliotheks-UI erweitert: jede Quelle zeigt die aktuelle Projektebene und kann pro Datei neu zugeordnet werden.

## 0.1.31 - 2026-07-17

- Integrationen-UI fuer operative Key-Eingabe verbessert: Integrationsfelder werden in der Suche/Web-Wetter-Konfiguration jetzt klar als Einzelzeilen dargestellt (eine Zeile pro Key statt mehrspaltiger Darstellung).
- Neue Direktaktion `Key testen` fuer die sechs produktionskritischen Provider (`OpenWeather`, `WeatherAPI`, `Tomorrow.io`, `Exa`, `Brave Search`, `Bing Search`) direkt am jeweiligen Key-Feld eingefuehrt.
- Provider-Tests laufen gegen die bestehenden Plugin-Endpunkte (`/api/plugins/execute`) und pruefen den jeweils ausgewaehlten Anbieter gezielt statt nur unspezifischer Fallbacks.
- Fehlerhafte Key-Tests werden jetzt deutlich visuell markiert: rotes Fehler-Highlight am Feld und Ausrufezeichen-Indikator mit konkreter Fehlermeldung.
- Fehlende/nicht gesetzte Keys werden beim Feldtest jetzt still uebersprungen (keine rote Fehlermarkierung), damit Setups ohne vollstaendige Provider-Abdeckung sauber bleiben.

## 0.1.30 - 2026-07-17

- Integrationen-UI angepasst: `Key holen` durch kompakten Target-Button (`↗`) ersetzt, inklusive stabilisiertem Eingabereihen-Layout in Hell-/Dunkelmodus.
- CSS-Reparatur fuer Integrationsfelder umgesetzt: dedizierte Klassen (`integration-target-btn`) verhindern Nebenwirkungen durch generische Button-Styles.
- Secret-Klassifizierung im Backend verdrahtet: beim Speichern von Integrations-Settings wird `is_secret` jetzt automatisch gesetzt.
- Sichere Settings-Ausgabe aktiviert: `GET /api/settings/{category}/{key}` maskiert Secrets standardmaessig (`********`), mit explizitem Opt-in ueber `include_secret=true`.
- Frontend-Settings-Lader angepasst, damit editierbare Secret-Werte weiterhin bewusst angefordert werden koennen.

## 0.1.29 - 2026-07-17

- Frontend-Integrationen vervollstaendigt: `AppShell` laedt/speichert jetzt alle Integrationsfelder aus/in DB-Settings statt nur zwei Keys.
- Integrationsspeicherung verallgemeinert ueber zentrales Mapping (`string`/`boolean`/`json`) inklusive JSON-Validierung fuer `custom_provider_keys`.
- Integrationen-UI erweitert: pro API-Key-Feld gibt es nun einen direkten Button `Key holen` mit externem Provider-Link (neuer Tab).
- Build-Validierung Frontend erfolgreich (`vite build`), keine neuen Fehler in geaenderten Dateien.

## 0.1.28 - 2026-07-17

- Laufzeitverdrahtung fuer Integrations-Keys erweitert: `weather`, `websearch` und `bing_search` lesen API-Keys jetzt aus DB-Settings (`integrations.*`) mit sauberem Env-Fallback.
- Wetter-Plugin um echten `tomorrowio`-Provider erweitert (Realtime + Forecast), inklusive Provider-Auswahl und Fallback-Kette.
- Websearch-Plugin von reinem DuckDuckGo auf echte Provider-Pipeline ausgebaut: Exa, Brave, Bing und DuckDuckGo als Fallback-Reihenfolge.
- Plugin-Runtime im Chat-Flow gehaertet: `ChatService` injiziert plugin-spezifische Integrations-Keys gezielt in `plugin_settings.integrations`.
- Plugin-API (`POST /api/plugins/execute`) auf denselben Integrationspfad gebracht, damit direkte Plugin-Ausfuehrung und Chat-Orchestrierung konsistent sind.

## 0.1.27 - 2026-07-17

- Integrationen-Endausbau umgesetzt: alle angeforderten API-Key-Kategorien erweitert (LLM/Enterprise, Vision/Video, Dokument/RAG, Suche/Web, Wetter/Karten, Finanzdaten, Kommunikation, Sicherheit).
- Integrationen-UX auf Tabs und einklappbare Gruppen umgestellt, damit große Key-Sammlungen strukturiert und skalierbar bleiben.
- Zukunftsfaehigkeit erhoeht: neues Feld `custom_provider_keys` als JSON-Objekt fuer beliebige spaetere Anbieter sowie `ollama_local_enabled` als zentraler Toggle integriert.
- Vollstaendige DB-Anbindung verifiziert: alle Integrationswerte werden ueber den Settings-Flow in der Datenbank gespeichert, geladen und validiert.
- `.env.example` synchron erweitert: sichere Platzhalter fuer die neuen Provider und klar gruppierte Sektionen fuer Setup und Betrieb.

## 0.1.26 - 2026-07-17

- Integrationen-Einstellungen deutlich erweitert: zusaetzlich zu OpenAI/DeepL koennen jetzt viele gaengige API-Keys zentral gespeichert werden (u. a. Anthropic, Google AI, Mistral, Cohere, Perplexity, Groq, Together, OpenRouter, Hugging Face, Replicate, DeepSeek, xAI).
- Wetter-/Web-/Karten-Integrationen ergaenzt: neue Key-Felder fuer OpenWeather, WeatherAPI, Tomorrow.io, Tavily, SerpAPI, NewsAPI, Google Maps und Mapbox hinzugefuegt.
- Kommunikations- und Plattform-Keys ergaenzt: neue Felder fuer Twilio, SendGrid, Slack Bot Token, Discord Bot Token, GitHub Token, Notion, Airtable und Stripe.
- Backend-Settings-Schema synchron erweitert: neue Integrations-Keys sind in Defaults und Validierung hinterlegt und werden robust als Secrets-Strings verarbeitet.
- `.env.example` um sichere Platzhalter fuer die neuen Integrationen erweitert, damit Setup und Dokumentation konsistent bleiben.

## 0.1.25 - 2026-07-17

- Markdown-Haertung Phase 2 umgesetzt: ausgewaehlte Plugin-READMEs wurden fuer `MD040` nachgezogen (Codefences mit expliziter Sprache versehen).
- Fragment-Links in `plugins/README.md` korrigiert, sodass die Inhaltsverzeichnis-Links fuer `Dynamische Settings` und `Admin-UI & Konfiguration` unter `MD051` wieder gueltig sind.
- `.markdownlint.json` weiter verschaerft: globale Ausnahme fuer `MD041` reduziert und Regelhaertung gezielt per Overrides auf den Phase-2-Batch der Plugin-READMEs erweitert.

## 0.1.24 - 2026-07-17

- Modellmanager-Praeferenzen pro Benutzer im Browser persistiert: aktive Modellfilter, gewaehlter Modell-Untertab und offene/geschlossene Modellgruppen werden jetzt benutzerbezogen wiederhergestellt.
- `ultravox-gemma-2-9b-it` entblockt: fuer `audio_text_generation` wurde ein kompatibler Transformers-Loader registriert, sodass das Modell nicht mehr mit `Kein kompatibler Loader registriert` erscheint.
- Sicherheitsbereinigung in `.env.example`: ein versehentlich enthaltener realer OpenAI-Schluessel wurde entfernt und durch den sicheren Platzhalter `your-openai-api-key` ersetzt.
- Markdownlint schrittweise verschaerft (Phase 1): in `.markdownlint.json` gelten fuer `docs/**/*.md` jetzt wieder strengere Regeln (`MD040`, `MD041`, `MD051`), waehrend die restliche Legacy-Baseline unveraendert bleibt.
- Doku-Qualitaetscheck fuer `docs/` validiert: die stricteren Phase-1-Regeln laufen fuer den Docs-Bereich aktuell ohne Befunde.

## 0.1.23 - 2026-07-17

- Modell-Einstellungsansicht neu gegliedert: `Modellverzeichnisse` und `Prompt-Profil` sind jetzt thematische Untertabs innerhalb von `Modelle` statt eigene Hauptreiter.
- Modellmanager-Filter erweitert: neben Suche, Familie, `Tools`, `Thinking` und `Vision` lassen sich jetzt auch `Audio`, `Speech` und `OCR` gezielt filtern.
- Modellgruppen entschlackt: Audio-/Speech-/OCR-/Hilfsgruppen und andere Nicht-Kernbereiche sind im Modellmanager standardmaessig eingeklappt; Eingabefelder und Filterflaechen wurden visuell vereinheitlicht.
- Neues `openai`-Modellbackend ergänzt: ChatGPT/OpenAI-Modelle koennen jetzt als virtuelle Remote-Modelle gescannt, aktiviert und ueber denselben Modellmanager wie lokale/Ollama-Modelle genutzt werden.
- OpenAI-Discovery an Integrations-Settings angebunden: vorhandene ChatGPT/OpenAI-API-Schluessel erzeugen beim Modellscan automatisch auswählbare Modelle wie `gpt-4.1-mini`, `gpt-4o-mini` und `o4-mini`.
- Laufzeithinweis verifiziert: die App liest produktive API-Schluessel aus den Integrations-Settings oder `.env`, nicht aus `.env.example`; mit Platzhalterwerten wird die OpenAI-Aktivierung korrekt mit `invalid_api_key` geblockt.
- Kritischer Startfehler behoben: in `app/models/ollama_integration.py` wurde ein syntaktisch fehlerhaftes Token in der Ollama-Cloud-Modellliste entfernt; der App-Start ueber `start.py` laeuft wieder stabil.
- Startup-Logging verfeinert: die Meldung zu fehlendem `MODEL_ALLOWED_BASE_DIRS` wird in Entwicklungsumgebungen jetzt als `info` statt `warning` ausgegeben, in nicht-dev Umgebungen bleibt sie eine Warnung.
- Markdownlint-Projektkonfiguration ergänzt: `.markdownlint.json` eingefuehrt, um bekannte, nicht-funktionale Doku-Lintregeln zentral zu steuern und den Problem-Status im Workspace zu beruhigen.

## 0.1.22 - 2026-07-17

- `.env.example` bereinigt: real wirkender API-Key entfernt, Beispielvariablen fuer externe Dienste auf sichere Platzhalter umgestellt und fehlerhafte DeepL-Beispielzeile korrigiert.
- Neue Einstellungsgruppe `Integrationen` hinzugefuegt: ChatGPT/OpenAI- und DeepL-API-Schluessel koennen jetzt direkt ueber die Oberflaeche gespeichert und aus den App-Settings geladen werden.
- Neuer Workspace-Neustart fuer sauberen Neuanfang implementiert: `POST /api/workspace/reset-clean-start` loescht alle Chats (inkl. Messages) und alle Projekte global aus der Datenbank.
- Bugfix: Neustart-Endpunkt auf globalen Hard-Reset erweitert (statt nutzerbezogen), damit nach dem Neustart keine fremden/restlichen Chats mehr sichtbar bleiben.
- Sicherheitsfix: Globaler Reset ist jetzt durch Admin-Berechtigung geschuetzt (Bearer-Token erforderlich, Nicht-Admin wird mit 403 abgewiesen).
- FK-sichere Bereinigung umgesetzt: Referenzen in Terminen, Wissensdokumenten und Trainings-Datasets werden vor Projektloeschung automatisch entkoppelt.
- Settings-Reset fuer Chat-Mappings integriert (`conversation_*_map`), damit nach dem Neustart keine veralteten Zuordnungen bestehen bleiben.
- Seed-Steuerung eingefuehrt: `workspace.seed_demo_data=false` verhindert nach dem Neustart das automatische Wiederanlegen von Demo-Daten.
- Einstellungen erweitert: In der Gruppe `System` gibt es jetzt den Button `Neustart: Chats & Projekte loeschen` mit Sicherheitsabfrage und Pending-Status.

## 0.1.21 - 2026-07-17

- Ollama als zusaetzliches Laufzeit-Backend integriert: lokale und cloudbasierte Ollama-Modelle werden beim Modellscan jetzt als aktivierbare virtuelle Modelle registriert und koennen ueber denselben Aktivierungsfluss wie andere Backends geladen werden.
- Modellauswahl im Chat erweitert: chatfaehige Modelle erscheinen jetzt quellengetrennt unter `Lokal`, `Ollama Local`, `Ollama Cloud` und `Remote`.
- Ollama-Faehigkeiten aus der Runtime abgebildet: Tool-/Thinking-/Vision-Merkmale werden aus den Ollama-Metadaten uebernommen und als Quellen-/Capability-Information im Modellmanager angezeigt.
- Ollama-Cloud-Katalog erweitert: zusaetzliche Standardmodelle wie `phi4`, `qwen2.5-coder`, `codestral`, `command-r`, `deepseek-r1`, `llava` und `moondream` werden jetzt direkt als auswählbare Cloud-Eintraege gelistet.
- Cloud-Katalog weiter ergänzt: `chatgpt-oss` und `deepseek-v3` sind jetzt ebenfalls als auswählbare Ollama-Cloud-Modelle vorhanden.
- Sichtbarer Pull-/Download-Status fuer Ollama Cloud umgesetzt: Cloud-Modelle koennen im Modellmanager explizit heruntergeladen werden; Download-Status und Fortschritt werden ueber die Modell-API geliefert und im UI angezeigt.
- Echter Abbrechen-/Retry-Flow fuer Ollama-Cloud-Downloads umgesetzt: laufende Downloads koennen serverseitig abgebrochen und danach erneut gestartet werden; der Modellstatus wechselt dabei sichtbar auf `cancelling` bzw. `cancelled`.
- Modellkarten im Modellmanager erweitert: lokale Filter nach Suche, Modellfamilie sowie `Tools`, `Thinking` und `Vision` erleichtern die Auswahl grosser Modellmengen.

## 0.1.20 - 2026-07-14

- Kokoro-TTS um deutsche Sprachauswahl erweitert: `GET /api/speech/models` liefert fuer Kokoro jetzt `de` und `de-de` als waehlbare Sprachoptionen im UI.
- Kokoro-Sprachmapping erweitert: zusaetzliche deutsche Aliaswerte (`de-at`, `de-ch`, `german`) werden stabil auf den `b`-Voice-Pfad aufgeloest.
- Laufzeittest bestaetigt: `POST /api/speech/synthesize` mit `model_id=19`, `language=de`, `speaker=bf_emma` liefert erfolgreich WAV-Audio (HTTP 200).

## 0.1.19 - 2026-07-14

- Live-Reasoning im Chat-Streaming ergaenzt: Token innerhalb von `<think>...</think>` werden waehrend der Generierung als separate Denkblase angezeigt statt in den finalen Antworttext geschrieben.
- Frontend-Streamingparser gehaertet: partielle Tag-Grenzen ueber Chunk-Grenzen hinweg werden korrekt behandelt, sodass sichtbarer Antworttext und Denktext stabil getrennt bleiben.
- Denkblase als temporaere Assistant-Message gestaltet und nach Abschluss/Fehler des Streams automatisch entfernt, damit die Chat-Historie sauber bleibt.

## 0.1.18 - 2026-07-14

- Ausgabe-Design im Chat deutlich auf natuerlichen Fliesstext umgestellt: der systemseitige Stil-Appendix bevorzugt jetzt standardmaessig klare Abschnitte ohne Markdown-Zwang, ohne Emojis und ohne erzwungene Listen.
- Prompt-Haertung fuer Bestandsprofile: alte Markdown-Stilfragmente im effektiven System-Prompt werden beim Zusammenbau bereinigt, damit bestehende Profile nicht weiter in Ueberschriften-/Listenstil gedrueckt werden.
- Antwort-Nachbearbeitung auf Klartext ausgerichtet: Markdown-Header und Listenmarker werden fuer normale Antworten in lesbaren Fliesstext normalisiert, statt aktiv weitere Markdown-Struktur zu erzwingen.

## 0.1.17 - 2026-07-14

- GGUF-Modellaktivierung gehaertet: bei Ordner-basierten GGUF-Modellen priorisiert der `llama_cpp`-Resolver jetzt echte Gewichtsdateien gegenueber `mmproj`/`projector`-Dateien und waehlt bevorzugt die groesste passende GGUF-Datei.
- Diagnose bei Aktivierungsfehlern verbessert: `POST /api/models/{id}/activate` liefert bei `409` jetzt die konkrete Root-Cause im Fehlerdetail (inkl. Rollback-Hinweis), statt nur generischem "Model activation failed".

## 0.1.16 - 2026-07-14

- VAD-Dekodierung im Speech-Backend gehaertet: Audio-Uploads werden jetzt mit mehrstufigen Decoder-Fallbacks und suffix-sensibler Temp-Datei-Erkennung verarbeitet, wodurch `POST /api/speech/detect-activity` und STT+VAD robuster auf Windows laufen.
- Qwen3-TTS-Synthese validiert: `POST /api/speech/synthesize` liefert im frischen Runtime-Prozess jetzt HTTP 200; die qwen/transformers-Kompatibilitaet wird ueber einen expliziten Causal-Mask-Bridge-Pfad und kompatible Decorator-Shims abgesichert.

## 0.1.15 - 2026-07-13

- STT um serverseitiges automatisches VAD-Precut erweitert: `POST /api/speech/transcribe` unterstuetzt jetzt `vad_enabled`, `vad_model_id`, `vad_threshold`, `vad_padding_ms` und `vad_merge_gap_ms` und schneidet erkannte Sprachsegmente vor der Transkription zusammen.
- STT-Flow fuer No-Speech-Faelle gehaertet: bei aktivem VAD und ohne Sprachsegmente liefert die API jetzt fruehzeitig eine stabile Antwort mit `note: no_speech_detected` statt spaeterem STT-Fehler.
- Frontend-Sprachaufnahme an den neuen Backend-Precut angebunden: VAD-Parameter werden beim Transkriptionsrequest mitgesendet, damit derselbe Segmentierungsweg serverseitig genutzt wird.

- Qwen3-TTS-Kompatibilitaet im bestehenden System verbessert: Runtime-Shims fuer `check_model_inputs`, RoPE-Key-Handling (`default`), `pad_token_id`-Bridge im Talker-Config und `create_causal_mask`-Argument-Mapping hinzugefuegt.
- Qwen3-TTS-Fehlermeldung weiter gehaertet: bekannte Inkompatibilitaeten werden als klare Pairing-Empfehlung fuer `qwen-tts`/`transformers` in derselben `.venv` ausgegeben statt als rohe Tensor-Tracebacks.

- VAD als dritte Sprach-Pipeline integriert: `voice_activity_detection`-Modelle (u. a. `silero-vad-v5`) werden jetzt in `GET /api/speech/models` gelistet.
- Neuer Speech-Endpoint fuer VAD: `POST /api/speech/detect-activity` analysiert Audiostreams und liefert `speaking`, Segmente, Konfidenz und Speech-Ratio zurueck.
- Chat-Spracheinstellungen erweitert: STT/TTS/VAD-Auswahl, optionaler VAD-Precheck vor STT-Aufnahme und konfigurierbare VAD-Schwelle im UI.

- Speech-Modell-Metadaten fuer UI-Auswahl verbessert: TTS-Modelle liefern jetzt korrekte `tasks` (`synthesize`), modellspezifische Sprachlisten und (u. a. fuer Qwen3) Sprecherlisten aus `config.json`.
- Kitten-TTS-Laufzeitpfad korrigiert: ONNX-Datei/`voices.npz` werden explizit geladen, Alias-Stimmen (`Bella` etc.) auf interne Voice-IDs gemappt und die ONNX-Inferenz laeuft mit passender Style-Shape.
- Kitten-TTS auf Windows gehaertet: phonemizer/espeak wird ueber `espeakng-loader` verdrahtet, damit keine systemweite espeak-Installation erforderlich ist.
- Qwen3-TTS-Fehlerbild verfeinert: statt unklarer `transformers`-`model_type`-Meldung liefert die API jetzt eine konkrete Runtime-/Version-Kompatibilitaetsmeldung mit Handlungsweg.

- Kokoro-Initialisierung fuer lokale Windows-Modellpfade final gehaertet: lokale Gewichte/Config werden direkt geladen, ohne den lokalen Pfad als ungueltige `repo_id` an Hugging Face zu uebergeben.
- Kokoro-Generator-Kompatibilitaet erweitert: Audio-Chunks werden jetzt sowohl aus Legacy-Tupeln als auch aus aktuellen `KPipeline.Result`-Objekten gelesen.
- Runtime-Dependency ergaenzt: `kokoro>=0.9.2` in `requirements.txt` aufgenommen, damit die Speech-API nach Umgebungserstellung ohne manuelle Nachinstallation startet.

- Kokoro-TTS-Ladepfad gehaertet: `POST /api/speech/synthesize` faellt fuer Kokoro-Modelle (z. B. `Kokoro-82M`) nicht mehr auf `transformers.pipeline` mit `model_type`-Pflicht zurueck, sondern nutzt einen dedizierten Kokoro-Fallback mit Sprach-/Stimmenzuordnung.
- Audio-Fehlerbild behoben: der 422-Fehler "Unrecognized model ... Should have a `model_type` key in its config.json" tritt fuer Kokoro-Modelle im Standardpfad nicht mehr auf.

- TTS-Request-Validierung fuer `POST /api/speech/synthesize` gehaertet: akzeptiert jetzt robuste Eingaben bei optionalen Feldern (`null`/leer), normalisiert `device`/`speed` auf sichere Defaults und reduziert dadurch 422-Fehler bei Audioausgabe-Anfragen.
- TTS-Schema-Regressionstest ergaenzt: neue Unit-Tests pruefen CamelCase-/`null`-Payloads sowie Fallback-Verhalten fuer ungueltige `device`- und `speed`-Werte.

- Plugin-Runtime-Anbindung umgesetzt: neue Registry und Executor laden Plugins aus `plugins/*/plugin.py` zur Laufzeit und fuehren sie gezielt per Plugin-ID aus.
- Neues API-Modul fuer Plugins bereitgestellt: `GET /api/plugins`, `POST /api/plugins/execute` und `POST /api/plugins/execute-from-markup`.
- Markup-Interaktionsmuster direkt unterstuetzt: Modellausgaben mit `<plugin_call>...</plugin_call>` und `<plugin_input>{...}</plugin_input>` koennen jetzt serverseitig geparstt und ausgefuehrt werden.
- Chat-Orchestrierung end-to-end aktiviert: der normale Chat-Flow laeuft bei aktivem Setting automatisch weiter von `plugin_call` ueber `plugin_input` bis zur Rueckgabe von `plugin_response` und einer finalen Modellantwort.
- Orchestrierung per Setting abschaltbar gemacht: `chat.plugin_orchestration_enabled` steuert die neue Runtime-Logik und ist im Chat-Settings-Panel sichtbar.
- Business-Letter-Plugin vollstaendig stabilisiert: fehlerhafte Plugin-Datei repariert, README vervollstaendigt und Ausgabe auf strukturierte Briefdaten plus klares Klartext-Rendering umgestellt (ohne ASCII-Rahmen).
- Plugin-Runtime fuer Admin-Settings erweitert: `POST /api/plugins/execute` akzeptiert jetzt optional `plugin_settings`, die an Plugins mit `settings`-Konstruktor durchgereicht werden (z. B. Logo, Basistexte, Signaturdaten im `business_letter`-Plugin).
- Admin-Einstellungen jetzt direkt nutzbar: in der Einstellungsgruppe `Plugins` wurde ein Formular fuer `business_letter` (Logo, Basistexte, Signatur, Kerndaten) eingebaut und als `plugins.business_letter_profile` persistiert.
- Chat-Orchestrierung nutzt gespeicherte Plugin-Profile automatisch: bei `plugin_call` werden die gespeicherten `plugins.<plugin_id>_profile`-Werte geladen und bei der Plugin-Ausfuehrung angewandt.
- Training modellwechsel-fest gemacht: `training.target_modules` verwendet jetzt standardmaessig `auto` statt fixer Q/K/V/O-Liste.
- PEFT-LoRA erweitert: Zielmodule werden im Auto-Modus pro Basismodell aus vorhandenen linearen Layernamen abgeleitet und als Laufzeit-Log sichtbar gemacht.
- Training-Preflight erweitert: vor Jobstart wird jetzt explizit angezeigt, welche `target_modules` bei `auto` fuer das aktuell gewaehlte Modell aufgeloest wurden (inkl. Aufloesungsquelle wie `config.model_type`/`config.architectures`/`fallback`).
- Registry ohne Seiteneffekte gehaertet: Plugin-Discovery instanziiert keine Plugins mehr, um unerwuenschte Initialisierungen (z. B. Modelldownloads) beim Listing zu verhindern.
- Plugin-Stabilisierung abgeschlossen: `wikipedia` behandelt HTTP-/Netzwerkfehler robust, `crm_hubspot` hat jetzt korrektes `__init__.py` fuer sauberes Package-Verhalten.

- Kontrolllauf als neuer Training-Standard gesetzt: Defaults stehen jetzt auf `num_train_epochs=4`, `learning_rate=1e-4`, `per_device_train_batch_size=1`, `gradient_accumulation_steps=4`, `max_sequence_length=768`, `lora_r=16`, `save_steps=10`.
- Qualitaetsgate fuer Geschaeftsbrief-Trainingsdaten ergaenzt: neues Modul `app/training/evaluation/business_letter_schema.py` validiert Assistant-Zieltexte als striktes JSON-Format und blockiert bekannte Fehlmuster (Markdown-Ueberschriften, ASCII-Rahmen, Meta-Einleitungen).
- Neues Lint-Werkzeug fuer Datensatzbereinigung hinzugefuegt: `scripts/lint_business_letter_dataset.py` prueft JSONL/Universal-Datasets vor dem Fine-Tuning und liefert pro fehlerhaftem Beispiel klare Regelverletzungen.
- Trainings-Settings erweitert und im UI konfigurierbar gemacht: `warmup_ratio`, `weight_decay`, `eval_steps`, `load_best_model_at_end`, `metric_for_best_model`, `greater_is_better` sind jetzt in Backend-Validierung, Default-Resolver und Settings-Panel verdrahtet.
- PEFT-TrainingArguments erweitert: die neuen Hyperparameter werden beim Lauf tatsaechlich an den Trainer uebergeben (inkl. `eval_steps` statt starrer Kopplung an `save_steps`).
- Evaluation-Report ausgebaut: pro Run wird jetzt `evaluation-report.json` geschrieben mit `base_vs_adapter`-Vergleich, Konfusionsmatrizen fuer `intent`/`agent`/`tool` und Warnung bei zu kleinem Testset.
- Trainings-Artefakt-Metadaten erweitert: `evaluation_report_path` wird beim Speichern erkannt und im Manifest/Saved-Payload referenziert.
- Datensatz-Splitpfade (`source`/`validation`/`test`) werden beim Job-Load in Hyperparameter gespiegelt, damit die Evaluation reproduzierbar den richtigen Split verwenden kann.
- Reproduzierbarer A-F-Experimentplan als Skript hinzugefuegt: `scripts/run_training_experiment_plan.py` (Preflight + Queueing, Report unter `artifacts/jobs/experiment-plan-af-last.json`).
- Passendes Runbook hinzugefuegt: `docs/training-experiment-plan-af.md`.

## 0.1.14 - 2026-07-12

- Dataset-Archivierung gehartet: `archive` und `unarchive` laden das Dataset nach dem Commit neu, damit die Antwort nicht mehr mit abgelaufenem ORM-Zustand in `MissingGreenlet` laeuft.

- Trainings-Batch hinzugefuegt: Im Trainingsbereich startet ein neuer Button alle startbaren Datensaetze aus dem konfigurierten Trainingsordner als Jobs. Erfolgreiche Runs koennen per Job-Metadatum automatisch ins Archiv verschoben werden.

- Dataset-Loeschung abgesichert: `DELETE /api/training/datasets/{id}` bricht jetzt mit einem klaren `training.dataset_in_use`-Konflikt ab, wenn bereits Trainingsjobs auf das Dataset verweisen, statt mit SQLite-Foreign-Key-Fehlern als 500 zu enden.

- Training-Submit stabilisiert: `POST /api/training/jobs` laedt den neu erzeugten Job nach Commit erneut aus der DB, um `sqlalchemy.exc.MissingGreenlet` beim Serialisieren (`updated_at`) zu vermeiden. Ergebnis: Job kann korrekt als `queued` zurueckgegeben werden.

- Jobstart-Logik entkoppelt von starren Dataset-Stati: bei `POST /api/training/jobs` blockiert der Status nicht mehr (ausser `archived`). Nicht-archivierte Datasets laufen in Preflight und werden bei Erfolg regulär als `queued` angelegt.

- Jobstart-Guard korrigiert: Datasets im Status `imported` werden nun fuer `POST /api/training/jobs` zugelassen und gehen in den regulären Preflight, statt vorzeitig mit `training.dataset_not_ready` zu scheitern.

- 409-Konflikttexte weiter verbessert: verschachtelte Backend-Details (`error.details.detail`) werden jetzt im Frontend ausgelesen, sodass konkrete Ursachen wie `training.preflight_failed` statt nur `[conflict] Request failed` sichtbar sind.

- API-Fehlerdarstellung im Frontend verbessert: objektbasierte `detail`-Payloads (z. B. `training.preflight_failed` bei `409`) werden jetzt mit `code`/`message` im Toast angezeigt statt nur generischem Status.

- PEFT-LoRA OOM-Fallback erweitert: bei CUDA-`out of memory` wird derselbe Lauf automatisch einmal im CPU/RAM-Modus erneut versucht (`device_map=cpu`, `no_cuda=true`, Batch=1), statt sofort final zu fehlschlagen.

- Training-Fehlerbehandlung verbessert: CUDA-OOM-Fehler werden jetzt mit konkreten Low-VRAM-Hinweisen (Batchsize, Seq-Len, Grad-Accumulation, Quantisierung) gespeichert; zusaetzlich wird standardmaessig `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` gesetzt, wenn nicht bereits konfiguriert.
- Job-Dateianzeige robuster: falls `result.dataset.files` bei aelteren Jobs fehlt, nutzt die UI nun automatisch die Dataset-Metadaten als Fallback statt `-`.

- Trainingsjobs aktualisieren jetzt automatisch im Hintergrund (2s Polling), solange mindestens ein Job in `queued`/`running`/`in_progress`/`processing` ist; dadurch aktualisiert sich der Fortschrittsbalken ohne manuelle Aktion.

- Python-Analyse stabilisiert: projektlokale `pyrightconfig.json` (venv `.venv-chat`) und `.vscode/settings.json` hinzugefuegt, damit Pylance Imports wie `fastapi`, `pydantic`, `sqlalchemy` zuverlaessig aufloest und Kaskadenfehler in API-Routen entfallen.

- Trainingscenter: laufende Training-Jobs zeigen jetzt direkt in der Job-Liste einen Fortschrittsbalken mit Prozentwert (und sofern verfuegbar Schrittzaehler), statt Fortschritt nur indirekt ueber Rohdaten zu sehen.

- Jobs deklarieren jetzt explizit die verwendeten Trainingsdateien: beim Submit wird ein `result.dataset.files`-Block mit den effektiven Rollenpfaden (`source`/`training`/`validation`/`test`/...) geschrieben und in der UI bei Job-Liste sowie Job-Details angezeigt.

- Trainingscenter erweitert um echte Archiv-Ansicht: Datasets und Jobs haben nun je einen `Aktiv/Archiv`-Toggle; archivierte Elemente koennen direkt per `Wiederherstellen` reaktiviert werden.
- Neue API-Operationen fuer Wiederherstellung: `POST /api/training/datasets/{id}/unarchive` und `POST /api/training/jobs/{id}/unarchive`.
- URL-Import erweitert: Wikipedia-URLs sind jetzt als Trainingsquelle erlaubt; URLs ohne Dateiendung werden fuer Wikipedia als `.html` gespeichert und vom Adapter verarbeitet.
- Workflow-Hinweise im UI praezisiert: klarere Schrittbezeichnungen (`Aus Ordner registrieren`, `Rollen-Dateien hochladen`, `ZIP-Bundle importieren`, `URL als Training verwenden`) sowie expliziter Hinweis zur automatischen Dataset-Namensgenerierung.

- Register-File-Request gehaertet: Frontend sendet fuer `/api/training/datasets/register-file` jetzt sowohl rollenbasierte `files[]` als auch Legacy-Felder (`file_name`, `validation_file_name`, `test_file_name`) fuer robuste API-Kompatibilitaet und zur Vermeidung von 422-Validierungsfehlern.
- Archiv-/Loesch-Workflow fuer Trainingsobjekte eingefuehrt: neue Endpunkte fuer Datasets und Jobs (`archive`, `delete`) plus UI-Aktionen im Trainingscenter.
- Archivierte Datasets/Jobs werden in den Standardlisten nicht mehr angezeigt (optional ueber `include_archived=true` abrufbar).

- Trainingscenter-UX modernisiert: neue Bereichs-Toggles erlauben das Ein-/Ausblenden von Training, Dateien/Datasets und Jobs fuer fokussiertes Arbeiten.
- ZIP-Workflow entschaerft: der Bundle-Importbutton ist nicht mehr an einen manuell gesetzten Dataset-Namen gebunden; ein valider Name wird bei Bedarf automatisch aus ZIP/Quelle abgeleitet.
- Workflow-Gruppierung verbessert: Register-/Upload-/ZIP-/URL-Import sind jetzt klar als zusammenhaengender Training-Workflow strukturiert.

- Trainingscenter auf rollenbasierte Dateifluesse erweitert: Register-/Upload-/URL-Import arbeiten jetzt mit `files`-Rollen (`source`, `training`, `validation`, `test`, `manifest`) statt nur mit einzelnen Dateinamenfeldern.
- Neuer ZIP-Bundle-Import ergaenzt: `POST /api/training/datasets/upload-bundle` akzeptiert ein ZIP mit `training.jsonl`, `validation.jsonl`, `test.jsonl`, `manifest.json`, extrahiert sicher und legt daraus direkt ein Dataset an.
- Datenmodell normalisiert: neue Tabellen `training_dataset_files` und `training_artifacts` eingefuehrt; Dataset-Rollen-Dateien und Job-Artefakte werden zusaetzlich strukturiert persistiert.
- Trainings-Executor erweitert: abgeschlossene Runs schreiben Adapter-/Tokenizer-/Manifest-/Metrik-Artefakte in die neue Artefakt-Tabelle.
- Worker-Queue-Claim optional atomar gehaertet: auf DBs mit Lock-Support wird `FOR UPDATE SKIP LOCKED` genutzt, mit kompatiblem Fallback fuer SQLite.

- Kontrollierte Vergleichslaeufe fuer Training eingefuehrt: `run_profile` (`A`/`B`/`C`) plus optionales `run_label` koennen jetzt in Job-Submit und Preflight gesetzt werden; die Profile setzen reproduzierbare Startwerte fuer `num_train_epochs`, `learning_rate` und `seed`.
- Dataset-Metadaten fuer rollenbasierte Dateizuordnung erweitert (`files.source|training|validation|test|manifest|canonical`) und Register-API entsprechend ausgebaut (Legacy-Felder bleiben kompatibel).
- Trainingsinput priorisiert jetzt explizit den Trainings-Split: wenn `files.training` gesetzt ist, wird dieser statt der Rohquelle als `source_path` fuer den Trainer verwendet.
- Artefaktablage vereinheitlicht: Trainingslaeufe schreiben jetzt in `training-artifacts/<dataset-slug>/v<version>.0.0/run-<job>-...` statt in ein globales Sammelverzeichnis.
- Preflight erweitert: erkennt jetzt Split-Leakage durch Duplikatpruefung zwischen Train/Validation/Test und blockiert bei Ueberlappungen.
- Dataset-Listing bereinigt: interne `*.canonical.jsonl`-Dateien und technische `_prep-smoke`-Pfade werden in `/api/training/datasets/files` nicht mehr als normale Trainingsdateien gelistet.
- Trainingsgate gehaertet: Job-Submit erlaubt nur noch Dataset-Status `ready` oder `validated`.

- Trainingscenter-Konsistenz verbessert: Dataset-Status-Default fuer neue Datensaetze auf `imported` umgestellt (statt fruehem `ready`) in API-Schemas und Training-Routen.
- Trainings-Dataset-API erweitert: optionale Testdatei/-URL ist jetzt in Register-/Upload-/Import-Pfaden verfuegbar; `test_source_path` wird in den Dataset-Metadaten persistiert und im Preflight mitvalidiert.
- Job-Lifecycle gehaertet: `TrainingService.submit(...)` erzeugt Jobs jetzt direkt in `queued` und kann Hyperparameter durchreichen, damit Worker-Verarbeitung nicht am Status/Parameterverlust haengen bleibt.
- Training-Repository gehaertet: `update_status(...)` loescht bestehendes `result_json` bei Status-only-Updates nicht mehr; Cancel-Logs werden konsistent unter `result.runtime.logs` gefuehrt.

- Pylance-Typdiagnostik in den Training-Repositories gehaertet: `TrainingDatasetRepository` und `TrainingJobRepository` verarbeiten JSON- und Listenfelder jetzt strikt typisiert statt mit `Unknown`-Ableitungen.
- Repository-Helper erweitert: `_json_dict(...)` akzeptiert nun robuste Eingabetypen (`str`/`dict`/`None`) und normalisiert konsistent auf `dict[str, object]`; in `TrainingJobRepository` ergaenzt um `_object_list(...)` und `_to_int(...)` fuer sichere Runtime-Auswertung.
- Verifikation abgeschlossen: fuer `app/database/repositories/training_dataset_repository.py` und `app/database/repositories/training_job_repository.py` liegen aktuell keine Pylance-Fehler mehr vor.

- Einstellungsgruppen `Chat`, `Wissen` und `Logs` im Frontend produktiv verdrahtet: Werte werden jetzt geladen, editiert und ueber `/api/settings` persistiert.
- Neue UI-Formulare mit Speichern-Flow fuer zentrale Chat-Parameter (`temperature`, `max_new_tokens`, `top_p`, `top_k`, `repetition_penalty`, `do_sample`, `seed`, Kontextbudget) integriert.
- Retrieval-Settings im Bereich `Wissen` funktional gemacht (`knowledge.top_k`, `min_score_ratio`, `min_absolute_score`, `min_score_gap`) inkl. Laden/Speichern.
- Loglevel-Steuerung im Bereich `Logs` funktional gemacht (`system.log_level` mit `DEBUG|INFO|WARNING|ERROR`).
- Frontend-Validierung erfolgreich: `npm run build` und `npm run test:run` im `frontend`-Projekt laufen gruen.

- Rebranding auf `Kernschmiede` fuer sichtbare Produktstellen umgesetzt (README, Backend-Titel, Frontend-Title, Meta-Service, Startbeschreibung).
- Neues Projektlogo als SVG hinzugefuegt und in README eingebunden: `docs/assets/kernschmiede-logo.svg`.
- Branding-bezogene Meta-Dokumente angepasst (`.github/CONTRIBUTING.md`, `.github/CODEOWNERS`).
- Logo-Integration im System-UI umgesetzt: Login-Screen, Header, Sidebar und Browser-Icon nutzen jetzt `frontend/public/kernschmiede-logo.svg`.
- Technische Namensmigration vervollstaendigt: `APP_NAME`, Python-Projektname und Frontend-Paketname auf `kernschmiede` angepasst (inkl. lockfile).
- Logo ohne Verlauf vereinheitlicht (flache Farbgebung) fuer `docs/assets/kernschmiede-logo.svg` und `frontend/public/kernschmiede-logo.svg`.
- Settings-Architektur auf Startup-Repair umgestellt: invalide persistierte Settings werden jetzt im Initialisierungsprozess repariert (`app/settings/repair.py`), waehrend der Read-Pfad (`SettingsService.get`) wieder strikt read-only ist.
- Startup erweitert: vor Modellscan wird eine dedizierte Settings-Reparatur ausgefuehrt und bei fehlender `MODEL_ALLOWED_BASE_DIRS` eine explizite Betriebswarnung geloggt.
- Modellpfadpruefung auf Boundary-first-Semantik angepasst: rohe `..`-Segmente werden nicht mehr pauschal verworfen, entscheidend ist die aufgeloeste Pfadgrenze gegen die Allow-List.
- Integrations- und Unit-Tests aktualisiert: Read-Only-Fallback fuer invalide Settings, expliziter Startup-Repair-Job sowie angepasste Traversal-Semantik sind abgedeckt.

## 0.1.13 - 2026-07-12

- Repository-Metastruktur vervollstaendigt: `LICENSE` (Apache-2.0), `.editorconfig` und `.gitattributes` hinzugefuegt.
- Security-Duplikat bereinigt: Root-`SECURITY.md` auf kurzen Verweis reduziert, verbindliche Richtlinie bleibt in `.github/SECURITY.md`.
- GitHub-Issue-Intake erweitert: neue Templates fuer Dokumentationsfehler und Modell-/Training-Probleme sowie verbesserte Bug/Feature-Templates.
- `.gitignore` fuer lokale Secrets, Datenbanken, Logs, Uploads, IDE-Dateien und Modell-/Training-Artefakte deutlich erweitert.
- `README.md`, `.github/CODEOWNERS`, `.github/release-drafter.yml` und `.github/dependabot.yml` konsolidiert und bereinigt.

## 0.1.12 - 2026-07-12

- Support-Richtlinie stark erweitert in `.github/SUPPORT.md`: klare Trennung von Fehlern, Bedienungsfragen, Funktionswuenschen und Sicherheitsmeldungen.
- Verbindlichere Angaben fuer Diagnose und Reproduktion ergaenzt, inklusive Modell-/GPU-/Training-spezifischer Felder.
- Regeln fuer Log-Redaktion und vertrauliche Daten explizit ausgebaut sowie Abschnitt zu orientierenden Reaktionszeiten hinzugefuegt.

## 0.1.11 - 2026-07-12

- README-Badges vervollstaendigt: fehlender Badge fuer den aktiven Stale-Workflow (`stale.yml`) ergaenzt.

## 0.1.10 - 2026-07-12

- GitHub-Workflow-Badges stabilisiert: `.github/workflows/release.yml` auf `contents: write` umgestellt, damit Release Drafter Draft-Releases erstellen darf.
- Dependency-Review-Badge stabilisiert: Workflow reagiert weiterhin auf PRs, erzeugt auf `main`/manuellen Runs aber einen erfolgreichen Status-Job fuer konsistente Badge-Anzeige.
- CodeQL-Workflow-Badge mit aktivierter GitHub-Default-Setup-Analyse entkoppelt: `.github/workflows/codeql.yml` liefert jetzt konfliktfreien Status, waehrend die eigentliche Code-Scanning-Analyse ueber den dynamischen Default-Setup-Run laeuft.

## 0.1.9 - 2026-07-12

- CodeQL-Alert #8 (`py/full-ssrf`) gehaertet: Trainings-URL-Import nutzt jetzt Host-Allowlist plus kanonisierte URL-Bildung und blockiert nicht erlaubte Hosts/Ports/Path-Traversal.
- CodeQL-Alert #9 (`py/path-injection`) gehaertet: Basisverzeichnis-Normalisierung akzeptiert nur serverseitig erlaubte Verzeichnisse (Allowlist) statt frei eingetragener Pfade.
- CodeQL-Alert #3 (`py/stack-trace-exposure`) gehaertet: Chat-Streaming liefert bei internen Fehlern keine rohen Exception-Texte mehr nach aussen.

## 0.1.8 - 2026-07-12

- GitHub-typische Workflow-Infrastruktur wieder aktiviert: GitHub Actions auf Repository-Ebene auf `enabled: true` gesetzt.
- CI/Release/Security-Workflows wiederhergestellt unter `.github/workflows/` (`ci.yml`, `codeql.yml`, `dependency-review.yml`, `release.yml`, `stale.yml`).
- Release-Drafter-Konfiguration (`.github/release-drafter.yml`) erneut hinzugefuegt.
- README wieder auf aktive Workflow-Badges und Workflow-Hinweis umgestellt.

## 0.1.7 - 2026-07-12

- Release-Drafter-Restkonfiguration entfernt: `.github/release-drafter.yml` geloescht, da keine GitHub-Workflows mehr aktiv sind.
- GitHub-Status verifiziert: Repository hat `0` registrierte Workflows und keine Runs; damit kann kein `release.yml`-Badge/Run mehr fehlschlagen.

## 0.1.6 - 2026-07-12

- Alle GitHub-Workflow-Runs im Repository beendet und die Run-Historie geloescht.
- Alle Workflow-Dateien unter `.github/workflows/` entfernt.
- GitHub Actions auf Repository-Ebene deaktiviert (`enabled: false`).
- README auf den neuen Workflow-Status angepasst (keine Actions-Badges, klare Notiz zur Deaktivierung).

## 0.1.5 - 2026-07-12

- CodeQL-Sicherheitsfunde in API-/Training-Pfaden gehaertet: URL-Importe fuer Trainingsdaten jetzt mit SSRF-Schutz (Host-/Schema-Validierung, Block privater IP-Ranges, Redirect-Revalidierung).
- Fehlerantworten gehärtet: keine stacktrace-nahen Detaildaten mehr in Chat- und Trainings-API-Fehlerpfaden.
- Pfadvalidierung haerter umgesetzt: Basisverzeichnisse akzeptieren nur sichere, lokale absolute Pfade ohne URL-Schemata.
- Unsicheren Legacy-SHA256-Passwort-Check entfernt; Legacy-Fallback bleibt auf Klartext-Altformat begrenzt.
- Regex-basiertes HTML-Strippen im Dataset-Parser durch parserbasiertes Extrahieren ersetzt.
- `scripts/scan_models.py` loggt nur noch redigierte Modellzusammenfassungen statt kompletter Modellobjekte.

## 0.1.4 - 2026-07-12

- Dependabot-Sammelupdate umgesetzt (Frontend, Python-Requirements und GitHub Actions).
- Frontend auf neue Basis angehoben: `typescript` auf `^7.0.2`, `react`/`react-dom` auf `^19.2.7`, `@types/react`/`@types/react-dom` auf `^19.x`, `jsdom` auf `^29.1.1`, `vitest` auf `^4.1.10`.
- Python-Abhaengigkeiten aktualisiert: `trl>=1.8.0`, `python-multipart>=0.0.32`, `pytest-asyncio>=1.4.0`, `accelerate>=1.14.0`, `llama-cpp-python>=0.3.34`, `pydantic>=2.13.4`, `httpx>=0.28.1`, `psutil>=7.2.2`, `transformers>=5.13.1`.
- GitHub Actions aktualisiert: `actions/checkout@v7`, `actions/setup-node@v6`, `actions/setup-python@v6`, `github/codeql-action@v4`, `actions/dependency-review-action@v5`, `actions/stale@v10`, `release-drafter/release-drafter@v7`.
- CI-Node-Version fuer `jsdom@29.1.1` Kompatibilitaet auf `22.13.0` angehoben.
- Verifikation erfolgreich: `npm run build`, `npm run test:run`, `npm audit` (0 Vulnerabilities).

## 0.1.3 - 2026-07-12

- Dependabot-Sicherheitsalerts im Frontend behoben: `vitest` auf `^4.1.10` und `vite` auf `^8.1.4` aktualisiert (inkl. transitive Fixes fuer `esbuild`, `vite-node`, `@vitest/mocker` und `launch-editor`).
- Sicherheitsverifikation durchgefuehrt: `npm audit` meldet fuer `frontend` jetzt `0 vulnerabilities`.
- Regression geprueft: `npm run build` und `npm run test:run` laufen nach dem Upgrade erfolgreich.

## 0.1.2 - 2026-07-12

- GitHub-Repository-Standardisierung deutlich erweitert: Community-Health-Dateien (`CODE_OF_CONDUCT`, `CONTRIBUTING`, `SECURITY`, `SUPPORT`, `CODEOWNERS`) und PR-/Issue-Templates hinzugefuegt.
- Automationen fuer Repository-Pflege aktiviert: Dependabot-Konfiguration sowie Workflows fuer CI, CodeQL, Dependency-Review, Stale-Management und Release-Drafting angelegt.
- README um GitHub-Badges und einen Abschnitt `GitHub Community Health` erweitert.

## 0.1.1 - 2026-07-12

- Sicherheitsdokumentation bereinigt: `docs/zugaenge.md` enthaelt keine Klartext-Passwoerter mehr und verweist nur auf Secret-Speicher.
- Repository-Hygiene fuer Public-Release verbessert: `.gitignore` schliesst lokale virtuelle Umgebungen und Laufzeitartefakte (`.venv-chat`, `.venv-training`, `artifacts`, `training-artifacts`, `data/cache`, `data/logs`, `data/temp`) aus.

## 0.1.0 - 2026-07-10

Hinweis: Dieser Changelog enthaelt nur tatsaechlich umgesetzte und lokal verifizierte Aenderungen. Geplante oder noch nicht gepruefte Punkte stehen in `docs/ROADMAP.md` und `docs/todo.md`.

- Einstellungsgruppe `Allgemein` produktiv verdrahtet: Sprache, Theme und Zeitzone werden jetzt ueber `system.language`, `system.theme` und `system.timezone` in der Settings-Datenbank gespeichert und geladen.
- Settings-Validierung erweitert: `system.language` (de/en), `system.theme` (system/light/dark) und IANA-Zeitzonenpruefung fuer `system.timezone` sind serverseitig abgesichert.
- Frontend-Einstellungen erweitert: neue UI-Karte `Allgemein` mit Speichern-Flow, inklusive unmittelbarer Theme-Anwendung (light/dark/system) und Dokument-Metadaten fuer Sprache/Zeitzone.
- KI-Selbstwissen erweitert: Chat-Service haengt allgemeine Benutzereinstellungen (Sprache, Theme, Zeitzone) an den effektiven System-Prompt an, damit diese Vorgaben bei Antworten beruecksichtigt werden.
- Startup-Fix fuer `model.base_directories`: Lifespan-Initialisierung faellt bei ungueltigen persistierten Settings nicht mehr hart aus, sondern nutzt sichere Fallbacks.
- Settings-Read-Pfad gehaertet: invalides JSON/ungueltige gespeicherte Werte werden bei `SettingsService.get(...)` uebersprungen, sodass gueltige Scope-Kandidaten oder Defaults weiter greifen.
- Pfadnormalisierung korrigiert: `normalize_base_directories(...)` vergleicht jetzt aufgeloeste Pfade statt roher Strings, damit relative Defaultpfade wie `./model-directories` korrekt akzeptiert werden.
- Neue Regression abgesichert: Integrationstest deckt den Fall "persistiertes invalides model.base_directories" ab und prueft den erfolgreichen Fallback auf gueltige Werte.
- Selbstheilung fuer Settings aktiviert: erkannte invalide persistierte Werte werden bei `SettingsService.get(...)` jetzt automatisch auf den aufgeloesten, validierten Wert zurueckgeschrieben (inkl. Commit) statt nur transient als Fallback genutzt zu werden.
- Selbstheilung gehaertet: Read-Repair greift nur noch bei bekannten Settings-Fehlern (`InvalidSettingError`, JSON-Decode) und behandelt keine allgemeinen Programm-/DB-Fehler als reparierbare Settings.
- Selbstheilungs-Audit ergaenzt: strukturierte Logs enthalten jetzt Schluessel, Scope, redigierten Altwert, Ersatzwert und Validierungsgrund; sensible Schluesselwerte werden maskiert.
- Scope-Sicherheit verifiziert: User-spezifische invalide Settings werden nur im selben Scope repariert; globale Settings bleiben unveraendert.
- Pytest-Konfig-Warnung entfernt: veraltete Option `asyncio_mode` aus `pyproject.toml` entfernt.
- Integrationssuiten gehaertet: mehrere Tests verwenden jetzt echte registrierte Benutzer statt harter `user_id=1`, um FK-Randfaelle in isolierten Testdatenbanken zu vermeiden.
- Voller Backend-Regressionlauf erfolgreich: `43 passed, 1 warning`.
- Punkt-2-Stabilisierung abgeschlossen: Frontend-Themeauflosung ist jetzt in Test- und Laufzeitumgebungen robust gegen fehlendes `matchMedia` (JSDOM/Legacy-Browser), inkl. abgesichertem System-Theme-Listener.
- Settings-Integrationstests gehaertet: user-scoped Settings-Updates legen in Tests vorab echte Benutzer an, wodurch FK-Verletzungen sauber vermieden und Scope-Verhalten realistisch geprueft werden.
- Chat-Selbstwissen-Bugfix: fehlender `asyncio`-Import in `app/chat/service.py` behoben; dadurch werden `system.language`, `system.theme` und `system.timezone` wieder korrekt asynchron geladen statt auf Fallbackwerte zurueckzufallen.
- Regressionstest-Suite stabilisiert: fokussierte Backend- und Frontend-Tests fuer Allgemein-Settings, Prompt-Selbstwissen und AppShell-Polling laufen wieder gruen (`12 passed` backend-focused, `5 passed` frontend-focused).

- Frontend-Serverdaten auf TanStack Query konsolidiert: zentrale Query-Keys fuer Modelle, Health, Workspace-Daten, Konversationen, Nachrichten und Presence eingefuehrt; lokaler React-State bleibt auf UI-Zustand fokussiert.
- QueryClient global verdrahtet (`QueryClientProvider` in `frontend/src/main.tsx`) und AppShell-Polling/Optimistic-Updates auf Query-Cache (`setQueryData`/`fetchQuery`) umgestellt.
- Frontend-Regressionstests fuer Polling/Praesenz ergaenzt: React-Strict-Mode haelt jetzt pro Scheduler genau ein aktives Intervall (Message 3s, Presence 20s).
- Heartbeat-In-Flight-Deduplikation testseitig abgesichert: parallele `sendPresenceHeartbeat`-Aufrufe fuehren nur einen API-Request aus und erlauben nach Abschluss wieder einen neuen Request.
- Systemdiagnostik erweitert: neuer API-Bereich `/api/system/diagnostics` liefert exportierbaren Diagnosebericht mit CUDA-Verfuegbarkeit, offenen Ports, zentralen Pfaden, Python-Umgebung und Backendstatus.
- Diagnose-Export produktiv: `/api/system/diagnostics/export` liefert Download (`attachment`) als JSON inklusive `no-store`-Header; Integrationstests fuer Inhalt und Header ergaenzt.
- Settings-Mutationen im Frontend vereinheitlicht: zentrale TanStack-Query-Helfer fuer `getSetting`/`updateSetting` eingefuehrt, inklusive standardisierter Cache-Aktualisierung und Invalidierung je Setting-Key.
- Einstellungen-UI erweitert: in Gruppe `System` kann der Diagnosebericht direkt aus dem Frontend exportiert werden.
- Modellfaehigkeiten ueber eigenen API-Endpunkt bereitgestellt: `GET /api/models/capabilities` liefert erforderliche Chat-Capabilities, Runtime-GPU-Status, aktive Backend-Informationen und Backend-Capability-Profile.
- API-Capability-Advertise erweitert: `GET /api/meta/capabilities` enthaelt jetzt `models.capabilities`, sodass Clients den Endpunkt feature-gated nutzen koennen.
- Integrationstests fuer Modell-Capabilities ergaenzt: Contract fuer `/api/models/capabilities` sowie Feature-Flag in `/api/meta/capabilities` abgesichert.
- Sidebar-Kontextnutzung auf externe Datenquellen umgestellt: im Reiter `Kontext` wird die Auslastung nun dynamisch aus den geladenen Quellen (Datei-Anzahl + Relevanz) berechnet und als Gesamt-/Teilwerte angezeigt.
- Kontext-Detailansicht verbessert: bei `Externe Daten` werden konkrete Quellen mit Position und normalisierter Relevanz direkt angezeigt statt statischer Platzhaltertexte.
- Kontextnutzung auf echte Servermetriken umgestellt: neuer Endpoint `GET /api/chat/context-usage` berechnet Budget- und Tokenwerte mit derselben Token-/Truncation-Logik wie der Prompt-Build (`TokenBudget`, `TokenCounter`, `truncate_messages`).
- Frontend-Sidebar nutzt jetzt serverseitige Werte fuer `System-Prompt`, `Chatverlauf`, `Antwortreserve` und `Gesamtauslastung` statt heuristischer Schaetzungen.
- Integrationstest ergaenzt: Contract von `/api/chat/context-usage` (Breakdown, Usage, External-Data-Metadaten) ist abgesichert.
- Externe Kontexttokens aus konkreter Retrieval-Auswahl pro Anfrage umgesetzt: `external_data_tokens` basiert jetzt auf den tatsaechlich ausgewaehlten Quellen (`knowledge.top_k`, Query-Term-Matching + Relevanzgewichtung) statt auf statischer Schaetzung.
- Prompt-Aufbau erweitert: `Knowledge`-Abschnitt wird budgetbewusst in den Prompt integriert; Truncation fuer Historie und Retrieval-Kontext erfolgt konsistent ueber dieselbe Builder-Logik.
- Kontext-API erweitert: `external_data` liefert nun `selected_count`, `dropped_count`, `top_k` und `selected_sources`; Sidebar-Detailansicht zeigt diese konkret ausgewaehlten Retrieval-Quellen an.
- Regressionstest verschaerft: nach Workspace-Seed muss `/api/chat/context-usage` jetzt positive `external_data_tokens` und `files_tokens` liefern.
- Modell-spezifischer System-Prompt wird jetzt im Chat-Service korrekt uebergeben: statt Hardcoding wird `prompt.model_{model_id}_system_prompt` (mit Fallback) fuer Prompt-Build und Token-Breakdown genutzt.
- Erweiterte Generierungsparameter eingefuehrt und verdrahtet: `top_k`, `top_p`, `repetition_penalty`, `stop_sequences`, `seed`, `do_sample` werden als Settings pro Modell gespeichert, serverseitig aufgeloest und an das Backend uebergeben.
- Settings-Validierung ausgebaut: neue Chat-Parameter inkl. modell-spezifischer Keys (`model_<id>_*`) werden typ- und bereichssicher validiert.
- Einstellungs-UI erweitert: im Bereich `Prompts` sind nun zusaetzlich `Sampling Top-K`, `Top-P`, `Repetition Penalty`, `Stop Sequences`, `Seed`, `do_sample` sowie Preset-Knoepfe `Modus praezise` und `Modus kreativ` verfuegbar; `Retrieval Top-K` bleibt separat steuerbar.
- Integrationstest ergaenzt: `/api/chat/generate` prueft jetzt explizit, dass modell-spezifischer System-Prompt und Generierungsparameter tatsaechlich im Backend-Aufruf landen.
- Konversationsprofile versioniert umgesetzt: API fuer Erstellen, Auflisten und Aktivieren von Generierungsprofil-Versionen pro Konversation ist produktiv (`/api/conversations/{id}/generation-profiles`, Aktivierung pro `version_id`).
- Chat-Kontextauflosung erweitert: aktive Konversations-Profilversion kann jetzt System-Prompt und Decoding-Parameter ueberschreiben (mit Prioritaet hinter Request-Overrides).
- Projektverwaltung vervollstaendigt: neue Workspace-Endpunkte fuer Projekt anlegen, umbenennen und loeschen eingefuehrt (`POST/PATCH/DELETE /api/workspace/projects...`).
- Chat-Projekt-Zuordnung eingefuehrt: Konversationen tragen optional `project_id` (persistiert ueber `chat.conversation_project_map`) und koennen per `PATCH /api/conversations/{id}/project` zugeordnet/entkoppelt werden.
- Frontend-Projektworkflow vervollstaendigt: Projekte koennen im Bereich `Projekte` erstellt, ausgewaehlt, umbenannt und geloescht werden; Header und Chat zeigen die aktuelle Projektzuordnung dynamisch statt statisch.
- Neuer-Chat-Flow erweitert: neue Konversationen koennen mit der aktuell ausgewaehlten Projektzuordnung gestartet werden.
- Frontend-Startup-Fix: `AppShell`-Crash durch `selectedConversation`-Initialisierungsreihenfolge behoben (TDZ/ReferenceError), App ist wieder erreichbar.
- Training-Grundgeruest eingefuehrt: neues Paket `app/training` mit `trainers/base.py` (Trainer-Interface, Run-Context, Result) sowie leerer Trainings-API-Route `GET /api/training/health`.
- Training-API in FastAPI registriert (`app/main.py`), sodass die neue Route direkt verfuegbar ist.
- Training-Scaffold erweitert: weitere Subpakete fuer `datasets`, `jobs`, `evaluation`, `services`, `repositories` und `models` mit ersten Placeholder-Typen/Services angelegt.
- Training-Settings ergaenzt: neue Defaults und Validator-Regeln fuer `training.*` (u. a. `enabled`, `default_trainer`, Verzeichnisse, Queue-Autostart, Evaluation/Registrierung und `max_concurrent_jobs` inkl. Hard-Limit).
- Erste echte Training-API-Operationen umgesetzt: Datasets koennen jetzt angelegt und gelistet werden (`POST/GET /api/training/datasets`), Jobs koennen eingereicht, gelistet und per ID abgefragt werden (`POST/GET /api/training/jobs`, `GET /api/training/jobs/{job_id}`).
- Persistenz fuer Training eingefuehrt: neue DB-Modelle und Repositories fuer Datasets/Jobs (`training_datasets`, `training_jobs`) inkl. Startup-Schemaerstellung ueber bestehende Runtime-Initialisierung.
- Frontend-Zugang fuer Training-Einstellungen in `Einstellungen` ergaenzt: neuer Bereich `Training` mit Laden/Speichern fuer `training.enabled`, `training.default_trainer`, Verzeichnisse, Queue-Autostart, Auto-Evaluation, Auto-Registrierung und `training.max_concurrent_jobs`.
- Training-Tab im Frontend erweitert: Dataset-Liste und Job-Liste werden jetzt live aus den neuen Training-Endpunkten geladen; zusaetzlich koennen Datasets und Jobs direkt aus dem Tab erstellt werden.
- Training-Job-Lifecycle erweitert: neue Endpunkte fuer `Cancel` und `Retry` (`POST /api/training/jobs/{job_id}/cancel`, `POST /api/training/jobs/{job_id}/retry`) inklusive Status-Guards fuer terminale Jobs.
- Training-Tab erweitert: Job-Detailansicht mit Hyperparametern, Resultat-JSON und Fehlertext verfuegbar; pro Job sind Aktionen `Details`, `Cancel` und `Retry` direkt in der UI angebunden.
- Training-Ausfuehrung aktiviert: separater Background-Worker verarbeitet jetzt `queued`-Jobs mit Lifecycle-Transitionen (`preparing`, `running`, `evaluating`, `completed`/`failed`/`cancelled`) ausserhalb des API-Request-Zyklus.
- Training-Runtime transparent gemacht: Job-Response enthaelt jetzt explizite Fortschrittsfelder (`progress`, `current_step`, `total_steps`, `current_epoch`, `loss`, `learning_rate`, `logs`) aus dem Worker-Lauf.
- Trainer-Architektur erweitert: neue Trainer-Registry mit einheitlicher Backend-Schnittstelle (`prepare`, `train`, `evaluate`, `save`) und initialer LoRA-Referenzimplementierung.
- Echten LoRA-Trainingspfad ergaenzt: neuer `PeftLoRATrainer` (Transformers/PEFT/bitsandbytes) mit 4-bit Option, Hugging-Face-Callback fuer Progress/Cancel und strukturierter Artefaktablage unter `artifacts/jobs/<job-id>/...`.
- Dataset-Adapter ergaenzt: JSONL-Parsing, Schema-Validierung (`messages` oder `input`/`target`), Duplikatfilterung und Secret-Erkennung vor Trainingsstart.
- Transparenz fuer Referenzlaeufe ergaenzt: Jobs liefern `is_simulation`; Health-Endpunkt listet verfuegbare Trainer inkl. Simulationseigenschaft.
- Training-Lifecycle erweitert: Status `saving` und `validation_failed` eingefuehrt; Validation-Probleme brechen kontrolliert mit nachvollziehbarem Status ab.
- Trainings-Basismodell an den zentralen Model Manager angebunden: `training.base_model` als neues Setting eingefuehrt und in Backend-Validation/Defaults verankert.
- Training-Job-Submit verwendet nun zentrale Modellaufloesung: ohne explizites `base_model_id` wird automatisch `training.base_model` genutzt; bekannte Registry-Modelle werden aufgeloest und Metadaten (`base_model`, `base_model_name`, `base_model_registry_id`, `base_model_backend`) im Job gespeichert.
- Frontend-Training-UI auf zentrale Modellverwaltung umgestellt: Basis-Modell-Auswahl in den Training-Einstellungen und beim Job-Start erfolgt ueber registrierte Modelle statt Freitext-ID; Modell-Metadaten (Backend/Status/Pfad) werden angezeigt.
- Trainings-Preflight eingefuehrt: neuer Endpoint `POST /api/training/preflight` prueft vor Jobstart Modellregistrierung, Pfad-/Formatgueltigkeit, Transformers-Tokenizer/Architektur, CUDA/4-bit-Abhaengigkeiten, Dataset-Validitaet, Artefaktverzeichnis und freien Speicherplatz.
- Job-Submit gehaertet: `POST /api/training/jobs` fuehrt den Preflight serverseitig aus und blockiert Queueing bei harten Fehlern mit strukturiertem Preflight-Report.
- Training-Tab erweitert: Preflight kann explizit gestartet werden; Ergebnis (Ready, Fehler, Warnungen, CUDA/4-bit/Dataset-Status) wird angezeigt und Jobstart waehrend laufendem Preflight gesperrt.
- Preflight-Hardening erweitert: fehlende Kernabhaengigkeiten (`transformers`, `peft`, `datasets`, `accelerate`) werden als harte Fehler vor Jobstart erkannt.
- CUDA-Logik verfeinert: fehlendes CUDA ist nur dann zwingend harter Fehler, wenn 4-bit angefordert ist; fuer CPU-Smoke-Runs ist ein explizites `allow_cpu_training=true` erforderlich.
- Trainings-Default auf `peft_lora` umgestellt (Backend-Default + Frontend-Initialwert); UI-Hinweis ergaenzt, dass `unsloth` aktuell nicht produktiv verfuegbar ist.
- Startskript gehaertet: `scripts/start_fullstack.ps1` priorisiert fuer das Backend jetzt `.venv-training` (danach `.venv`, danach globales `python`), damit Training mit der korrekten Laufzeit startet.
- Lokale Trainingslaufzeit korrigiert: dedizierte `.venv-training` mit CUDA-faehigem PyTorch (`2.11.0+cu128`) sowie `transformers`, `peft`, `datasets`, `accelerate`, `bitsandbytes` verifiziert.
- Trainings-Dataset fuer Smoke-Run konkretisiert: JSONL-Datei angelegt und `training_datasets.metadata_json.source_path` auf gueltigen lokalen Pfad gesetzt.
- Runtime-Bugs im echten PEFT-Pfad behoben: Executor verwendet jetzt den von `prepare()` erzeugten Payload; `TrainingArguments` ist gegen API-Unterschiede (`evaluation_strategy`/`eval_strategy`) robust; Callback-Fehler bei `args`-Nutzung korrigiert.
- Echter 4-bit-PEFT-Smoke-Run erfolgreich verifiziert (`max_steps=5`): Job abgeschlossen, Adapter-/Tokenizer-Artefakte geschrieben und Adapter-Ladecheck (`PeftModelForCausalLM`) erfolgreich.
- Faehigkeitsbasierte Modellklassifikation eingefuehrt: Scanner erkennt jetzt strukturierte Modellmerkmale (Format/Familie/Task) via `config.json`, `model_index.json`, ONNX-/GGUF-Hinweise, README-Frontmatter (`pipeline_tag`/`tags`) und Namensheuristiken.
- Systemverzeichnisse beim Modellscan ausgeschlossen (`manifests`, `_e2e`, `_system`), um nicht nutzbare Hilfsartefakte aus der Modellliste herauszuhalten.
- Loader-Registry fuer Modellverfuegbarkeit ergaenzt: kompatible Loader werden task-/formatbasiert aufgeloest; fehlende Loader liefern jetzt nachvollziehbare `reason_unavailable`-Gruende.
- Modell-API erweitert: `GET /api/models` liefert jetzt gruppierte und sortierbare Capability-Metadaten (`group`, `task_type`, `model_format`, `model_family`, `relevance`, `status_label`, `status_color`, `reason_unavailable`, `capabilities.*`).
- Statussemantik fuer Modell-UI vereinheitlicht: aktive/ladende/bereite/fehlerhafte/nicht-verfuegbare Modelle werden serverseitig mit semantischer Farbzuordnung vorbereitet.
- Trainings-API erweitert: neuer Endpoint `GET /api/training/trainers` liefert verfuegbare Trainer inklusive Availability-Reason; nicht verfuegbare Trainer werden beim Jobstart/preflight serverseitig blockiert.
- Trainings-Kompatibilitaet eingefuehrt: neuer Endpoint `GET /api/training/compatibility?trainer_name=...` bewertet Modell-Trainer-Paare inkl. Grund fuer Inkompatibilitaet.
- PEFT-Kompatibilitaetsregeln serverseitig verankert: `peft_lora` akzeptiert nur trainierbare Transformers-Textgeneration-Modelle; GGUF/inkompatible Tasks werden sauber abgelehnt.
- Frontend-Trainingseinstellungen umgestellt: `defaultTrainer` ist jetzt Dropdown aus API-Trainerliste statt Freitext; nicht verfuegbare Trainer sind sichtbar, aber blockiert und begruendet.
- Frontend-Training-Jobformular erweitert: trainergebundene Modellkompatibilitaet wird bei Basismodell-Auswahl angezeigt; inkompatible Modelle bleiben sichtbar, aber deaktiviert (mit Grund).
- Modellverwaltung in den Einstellungen auf Gruppierung/Statusdarstellung erweitert: Modelle werden nach Capability-Gruppen dargestellt und mit farblicher Statusanzeige samt Unverfuegbarkeitsgrund ausgegeben.
- Runtime-Loader schrittweise produktiv gemacht: `transformers` ist jetzt als reales Modell-Backend registriert und lokal fuer Textgenerierung inkl. Streaming nutzbar.
- Loader-Registry von statischen Platzhaltern auf echte Runtime-Probes umgestellt: Verfuegbarkeit fuer Embedding/Reranker/Speech/ONNX/Diffusers/OCR wird jetzt aus installierten Abhaengigkeiten abgeleitet und mit konkreten Ursachen begruendet.
- Persistente Modell-Relevanz eingefuehrt: Nutzer koennen Modelle als `favorite` oder `irrelevant` markieren; die Markierungen werden ueber Settings gespeichert (`model.relevance_flags`).
- Modellsortierung erweitert: persistente Relevanzflags fliessen jetzt serverseitig in Relevanzstufe und Sortierreihenfolge ein (`active > favorite > relevant > unavailable > irrelevant`).
- Neue Model-API fuer Relevanz-Updates: `POST /api/models/{model_id}/relevance` speichert/entfernt benutzerbezogene Relevanzflags.
- Modell-UI erweitert: in `Einstellungen > Modelle` koennen Relevanzflags direkt gesetzt/entfernt werden (`Favorit`, `Irrelevant`).
- Trainings-Kompatibilitaet im UI dynamisiert: bei Trainerwechsel wird serverseitige Kompatibilitaet gezielt neu geladen und inkompatible Modelle bleiben sichtbar, aber deaktiviert.
- Neuer Frontend-Test: Trainerwechsel aktualisiert Kompatibilitaet und deaktiviert inkompatible Basismodelle im Training-Formular.
- Neuer Backend-Integrations-Test: End-to-End-Flow prueft Trainerwechsel-Kompatibilitaet sowie erfolgreichen `peft_lora`-Preflight und Job-Submit.
- Verifikations-Hardening fuer reale Modellbestaende abgeschlossen: Vollscan gegen `F:\\KI\\models` erneut ausgefuehrt und Klassifikation/Loaderauflosung live verifiziert.
- Modellheuristiken praezisiert: GGUF-Verzeichnis-Erkennung (inkl. nested `*.gguf`), Priorisierung von Transformers vor ONNX bei gemischten Artefakten, robuste Reranker/Embedding-Erkennung sowie BERT-Default auf `feature_extraction`.
- Multimodal-Disambiguierung verbessert: `image-text-to-text` aus README wird bei klassischen Instruct-LLMs nicht mehr blind auf `vision_text_generation` gemappt; klare VLM-Hinweise bleiben weiterhin multimodal.
- Loader-Registry erweitert: dedizierte Loader fuer GGUF-Embedding/Reranking (`llama_cpp_embedding`, `llama_cpp_reranker`) sowie VAD-Loader und `feature_extraction`-Support im Embedding-Pfad.
- Scan-Upsert gehaertet: Re-Scan aktualisiert jetzt auch Legacy-Modelle ohne/mit abweichendem Pfad via Namensabgleich; GGUF-Verzeichnispfade werden in der Registry-Validierung akzeptiert, wenn mindestens eine GGUF-Datei vorhanden ist.
- Modellstatussemantik verfeinert: erkannte, aber durch fehlende Runtime-Abhaengigkeiten limitierte Modelle werden als `eingeschraenkt` (gelb) statt pauschal `nicht verfuegbar` markiert.
- Verifikation erneut bestanden: `python -m pytest tests/integration/test_training_end_to_end.py -q`, `npm run build`, `npx vitest run src/components/content/WorkspacePage.training-compatibility.test.tsx`.
- Settings-Fallback fuer modell-spezifische Keys gehaertet: `GET /api/settings/*/model_<id>_*` faellt bei fehlendem Override jetzt korrekt auf Basis-Keys/Defaults zurueck (statt `400`).
- Chat-Composer entkoppelt von reinem Health-Flag: Eingabe/Senden bleibt bei gewaehltem Modell moeglich; harter Disabled-Zustand nur noch ohne Modellauswahl.
- Layout-Stabilitaet verbessert: Header/Footer bleiben dauerhaft sichtbar, zentrale Ansicht und linke/rechte Sidebars scrollen unabhaengig, Ueberdecken von Inhalt durch die Kontext-Sidebar reduziert.
- Conversation-UX bei Team-/Stale-Chats gehaertet: Projektzuordnung nur noch fuer eigene Konversationen, Loeschen fuer Fremdchats im UI blockiert und `404`-Faelle (bereits geloescht/nicht mehr sichtbar) werden mit automatischer Listenbereinigung abgefangen.
- Modellaktivierung diagnostischer gemacht: `POST /api/models/{id}/activate` liefert bei fehlender Runtime/Loader jetzt strukturierte `409`-Fehler (`model.loader_not_found` / `model.loader_unavailable`) inkl. `loader_id`, `model_format` und `task_type`.
- Lokaler Prompt-Diagnosemodus fuer Chat-Anfragen ergaenzt: aktivierbar ueber `LOCAL_PROMPT_DIAGNOSTICS`, mit strukturierten Logs zu Modell/Backend, Rollenfolge, Chat-Template-Quelle, Tokenverteilung und Retrieval-Auswahl inkl. Scores; finaler Prompt wird nur optional ueber `LOCAL_PROMPT_DIAGNOSTICS_INCLUDE_PROMPT` geloggt.
- Transformers-Chatformat gehaertet: bei strukturierten Nachrichten verwendet das Backend jetzt bevorzugt `tokenizer.apply_chat_template(..., add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors="pt")`; Legacy-Stringprompt bleibt nur Fallback.
- Retrieval-Selektion robuster gemacht: tokenbasierte Query-Matches (statt Substring-Treffern), konfigurierbare Schwellwerte (`knowledge.min_score_ratio`, `knowledge.min_absolute_score`, `knowledge.min_score_gap`) und detaillierte Selektionsdiagnostik (`selected`/`discard_reason`) pro Kandidat.
- Frontend-Keying korrigiert: hartcodiertes `conversation_tree_user_1` durch benutzerkontextbezogenen Key `conversation_tree_user_<currentUser.id>` ersetzt.
- Regressionstests erweitert: Unit-Tests fuer Retrieval-Gating und Transformers-Chat-Template-Nutzung sowie Frontend-Regression fuer benutzerbezogenen Conversation-Tree-Key hinzugefuegt.
- GGUF/llama.cpp-Chatformat erweitert: bei strukturierten Rollen-Nachrichten nutzt das Backend jetzt bevorzugt `create_chat_completion(...)` (modellinternes Chat-Template) statt universellem Prompt-String; Completion-Flow bleibt als Fallback erhalten.
- Lokaler Diagnose-Endpunkt fuer Prompt-/Retrieval-Analyse hinzugefuegt: `GET /api/chat/diagnostics/prompts` ist nur bei `LOCAL_PROMPT_DIAGNOSTICS=1` aktiv und liefert letzte Anfrage-Diagnosen ohne Log-Parsing.
- Diagnose-Endpunkt um Runtime-Abhaengigkeiten erweitert: Rueckgabe enthaelt jetzt explizit `onnxruntime_installed`, `llama_cpp_installed` und `transformers_installed` fuer schnelle Ursachenanalyse bei fehlenden Loadern.
- Regressionstests fuer neue Diagnose-API und GGUF-Template-Pfad ergaenzt: Integrationstest fuer aktivierten/deaktivierten Diagnose-Endpunkt sowie Unit-Tests fuer llama.cpp Chat-Completion-Pfad.
- Custom-Architecture-Erkennung fuer Supra-A2A-Nano-Exp und aehnliche Modelle produktiv eingefuehrt: neue Formate `custom_safetensors` / `custom_pytorch`, neuer Task-Typ `any_to_any` und Backend-Zuordnung `custom_pytorch`.
- Plugin-basiertes Custom-Loader-Registry-Subsystem eingefuehrt (`app/models/loaders/custom/*`) inklusive Supra-A2A-Nano-Plugin und runtime-abhängiger Loader-Verfuegbarkeit.
- Trust-Gating fuer benutzerdefinierten Modellcode umgesetzt: Modelle mit `requires_custom_code` bleiben bis zur expliziten Freigabe (`custom_code_trusted`) als eingeschraenkt/unverfuegbar markiert.
- Neue Model-API fuer explizite Trust-Entscheidung eingefuehrt: `POST /api/models/{model_id}/trust-custom-code` setzt Vertrauensstatus fuer Custom-Code pro Modell.
- Trainingskompatibilitaet erweitert: `any_to_any`-Modelle werden explizit aus `peft_lora` ausgeschlossen mit klarer Meldung `Nicht mit PEFT-LoRA kompatibel...`.
- Frontend-Modelltypen erweitert: Custom-Code-Flags (`requiresCustomCode`, `customCodeTrusted`, `customLoaderId`) werden aus `GET /api/models` uebernommen.
- Neue Tests ergaenzt: Scanner-Unit-Test fuer Supra-Custom-Erkennung sowie Integrationstest fuer Trust-Gating und PEFT-Inkompatibilitaet.
- Echter `custom_pytorch`-Runtime-Backendpfad implementiert: Aktivierung und Inferenz fuer trusted Custom-Modelle laufen nun ueber einen Plugin-Adapter (`load_model`/`generate`/`stream`) statt an `Unsupported backend` zu scheitern.
- Modellaktivierung erweitert: Metadaten werden beim Laden an den `ModelManager` durchgereicht, sodass Trust-Gating und Custom-Entrypoints im Backend wirksam geprueft werden.
- Backend-Abdeckung erweitert: `custom_pytorch` ist jetzt in der Backend-Factory registriert und erscheint dadurch konsistent in Capability-/Ladepfaden.
- Universelles Dataset-MVP fuer Training integriert: neue modulare Parser-/Konverter-Pipeline mit Auto-Format-Erkennung und kanonischem internem Format (`id`, `messages`, `metadata`, `evaluation`) eingefuehrt.
- Erste Parser produktiv: OpenAI Messages JSON/JSONL, ShareGPT, Alpaca, Q/A-JSON, CSV-QA, Markdown-QA, ChatML-Text sowie YAML/XML/HTML; PDF/DOCX werden optional ueber vorhandene Abhaengigkeiten eingelesen.
- Training-Dataset-Adapter auf kanonischen Import umgestellt: eingehende Formate werden in trainierbare Prompt/Completion-Paare normalisiert, validiert, dedupliziert und als `.canonical.jsonl` neben der Quelldatei persistiert.
- Training-Dateiworkflow erweitert: `GET /api/training/datasets/files` und Upload/Registrierung akzeptieren jetzt mehrere Datensatzformate (`jsonl/json/csv/md/txt/yaml/xml/html/pdf/docx`) statt nur JSONL.
- Frontend-Training-UI aktualisiert: Dateiupload akzeptiert die erweiterten Formate und die Dateiliste verwendet eine formatneutrale Beschriftung.
- Scan-Upsert fuer Custom-Modelle weiter gehaertet: Trust-Status (`custom_code_trusted`) bleibt bei Re-Scans stabil erhalten, und Upsert-Matching laeuft jetzt pfadbasiert deterministisch (Pfad zuerst, Name nur als Fallback), um Konflikte auf `model_path` zu vermeiden.
- Einmalige Legacy-Bereinigung im Scan integriert: Datei-vs-Ordner-Dubletten pro Modellordner werden jetzt auf einen kanonischen Ordner-Datensatz zusammengefuehrt; `custom_code_trusted` wird dabei sicher uebernommen.
- Scanner-Klassifikation fuer Ultravox korrigiert: `ultravox`-Modelle und `audio-text-to-text`-Hinweise werden jetzt als `audio_text_generation` statt `vision_text_generation` eingeordnet.
- Loader-Registry fuer multimodale Transformers erweitert: neuer Loader `transformers_vision` fuer `vision_text_generation`-Modelle (z. B. SmolVLM2) mit klarer Runtime-Abhaengigkeit auf `transformers` + `pillow`.
- Transformers-Backend erweitert: `vision_text_generation` laedt jetzt `AutoProcessor` + `AutoModelForVision2Seq` und kann Bild-Payloads (`images[]` mit Base64) zur Generierung verwenden.
- Chat-Pfad fuer echte Bilddaten durchgaengig umgesetzt: Frontend sendet Bildanhaenge als strukturierte `images[]`-Payload an `/api/chat/generate`, Backend reicht diese bis zum Modellbackend durch (statt reiner Textplatzhalter).
- SmolVLM2-Liveaktivierung stabilisiert: `transformers_vision` faellt nicht mehr am generischen Health-Check, da Vision-Backends nun auf `processor` statt `tokenizer` validiert werden.
- Vision-Generate-Pfad gehaertet: bei Prozessoren mit Bildplatzhalter-Pflicht (z. B. SmolVLM) wird bei Bedarf automatisch ein passender `<image>`-Prefix injiziert statt mit `number of images in the text ... should be the same` abzubrechen.
- End-to-End-Smoke verifiziert: SmolVLM2 laesst sich live aktivieren und ein echtes JPEG wird ueber `/api/chat/generate` durch den kompletten Chat-Pfad verarbeitet.
- GGUF-Loaderdiagnostik gehaertet: `llama_cpp*`-Loader melden bei fehlendem Modul jetzt den tatsaechlich laufenden Backend-Interpreter und den konkreten Importfehler statt nur "nicht installiert".
- Antwortstil serverseitig stabilisiert: Chat-Service erweitert den effektiven Systemprompt um klare Markdown-/Strukturregeln (ohne bestehende modellspezifische Overrides zu brechen).
- Chat-Generierungsdefaults fuer sachliche Antworten angepasst: `temperature=0.3`, `top_p=0.9`, `top_k=40`, `repetition_penalty=1.1`, `max_new_tokens=512`.
- Optionale Nachbearbeitung im Chat-Service eingefuehrt: nur whitespace-/listenbezogene Normalisierung (keine inhaltliche Umschreibung oder kuenstliche Abschnittserfindung).
- Frontend-Chat rendert Modellantworten jetzt als Markdown (`react-markdown`) statt als reinen Fliesstext; zusaetzliche CSS-Abstaende fuer Ueberschriften, Absaetze und Listen ergaenzt.
- Projektabfragen im Frontend benutzerbezogen korrigiert: `GET /api/workspace/projects` wird nun mit `user_id` des eingeloggten Nutzers geladen, inklusive user-spezifischem Query-Key im Cache.
- Neue-Konversation-Flow gehaertet: bei stale/ungueltiger Projektzuordnung (`project.not_found` / 404) wird die Zuordnung lokal zurueckgesetzt, Projekte neu geladen und die Konversation ohne Projekt erneut erstellt statt komplett zu scheitern.
- Startskripte auf gemeinsame Chat-Umgebung vorbereitet: `.venv-chat` wird jetzt als primaerer Backend-Interpreter vor `.venv-training`/`.venv` aufgeloest.
- Neues Setup-Skript hinzugefuegt: `scripts/setup_venv_chat.ps1` erstellt eine `.venv-chat` auf Basis von Python 3.12 und kann optional Core-Abhaengigkeiten installieren.
- Python 3.12 als neue Haupt-Chatlaufzeit lokal eingerichtet: `.venv-chat` ist erstellt, Kernabhaengigkeiten sind installiert, und die Startskripte starten den Stack nun bevorzugt aus dieser Umgebung.
- GGUF-Runtime unter `.venv-chat` produktiv verifiziert: `llama-cpp-python` wurde erfolgreich installiert und GGUF-Loader werden live wieder als verfuegbar angezeigt.
- llama.cpp-Backend gehaertet: GGUF-Ordnerpfade werden jetzt auf die enthaltene `.gguf`-Datei aufgeloest, statt bei Verzeichnis-Pfaden mit `Model file not found` zu scheitern.
- llama.cpp-Chatformat robuster gemacht: wenn ein GGUF-Chat-Template die Rolle `system` nicht unterstuetzt, faellt das Backend jetzt automatisch auf den bestehenden Prompt-String-Fallback zurueck statt mit `System role not supported` abzubrechen.
- Live-End-to-End erneut verifiziert: Projekt erstellen, Konversation anlegen, GGUF-Modell aktivieren und echte Chatantwort ueber `/api/chat/generate` funktionieren auf dem laufenden Stack.
- Trainings-Dataset-Flow erweitert: vorhandene `.jsonl`-Dateien im `training-datasets`-Ordner koennen jetzt per API/UI entdeckt und direkt als Dataset registriert werden.
- Neue Trainings-Importpfade umgesetzt: Datasets koennen jetzt zusaetzlich per Datei-Upload oder per Web-URL in den Trainingsordner uebernommen und registriert werden.
- Trainings-UI erweitert: im Workbench-Bereich stehen jetzt `Ordnerdatei registrieren`, `Datei hochladen` und `URL importieren` direkt neben dem Dataset-Formular zur Verfuegung.
- Trainingsbetrieb fuer den aktuellen Nutzer live verifiziert: `training.enabled=true`, `training.base_model=Qwen3.5-2B`, Naturstein-Dataset registriert, Preflight erfolgreich (`ready=true`) und Job `#5` erfolgreich auf `queued` gestellt.
- PEFT-Trainer gehaertet: wenn `validation_source_path` in den Dataset-Metadaten vorhanden ist, wird diese Datei jetzt separat mitverwendet statt die Trainingsdatei erneut per `train_test_split` aufzuteilen.
- Naturstein-Dataset-Pfade verifiziert: der vorbereitete Datensatz liefert jetzt tatsaechlich `110` Trainings- und `20` Validierungsbeispiele im Trainer-Prepare-Pfad.
- Tokenizer/Modell-Spezialtokens im PEFT-Lauf gehaertet: ungueltige `pad_token_id`-/`eos_token_id`-/`bos_token_id`-Konfigurationen werden vor dem Training korrigiert oder im Preflight als harte Fehler gemeldet.
- Transformers-Ladepfad im Trainer modernisiert: `dtype` wird bevorzugt verwendet, mit kompatiblem Fallback auf `torch_dtype` fuer aeltere Laufzeiten.
- Trainings-Heartbeat verbessert: `logging_first_step` und fruehe Progress-Logs (`training initialized`, `first training step running`) werden jetzt bereits vor dem ersten abgeschlossenen Schritt in den Job-Runtime-Status geschrieben.
- Kontrollierter Kurzlauf produktiv moeglich: Job `#6` wurde mit `max_steps=5`, `max_sequence_length=512`, `logging_steps=1` und `logging_first_step=true` erfolgreich auf `queued` gestellt.
- Trainings-Artefaktcheck erweitert: neuer Live-Endpunkt fuer abgeschlossene Jobs prueft Adapter-Dateien, Manifest, Trainer-State und fuehrt einen PEFT-Adapter-Ladecheck gegen das Basismodell aus.
- Kurzlauf `#6` vollstaendig verifiziert: Status `completed`, Artefakte vorhanden (`adapter`, `tokenizer`, `manifest.json`, `metrics.json`, `trainer-state.json`), Adapter-Ladecheck erfolgreich.
- Trainings-UI aufgeraeumt: vorhandene Ordnerdateien sind jetzt in einem eigenen Bereich sichtbar, zeigen Registrierungsstatus an und werden in den Auswahlfeldern als `bereits registriert` markiert.
- Testabdeckung erweitert: neuer Unit-Test fuer `CustomPyTorchBackend` (Load/Generate/Stream/Health/Trust) und Integrationstest fuer erfolgreiche Aktivierung nach expliziter Trust-Freigabe.
- Sicherheitsdokumentation bereinigt: `docs/zugaenge.md` enthaelt keine Klartext-Passwoerter mehr und verweist nur noch auf Secret-Speicher.
- Supra-Erkennung gehaertet: `SupraA2ANanoLoader.detect()` sucht Pflichtartefakte (`model.safetensors`, `vqvae.safetensors`, `tokenizer.json`) sowie Custom-Entrypoints jetzt robust rekursiv statt nur im Wurzelordner.
- Scan-Upsert gehaertet: bestehende `ModelConfig`-Eintraege werden bei Rescan auch dann aktualisiert, wenn alte Datensaetze auf verwandte Pfade zeigen (z. B. Datei- statt Ordnerpfad); dabei werden Name, Pfad, Backend, Format, Task und Metadaten konsistent ueberschrieben.
- Live-Verifikation gegen `F:\KI\models` abgeschlossen: `Supra-A2A-Nano-Exp` wird nach Full-Rescan als `backend=custom_pytorch`, `model_format=custom_safetensors`, `task_type=any_to_any`, `loader=supra_a2a_nano` und `status_label=eingeschraenkt` ausgeliefert.
- Prompt-Persistenz im Frontend gehaertet: im Modellprofil faellt der modellspezifische Prompt jetzt auf den globalen `prompt.system_prompt` zurueck, statt als leer zu erscheinen.
- Quellen-Retrieval von Mockdaten entkoppelt: Seed-Quellen werden nicht mehr als echte Upload-Daten behandelt (`seed_mock`) und bei fehlenden echten Quellen wird intern explizit "Keine relevanten externen Quellen gefunden." gesetzt.
- Antwortausgabe gehaertet: unbelegte Quellenblaecke/Links werden bei `external_data_selected_count=0` aus der finalen Antwort entfernt.
- Bibliothek erweitert: neuer Upload-Endpunkt fuer echte Quellen (`POST /api/workspace/sources/upload`) akzeptiert `pdf`, `md`, `txt`, `docx`; Frontend-API/Ansicht sind angebunden.
- Antwortlesbarkeit im Chat-Postprocessing weiter gehaertet: automatische Header-Promotion, Aufspaltung inline-verdichteter Listenbloecke und saubere Header-Abstaende fuer besser strukturierte Ausgabe bei langen Modellantworten.
- Evaluationshilfe fuer Fachhalluzinationen ergaenzt: neuer Pruefprompt fuer die Fehlklassifikation der Charta von Venedig (`docs/venedig-pruefprompt.md`) mit harten Fehlerkriterien und JSON-Urteilsschema.

- Dokumentstruktur bereinigt: Roadmap, TODO und Changelog inhaltlich nach Status getrennt (umgesetzt vs geplant vs naechste Pakete).
- Priorisierte TODO-Struktur eingefuehrt: Kritisch, Hoch, Mittel, Niedrig.
- Spaete und optionale Themen in separaten Backlog ausgelagert.

- Komplettes Projektgeruest erzeugt
- Kernarchitektur fuer Entwicklungsstufe 1 implementiert
- FastAPI + SQLAlchemy async + Settings-Service + Modellscan + Streaming-Chat hinzugefuegt
- Startdatei `start.py` erstellt (Initialisierung + Serverstart)
- Standard-Scanpfade erweitert um `F:\\KI\\models` und dynamischen Startup-Scan aktiviert
- Fullstack-Startskripte hinzugefuegt: `scripts/start_fullstack.ps1` und `scripts/start_fullstack.sh`
- Fullstack-Startskripte verbessert: Port-Konflikte werden erkannt, doppelte Starts vermieden und Vite-Startparameter korrekt uebergeben
- Fullstack-Startskripte erweitert: Option zum Beenden laufender Instanzen (`-StopExisting` bzw. `STOP_EXISTING=1`)
- Workspace-Root-Wrapper hinzugefuegt: `F:\symple chat\scripts\start_fullstack.ps1`
- Neustartverhalten verhaertet: Bei `-StopExisting` wird abgebrochen, wenn Backend oder Frontend nicht wirklich gestoppt werden koennen
- Windows-Stoplogik verhaertet: Taskkill-Erfolg wird korrekt geprueft und ein CIM-Terminate-Fallback fuer haengende Prozesse genutzt
- Frontend-Startfehler behoben: fehlende `frontend/index.html` wiederhergestellt (Root-URL liefert wieder HTTP 200)
- GPU-First Ladepolitik implementiert: ModelManager bevorzugt GPU bei Aktivierung und faellt bei fehlender CUDA-Verfuegbarkeit automatisch auf CPU zurueck
- Codequalitaet verbessert: Markdown-Lint in `docs/AGENTS.md` bereinigt und Typwarnungen in `app/models/registry.py` aufgeloest
- Clean-Code-Refactoring abgeschlossen: Typisierung in `app/chat/service.py`, `app/models/executor.py`, `app/core/events.py`, `app/database/session.py` und `app/models/scanner.py` vereinheitlicht
- Error-Handler-Registrierung robust typisiert und ohne ungenutzte lokale Funktionen umgesetzt
- Zusätzliche Typfixes: `app/settings/service.py` Kandidaten-Typen annotiert und `app/startup.py` Session/Directory-Verarbeitung sauber typisiert
- Frontend-Diagnostik bereinigt: Inline-Styles aus `frontend/src/App.tsx` entfernt, `frontend/src/App.css` + `frontend/src/vite-env.d.ts` ergänzt, TypeScript-Casing-Option aktiviert
- Modulares Frontend-Design implementiert: AppShell mit Header, linker Navigation, zentralem Chatbereich, rechter Kontext-Sidebar und Status-Footer
- UI-Zustaende und Shortcuts fuer Sidebars/Composer ergaenzt (`Strg+B`, `Strg+Umschalt+B`, `Strg+K`, `Strg+N`, `Strg+Enter`, `Esc`)
- Responsive Verhalten abgestimmt: rechte Sidebar unter 1200px aus, linke Sidebar unter 900px eingeklappt, mobile Priorisierung des Chatbereichs unter 700px
- Benachrichtigungs- und Systemfeedback erweitert: Toast-System (auto-hide + persistente Fehlermeldungen) und persistente Warnanzeige bei fehlendem Modell
- Chat-UX erweitert: sichtbarer Modellwechsel als Dropdown (lokal/remote), Quellen-Fussnoten in Antworten, Enter/Shift+Enter-Verhalten, Auto-Resize im Composer und Eingabe-Loeschen-Button
- Informations-UX erweitert: rechte Sidebar um Quellen-Tab und interaktive Kontext-Inspektion ergaenzt; Seitenansichten fuer Projekte/Bibliothek/Termine/Plugins/Einstellungen im Hauptbereich umgesetzt
- Shortcuts und Power-User-Funktionen erweitert: Export, Chat-Fokusmodus, Konversationswechsel per Alt+Pfeile, Performance-Overlay und mobile Overlay-Menues
- Neue Backend-Routen fuer Workspace-Daten eingefuehrt: `/api/workspace/projects`, `/api/workspace/appointments`, `/api/workspace/sources`
- Frontend auf API-Client umgestellt: Modelle (`/api/models` + Aktivierung), Health-Status (`/api/health/model`) sowie Workspace-Daten werden nun beim Start geladen
- Vite-Dev-Proxy fuer `/api` auf Backend (`127.0.0.1:8000`) konfiguriert, um lokale CORS-Probleme zu vermeiden
- Persistente Workspace-Modelle und Repositories eingefuehrt (`Project`, `Appointment`, `KnowledgeDocument`) und statische Workspace-Responses durch DB-Abfragen ersetzt
- Neue API-Endpunkte fuer Chat-Historie eingefuehrt: `/api/conversations` (listen/anlegen) und `/api/messages` (listen/senden)
- Chat-Service erweitert: neue Konversationen erhalten automatisch sinnvolle Titel aus der ersten Benutzeranfrage
- Frontend-Chat auf echte Historie umgestellt: linke Chatliste und Nachrichtenverlauf werden aus Conversations/Messages-Endpunkten geladen
- Send-Workflow verfeinert: explizite Zustandsmaschine (`disabled|idle|submitting|streaming|success|error|stopping`), persistente Fehlermeldung, Retry-Option und `aria-live`-Status
- Startup erweitert: alle DB-Modelle werden vor `create_all` explizit geladen, damit neue Tabellen konsistent erstellt werden
- Einstellungsseite um Modellverwaltung erweitert: Modellscan (`/api/models/scan`) und Modellaktivierung sind nun direkt unter `Einstellungen` verfuegbar
- Frontend-Modellaktivierung zentralisiert: Chat-Header und Einstellungen nutzen denselben Aktivierungs- und Reload-Flow fuer konsistente Statusanzeige
- Einstellungen erweitert: `model.base_directories` ist jetzt im Frontend editierbar (Pfad hinzufuegen/entfernen/speichern) und triggert anschliessend automatisch einen Modellscan
- Einstellungen-UX verbessert: in der Einstellungsansicht wird nur noch die aktuell gewaehlte Kategorie angezeigt
- Modellbezogene Profile ergaenzt: individuelle Prompt- und Parameterwerte werden pro Modell ueber Settings-Keys geladen und gespeichert
- Modellverwaltung verbessert: Deaktivierungs-Endpoint im Frontend angebunden und aktives Modell kann direkt entladen werden (`Entladen` als roter Aktionsbutton)
- Nachrichten-Endpoint gehaertet: wenn ein `model_id` uebergeben wird, wird dieses Modell vor der Antwortgenerierung serverseitig geladen und als aktiv markiert
- Llama-CPP-Stub korrigiert: Antwort basiert nur auf der letzten `User:`-Zeile statt den gesamten Prompt erneut zu spiegeln (verhindert History-Schleifen)
- Llama-CPP-Backend produktiv geschaltet: reales Laden von GGUF-Modellen, echte Completion-Generierung und thread-basiertes Token-Streaming via `llama-cpp-python`
- Sidebar-Chatverwaltung erweitert: Konversationen koennen per Drag-and-Drop als Unterchats organisiert werden; Struktur wird in Settings (`chat.conversation_tree_user_1`) gespeichert
- Konversations-Loeschen hinzugefuegt: neuer Backend-Endpoint `DELETE /api/conversations/{conversation_id}` archiviert Chats und Frontend bietet direkte Loeschaktion je Eintrag
- Chat-Kontextmenue im Sidebar umgesetzt: je Konversation stehen `Umbenennen`, `In Unterchat verschieben` (inkl. Hauptebene) und `Loeschen` mit Bestaetigung bereit
- Konversations-Umbenennen eingefuehrt: neuer Endpoint `PATCH /api/conversations/{conversation_id}` aktualisiert den Titel benutzerbezogen
- Delete-Flow gehaertet: zusaetzliche Kompatibilitaetsrouten (`DELETE` mit Trailing-Slash und `POST /api/conversations/{id}/delete`) sowie Frontend-Fallback gegen 404-Varianten
- Rename-Endpoint `PATCH /api/conversations/{id}` gegen interne 500er gehaertet: SQLAlchemy-Fehler werden kontrolliert behandelt und `updated_at` wird beim Titel-Update explizit gesetzt, um Async-`MissingGreenlet` bei ORM-Feldzugriffen zu vermeiden
- Authentifizierung erweitert: neue Endpunkte `POST /api/auth/register`, `POST /api/auth/login` und `GET /api/auth/me` inklusive passwortbasiertem Login mit PBKDF2-Hashing
- Frontend-Login eingefuehrt: App startet mit Anmelde-/Registrierungsmaske und persistiert den angemeldeten Benutzer lokal
- Benutzerkontext im UI verdrahtet: Chat-/Settings-Aktionen verwenden die angemeldete `user_id`, Sidebar-Profil zeigt den aktuellen Benutzernamen
- Benutzerbereich erweitert: Abmelden-Button in der Sidebar entfernt die lokale Session und wechselt zur Anmeldemaske
- Chat-Rollenanzeige verbessert: Assistenten-Name wird aus Settings (`prompt.assistant_display_name`) geladen und im Chat angezeigt
- Chat-Menue erweitert: Sichtbarkeit pro Konversation (`private|internal|public`) im Kontextmenue speicherbar
- Konversations-Listing erweitert: `public` markierte Konversationen werden benutzeruebergreifend in der Chatliste angezeigt
- Multi-User-Chatdarstellung erweitert: Benutzernachrichten nutzen nun autorbezogene Labels (`author_username`) fuer korrekte Namensanzeige je Teilnehmer
- Multi-User-UX erweitert: benutzerbezogene Farbvarianten fuer Nachrichten-Labels ermoeglichen bessere visuelle Trennung von Teilnehmern
- KI-Teilnahmesteuerung eingefuehrt: Checkbox `KI redet mit` pro Konversation mit Intent-Gating (bei deaktivierter Teilnahme antwortet KI nur bei direkter Ansprache)
- Composer-Werkzeugleiste aktiviert: `📎` und `🖼` oeffnen Dateiauswahl und fuegen Dateihinweise in den Entwurf ein; `🔧` oeffnet das Kontext-/Werkzeugpanel
- Chat-Bedienhilfe verbessert: Hover-Tooltips (`title`) fuer Composer- und Sendeaktionen zeigen jetzt die jeweilige Funktion direkt an
- Startup-Verhalten verbessert: zuletzt als aktiv markiertes Modell wird beim Serverstart automatisch zu laden versucht
- Intent-Marker-Konfiguration erweitert: KI-Trigger werden aus Settings geladen (Default pro Benutzer, optional pro Konversation ueberschreibbar)
- Alembic-Einfuehrung abgeschlossen: `alembic.ini`, Migrations-`env.py` und `script.py.mako` produktiv befuellt sowie Initialmigration `initial_schema` erzeugt
- Migrationszyklus verifiziert: Upgrade auf `head`, Downgrade auf `base` und erneutes Upgrade erfolgreich gegen Testdatenbank ausgefuehrt
- Safe-Migrationspfad fuer bestehende lokale Instanzen umgesetzt: `scripts/migrate_database.py` mit Stamp-Strategie fuer unversionierte Legacy-Schemata, Backup-Erstellung und Restore-Fallback bei Fehlern
- SSE-Streaming produktiv angeschlossen: Frontend verarbeitet echte `text/event-stream` Token-Events, schreibt Live-Token in die UI und nutzt `AbortController` fuer Stop
- Serverseitiger Streaming-Abbruch bis ins Modell-Backend durchgereicht: Client-Disconnect/Stop setzt Cancel-Signal, Backend beendet laufende Token-Iteration kontrolliert
- Rename-Endpoint gehaertet: `PATCH /api/conversations/{id}` validiert leere/null Titel explizit und liefert `400` statt intermittierendem `500`
- Idempotency-Key fuer Nachrichtenversand umgesetzt: Backend erkennt doppelte Requests und liefert bestehende Antwort statt erneuter Generierung
- Retry-Flow im Frontend idempotent gemacht: pro Nachricht wird ein stabiler Key erzeugt und bei `Retry` wiederverwendet
- Modellwechsel gehaertet: Aktivierung prueft den Backend-Healthcheck und fuehrt bei Fehlschlag automatisch ein Rollback auf das zuvor aktive Modell aus
- Tokenbudget pro Konversation eingefuehrt: Chat-Service liest `chat.context_limit_tokens` plus optionale Ueberschreibung je Konversation aus `chat.conversation_context_limit_map`
- Kontextkuerzung verfeinert: Prompt-Budget beruecksichtigt feste Prompt-Teile, Antwortreserve und konfigurierbare Sicherheitsmarge (`chat.context_safety_margin_tokens`) vor History-Trim
- Netzwerkreichweite fuer localhost/Intranet/Internet verbessert: konfigurierbare CORS-Origin-Liste im Backend sowie host-/proxy-konfigurierbarer Vite-Server mit optionaler `VITE_API_BASE_URL`
- Chat-Reaktionsprobleme fuer nicht-lokale Origins adressiert: CORS-Default erweitert, damit Requests auch bei Intranet/Domain-Zugriff nicht blockiert werden
- Nutzerpraesenz ergaenzt: neuer Endpoint `GET /api/auth/users` liefert Online/Offline-Status (auf Basis letzter Konversationsaktivitaet), rechte Sidebar zeigt Status inkl. "Du"-Markierung
- 404-Logflut bei Nutzerpraesenz behoben: laufender Stack neu gestartet (Route aktiv) und Frontend-Polling mit 404-Capability-Fallback abgesichert
- API-Capabilities-Endpunkt umgesetzt: `GET /api/meta/capabilities` liefert stabil erkennbare Feature-Flags (u. a. `auth.users_presence`)
- Frontend auf Capabilities-Gating umgestellt: Nutzerpraesenz-Polling startet nur noch bei gesetzter Capability statt 404-Heuristik
- Presence-500 behoben: Datumsvergleich in `list_with_presence` fuer naive und timezone-aware Zeitstempel robust gemacht (SQLite-kompatibel)
- Auth-Session-Handling verbessert: wenn gespeicherte `user_id` nicht mehr existiert (`/api/auth/me` 404), wird die lokale Session geloescht und ein klarer Login-Hinweis angezeigt
- Team-Chat-Sichtbarkeit korrigiert: Konversationen ohne explizites Mapping gelten jetzt als `internal` (statt effektiv privat) und sind fuer angemeldete Nutzer sichtbar
- Presence-Status verbessert: erfolgreicher Login aktualisiert `updated_at`; Online/Offline nutzt nun die juengste Aktivitaet aus Login und Chat-Aktualisierung
- Presence-Fehlanzeige korrigiert: neu angelegte Benutzer werden nicht mehr sofort als online markiert; Online-Status beruecksichtigt `updated_at` nur wenn dieser Zeitstempel nach `created_at` liegt
- Presence-Logik auf explizite Login-Events umgestellt: `GET /api/auth/users` markiert Nutzer nur dann als online, wenn ein aktuelles `user.login`-Event vorliegt (keine Anzeige mehr durch allgemeine Profil-/Admin-Updates)
- Admin-Benutzerverwaltung erweitert: neuer Endpoint `POST /api/auth/admin/users` erlaubt das Anlegen von Benutzerkonten durch Admins (inkl. optionalem Admin-Flag)
- Einstellungen erweitert: Bereich `Benutzer` enthaelt jetzt eine Admin-Maske zum Anlegen neuer Benutzerkonten direkt im Frontend
- Nutzerstatus-Sidebar erweitert: Admins haben pro Benutzer einen `Einstellungen`-Button mit Inline-Editor (Name, Aktiv-Status, Adminrechte, optionales Passwort-Reset)
- Admin-Benutzerverwaltung erweitert: neuer Endpoint `PATCH /api/auth/admin/users/{target_user_id}` fuer serverseitige Benutzer-Aenderungen inkl. Username-Konfliktpruefung und optionalem Passwort-Update
- Praesenzliste erweitert: `is_active` wird im API-Response geliefert; inaktive Konten erscheinen als `Gesperrt` statt faelschlich als online/offline aktiv
- Sicherheitsregel ergaenzt: letzter aktiver Admin kann nicht deaktiviert oder von Adminrechten entfernt werden
- Authentifizierung gehaertet: Login/Register geben jetzt Bearer-Access-Token zurueck; Frontend persistiert Token lokal und nutzt ihn fuer authentifizierte API-Aufrufe
- Admin-Autorisierung auf Session/Token umgestellt: `POST /api/auth/admin/users` und `PATCH /api/auth/admin/users/{id}` pruefen jetzt den eingeloggten Bearer-User statt `admin_user_id` aus dem Payload
- Benutzer-Auditlog eingefuehrt: neue Tabelle `user_audit_logs` protokolliert Admin-Aktionen auf Benutzerkonten (`user.created`, `user.updated`) mit Akteur, Zielnutzer und Detaildaten
- Passwort-Kompatibilitaet verbessert: Login akzeptiert zusaetzlich Legacy-Passworthash-Formate (Plaintext/sha256 ohne Prefix) und migriert diese beim erfolgreichen Login automatisch auf PBKDF2
- Admin-Nutzeraktionen erweitert: neue Endpunkte `POST /api/auth/admin/users/{id}/kick` und `DELETE /api/auth/admin/users/{id}` fuer Rausschmeissen (offline) und Loeschen
- Admin-Sperrverwaltung erweitert: neuer Endpoint `POST /api/auth/admin/users/{id}/unlock` und Sidebar-Aktion `Entsperren` fuer gesperrte Konten
- Admin-Audit erweitert: Entsperren wird jetzt als `user.unlocked` protokolliert
- Loeschen als sichere Soft-Delete-Variante umgesetzt: Benutzer wird deaktiviert, Adminrechte entfernt, Passwort geloescht und als `__deleted__{id}` markiert (Datenkonsistenz fuer bestehende Konversationen bleibt erhalten)
- Nutzerliste bereinigt: soft-geloeschte Konten werden in `GET /api/auth/users` ausgefiltert
- Sidebar erweitert: im Reiter `Nutzerstatus` gibt es jetzt pro Nutzer die Admin-Aktionen `Rausschmeissen` und `Loeschen` (mit Bestaetigungsdialog)
- Admin-Aktionsleiste im Nutzerstatus auf Symbol-Buttons umgestellt (`Einstellungen`, `Rausschmeissen`, `Entsperren`, `Loeschen`) inklusive Hovertext (`title`) und `aria-label`
- Chat-Header-UX verbessert: Schalter `KI redet mit` ist jetzt auch in der Desktop-Ansicht konsistent sichtbar; bei Solo-Chat wird er sichtbar aber deaktiviert dargestellt
- Header-Layout robust gemacht: Chat-Meta-Bereich erlaubt Umbruch, damit Controls bei engerem Desktop-Layout nicht abgeschnitten werden
- Nachrichten-Endpoint korrigiert: doppelter `generate_response`-Aufruf in `POST /api/messages` entfernt, sodass pro Request nur eine KI-Antwort erzeugt wird
- Sichtbarkeitspruefung vereinheitlicht: Nachrichten-Lesen/Schreiben und Chat-Service nutzen jetzt dieselbe konversationsbezogene Zugriffskontrolle (inkl. `conversation_not_found`-Mapping auf `404`)
- Presence-Heartbeat eingefuehrt: neuer Endpoint `POST /api/auth/heartbeat`, Frontend sendet periodischen Heartbeat, Presence-Auswertung beruecksichtigt `user.login` + `user.heartbeat`
- Frontend-Message-Laden benutzerbezogen gehaertet: `GET /api/messages` wird mit `user_id` des aktuell angemeldeten Nutzers aufgerufen
- Teamchat-Versand korrigiert: bei deaktivierter KI-Teilnahme werden menschliche Nachrichten jetzt ueber `POST /api/messages/user-only` gespeichert statt vom Frontend blockiert
- Teamchat ohne KI-Antwort ermoeglicht: Nutzer-zu-Nutzer-Gespraeche bleiben moeglich; KI antwortet nur noch bei explizitem Intent-Trigger
- Zugangsdokumentation in `docs/zugaenge.md` ergaenzt (Benutzerkonten ohne Klartext-Passwoerter, entsprechend Sicherheitsrichtlinie)
- Chat-Liveaktualisierung ergaenzt: aktiver Chat wird im Frontend zyklisch aktualisiert, damit neue Nachrichten anderer Nutzer ohne manuelles Reload sichtbar werden
- Typstabilitaet in `app/chat/service.py` verbessert: unnoetige `None`-Vergleiche entfernt und Sichtbarkeits-Mapping explizit typisiert (Pylance-Diagnosen bereinigt)
- Einheitliches API-Fehlerformat serverweit aktiviert: HTTP-, Validierungs- und unerwartete Fehler liefern nun konsistent `error.code`, `error.message`, `error.retry` und `error.details`
- Konversations-Endpunkte auf strukturierte Fehlerdetails gehaertet: Rename/Delete liefern maschinenlesbare Fehlercodes und Kontextdaten (`conversation_id`, `user_id`)
- Frontend-API-Client auf neues Fehlerformat erweitert (abwaertskompatibel zu legacy `detail`-Antworten)
- SSE-Fehler im Streaming vereinheitlicht: `event:error` liefert nun denselben Error-Envelope (`error.code`, `error.message`, `error.retry`, `error.details`) wie REST-Fehler
- Streaming-Fehleranzeige im Frontend erweitert: Error-Codes aus dem SSE-Envelope werden direkt im UI angezeigt (mit Legacy-`detail`-Fallback)
- Browser-Form-Warnung behoben: Login-/Admin-Passwortfelder mit korrekten `autocomplete`-Attributen versehen
- Polling im Frontend entlastet: Chat- und Presence-Refresh pausieren bei unsichtbarem Tab, wodurch wiederholte Dev-Konsole-`Fetch finished loading`-Eintraege reduziert werden
- Modellpfadvalidierung gehaertet: `model.base_directories` wird jetzt normalisiert und gegen Path-Traversal geprueft; Modellpfade muessen innerhalb erlaubter Basisverzeichnisse liegen
- Modellaktivierung und Startup-Restore abgesichert: unzulaessige oder ausgelagerte Modellpfade werden geblockt (`model.invalid_path` / `invalid_model_path`)
- Harte Polling-Deduplikation umgesetzt: Message- und Presence-Polling mit Single-Scheduler + In-Flight-Guard; Heartbeat-Aufrufe im API-Client zusaetzlich gegen parallele Requests dedupliziert
- Integrationstests erweitert: Modellaktivierung ausserhalb erlaubter Basisverzeichnisse und Modellwechsel-Rollback bei Ladefehlern sind jetzt als Regressionstests abgedeckt
- Streaming-Fehlerpfad verifiziert: `event:error` im Chat-Stream wird auf den standardisierten Error-Envelope (`error.code`, `error.message`, `error.retry`, `error.details`) getestet
