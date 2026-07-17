# TODO

## Kritisch

- Nach unit-seitig abgesicherter Execute-Contract-Validierung: API-/E2E-Regressionen fuer `/api/plugins/execute` mit denselben Contract-Fehlercodes (`plugin_contract_invalid_input`/`plugin_contract_invalid_output`) ergaenzen.
- Skip-Semantik vereinheitlichen: bei kanalbedingtem Ueberspringen pluginuebergreifend konsistente Antwortstruktur (`status=skipped`, `reason=unsupported_channel`) in Runtime- und API-Tests absichern.

- Legacy-Quellenbereinigung vorbereiten: unzugeordnete Wissensdokumente (`project_id = null`) analysieren und geordnet auf Mandant/Bereich/Projekt-Ebenen mappen, um fachfremde Rueckfaelle zu vermeiden.

- Secret-Scan fuer Konfigurationsbeispiele ergaenzen: `.env.example`, Doku-Snippets und Setup-Dateien automatisiert auf echte API-Keys oder Tokens pruefen.
- Nach Secret-Bereinigung in `.env.example`: den betroffenen externen API-Schluessel rotieren und pruefen, ob derselbe Wert in Shell-History, lokalen Notizen oder CI-Variablen erneut auftaucht.
- Integrations-Schluessel weiter haerten: Sichtbarkeit/Masksierung im UI verbessern und Berechtigungspfad fuer besonders sensible Einstellungen einschaerfen.
- Nach Erweiterung der Integrationen auf viele API-Keys: pro Feld klar markieren, welche Backends/Plugins den jeweiligen Key bereits nutzen und welche nur vorbereitet sind.
- Integrationen-UX erweitern: optionalen "Verbindung testen"-Button pro Provider (insb. Wetter/Web-APIs) mit klarer Erfolgs-/Fehlerdiagnose einfuehren.
- Nach Einfuehrung von `Key testen` pro Feld: Sammelaktion `Alle Keys testen` fuer die sechs Kernprovider umsetzen und als Re-Validation-Flow im Integrationen-Bereich sichtbar machen.
- Nach ausgelieferter Sammelaktion `Alle Keys testen`: Ergebnisliste um Laufmetadaten (Zeitpunkt, Dauer) und optionalen `Erneut testen`-Shortcut pro fehlgeschlagenem Key erweitern.
- Re-Validation-UX praezisieren: fuer leere Keys explizit `uebersprungen` anzeigen (ohne Fehlerstatus), damit unvollstaendige Provider-Sets nachvollziehbar bleiben.
- Nach rotem Fehler-Highlight bei fehlgeschlagenem Provider-Test: Erfolgs-/Fehlerstatus je Key serverseitig persistieren und beim erneuten Oeffnen der Einstellungen wiederherstellen.
- Integrationen-UX nach CSS-Reparatur absichern: visuellen Regressionstest fuer kompakte Target-Buttons (`↗`) in allen Integrationsgruppen und Themes ergaenzen.
- Nach Einfuehrung der Integrationen-Tabs/Klappgruppen: aktiven Tab und Klappzustand pro Benutzer persistent speichern.
- Runtime-Anbindung erweitern: neue Keys (`azure_openai`, `bedrock`, `stability`, `unstructured`, `pinecone`, `exa`, `whatsapp`, `virustotal` etc.) schrittweise in konkrete Plugins/Tools verdrahten.
- Integrationen-Settings: Secret-Maskierung und serverseitige Secret-Kennzeichnung (`is_secret`) beim Speichern konsequent durchziehen.
- Integrationen-Settings: neue `include_secret=true`-Nutzung auf den benoetigten Frontend-Pfad begrenzen und fuer allgemeine Settings-Views Maskierung standardmaessig erzwingen.
- Integrationen-Settings: Response-Schema von Weather/Websearch vereinheitlichen (`provider`, `success`, `error`) fuer konsistente E2E-Auswertung.
- `custom_provider_keys` operationalisieren: einheitliches Schema und Discovery-Konvention fuer dynamische Provider im Tool-Runner dokumentieren und testen.
- Nach verdrahtetem `weather`-/`websearch`-Pfad: Provider-spezifische Integrationstests fuer Exa, Brave, Bing, OpenWeather, WeatherAPI und Tomorrow.io mit echten Mock/Contract-Faellen ergaenzen.
- Plugin-Settings-Harmonisierung: verbleibende API-Plugins auf `set_settings`/`integrations`-Injektion standardisieren, damit DB-Keys systemweit konsistent greifen.
- OpenAI-Flow absichern: API- und UI-Regression fuer Integrations-Key -> Modellscan -> Aktivierung -> Kurzantwort ergaenzen sowie Hinweistext fuer `.env.example` als Nicht-Runtime-Datei sichtbar machen.
- Modellmanager-Persistenz optional serverseitig machen: aktuelle Browser-Persistenz spaeter in echte Benutzer-Settings ueberfuehren, falls dieselben Praeferenzen geraeteuebergreifend gelten sollen.
- Neustart-Flow absichern: API- und UI-Regressionstests fuer `POST /api/workspace/reset-clean-start` inkl. FK-Detach (Termine, Wissensdokumente, Trainings-Datasets) und leerem Chat-/Projektzustand nach Ausfuehrung ergaenzen.
- Globalen Neustart regressionssicher machen: automatisierte API-Tests fuer Auth-Faelle (`401` ohne Token, `403` fuer Nicht-Admin, `200` fuer Admin) ergaenzen.
- Neustart-UX verfeinern: optionalen zweiten Bestaetigungsschritt ("LOESCHEN" eintippen) fuer produktive Umgebungen anbieten.

