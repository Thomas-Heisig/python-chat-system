# TODO

## Kritisch

- `.venv-chat` Migration abschliessen: Python 3.12 installieren, Umgebung mit `scripts/setup_venv_chat.ps1` erstellen, dann Chat/Transformers/GGUF/ONNX/SmolVLM2/PEFT-Smoke durchtesten.
- `.venv-chat` GPU-Upgrade abschliessen: CUDA-Torch-Wheels vollstaendig installieren und danach CUDA-Verfuegbarkeit (`torch.cuda.is_available()`) sowie Vision-/Training-Smoketests erneut pruefen.

- Einstellungen sollen als Popup in der Mitte ausreichend groß angezeigt werden.
- Projekt- und Konversationsflows end-to-end absichern: API- und UI-Tests fuer Projekt erstellen/umbenennen/loeschen/auswaehlen sowie Chat-Projekt-Zuordnung ergaenzen.
- Dataset-Management als erster Lieferblock umsetzen: Import, Validierung, Versionierung, Explorer-API (Editieren/Pruefen) und reproduzierbare Metadaten.
- Training-API naechster Ausbauschritt: Worker-Lifecycle um Validierung/Tokenisierung/Saving/Registering erweitern und feingranulare Statusuebergaenge verhaerten.
- Frontend Training-Bereich vertiefen: Job-Detailansicht um Live-Logs/Progress erweitern und an den erweiterten Worker-Lifecycle anbinden.
- Nach zentraler Base-Model-Integration: Fallback-/Fehlermeldungen fuer nicht registrierte oder entfernte Trainings-Basismodelle im UI klarer fuehren.
- PEFT-Smoke-Run als wiederholbaren Standardlauf verankern (einheitliches Test-Dataset, feste Hyperparameter, reproduzierbare Erfolgs-/Fehlerkriterien).
- Start-/Ops-Dokumentation auf `.venv-training` ausrichten (inkl. Checks fuer Interpreter-Pfad, CUDA-Status und Pflichtpakete vor Jobstart).
- Model-Manager-Metadaten um Trainingsfaehigkeit erweitern (`supports_peft_training`, Modellformat) und im Training-Tab auswerten.
- Nach Runtime-Checks und taskbasierter Loader-Aufloesung: fuer jede Loader-ID den produktiven Inferenzpfad (Load/Run/Health) inklusive API- und Integrationsabdeckung vervollstaendigen.
- Prompt-Diagnosemodus haerten: sensible Felder standardmaessig redigieren, nur lokal aktivieren und strukturierten Export fuer reproduzierbare Fehleranalysen anbieten.
- Custom-Loader-Runtime haerten: standardisierte Plugin-Validierung (Pflichtfunktionen, klare Fehlercodes, optional Signaturpruefung) fuer `custom_pytorch` erweitern.
- Custom-Scan-Wartung optional nachziehen: verbleibende historische Sonderfaelle ausserhalb regulärer Scan-Laeufe analysieren und bei Bedarf mit einem expliziten Maintenance-Command bereinigen.
- Modellscan fuer Custom-Architekturen erweitern: robuste Entrypoint-Erkennung und optional signierte Trust-Marker statt rein dateibasierter Heuristik.
- Diagnose-API weiter haerten: `GET /api/chat/diagnostics/prompts` um Rollen-/Quellenfilter, Paging und redigierten Export fuer lokale Debug-Sessions erweitern.
- Retrieval-Qualitaet vertiefen: aktuelle scorebasierte Heuristik auf inhaltsbasierte Chunk-Retrieval-Pipeline mit nachvollziehbarer Selektion (`rohscore`, `normalisiert`, `selected`) erweitern.
- Trainer-Kompatibilitaetsmatrix erweitern: serverseitige Regeln fuer weitere Trainer und harte Hardware-/Format-Constraints einbauen.
- Training fuer benutzerdefinierte Architekturen ergaenzen: separaten Supra-A2A-Trainer (nicht-PEFT) mit klaren Preflight-Checks und Artefaktstrategie einfuehren.
- Multimodalen Chat-Pfad fuer Audio abschliessen: nach umgesetztetem Bildtransport nun Audio-Payloads bis zum Backend transportieren, damit `audio_text_generation`/`any_to_any` nicht auf Text-only degradiert.
- Ultravox-Loader als eigener Runtime-Pfad ergaenzen: `ultravox_audio_text` mit Trust-Gating (`trust_remote_code` nur nach Freigabe), Audio-Preprocessing (Samplingrate/Normalisierung) und klaren Fehlermeldungen implementieren.
- Vision-Antwortaufbereitung verbessern: bei `vision_text_generation` Echo/Prompt-Artefakte im Chat-Output entfernen (nur eigentliche Bildbeschreibung ausgeben) und mit API-Test absichern.
- GGUF-Runtime auf Windows/Python 3.13 stabilisieren: `llama-cpp-python`-Installationspfad fuer fehlende Wheels/Long-Path-Probleme dokumentieren und optionalen Fallback-Interpreter (z. B. 3.12) pruefen.
- Markdown-Rendering im Chat per UI-Regressionstest absichern (Ueberschriften/Listen/Absaetze sichtbar formatiert statt Rohtext).
- Trainings-Dataset-Import weiter haerten: Manifest/README beim Upload oder URL-Import optional mit uebernehmen, Checksummen validieren und JSONL-Format schon vor der Registrierung explizit vorpruefen.
- Training-Monitoring verfeinern: UI um sichtbaren Heartbeat/Phase-fuer-Schritt-0, erste Logzeile und getrennte Anzeige von Trainings-/Validierungsbeispielanzahl erweitern.
- Trainings-Artefakte weiter integrieren: abgeschlossene Adapter aus dem Artifact-Check direkt registrierbar machen und eine kurze Inferenz mit/ohne Adapter ueber denselben UI-Flow anbieten.
- Modell-Relevanzworkflow ergaenzen: `favorite`/`irrelevant` als persistente Nutzermarkierungen einfuehren und Sortierung im UI darauf ausrichten.
- Relevanzworkflow erweitern: Mehrfachaktionen und Filter (nur Favoriten / ohne Irrelevante) im Modellmanager-UI ergaenzen.
- Lifecycle-Konsistenz abschliessen: granularen Trainingsstatus als API-Standard festlegen und `running`/`phase` eindeutig trennen.
- Frontend-Workspace-Caches weiter pruefen: benutzerbezogene Query-Keys konsistent fuer weitere user-abhaengige Listen (z. B. Termine/Quellen) verankern, um Cross-User-Leakage zu vermeiden.
- Prompt-Stabilitaet finalisieren: modell-spezifischen Prompt-Editor gegen race conditions beim Modellwechsel absichern (keine visuelle Ruecksetzung waehrend laufender Save-Operationen).
- Quellen-Upload vervollstaendigen: nach `sources/upload` die inhaltliche Verarbeitung (Parsing/Chunking/Indexierung) fuer `pdf/md/txt/docx` aktivieren, damit Retrieval auf echten Dateiinhalten statt nur Dateimetadaten arbeitet.
- Halluzinations-Regression einbauen: `docs/venedig-pruefprompt.md` in die Eval-Pipeline integrieren und Antworten bei harten Fehlern (UNO/Friedens-Frame) automatisch als `fail` markieren.
- Allgemein-Settings weiterfuehren: verbleibende Oberflaechenbereiche vollstaendig auf Sprache/Zeitzone umstellen und bisherige DE/EN-Inline-Texte durch ein einheitliches i18n-Mapping ersetzen.
- Universelles Dataset-MVP vertiefen: fehlende Formate (Webseiten-Import, Unternehmens-Plugins) als eigenstaendige Parsermodule ergaenzen und in Auto-Erkennung einbinden.
- KANONISCHES Datensatzschema erweitern: Versionshistorie, Hashes, Split-Informationen, Qualitaetsscore und Evaluationsfelder API-seitig persistieren statt nur als Datei-Artefakt.
- Trainings-UI ausbauen: Import-Assistent mit Format-Erkennung, Vorschau, Validierungsbericht und Fehlerliste fuer universelle Datensaetze bereitstellen.

