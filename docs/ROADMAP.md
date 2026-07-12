# Roadmap

## Ziel und Abgrenzung

- Diese Datei enthaelt nur geplante Ausbaustufen und Ziele.
- Bereits implementierte Punkte stehen ausschliesslich im Changelog.
- Konkrete naechste Arbeitspakete mit Prioritaet stehen im TODO.
- Spaetere Enterprise-Themen stehen im Backlog.

## V1 Stabilisierung und Produktreife lokal

- Python-Laufzeit konsolidieren: `.venv-chat` (Python 3.12) als primaere Umgebung fuer Chat/Loader/Training etablieren und Interpreter-Drift zwischen lokalen Starts vermeiden.
- Nach erfolgreicher `.venv-chat`-Migration: GPU-Paritaet der neuen Hauptumgebung vervollstaendigen (CUDA-Torch final angleichen und gegen Transformers/Vision/Training live pruefen).

- Einheitliche API-Fehlerstruktur mit Fehlercode, Retry-Hinweis und Details bereitstellen.
- Nach vereinheitlichtem HTTP- und SSE-Error-Envelope: zentrale Client-Error-Utility fuer Toasts, Retry-Hinweise und Telemetrie standardisieren.
- Polling weiter optimieren: sichtbarkeitsbasierten Refresh um Fokus-/Idle-Strategie erweitern, um Hintergrundlast weiter zu senken.
- Konversations-Lifecycle weiter haerten: Rename/Delete/Create-Endpunkte konsistent gegen Async- und DB-Randfaelle absichern.
- Nach Settings-Fallback-Hardening fuer `model_<id>_*`: End-to-End-Tests fuer modell-spezifische Prompt-/Parameterauflosung ueber mehrere Benutzerkonten ausbauen.
- Modellpfade mit Path-Traversal-Schutz und Basisverzeichnis-Pruefung haerten.
- Nach Modellpfad-Haertung: bestehende `ModelConfig`-Datensaetze per Migrations-/Health-Check auf unerlaubte Pfade pruefen und bereinigen.
- Nach Polling-Deduplikation: Fokus-/Idle-basierte Polling-Intervalle dynamisch staffeln, um Last unter aktiver Nutzung weiter zu optimieren.
- Nach TanStack-Query-Konsolidierung: Cache-Invalidierung und Mutation-Flows fuer Einstellungen/Chataktionen weiter standardisieren.
- Nach zentralen Settings-Query-Helfern: verbleibende Chat-Mutationen schrittweise in denselben einheitlichen Invalidation-/Optimistic-Update-Pfad ueberfuehren.
- Nach Strict-Mode-Regressionstests: Polling-Testabdeckung auf Fokus-/Idle-Intervallstaffelung und Sichtbarkeitswechsel erweitern.
- Prompt-Persistenz im Modellprofil weiter haerten: UI-Race-Conditions beim Modellwechsel/Speichern eliminieren und globalen Fallback (`prompt.system_prompt`) als sichtbaren Standardpfad absichern.
- API-/Integrationstests fuer Startup-Restore und Modellpfad-Gueltigkeit gegen Datenbank-Bestandsdaten ausbauen.
- Nach retrieval-basierten Kontextmetriken: externe Datenanteile von Metadaten-Kontext auf inhaltsbasierte Chunk-Selektion (inkl. Embedding-/Hybrid-Ranking) weiterentwickeln.
- Nach lokalem Prompt-Diagnosemodus und API-Endpunkt: optionalen redigierten Export (Datei/Snapshot) fuer reproduzierbare Prompt-/Retrieval-Analysen ergaenzen.
- Nach modell-spezifischer Prompt-/Decoding-Steuerung: einheitliche Parameterunterstuetzung fuer weitere Backends (neben llama.cpp) und capability-gesteuerte UI-Enablement-Regeln einfuehren.
- Modellstil gezielt steuerbar machen: pro Modell/Profilebene robuste Ausgabe-Templates (Kurzantwort/Analyse/Schrittfolge) und automatische Halluzinations-Checks fuer bekannte Domainthemen (z. B. Charta von Venedig) integrieren.
- Nach interpreter-aware Loaderdiagnostik fuer `llama_cpp`: Installationspfad fuer Python-3.13/Windows (Long-Path- und Wheel-Strategie) als dokumentierten Ops-Runbook-Schritt standardisieren.