- Ollama-Flow end-to-end absichern: API- und UI-Regression fuer Scan -> Auswahl -> Aktivierung eines `Ollama Local`- und eines `Ollama Cloud`-Modells ergaenzen.
- Ollama-UX vertiefen: Download-/Pull-Status fuer `Ollama Cloud` beim Aktivieren sichtbar machen und klare Fehlermeldungen bei nicht erreichbarem lokalen Daemon anzeigen.
- Ollama-Pull robust machen: optionalen Abbruch-/Retry-Flow und echten Fortschrittstest fuer ein noch nicht lokal installiertes Cloud-Modell automatisiert absichern.
- Ollama-Fortschritt weiter verfeinern: fuer grosse Cloud-Modelle den Live-Fortschritt mit laenger laufendem End-to-End-Test absichern und optional ETA/Byte-Infos anzeigen.
- Modellfilter persistieren: Suche/Familie/Tools/Thinking/Vision pro Benutzer merken und beim Oeffnen des Modellmanagers wiederherstellen.

- Plugin-Loop sichtbar machen: im Chat eine kompakte Tool-Statusanzeige und optional einen Debug-Drawer fuer `plugin_call` -> `plugin_response` integrieren.
- Nach gruenen Runtime-Tests fuer `BusinessLetterPlugin.execute()`: API-/E2E-Regressionstests fuer den Versandpfad (`/api/plugins/execute` und Chat-Orchestrierung) mit denselben sechs Kernfaellen ergaenzen.
- `business_letter`-Versandpfad finalisieren: Delivery-Objekt an echten Mail-/Queue-Adapter anbinden und Statusuebergaenge (`ready` -> `queued` -> `sent`/`failed`) serverseitig persistieren.
- `business_letter`-Adminprofil im Frontend erweitern: neue strukturierte Plugin-Settings (Rechtliches/Bank/Kommunikation/Fachhinweise) vollstaendig erfassbar machen.
- Live-Reasoning regressionssicher machen: Streaming mit `<think>`-Segmenten gegen Chunk-Grenzen testen, inklusive korrekter Trennung zwischen Denkblase und finaler Assistant-Nachricht.
- Plugin-Ausfuehrung absichern: Allowlist pro Benutzer/Team einfuehren und fuer `apiKeyRequired`-Plugins vor Execute einen konfigurierten Secret-Check erzwingen.
- Plugin-Settings-Hardening (Folgeschritt): Cross-Field-Validierung (z. B. kombinierte Pflichtregeln), Rechte-/Sichtbarkeitsregeln pro Feld und API-/UI-Regressionstests fuer plugin-spezifische Validierungsfehler ergaenzen.
- Speech-Endpoint end-to-end absichern: `POST /api/speech/synthesize` mit Payload-Varianten (`model_id`/`modelId`, optionale `null`-Felder) als API-Test gegen 422-Regressionen abdecken.
- Kokoro-DE-Regressionscheck ergaenzen: absichern, dass `GET /api/speech/models` fuer Kokoro dauerhaft `de`/`de-de` ausliefert und `de-at`/`de-ch`/`german` korrekt auf den `b`-Voice-Pfad gemappt werden.
- Kokoro-TTS-Smoke-Test ergaenzen: End-to-End-Check fuer lokales Modell ohne `model_type` in `config.json` (inkl. Sprach-/Stimmenfallback und WAV-Ausgabe) in den Regressionlauf aufnehmen.
- Startup-Preflight fuer Speech-Backends ergaenzen: fehlende optionale Runtime-Pakete (u. a. `kokoro`) beim Start als klare Warnung mit Installationshinweis ausgeben.
- Qwen3-TTS-Regressionsschutz halten: den validierten `qwen-tts`/`transformers`-Stack mit CPU-Smoke, Causal-Mask-Bridge und Dokumentation des optionalen Backend-Startmodus dauerhaft absichern.
- Voice-UX regressionssicher machen: fuer Kokoro/Qwen/Kitten API- und UI-Smokes aufnehmen (Sprecherliste sichtbar, ausgewaehlte Stimme wird wirklich genutzt).
- VAD-Regressionstest ergaenzen: `POST /api/speech/detect-activity` mit Beispielaudio (Speech/No-Speech) automatisiert pruefen.
- Plugin-Trainingsdatensatz einbinden: `C:/Users/T_hei/Downloads/Training/plugins_agent_training_v1.0.0.jsonl` als eigenes Evaluationsset aufnehmen und Basis-vs-Plugin-Verhaltensvergleich in den Report integrieren.
- Training-UI verbessern: bei `target_modules=auto` erkannte Zielmodule je Basismodell anzeigen und optional als explizite Override-Liste speicherbar machen.
- Preflight-UX erweitern: aus der angezeigten `target_modules`-Vorschau einen "als Override uebernehmen"-Button im Training-Dialog anbieten.