## Hoch

- Chat-Feedback und Regeneration einzelner Antworten einfuehren.
- Nach initialem PEFT-Trainerpfad: produktiven `UnslothTrainer` hinter der vorhandenen Abstraktion anbinden.
- PEFT-Hardening: Trainings-Evaluation auf echten Holdout-Split und task-spezifische Metriken (`agent_tool_router`) erweitern.
- Dataset-Pipeline vertiefen: dedizierte Train/Validation-Split-Policies, Dateiquellen aus Workspace und detailliertere Secret-Reports (ohne Secret-Leak im Log) ergaenzen.
- Job-System weiter haerten: Recovery nach Prozessabbruch, Lease/Heartbeat, verwaiste Jobs, Retry-Limits und konkurrierende Worker absichern.
- Evaluations- und Benchmark-Gates implementieren: kein automatisches Aktivieren ohne Evaluation, Healthcheck und Benchmark.
- Modellregistrierung als separaten Schritt nach bestandenem Gate einbauen (nur dann im Modellmanager aktivierbar).
- Base-Model-Lifecycle verfeinern: Auto-Refresh der Trainings-Modelldropdowns nach Modellscan/-registrierung und klare Kennzeichnung von inaktiven Modellen.
- Experiment-Tracking und Run-Historie persistieren (Hyperparameter, Seed, Commit, CUDA, Dataset/Base-Model-Version, Ergebnisdaten).
- Dataset-Exporter erweitern: Quellen aus Chats, Bibliothek, Dokumenten, Bewertungen und Projekten in trainierbare Formate ueberfuehren.
- Prompt-Template-Konvertierung fuer Exportpfad einbauen (ChatML, Alpaca, ShareGPT, OpenAI, Llama, Qwen, Gemma).
- Frontend fuer Dataset-Explorer und Trainingslauf-Ansicht planen und umsetzen (Status, Logs, Metriken, Vergleich von Runs).
- GPU-Scheduler priorisieren: Chat vor Embedding vor Training, damit Trainingsjobs den Live-Chat nicht blockieren.
- Konversations-Generierungsprofile im Frontend vervollstaendigen: Versionshistorie und Versionsauswahl sichtbar in der Chat-UI integrieren.
- Kontextnutzung serverseitig weiter absichern: Retrieval-Auswahl um echten Inhaltskontext (Chunk-Text statt reiner Dokumentmetadaten) erweitern und Token-Breakdown entsprechend praezisieren.
- Generierungssteuerung weiter ausbauen: modell-spezifische Parameterprofile optional direkt im Chat (Quick-Switch fuer `praezise`/`kreativ`) umschaltbar machen.
- Sichtbarkeitsmodell absichern: internal an Team-Mitgliedschaft koppeln statt globaler Anzeige.
- Multi-User-Chat-Endpunkte per API-Tests absichern: shared/internal lesbar und schreibbar, private fuer Nicht-Besitzer konsequent `404`.
- Conversation-API-Rechte konsolidieren: fuer nicht-eigene, aber sichtbare Chats bei mutierenden Aktionen (`project`, `delete`, `rename`) konsistente Permission-Fehler definieren und testbar machen.
- Health- und Laufzeitdaten im Footer vervollstaendigen (API, DB, Modell, Queue, Index).
- Strukturiertes Logging mit Request-, Conversation- und Trace-ID durchgaengig einfuehren.
- Frontend Error Boundary integrieren.
- React Router mit Deep Links fuer Chats, Projekte, Dokumente und Einstellungen umsetzen.
- Einstellungen exportieren, importieren und zuruecksetzen.
- Einstellungsoberflaeche fuer assistant_display_name in den Benutzer-Settings sichtbar machen.
- Multi-User-Labeling konsolidieren: author_username fuer historische Nachrichten ohne Metadata robust nachziehen.
- KI-Teilnahmemodus erweitern: konfigurierbare Intent-Marker je Benutzer und Team bereitstellen.
- KI-Teilnahmeschalter UX weiter haerten: deaktivierten Zustand mit klarer Begruendung im UI anzeigen (Tooltip/Hinweistext), wenn noch kein Teamchat aktiv ist.
- Teamchat-Regressionstests ergaenzen: bei deaktivierter KI-Teilnahme muss `POST /api/messages/user-only` Nachrichten speichern und in allen Clients sichtbar machen.
- Regressionstests fuer Settings-Fallback ergaenzen: `GET /api/settings/*/model_<id>_*` darf ohne expliziten Override keinen `400` mehr liefern.
- Live-Refresh absichern: automatisches Nachladen im aktiven Chat gegen Duplikate/Race-Conditions mit API- und UI-Tests validieren.
- Typdiagnostik absichern: Pylance-Warnungen in Kernpfaden (`app/chat/service.py`, Repositories, API-Routen) als Regression-Check aufnehmen.
- Composer-Anhaenge ausbauen: echte Upload-API fuer Dateien und Bilder statt Draft-Platzhalter integrieren.
- Sichere Zugangsverwaltung fuer lokale Entwicklung dokumentieren (nicht versionierte Secret-Datei / Passwortmanager statt Klartext in `docs`).
- Public-Release-Checkliste ergaenzen: vor jedem oeffentlichen Push automatisierten Secret-Scan und `.gitignore`-Validierung ausfuehren.
- GitHub-Automation nachziehen: Label-Set vereinheitlichen und CI-Workflows schrittweise auf stabile, reproduzierbare Test-Segmente (Backend/Frontend getrennt) verfeinern.
- Security-Wartung fest verankern: nach jedem Frontend-Dependency-Update `npm audit` und `npm run test:run` als Pflichtcheck ausfuehren.
- Nach React-19/TypeScript-7-Migration gezielte UI- und Typecheck-Regression erweitern (inkl. strict TS-Checks im Frontend-CI-Job).
- Security-Regressionstests ergaenzen: SSRF-Blocklisten (private IPs/localhost), Error-Redaction und sichere HTML-Extraktion im Dataset-Import automatisiert testen.
- Workflow-Hygiene-Check ergaenzen: Badge-Links, Workflow-Dateien und Repo-Actions-Status muessen konsistent bleiben.
- Actions-Monitoring erweitern: bei Workflow-Fehlern automatischen Check einbauen, ob Berechtigungen/Trigger zur Badge-Anzeige passen (insb. Release Drafter, Dependency Review, CodeQL).
- README-Workflow-Badges periodisch abgleichen: neue oder umbenannte Workflows (`.github/workflows/*.yml`) sofort in der Badge-Zeile nachziehen.
- Issue-Templates mit SUPPORT.md abgleichen: Felder fuer Modell-/GPU-/Training-Probleme, Log-Redaktion und Anfrage-Typ (`bug`/`question`/`feature`) ergaenzen.
- Maintainer-Preflight definieren: vor jedem Release Lizenzdatei, Security-Pfade, CODEOWNERS, Issue-Templates und Git-Standards (`.editorconfig`, `.gitattributes`, `.gitignore`) automatisiert pruefen.
- Rebranding-Checkliste einfuehren: bei Namenswechseln README, UI-Titel, API-Meta, User-Agent, CONTRIBUTING und Branding-Assets zwingend gemeinsam pruefen.
- Branding-Regressionstest ergaenzen: visuell pruefen, dass Logo in Login/Header/Sidebar sowie Favicon auf Desktop und Mobil korrekt dargestellt wird.
- Security-Tests erweitern: URL-Allowlist/Port-Blockade fuer Trainings-Import und redigierte Streaming-Fehlerantworten als feste Regressionstests aufnehmen.
- Admin-Aenderungen nachvollziehbar machen: Audit-Log (Akteur, Zielnutzer, Feld, Zeit) fuer Benutzer-Updates einfuehren.
- Audit-Log im UI nutzbar machen: Admin-Ansicht fuer Benutzer-Aenderungshistorie (Filter nach Nutzer/Aktion/Zeit) ergaenzen.
- Reaktivierung fuer Soft-Delete-Nutzer ergaenzen: geloeschte Konten optional wiederherstellbar machen (neuer Benutzername + Passwort setzen).
- Admin-Audit erweitern: `user.kicked`, `user.unlocked` und `user.deleted` in eigener Admin-Historienansicht anzeigen.
- Token-Session-Lifecycle ausbauen: Refresh/Expiry-Handling und explizites Logout-Invalidieren umsetzen.