## V2 Funktionsausbau Chat, Settings und Wissensbasis

- Nach Einfuehrung von `/api/models/capabilities`: Frontend-Modelleinstellungen und Ladeentscheidungen schrittweise auf capability-basierte Validierung umstellen.
- Nach Erweiterung von `GET /api/models` um Capability-Metadaten: persistente Favoriten/Irrelevanz-Labels (`favorite`/`irrelevant`) und nutzerbezogene Gruppierungs-Praeferenzen ergaenzen.
- Nach Einfuehrung persistenter Relevanzflags: Team-/rollenbezogene Relevanzansichten (pro Nutzer vs. globales Teamprofil) und Bulk-Markierung im Modellmanager ausbauen.
- Nach Einfuehrung des plugin-basierten Custom-Loader-Registrysystems: weitere benutzerdefinierte Architektur-Plugins (neben Supra-A2A) standardisiert ueber dieselbe Registry integrieren.
- Nach Trust-Gating fuer Custom-Code: dedizierte UI-Interaktion fuer sichere Freigabe/Widerruf und differenzierte Risiko-Hinweise im Modellmanager ausbauen.
- Nach Einfuehrung des `custom_pytorch`-Runtime-Backends: multimodalen Request-Pfad (Text+Bild) in Chat-API/Service fuer `vision_text_generation` ist umgesetzt; als naechster Schritt bleibt die Ausweitung auf weitere Modalitaeten (`any_to_any`, Audio-Pfade).
- Nach erfolgreicher SmolVLM2-Liveaktivierung inkl. JPEG-Smoke-Test: Vision-Postprocessing weiter verbessern, damit Antworten nicht mehr Prompt-/History-Echo enthalten und modelltypisch kompakt ausgegeben werden.
- Nach Frontend-Umstellung auf Markdown-Rendering: optionale Safe-Plugins (z. B. GFM) und feinere Typografie fuer Tabellen/Codebloecke evaluieren, ohne Sicherheit und Lesbarkeit zu verschlechtern.
- Nach produktiver Einfuehrung und Stabilisierung von `Allgemein`-Settings: verbleibende Frontend-Texte auf durchgaengige i18n-Struktur umstellen (statt partieller DE/EN-Inline-Texte in einzelnen Komponenten).
- Nach Selbstwissen-Erweiterung im Chat-Systemprompt: steuerbare Auspraegung festlegen, welche Benutzer-/Team-Einstellungen als Prompt-Kontext zwingend oder optional einbezogen werden.
- Nach integrierter In-Scan-Bereinigung von Datei-vs-Ordner-Dubletten: optionalen expliziten Maintenance-/Migrationspfad fuer historische Sonderfaelle ausserhalb regulärer Scan-Laeufe standardisieren.
- Nach Runtime-Probes und produktiver Loader-Aufloesung: echte Inferenzpfade je Task-Typ (Embedding/Reranker/Speech/OCR/Bild) hinter denselben Loader-IDs weiter vertiefen und benchmarken.
- Chat-Template-Strategie backenduebergreifend weiter haerten: GGUF/llama.cpp-Template-Verhalten gegen reale Modellmetadaten und Sonderfaelle (fehlendes Chat-Template) systematisch validieren.
- Trainings-Kompatibilitaet vertiefen: neben `peft_lora` weitere Trainer-spezifische Regeln und hardwareabhaengige Constraints (VRAM/CUDA/Quantisierung) serverseitig auswerten.
- Nach Einfuehrung versionierter Konversations-Generierungsprofile: Versionsvergleich und schnelle Wiederherstellung (Diff/Restore) im UI erweitern.
- Projektverwaltung weiter ausbauen: projektbezogene Filter und Bulk-Aktionen fuer Konversationen, Termine und Wissensquellen konsistent machen.
- Quellenfluss produktivieren: nach `sources/upload` echte Inhaltsverarbeitung (Parsing/Chunking/Indexierung) fuer `pdf/md/txt/docx` aufbauen, damit Retrieval auf Dokumentinhalt statt Dateimetadaten basiert.
- Projektzuordnung robuster machen: stale Projekt-IDs in Konversations-Create-/Assign-Flows automatisch erkennen, ruecksetzen und mit klarer UX-Rueckmeldung recovern.
- Chat-Feedback und Regeneration einzelner Antworten einfuehren.
- Multi-User-Chat-Darstellung verfeinern: Benutzerlabels je Nachricht mit klarer visueller Unterscheidung.
- KI-Teilnahmemodus je Konversation steuern ("KI redet mit"), inklusive Intent-gesteuerter Zurueckhaltung.
- Intent-Marker konfigurierbar machen: Default pro Benutzer plus optionale Ueberschreibung pro Team-Chat.
- Bedienhilfe uebergreifend vereinheitlichen: aussagekraeftige Hover-Hinweise fuer verbleibende Header-/Sidebar-Aktionen vervollstaendigen.
- Einstellungen exportieren, importieren und zuruecksetzen.
- Dokumentversionierung und kontrollierte Neuindizierung bei Embedding-Wechsel.
- Kaskadenloeschung fuer Dokumente, Chunks und Embeddings durchgaengig absichern.
- Strukturierte Request-, Conversation- und Trace-IDs durchgaengig loggen.
- Virtuelle Nachrichtenliste fuer sehr lange Chats im Frontend einfuehren.
- Frontend Error Boundary fuer robuste Fehlerisolierung ergaenzen.
- Navigation mit React Router und Deep Links fuer Chats, Projekte und Dokumente.
- Teststrategie mit kleinen lokalen Testmodellen fuer CI und lokale Entwicklung.