- A-F-Experimentlauf produktiv ausfuehren und dokumentieren: `scripts/run_training_experiment_plan.py` mit realen Dataset-/Modell-IDs laufen lassen, Job-IDs im Projekt festhalten und Best-Run fuer Folgezyklus markieren.
- Eval-Qualitaet absichern: fuer `evaluation-report.json` ein dediziertes, unangetastetes Routing-Testset mit stabilen JSON-Labels (`intent`, `agent`, `tools`) pflegen, damit Base-vs-Adapter-Delta belastbar wird.
- Geschaeftsbrief-Datensaetze vor Training verpflichtend linten: `scripts/lint_business_letter_dataset.py --input <dataset>` in den operativen Trainingsablauf aufnehmen und bei Verstoessen den Lauf stoppen.
- Dokumenttypen trennen und nachziehen: Trainingsbeispiele fuer `geschaeftsbrief`, `angebot`, `auftragsbestaetigung`, `rechnung` strikt separieren, damit das Modell keine Angebots-/Rechnungsinhalte in allgemeine Briefe halluciniert.
- Trainings-UI um Eval-Report-Viewer erweitern (statt nur Roh-`result` JSON), inklusive kompakter Anzeige von Konfusionsmatrix und Testset-Warnungen.

- `.venv-chat` Migration abschliessen: Python 3.12 installieren, Umgebung mit `scripts/setup_venv_chat.ps1` erstellen, dann Chat/Transformers/GGUF/ONNX/SmolVLM2/PEFT-Smoke durchtesten.
- `.venv-chat` GPU-Upgrade abschliessen: CUDA-Torch-Wheels vollstaendig installieren und danach CUDA-Verfuegbarkeit (`torch.cuda.is_available()`) sowie Vision-/Training-Smoketests erneut pruefen.

