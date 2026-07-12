# Python Chat System

[![CI](https://github.com/Thomas-Heisig/python-chat-system/actions/workflows/ci.yml/badge.svg)](https://github.com/Thomas-Heisig/python-chat-system/actions/workflows/ci.yml)
[![CodeQL](https://github.com/Thomas-Heisig/python-chat-system/actions/workflows/codeql.yml/badge.svg)](https://github.com/Thomas-Heisig/python-chat-system/actions/workflows/codeql.yml)
[![Dependency Review](https://github.com/Thomas-Heisig/python-chat-system/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/Thomas-Heisig/python-chat-system/actions/workflows/dependency-review.yml)
[![Release Drafter](https://github.com/Thomas-Heisig/python-chat-system/actions/workflows/release.yml/badge.svg)](https://github.com/Thomas-Heisig/python-chat-system/actions/workflows/release.yml)
[![Stale](https://github.com/Thomas-Heisig/python-chat-system/actions/workflows/stale.yml/badge.svg)](https://github.com/Thomas-Heisig/python-chat-system/actions/workflows/stale.yml)

Modulares Python-Chatsystem mit FastAPI, SQLAlchemy und austauschbaren Modell-Backends.

## GitHub Community Health

- Contributing guide: `.github/CONTRIBUTING.md`
- Security policy: `.github/SECURITY.md`
- Code of conduct: `.github/CODE_OF_CONDUCT.md`
- Support guide: `.github/SUPPORT.md`
- Pull request template: `.github/PULL_REQUEST_TEMPLATE.md`
- Issue templates: `.github/ISSUE_TEMPLATE/*`
- Ownership rules: `.github/CODEOWNERS`
- Automated updates: `.github/dependabot.yml`
- CI/CD and security workflows: `.github/workflows/*`

## Entwicklungsstufe 1 (enthalten)

- FastAPI Grundserver mit klarer Schichtenstruktur
- SQLite Datenbank mit SQLAlchemy 2 (async)
- Settings in Datenbank mit TTL-Cache und Prioritaetsaufloesung
- Modellscanner fuer lokale Verzeichnisse (GGUF und Transformer-Hinweise)
- Einheitliche Backend-Schnittstelle
- GGUF-Backend mit llama-cpp-python (echte Generierung + Streaming)
- Sicherer Modellwechsel mit Rollback-Logik
- Async Executor-Bruecke mit to_thread
- Streaming-Chat-Endpunkt
- Grundlegende Health-Endpunkte
- Startdatei `start.py` fuer Initialisierung + Serverstart

## Schnellstart

1. Python 3.11+ installieren
2. Virtuelle Umgebung erstellen
3. Abhaengigkeiten installieren
4. Datenbank initialisieren
5. Server starten

PowerShell:

- pip install -r requirements.txt
- python start.py --reload

Backend + Frontend gemeinsam starten:

- Windows: `./scripts/start_fullstack.ps1`
- Linux/macOS: `./scripts/start_fullstack.sh`

Start auch direkt aus dem Workspace-Root (`F:\symple chat`):

- Windows: `powershell -ExecutionPolicy Bypass -File .\scripts\start_fullstack.ps1 -NoReload -StopExisting`

Optional laufende Instanzen vorher stoppen:

- Windows: `./scripts/start_fullstack.ps1 -StopExisting`
- Linux/macOS: `STOP_EXISTING=1 ./scripts/start_fullstack.sh`
- Wenn ein Dienst nicht gestoppt werden kann, wird der Neustart mit klarer Fehlermeldung abgebrochen.

Hinweis:

- Das Script funktioniert unabhaengig vom aktuellen Arbeitsverzeichnis, weil es den Projektpfad selbst ermittelt.
- Bei bereits belegten Ports werden laufende Dienste erkannt und nicht doppelt gestartet.
- Das Frontend wird direkt mit `npx vite --host ... --port ...` gestartet.

## Empfohlene Python-Umgebung

Fuer den stabilen Betrieb als einheitliche Chat-Laufzeit wird eine dedizierte Umgebung `.venv-chat` (Python 3.12) empfohlen.

- Startskripte priorisieren jetzt: `.venv-chat` -> `.venv-training` -> `.venv` -> globales `python`.
- Setup-Helfer (Windows PowerShell):

  - `./scripts/setup_venv_chat.ps1 -TargetPython "C:\\Pfad\\zu\\Python312\\python.exe" -InstallCoreDeps`

Wenn Python 3.12 noch nicht installiert ist, meldet das Setup-Skript den fehlenden Interpreter mit klarer Anweisung.

## Zugriff: localhost, Intranet und Internet

Der Start ueber `start.py` und `scripts/start_fullstack.*` bindet standardmaessig auf `0.0.0.0`.
Damit ist die App nicht nur lokal, sondern auch im LAN/Intranet erreichbar.

Beispiele:

- Lokal: `http://localhost:5173`
- Intranet: `http://<LAN-IP>:5173`
- Internet: ueber Reverse Proxy + Domain, z. B. `https://chat.example.com`

Wichtige Umgebungsvariablen (siehe `.env.example`):

- `CORS_ALLOW_ORIGINS`: erlaubte Frontend-Origins fuer Backend-API
- `CORS_ALLOW_ORIGIN_REGEX`: optionales Pattern fuer dynamische Domains/Subdomains
- `CORS_ALLOW_CREDENTIALS`: CORS Credentials-Flag
- `FRONTEND_HOST`, `FRONTEND_PORT`: Bind-Adresse/Port des Vite-Servers
- `VITE_DEV_BACKEND_TARGET`: Backend-Target fuer Vite-Dev-Proxy
- `VITE_API_BASE_URL`: explizite API-Basis-URL fuer Intranet/Internet-Deployments
- `VITE_ALLOWED_HOSTS`: optionale Host-Allowlist fuer Vite

Optional:

- Nur Initialisierung (DB + Defaults + Modellscan): `python start.py --init-only`
- Initialisierung ohne Modellscan: `python start.py --init-only --skip-model-scan`

## Modellverzeichnisse

Standardmaessig werden beim Start folgende Verzeichnisse dynamisch gescannt:

- `./model-directories`
- `F:\\KI\\models`

Die Liste ist zur Laufzeit ueber die Settings (`model.base_directories`) aenderbar.

## GPU-First Verhalten

- Beim Modell-Aktivieren wird standardmaessig immer zuerst GPU versucht.
- Falls keine GPU verfuegbar ist, faellt das System automatisch auf CPU zurueck.
- Standard-Setting: `model.prefer_gpu = true`.

## Naechste Schritte

- Alembic Migrationen aktivieren
- Embeddings und Hybrid-Retrieval integrieren
- RQ/Celery fuer verteilte Worker ergaenzen
- PostgreSQL + pgvector fuer Produktion umstellen