## V3 Teamfaehigkeit und Betriebsstabilitaet

- Teambezogene Sichtbarkeit fuer Konversationen abschliessen (internal statt global).
- Nach UI-Ownership-Guards: Conversation-API-Semantik fuer Teamchats finalisieren (sichtbar vs. bearbeitbar/loeschbar) und konsistente `403`-Antworten fuer fehlende Rechte statt generischer `404` evaluieren.
- Nach interner Default-Sichtbarkeit Team-/Rollenregeln pro Konversation durchsetzen (internal nicht mehr global fuer alle Nutzer).
- Rollen- und Rechtekonzept fuer Projekte, Dokumente und Konversationen erweitern.
- Admin-Benutzerverwaltung weiter haerten: serverseitige Admin-Autorisierung von `admin_user_id` auf echte Session-/Token-Pruefung umstellen.
- Admin-Benutzerverwaltung erweitern: Audit-Log fuer Benutzer-Aenderungen (wer, was, wann) inklusive Rueckverfolgbarkeit im UI bereitstellen.
- Auth-Layer weiterentwickeln: token-basierte Anmeldung um Refresh-/Logout-Invalidierung und optionales Rolling-Session-Konzept ergaenzen.
- Admin-Lifecycle vervollstaendigen: nach Kick-Entsperren jetzt Soft-Delete-Events in der Admin-Historie visualisieren und Reaktivierung geloeschter Konten ergaenzen.
- Teamchat-UX weiterentwickeln: Teilnahme-Schalter und Kollaborationshinweise einheitlich ueber Desktop/Tablet/Mobil verhalten (inkl. klarer Disabled-Zustaende).
- Teamchat-Flow ausbauen: nach User-only-Sendepfad optional konfigurierbar machen, ob bei deaktivierter KI automatisch ein rein menschlicher Modus aktiv ist.
- Hintergrundjobs fuer Import, Embeddings und Reindizierung stabilisieren.
- Hybridsuche aus Volltext und Vektor inklusive Quellen-Nachvollziehbarkeit verfeinern.
- Betriebsmetriken fuer Queue, Modellzustand und Antwortlatenz standardisieren.
- Produktiven Internet-Betrieb standardisieren: Reverse-Proxy-Referenzkonfiguration inkl. TLS, Forwarded-Headern und sicheren CORS-Vorgaben bereitstellen.
- Nutzerpraesenz von Heartbeat-Polling auf push-basierte Echtzeitpraesenz (WebSocket/SSE-Presence-Events) weiterentwickeln.
- Secret-Handling standardisieren: Zugangsdaten und API-Secrets ausschliesslich ueber sichere, nicht versionierte Secret-Speicher verwalten.
- Release-Haertung fuer oeffentliche Repositories ausbauen: standardisierte Pre-Publish-Checks fuer Secret-Scan und Ignore-Regeln vor jedem Public Push etablieren.
- GitHub-Repository-Governance weiter ausbauen: Label-Strategie, Auto-Triage und semantische Release-Notes entlang PR-Kategorien weiter verfeinern.
- Frontend-Devtool-Sicherheit dauerhaft absichern: Vite/Vitest/esbuild-Updates regelmaessig einplanen und Dependabot-PRs zeitnah mergen.
- Nach Major-Upgrades (React/TypeScript/jsdom) verbindliche Kompatibilitaetspruefung ueber CI + UI-Regressionspfade etablieren.
- Backend-Security weiter vertiefen: zentralisiertes Error-Redaction-Pattern fuer alle API-Routen vereinheitlichen und testbar machen.
- Workflow-Stack kontinuierlich haerten: Trigger, Berechtigungen und Secret-Policy regelmaessig ueberpruefen.
- Code-Scanning-Strategie konsolidieren: genau einen produktiven CodeQL-Pfad (Default Setup oder Advanced Setup) verbindlich festlegen und dokumentieren, um SARIF-Konflikte dauerhaft zu vermeiden.
- README-Badge-Pflege standardisieren: fuer jeden aktiven Workflow in `.github/workflows` eine eindeutige Badge-Strategie hinterlegen.
- Trainings-URL-Import langfristig produktivieren: Host-Allowlist aus Settings verwalten (statt statischer Basen) und mit dedizierten Security-Tests absichern.
- Chat-Updates von Polling auf push-basiertes Eventing (SSE/WebSocket) umstellen, um geraeteuebergreifend niedrigere Latenz zu erreichen.
- Statische Typqualitaet im Backend weiter schaerfen (Pylance strict): unbekannte Typen in Service-/Repository-Pfaden systematisch eliminieren.