- Einstellungen sollen als Popup in der Mitte ausreichend groß angezeigt werden.
- Nach funktionaler Verdrahtung von `Chat`/`Wissen`/`Logs`: verbleibende Settings-Gruppen (`Darstellung`, `Datenbank`, `System`) mit echten Lade-/Speicherfluesse statt Platzhaltern umsetzen.
- Wartungsaktion nachziehen: fuer `POST /api/settings/chat/cleanup-obsolete` optionales Audit-Logging (wer/wann/wie viele Eintraege) ergaenzen.
- Security-Standard aus `docs/security/` operationalisieren: gemeinsame Admin-Guard-Dependency konsolidieren und Audit-Pflichtfelder (`actor_user_id`, `request_id`, `result`, `error_message`) fuer weitere Admin-Endpunkte vereinheitlichen.
- Security-README in den Workflow ziehen: bei jedem neuen Admin-Endpoint die Reihenfolge/Review-Checkpunkte aus `docs/security/README.md` verpflichtend anwenden.
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
- GGUF-Ordnerauswahl per Regressionstest absichern: bei mehreren `.gguf`-Dateien (inkl. `mmproj`/`projector`) muss fuer Textmodelle die richtige Gewichtsdatei aktiviert werden.
- Modellaktivierungs-Fehler im UI weiter schaerfen: bei `POST /api/models/{id}/activate` den vom Backend gelieferten Root-Cause-Text in der Konfliktmeldung klar anzeigen.
- Klartext-Default per Regression absichern: Chat-Antworten sollen ohne expliziten Wunsch keine Markdown-Ueberschriften, Listenmarker oder Emoji-Dekoration enthalten.
- Markdown-Rendering im Chat per UI-Regressionstest absichern (Ueberschriften/Listen/Absaetze sichtbar formatiert statt Rohtext).
- Trainings-Dataset-Import weiter haerten: Manifest/README beim Upload oder URL-Import optional mit uebernehmen, Checksummen validieren und JSONL-Format schon vor der Registrierung explizit vorpruefen.
- Nach Umstellung auf Rollen-UI inkl. ZIP-Bundle-Import: Trainingscenter um Rollenvollstaendigkeit und Plausibilitaetschecks erweitern (z. B. Manifest-Keys, optionaler `source`-Fallback, klare Inline-Hinweise bei fehlenden Rollen).
- Nach aktivierter Auto-Namensableitung in ZIP/URL/Upload-Workflows: optionalen Name-Praefix pro Projekt einfuehren und automatische Namenskollisionen sichtbar aufloesen.
- Bereichs-Toggles im Trainingscenter persistieren (Training/Dateien/Jobs), damit die gewaehlte Ansicht pro Nutzer erhalten bleibt.
- Archiv-Ansicht fuer Trainingscenter ergaenzen (umschaltbar), inklusive Filter nach `archived` und einfacher Wiederherstellung (Unarchive).
- Aufbewahrungsstrategie fuer Training definieren: automatische Loeschfristen fuer archivierte Jobs/Datasets und optionale Cleanup-Tasks.
- Nach Wikipedia-URL-Support: Inhaltsnormalisierung fuer lange HTML-Quellen verbessern (Chunking/Boilerplate-Filter fuer Navigationsanteile) und Import-Qualitaetsbericht im UI ausgeben.
- Job-Provenance vertiefen: neben Dateipfaden zusaetzlich Dateihashes/Record-Counts je verwendeter Trainingsdatei im Job-Resultat ausgeben.
- Trainings-Fortschrittsanzeige verfeinern: Queue-/Warmup-Phase klar markieren (z. B. "Warteschlange", "Initialisiere Trainer") bevor numerischer Progress vorhanden ist.
- Entwickler-Onboarding absichern: kurzen VS-Code-Check in Doku ergaenzen (Interpreter = `.venv-chat`, Pylance nutzt `pyrightconfig.json`) fuer reproduzierbare lokale Typanalyse.
- Trainings-Job-Updates langfristig von Polling auf push-basiertes Eventing (SSE/WebSocket) umstellen, um Live-Progress mit geringerer Last zu liefern.
- Low-VRAM-Profil im Training-Workflow anbieten (z. B. Batch=1, reduzierte Seq-Len, aktiviertes Checkpointing) und beim OOM direkt als Retry-Voreinstellung uebernehmen.
- CPU-Fallback-Run optimieren: optionales `offload_folder`/Disk-Offload fuer sehr grosse Modelle und klare UI-Kennzeichnung "CPU-Fallback aktiv" in Job-Details ergaenzen.
- Preflight-Fehler-UX ausbauen: bei `training.preflight_failed` die wichtigsten Blocker direkt als strukturierte Liste im Jobstart-Bereich hervorheben.
- Bei verschachtelten API-Konflikten (`error.details.detail`) optional rohe Diagnosedaten in ausklappbarem Debug-Panel anzeigen (nur Dev-Modus).
- Dataset-Lifecycle nachschaerfen: klare, explizite Uebergaenge `imported -> ready/validated` inkl. UI-Indikator "Preflight erforderlich" vor Jobstart.
- Jobstart-UX erweitern: bei Preflight-Konflikten den Grund mit konkretem Fix-Hinweis anzeigen und klar markieren, wann ein Job wirklich `queued` wurde.
- Vor Submit Dateiexistenz-Hinweis in der UI anzeigen (z. B. `dataset_file_not_found`), damit fehlende `source_path`-Referenzen sofort sichtbar werden.
- Dataset-Delete-Dialog um Hinweis erweitern, dass benutzte Trainingsdatasets nur archiviert oder nach Jobbereinigung geloescht werden koennen.
- Batch-Job-Status im UI sichtbar machen (z. B. Anzahl eingereihter Jobs und automatisch archivierte erfolgreiche Runs).
- Live-Backend nach einem Refactor/Hotfix neu starten, wenn Archivierungsantworten oder Delete-Guards aus einer lauffaehigen alten Instanz kommen.
- Training-Monitoring verfeinern: UI um sichtbaren Heartbeat/Phase-fuer-Schritt-0, erste Logzeile und getrennte Anzeige von Trainings-/Validierungsbeispielanzahl erweitern.
- Trainings-Artefakte weiter integrieren: abgeschlossene Adapter aus dem Artifact-Check direkt registrierbar machen und eine kurze Inferenz mit/ohne Adapter ueber denselben UI-Flow anbieten.
- Vergleichslauf-Auswertung ausbauen: fuer Run-Profile A/B/C einheitliche Run-Matrix im UI anzeigen (Loss/Validation-Loss/Dauer/Parameter/Adapterpfad je Lauf).
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
- Nach behobenen Training-Repository-Fehlern: Pylance-Strict-Checks auf `app/training/services` und `app/api/routes/training.py` ausweiten, damit `Unknown`-Typen dort ebenfalls frueh erkannt werden.
- Nach eingefuehrter Tabelle `training_dataset_files`: API- und UI-Darstellung auf table-first umstellen und JSON-Metadaten nur noch als Kompatibilitaetslayer nutzen.
- Nach eingefuehrter Tabelle `training_artifacts`: Job-Detailansicht im Frontend um Artefaktliste (Typ, Pfad, Hash, Status) erweitern.
- Settings-Selbstheilung nachziehen: Audit-/Telemetry-Hinweise fuer automatisch reparierte `model.base_directories` im Monitoring sichtbar machen und klare Auto-Commit-Richtlinie fuer Read-Pfade dokumentieren.
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
- Optionalen Repo-Slug-Wechsel evaluieren (`python-chat-system` -> `kernschmiede`) und danach Badge-/Clone-/Remote-Links zentral validieren.
- CI-Failure-Tracking verbessern: fehlgeschlagene Runs zu Rebranding-Commits zeitnah analysieren und dokumentiert nachziehen.
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
- Aktuelle Restwarnung konkret beheben: `SAWarning non-checked-in connection` aus Integrationstestpfaden (derzeit auffaellig im custom-loader-Flow) durch sauberen Session-/Connection-Abschluss eliminieren.
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
- Markdownlint-Baseline nachziehen: temporaere Rule-Overrides in `.markdownlint.json` schrittweise durch echte Doku-Korrekturen ersetzen und danach Regeln wieder stricter stellen.
- Markdown-Strictness Phase 2 vorbereiten: nach erfolgreicher Phase 1 (`docs/**/*.md`) als naechsten Batch ausgewaehlte `plugins/*/README.md` auf `MD040/MD041/MD051` nachziehen und die globalen Ausnahmen danach weiter reduzieren.
- Markdown-Strictness Phase 3 planen: verbleibende Legacy-Plugin-READMEs mit nicht-standardisiertem Start (z. B. Wrapper-Codefences vor der H1) auf saubere H1-First-Line-Struktur umstellen, damit die letzten `MD041`-Ausnahmen entfallen koennen.

## Arbeitsweise

- Changelog enthaelt nur umgesetzte und verifizierte Punkte.
- Roadmap enthaelt nur Ausbaustufen und Ziele.
- TODO enthaelt nur konkrete naechste Arbeitspakete.
- Spaetere oder optionale Themen werden in Backlog gepflegt.