## Mittel

- Dokumentversionierung und Neuindizierung bei Embedding- oder Parser-Aenderungen einbauen.
- Kaskadenloeschung fuer KnowledgeDocument, Chunks und Embeddings absichern und testen.
- Pytest-Konfiguration harmonisieren: `asyncio_mode`-Warnung entfernen (Plugin sauber installieren oder Config ohne Plugin kompatibel machen).
- SQLAlchemy-Session-/Connection-Lifecycle in Integrationstests haerten, damit keine Pool-GC-Warnungen mehr auftreten.
- Virtuelle Nachrichtenliste fuer sehr lange Chats einfuehren.
- Reverse-Proxy-Beispiel fuer Internetbetrieb (TLS, Host-Weitergabe, CORS-Origins) als lauffaehige Deploy-Vorlage dokumentieren.
- Nutzerpraesenz weiterentwickeln: Heartbeat-Polling durch push-basierte Presence-Events (WebSocket/SSE) ersetzen.
- Retry-Strategie differenzieren: GET mit begrenzten Retries, POST/PUT/DELETE nur mit Idempotency oder Safe-Markierung.
- Auth-Lifecycle haerten: bei DB-Reset oder Nutzerloeschung gespeicherte Sessions sauber invalidieren und Re-Login-Flow ohne 401/404-Loop erzwingen.
- OOM-Wiederherstellung als kontrollierte Sequenz implementieren: Anfrage abbrechen, Zustand pruefen, entladen, Speicher freigeben, neu laden.
- Seed-Service fuer Standardwerte und Standard-Prompts idempotent beim Start ausfuehren.
- Backup- und Restore-Skripte fuer SQLite dokumentiert bereitstellen.
- Startwiederherstellung fuer Modelle haerten: Retry-/Fallback-Strategie und Nutzerhinweis bei fehlgeschlagenem Autoload.
- ONNX-Runtime-Betriebspfad absichern: fuer fehlendes `onnxruntime` klare Installationshinweise im UI und im Diagnose-Panel anzeigen sowie Loader-Fallbacks explizit testen.
- Hilfetexte im Chat ausbauen: nach Admin-Symbolbuttons konsistente Hover-Hinweise fuer verbleibende Header-/Sidebar-Buttons ausserhalb des Composers ergaenzen.

## Niedrig

- Modell-Cache fuer mehrere gleichzeitig geladene Modelle nur optional und nur bei ausreichend RAM/VRAM freischalten.
- Erweiterte Accessibility-Checks mit axe automatisieren.
- Performance-Messung fuer TTFT und Tokens pro Sekunde standardisieren.
- CI-Gates fuer Ruff, Typpruefung, Pytest, Frontend-Build und Markdown-Lint vervollstaendigen.

## Arbeitsweise

- Changelog enthaelt nur umgesetzte und verifizierte Punkte.
- Roadmap enthaelt nur Ausbaustufen und Ziele.
- TODO enthaelt nur konkrete naechste Arbeitspakete.
- Spaetere oder optionale Themen werden in Backlog gepflegt.