## V4 Training Workbench und Modellverbesserung

- Trainingsdomane als allgemeines `training`-Subsystem aufbauen (statt enger `finetuning`-Bezeichnung), damit neben Fine-Tuning auch LoRA/QLoRA, DPO/PPO, Reranker und Reward-Model-Pfade erweiterbar bleiben.
- Trainings-Preflight fuer lokales Basismodell und Dataset weiter ausbauen (inkl. klarer Fehlerklassifizierung und Recovery-Hinweisen).
- Lifecycle-Konsolidierung abschliessen: `running` als Oberstatus gegen granulare Trainingsstatus/Phasen sauber abloesen.
- Realen PEFT-Smoke-Run als wiederholbaren Verifikationspfad weiter standardisieren (automatisierte Ausfuehrung, reproduzierbare Artefaktpruefung, klare Abbruchsignale).
- Nach fruehem Trainer-Heartbeat und explizitem Validierungsdatei-Support: Trainingsbeobachtbarkeit im UI weiter ausbauen (sichtbare Phase vor Schritt 1, Datensatzgroessen, Tokenizer-/Pad-Checks im Report).
- Nach erfolgreichem Adapter-Artefaktcheck: Trainingsartefakte in den Modellmanager rueckfuehren (registrieren, vergleichen, kurze Testinferenz mit/ohne Adapter).
- Trainer ueber Interface abstrahieren (Unsloth, Axolotl, TRL, MLX, FutureTrainer), damit Backendwechsel ohne Umbau in Services/API moeglich ist.
- Dataset-Domane mit Versionierung und reproduzierbaren Metadaten ausbauen (Quelle, Split, Tokenizer, Promptformat, Lizenz, Sprache, Checksum, Ersteller, Projektbezug).
- Nach Datei-/URL-Import fuer Trainingsdatasets: Metadatenfluss fuer Manifest/README/Checksummen automatisch auslesen und bei Importen direkt am Dataset hinterlegen.
- Nach universellem Dataset-MVP: Parser-/Validator-/Exporter-Plugins fuer weitere Formate und unternehmensspezifische Schemata standardisieren, inklusive Auto-Split (train/val/test), Qualitaetsbewertung und Benchmark-Generierung aus demselben kanonischen Datensatz.
- Exporter und Validator als Pflichtbausteine einfuehren: Datenqualitaet/Schema/Tokenlaengen/Rollen/Duplikate validieren und Daten aus Chats/Bibliothek/Dokumenten/Bewertungen/Projekten exportieren.
- Job-Lifecycle fuer Training weiter granularisieren (`created`, `queued`, `preparing`, `validating`, `tokenizing`, `training`, `saving`, `registering`, `completed`, `cancelled`, `failed`) und im UI transparent machen.
- Promotions-Gate verpflichtend machen: Training -> Evaluation -> Healthcheck -> Benchmark -> Registrierung -> Aktivierbar.
- Evaluationsmodul nach jedem Training automatisch ausfuehren (Perplexity, Testsatz, Qualitaet, Benchmark, Regression).
- Experiment-Tracking und Trainingshistorie persistieren (Hyperparameter, Seed, Commit, Dataset-/Trainer-Versionen, CUDA, Loss/LR/Epoch/ETA/Checkpoint, GPU/VRAM/RAM).
- GPU-Scheduler mit klaren Prioritaeten einfuehren: Chat (1), Embedding (2), Training (3).
- Referenzarchitektur laufend pflegen in [docs/training-workbench.md](docs/training-workbench.md).

## Technische Leitplanken

### API-Kompatibilitaet zwischen Client und Server

- Capability-Modell nach Einfuehrung von `/api/meta/capabilities` auf weitere Featurebereiche ausdehnen (z. B. Uploads, Teamfunktionen, Streaming-Varianten).
- Persistente Frontend-Sessions gegen geloeschte oder ungueltige Benutzer robust validieren (klare Re-Auth statt stiller Fehlerpfade).

### Modellstatus und Tests

- Passiver Modellstatus wird regelmaessig geprueft.
- Aktive Test-Inferenz erfolgt nach dem Laden.
- Erneute Test-Inferenz erfolgt nur bei konkretem Fehlerverdacht.

### OOM-Wiederherstellung

1. Anfrage abbrechen.
2. Backendzustand pruefen.
3. Modell bei Bedarf entladen.
4. Speicher freigeben.
5. Modell kontrolliert neu laden.
6. Erst danach neue Anfragen zulassen.

### Modell-Cache

- Optionaler Mehrmodell-Cache nur bei ausreichend RAM/VRAM.
- Standard bleibt ein gleichzeitig geladenes Modell.

### Zustandsarchitektur Frontend

- TanStack Query verwaltet Serverdaten: Conversations, Messages, Models, Projects, Documents.
- Zentraler UI-Store verwaltet nur Oberflaechenzustand: Sidebars, Theme, aktiver Tab, Fokusmodus, Composer.

### Retry-Strategie API-Client

- GET: begrenzte Retries erlaubt.
- POST, PUT, DELETE: nur mit Idempotency-Key oder explizit als sicher markiert.

### Migration und Seeding

- Migrationen verwalten ausschliesslich Datenbankschema.
- Standardwerte und Standard-Prompts werden idempotent ueber Seed-Service bereitgestellt.
