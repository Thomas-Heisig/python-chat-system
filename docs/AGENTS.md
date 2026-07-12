# AGENTS.md

## Verbindliche Regeln für KI-Agenten und Entwicklungsassistenten

Diese Datei enthält verbindliche Arbeitsregeln für alle KI-Agenten, Coding-Assistenten und automatisierten Werkzeuge, die dieses Projekt lesen, analysieren oder verändern.

Dazu gehören insbesondere:

* GitHub Copilot
* OpenAI Codex
* ChatGPT
* Claude Code
* Gemini Code Assist
* Cursor
* Windsurf
* lokale Coding-Agenten
* automatisierte Refactoring-Agenten
* Review- und Test-Agenten

Die Regeln gelten für das gesamte Repository und alle Unterverzeichnisse, sofern in einem Unterverzeichnis keine ergänzende `AGENTS.md` mit strengeren oder spezielleren Vorgaben vorhanden ist.

---

## 1. Projektziel

Das Projekt ist ein modulares Python-Chatsystem mit:

* frei wählbaren Modellverzeichnissen
* Unterstützung mehrerer Modell-Backends
* lokaler und externer Modellinferenz
* Chatverwaltung
* Wissensdatenbank
* Datenbank-basierten Einstellungen
* Datenbank-basierten Prompts
* Benutzer- und Rechteverwaltung
* kontrollierter CPU-, RAM- und GPU-Nutzung
* Streaming-Ausgabe
* modularer Erweiterbarkeit
* klar getrennten Zuständigkeiten

Die Architektur muss langfristig wartbar, nachvollziehbar und erweiterbar bleiben.

Eine kurzfristig funktionierende Lösung darf nicht zu Lasten der Gesamtarchitektur umgesetzt werden.

---

## 2. Grundregeln

Jeder Agent muss vor Änderungen:

1. die bestehende Projektstruktur prüfen,
2. vorhandene Implementierungen suchen,
3. bestehende Schnittstellen berücksichtigen,
4. abhängige Module identifizieren,
5. vorhandene Tests prüfen,
6. bestehende Dokumentation lesen,
7. mögliche Seiteneffekte bewerten.

Kein Agent darf ohne Prüfung annehmen, dass eine Datei, Klasse, Methode, Datenbanktabelle oder Einstellung noch nicht existiert.

Vor der Erstellung neuer Komponenten ist im Repository nach ähnlichen oder bereits vorhandenen Lösungen zu suchen.

---

## 3. Keine unnötigen Neuerstellungen

Bestehende Funktionen, Klassen und Module sind nach Möglichkeit zu erweitern.

Nicht zulässig:

* parallele Implementierung derselben Funktion
* doppelte Services
* doppelte Repository-Klassen
* mehrere konkurrierende Konfigurationssysteme
* mehrere unterschiedliche Fehlerformate
* mehrere unabhängige Event-Systeme
* neue Hilfsfunktionen, wenn bereits eine passende vorhanden ist
* Kopieren bestehender Logik in andere Module

Vor jeder Neuerstellung ist zu prüfen:

```text
Existiert bereits eine ähnliche Klasse?
Existiert bereits ein passender Service?
Existiert bereits eine Utility-Funktion?
Kann eine vorhandene Schnittstelle erweitert werden?
Ist die neue Datei wirklich erforderlich?
```

---

## 4. Architekturgrenzen

Die festgelegten Schichten dürfen nicht unkontrolliert vermischt werden.

Grundstruktur:

```text
API
↓
Services / Orchestratoren
↓
Repositories
↓
Datenbank
```

Zusätzlich:

```text
ChatService
↓
ModelManager
↓
ModelExecutor
↓
ModelBackend
```

und:

```text
KnowledgeService
↓
Retriever / Indexer / Parser
↓
Repository / Vektorspeicher
```

## Verbotene direkte Zugriffe

Nicht zulässig:

* SQL-Abfragen direkt in API-Routen
* Modellladen direkt in API-Routen
* Dateizugriffe direkt aus API-Routen, sofern ein Service vorhanden ist
* Zugriff auf globale Settings ohne Settings-Service
* direkte Nutzung konkreter Modell-Backends aus dem ChatService
* Datenbankzugriffe aus Pydantic-Schemas
* Geschäftslogik in ORM-Modellen
* HTTP-spezifische Fehler in tiefen Services
* direkte Frontend-Abhängigkeiten im Backend

API-Routen sollen möglichst dünn bleiben.

Beispiel:

```python
@router.post("/chat")
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    return await service.generate(request)
```

---

## 5. Modulverantwortung

## `app/api/`

Enthält:

* HTTP-Routen
* Request- und Response-Verarbeitung
* Dependency Injection
* Authentifizierungsprüfung
* Umwandlung von Fehlern in HTTP-Antworten

Enthält nicht:

* SQL-Logik
* Modellladevorgänge
* komplexe Geschäftslogik
* Dateiparsing
* Embedding-Erzeugung

## `app/services/`

Enthält übergreifende Anwendungslogik.

Services koordinieren andere Komponenten, führen aber keine unstrukturierten Direktzugriffe auf interne Implementierungen aus.

## `app/database/repositories/`

Enthält Datenbankzugriffe.

Repositories:

* kapseln SQLAlchemy-Abfragen
* geben definierte Modelle oder DTOs zurück
* führen keine Modellinferenz aus
* enthalten keine HTTP-Logik
* enthalten keine Frontend-Logik

## `app/models/`

Enthält die Modellverwaltung.

Dazu gehören:

* Modellscan
* Modellregistrierung
* Laden und Entladen
* Lebenszyklus
* Modellausführung
* Ressourcenprüfung
* Backend-Schnittstellen

## `app/chat/`

Enthält:

* Chatorchestrierung
* Kontextaufbau
* Tokenzählung
* Tokenbudget
* Kürzungsstrategien
* Streaming
* Chatverlauf

## `app/knowledge/`

Enthält:

* Dokumentimport
* Parser
* Chunking
* Embeddings
* Indexierung
* Vektorsuche
* Schlüsselwortsuche
* Hybrid-Suche
* Reranking

## `app/settings/`

Enthält:

* Laden von Einstellungen
* Validierung
* Prioritätsauflösung
* Caching
* Cache-Invalidierung
* Standardwerte

## `app/prompts/`

Enthält:

* Promptverwaltung
* Prompt-Rendering
* Prompt-Versionierung
* Standard-Prompts
* Datenbank-Fallbacklogik

---

## 6. Datenbankregeln

Alle veränderbaren Anwendungseinstellungen gehören grundsätzlich in die Datenbank.

Die `.env`-Datei enthält nur Werte, die vor dem Aufbau der Datenbankverbindung benötigt werden oder nicht in die normale Einstellungsverwaltung gehören.

Geeignet für `.env`:

* Datenbankverbindung
* initialer Secret Key
* Laufzeitumgebung
* externe Zugangsdaten
* Bootstrap-Konfiguration

Nicht geeignet für `.env`:

* Temperatur
* aktives Modell
* Modellverzeichnis
* Kontextlänge
* Chunk-Größe
* Top-K-Werte
* UI-Einstellungen
* aktive Prompts
* benutzerbezogene Einstellungen

## Migrationen

Datenbankänderungen müssen über Alembic-Migrationen erfolgen.

Nicht zulässig:

* Tabellen manuell außerhalb von Migrationen ändern
* produktive Tabellen beim Start unkontrolliert neu erstellen
* bestehende Spalten ohne Migrationspfad umbenennen
* Daten löschen, ohne Migration und Rückwärtsstrategie zu prüfen

Jede Schemaänderung benötigt:

1. ORM-Anpassung,
2. Alembic-Migration,
3. Prüfung vorhandener Daten,
4. Test der Migration,
5. gegebenenfalls Dokumentationsanpassung.

---

## 7. Datenintegrität

Foreign Keys sind zu verwenden, wenn Datensätze logisch miteinander verbunden sind.

Beispiele:

* `conversation.user_id`
* `message.conversation_id`
* `knowledge_chunk.document_id`
* `embedding.chunk_id`
* `model_config.directory_id`

Benutzer-, Team- und globale Daten müssen sauber getrennt werden.

Jede Abfrage auf benutzerbezogene Inhalte muss den Benutzer- oder Teamkontext berücksichtigen.

Nicht zulässig:

```python
conversation = await repository.get_by_id(conversation_id)
```

wenn dadurch fremde Unterhaltungen geladen werden könnten.

Erforderlich:

```python
conversation = await repository.get_by_id(
    conversation_id=conversation_id,
    user_id=user_id,
)
```

---

## 8. Einstellungen

Alle Einstellungen werden über den zentralen `SettingsService` geladen.

Nicht zulässig:

```python
temperature = 0.7
```

an mehreren Stellen fest zu hinterlegen.

Zulässig:

```python
temperature = await settings_service.get_float(
    category="chat",
    key="temperature",
    user_id=user_id,
)
```

Standardwerte dürfen im Quellcode vorhanden sein, müssen aber zentral definiert sein.

Einstellungspriorität:

```text
Anfrage
Benutzer
Team
System
Standardwert
```

Sicherheitsgrenzen und technische Maximalwerte dürfen durch niedrigere Ebenen nicht überschrieben werden.

---

## 9. Modellverzeichnisse

Modellpfade dürfen nicht hart im Quellcode eingetragen werden.

Nicht zulässig:

```python
MODEL_PATH = "F:\\KI\\models\\model.gguf"
```

Stattdessen:

* Modellverzeichnisse aus der Datenbank laden
* Verfügbarkeit prüfen
* Pfade normalisieren
* Pfadzugriffe validieren
* rekursives Scannen konfigurierbar machen

Modellpfade müssen plattformübergreifend über `pathlib.Path` verarbeitet werden.

Beispiel:

```python
from pathlib import Path

model_path = Path(configured_path).expanduser().resolve()
```

---

## 10. Modell-Backends

Jedes Modell-Backend muss dieselbe definierte Basisschnittstelle implementieren.

Ein Backend darf nicht direkt vom restlichen System aufgerufen werden, wenn dafür `ModelManager` oder `ModelExecutor` vorgesehen sind.

Pflichtfunktionen eines Backends:

* Laden
* Entladen
* Generieren
* Streaming
* Health-Check
* Ermittlung der Fähigkeiten
* Tokenzählung, sofern unterstützt
* geordnete Speicherfreigabe

Backend-spezifische Optionen dürfen nicht unkontrolliert in allgemeine Module gelangen.

Backend-spezifische Einstellungen gehören in einen klar abgegrenzten Konfigurationsbereich.

---

## 11. Blockierende Modellinferenz

CPU- und GPU-intensive Modellinferenz darf den FastAPI-Event-Loop nicht blockieren.

Nicht zulässig:

```python
@router.post("/chat")
async def chat(request: ChatRequest):
    return backend.generate(request.prompt)
```

Stattdessen ist der `ModelExecutor` zu verwenden.

Beispiel:

```python
result = await model_executor.generate(
    model_id=model_id,
    prompt=prompt,
    generation_config=generation_config,
)
```

Synchrone Backend-Aufrufe müssen kontrolliert über:

* `asyncio.to_thread`,
* einen Thread-Pool,
* einen dedizierten Worker,
* oder eine geeignete Queue

ausgeführt werden.

Ein Prozess-Pool darf für GPU-Modelle nicht ohne Prüfung eingesetzt werden, da dadurch Modelle mehrfach geladen werden können.

---

## 12. GPU-, RAM- und Ressourcenregeln

Vor dem Laden oder Ausführen eines Modells sind Ressourcen zu prüfen.

Zu berücksichtigen:

* verfügbarer VRAM
* verfügbarer RAM
* geschätzter Modellbedarf
* Kontextgröße
* maximale Parallelität
* Warteschlangenlänge
* bereits geladene Modelle
* gewünschte Antwortlänge

Mehrere parallele Generierungen dürfen nicht standardmäßig zugelassen werden.

Die maximale Parallelität muss konfigurierbar sein.

OOM-Fehler dürfen nicht ungefiltert zum Absturz der Anwendung führen.

Bei Speicherfehlern muss:

1. die Generierung kontrolliert beendet werden,
2. der Fehler protokolliert werden,
3. der Modellstatus geprüft werden,
4. gegebenenfalls Speicher bereinigt werden,
5. eine strukturierte Fehlermeldung erzeugt werden.

---

## 13. Modellwechsel

Ein Modellwechsel darf nicht nur durch Änderung von `is_active` in der Datenbank erfolgen.

Vorgeschriebener Ablauf:

```text
1. Modellwechsel sperren
2. Konfiguration prüfen
3. Modell laden
4. Health-Check ausführen
5. kurze Test-Inferenz durchführen
6. Laufzeitstatus aktualisieren
7. Datenbankstatus aktualisieren
8. altes Modell entladen
9. Speicher bereinigen
10. Ereignis veröffentlichen
```

Wenn das neue Modell nicht geladen werden kann, ist ein Rollback zu versuchen.

Das bisherige Modell darf nicht endgültig verworfen werden, bevor der Zustand des neuen Modells geklärt ist, sofern der verfügbare Speicher dies erlaubt.

---

## 14. Tokenmanagement

Kontextgrenzen dürfen nicht anhand von Zeichenanzahl geschätzt werden, wenn ein geeigneter Tokenizer verfügbar ist.

Der aktive Modell-Tokenizer hat Vorrang.

Das Tokenbudget muss mindestens folgende Bestandteile berücksichtigen:

* System-Prompt
* Entwickler-Prompt
* Chatverlauf
* Zusammenfassungen
* Wissensfragmente
* Tool-Definitionen
* Benutzeranfrage
* Antwortreserve
* Sicherheitsreserve

Die Antwortreserve ist vor dem Aufbau des restlichen Kontexts abzuziehen.

System-Prompts und aktuelle Benutzeranfragen dürfen nicht unkontrolliert abgeschnitten werden.

---

## 15. Kürzung des Kontexts

Die Kürzungsreihenfolge lautet grundsätzlich:

1. irrelevante Wissensfragmente entfernen,
2. nicht benötigte Tool-Beschreibungen entfernen,
3. ältere Chatnachrichten zusammenfassen,
4. ältere Nachrichten entfernen,
5. Metadaten reduzieren,
6. Benutzer über verbleibende Einschränkungen informieren.

Aktuelle Nachrichten haben Vorrang vor alten Nachrichten.

Eine Zusammenfassung darf den ursprünglichen Inhalt nicht als exakte Wiedergabe darstellen.

---

## 16. Wissensdatenbank

Dokumente müssen nachvollziehbar verarbeitet werden.

Zu speichern sind mindestens:

* Quelle
* Dateipfad oder Ursprungskennung
* Prüfsumme
* Dokumenttyp
* Benutzer- oder Teamzuordnung
* Importstatus
* Parser
* Chunk-Index
* Embedding-Modell
* Erstellungs- und Aktualisierungsdatum

Doppelte Dokumente oder identische Chunks sind über Prüfsummen zu erkennen.

Bestehende Embeddings dürfen nicht ohne Prüfung neu erzeugt werden.

Wenn sich das Embedding-Modell ändert, müssen betroffene Embeddings versioniert oder neu erstellt werden.

---

## 17. Hybrid-Suche

Die Wissenssuche soll nicht ausschließlich auf Vektorsuche beruhen.

Wenn vorgesehen, sind zu kombinieren:

* semantische Vektorsuche
* Schlüsselwortsuche
* FTS5 oder PostgreSQL Full Text Search
* optionaler Reranker

Exakte technische Begriffe, Nummern, Namen und Aktenzeichen müssen durch die Schlüsselwortsuche auffindbar bleiben.

Gewichtungen müssen konfigurierbar sein.

---

## 18. OCR-Regeln

OCR ist nur einzusetzen, wenn keine ausreichend brauchbare Textextraktion möglich ist.

Ablauf:

```text
1. native Textextraktion versuchen
2. Textmenge prüfen
3. Textqualität prüfen
4. nur bei Bedarf OCR ausführen
```

OCR-Ergebnisse dürfen nicht ungeprüft als fehlerfrei behandelt werden.

Originaltext, extrahierter Text und OCR-Text müssen nachvollziehbar bleiben.

OCR darf nicht bei jedem Import automatisch mehrfach ausgeführt werden.

---

## 19. Fehlerbehandlung

Es sind projektspezifische Exceptions zu verwenden.

Beispiele:

* `ModelLoadError`
* `ModelNotAvailableError`
* `ModelOutOfMemoryError`
* `ContextOverflowError`
* `KnowledgeRetrievalError`
* `InvalidSettingError`
* `PermissionDeniedError`
* `BackendUnavailableError`

Keine pauschalen Fehlerbehandlungen wie:

```python
except Exception:
    return None
```

Fehler dürfen nicht stillschweigend verschluckt werden.

Jeder behandelte Fehler muss je nach Bedeutung:

* protokolliert,
* weitergereicht,
* in einen fachlichen Fehler umgewandelt,
* oder nachvollziehbar ignoriert werden.

Technische Stacktraces dürfen nicht ungefiltert an Benutzer ausgegeben werden.

---

## 20. Wiederholungen und Retries

Retries sind nur bei wahrscheinlich vorübergehenden Fehlern zulässig.

Geeignet:

* Netzwerk-Timeout
* temporär nicht erreichbarer Dienst
* vorübergehend gesperrte Datenbank
* kurzzeitig unterbrochene Remote-Verbindung

Nicht geeignet:

* ungültiger Modellpfad
* nicht unterstütztes Modellformat
* fehlende Berechtigung
* dauerhaft zu kleiner VRAM
* ungültige Eingabedaten
* zu großer Kontext

Retries müssen begrenzt sein und exponentielles Backoff verwenden.

Kein Agent darf Endlosschleifen oder unbegrenzte Wiederholungen einführen.

---

## 21. Ereignisse

Komponenten sollen über das zentrale Event-System gekoppelt werden, wenn eine direkte Abhängigkeit nicht erforderlich ist.

Beispiele:

* `model_loaded`
* `model_unloaded`
* `model_load_failed`
* `knowledge_import_progress`
* `knowledge_import_finished`
* `settings_updated`
* `token_warning`
* `context_truncated`

Keine zweite unabhängige Event-Bus-Implementierung erstellen.

Events müssen klar benannt und dokumentiert sein.

Event-Payloads benötigen definierte Schemas.

---

## 22. Streaming und SSE

Streaming-Antworten müssen:

* kontrolliert abgebrochen werden können,
* Client-Abbrüche erkennen,
* Fehler sauber melden,
* nach Abschluss korrekt gespeichert werden,
* unvollständige Antworten kennzeichnen.

SSE-Verbindungen dürfen keine unbegrenzten Ressourcen binden.

Für Keepalive, Verbindungsabbau und Timeouts sind definierte Regeln zu verwenden.

---

## 23. Sicherheit

Sicherheitsrelevante Prüfungen dürfen nicht allein dem Frontend überlassen werden.

Das Backend muss prüfen:

* Benutzerrechte
* Teamzugehörigkeit
* Dateipfade
* erlaubte Dateitypen
* Dateigröße
* Modellpfade
* Tool-Berechtigungen
* API-Zugriffe
* administrative Einstellungen

## Pfadsicherheit

Benutzereingaben dürfen nicht ungeprüft als Dateipfade verwendet werden.

Path-Traversal muss verhindert werden.

Nicht zulässig:

```python
path = base_directory / user_input
```

ohne anschließende Prüfung, ob der aufgelöste Pfad innerhalb des erlaubten Basisverzeichnisses liegt.

## Geheimnisse

Nicht speichern oder protokollieren:

* Klartextpasswörter
* API-Schlüssel
* vollständige Zugriffstoken
* Session-Secrets
* private Schlüssel

Geheimnisse dürfen nicht in Fehlermeldungen, Logs oder Audit-Daten erscheinen.

---

## 24. Tool-Ausführung

Werkzeuge benötigen eine definierte Berechtigungsprüfung.

Gefährliche Werkzeuge sind standardmäßig deaktiviert.

Dazu gehören:

* Shell-Ausführung
* Python-Codeausführung
* Dateiänderungen außerhalb erlaubter Verzeichnisse
* Dateilöschung
* beliebige SQL-Schreibzugriffe
* Netzwerkzugriff auf beliebige Ziele
* Versenden von Nachrichten oder E-Mails

Tool-Aufrufe müssen nachvollziehbar protokolliert werden.

Kein Agent darf Schutzprüfungen umgehen, um eine Funktion schneller umzusetzen.

---

## 25. Logging

Es ist das zentrale Logging-System zu verwenden.

Nicht zulässig:

```python
print("Model loaded")
```

für produktive Statusmeldungen.

Stattdessen:

```python
logger.info(
    "model_loaded",
    extra={"model_id": model_id},
)
```

Logs sollen ausreichend Kontext enthalten, aber keine vertraulichen Inhalte unnötig speichern.

Nicht vollständig protokollieren:

* komplette private Chatverläufe
* Passwörter
* Zugangstoken
* vertrauliche Dokumente
* vollständige Prompts mit sensiblen Daten

---

## 26. Audit-Log

Administrative und sicherheitsrelevante Änderungen müssen im Audit-Log gespeichert werden.

Beispiele:

* Modellverzeichnis geändert
* aktives Modell geändert
* Prompt geändert
* Wissen gelöscht
* Benutzerrechte geändert
* globale Einstellung geändert
* gefährliches Werkzeug ausgeführt

Das Audit-Log darf nicht als allgemeines Debug-Log missbraucht werden.

---

## 27. Codequalität

Der Code muss:

* verständlich benannt,
* typisiert,
* modular,
* testbar,
* nachvollziehbar,
* möglichst frei von Seiteneffekten

sein.

## Typisierung

Neue öffentliche Funktionen und Methoden benötigen Typannotationen.

Beispiel:

```python
async def get_conversation(
    conversation_id: int,
    user_id: int,
) -> Conversation:
    ...
```

Unbegründetes `Any` ist zu vermeiden.

## Funktionsgröße

Große Funktionen sind aufzuteilen, wenn sie mehrere unterschiedliche Verantwortlichkeiten übernehmen.

## Benennung

Bezeichnungen müssen die tatsächliche Funktion ausdrücken.

Nicht geeignet:

```text
helper.py
utils2.py
manager_new.py
temp_service.py
data_handler.py
```

Geeignet:

```text
token_budget.py
model_lifecycle.py
knowledge_retriever.py
settings_validator.py
```

---

## 28. Kommentare und Dokumentation

Kommentare sollen erklären, warum etwas notwendig ist.

Kommentare sollen nicht lediglich den Code wiederholen.

Nicht sinnvoll:

```python
# Add one
value += 1
```

Sinnvoll:

```python
# Ein zusätzlicher Token wird für das Backend-spezifische
# Nachrichtenende reserviert.
value += 1
```

Öffentliche Schnittstellen und komplexe Komponenten benötigen Docstrings.

Architekturentscheidungen mit langfristigen Folgen sollen dokumentiert werden.

---

## 29. Keine erfundenen Funktionen

Agenten dürfen keine Bibliotheksfunktionen, Parameter oder APIs erfinden.

Vor Verwendung externer Bibliotheken ist zu prüfen:

* ist das Paket bereits installiert?
* passt die verwendete Version?
* existiert die Methode tatsächlich?
* ist die Funktion synchron oder asynchron?
* ist sie für das Zielbetriebssystem geeignet?

Unsichere oder unbestätigte Annahmen müssen kenntlich gemacht und geprüft werden.

---

## 30. Abhängigkeiten

Neue Pakete dürfen nur ergänzt werden, wenn sie wirklich erforderlich sind.

Vor Hinzufügen einer Abhängigkeit ist zu prüfen:

1. Kann die Standardbibliothek die Aufgabe übernehmen?
2. Ist bereits eine passende Abhängigkeit vorhanden?
3. Wird das Paket aktiv gepflegt?
4. Ist die Lizenz geeignet?
5. Gibt es bekannte Sicherheitsprobleme?
6. Ist das Paket mit Windows und Linux kompatibel?
7. Erhöht es das Konfliktrisiko bei CUDA oder PyTorch?

Neue Abhängigkeiten müssen in:

* `pyproject.toml`,
* `requirements.txt`,
* oder der vorgesehenen Abhängigkeitsverwaltung

eingetragen und dokumentiert werden.

---

## 31. Plattformkompatibilität

Das Projekt soll grundsätzlich unter Windows und Linux lauffähig bleiben.

Zu vermeiden:

* fest kodierte Windows-Pfade
* fest kodierte Linux-Pfade
* Shell-Befehle ohne Plattformprüfung
* ausschließlich Bash-basierte Kernfunktionen
* Annahmen über verfügbare Laufwerke

Für Dateipfade ist `pathlib` zu verwenden.

Für Startskripte können getrennte Dateien bestehen:

```text
start_server.sh
start_server.ps1
```

Die Kernlogik darf nicht von einem bestimmten Shell-System abhängen.

---

## 32. Asynchronität

`async` darf nicht nur formal verwendet werden.

Nicht zulässig:

```python
async def load_model():
    model.load()
```

wenn `model.load()` lange blockiert.

Blockierende Funktionen müssen in geeignete Worker ausgelagert werden.

Datenbankzugriffe sollen bei Verwendung des asynchronen SQLAlchemy-Stacks ebenfalls asynchron erfolgen.

Synchrone und asynchrone Datenbankzugriffe dürfen nicht unkontrolliert vermischt werden.

---

## 33. Transaktionen

Zusammengehörende Datenbankänderungen müssen transaktional ausgeführt werden.

Beispiel:

```text
Unterhaltung erstellen
erste Nachricht speichern
Modellzuordnung speichern
Audit-Eintrag schreiben
```

Wenn ein Vorgang nur vollständig sinnvoll ist, darf kein unvollständiger Zwischenzustand gespeichert bleiben.

Transaktionen dürfen nicht unnötig lange während einer Modellinferenz offen bleiben.

---

## 34. Tests

Jede neue oder geänderte Funktion benötigt angemessene Tests.

Mindestens zu prüfen:

* Normalfall
* ungültige Eingabe
* fehlende Daten
* Berechtigungsfehler
* Backendfehler
* Grenzwerte
* Abbruchverhalten

## Testarten

### Unit-Tests

Für isolierte Logik:

* Tokenberechnung
* Settings-Auflösung
* Pfadvalidierung
* Chunking
* Retry-Logik
* Modellmetadaten-Erkennung

### Integrationstests

Für:

* API und Datenbank
* Modellwechsel
* Wissensimport
* Migrationen
* Settings-Hot-Reload
* Streaming

### Performance-Tests

Für:

* Time to First Token
* Tokens pro Sekunde
* RAM-Verbrauch
* VRAM-Verbrauch
* parallele Anfragen
* Warteschlangenverhalten

Tests dürfen nicht nur deshalb entfernt oder abgeschwächt werden, weil eine Änderung sie fehlschlagen lässt.

---

## 35. Testisolierung

Tests dürfen nicht:

* produktive Datenbanken verändern,
* echte Benutzerdaten verwenden,
* reale Modellverzeichnisse löschen,
* unbeabsichtigt große Modelle herunterladen,
* externe kostenpflichtige APIs aufrufen.

Externe Dienste und große Modelle sind nach Möglichkeit zu mocken oder durch kleine Testmodelle zu ersetzen.

GPU-Tests müssen klar markiert sein.

Beispiel:

```python
@pytest.mark.gpu
def test_model_gpu_loading():
    ...
```

---

## 36. Datenmigration und Rückwärtskompatibilität

Bei Änderungen bestehender Datenstrukturen ist zu prüfen:

* können vorhandene Daten weiterverwendet werden?
* ist eine Migration nötig?
* ist ein Rollback möglich?
* ändern sich API-Antworten?
* sind alte Konfigurationen weiterhin gültig?

Breaking Changes müssen ausdrücklich dokumentiert werden.

---

## 37. API-Regeln

API-Endpunkte sollen konsistent benannt werden.

Beispiele:

```text
GET    /api/models
POST   /api/models/scan
POST   /api/models/{id}/load
POST   /api/models/{id}/unload

GET    /api/conversations
POST   /api/conversations
GET    /api/conversations/{id}
DELETE /api/conversations/{id}
```

Fehlerantworten verwenden ein einheitliches Format.

Beispiel:

```json
{
  "error": {
    "code": "MODEL_NOT_AVAILABLE",
    "message": "Das ausgewählte Modell ist nicht verfügbar.",
    "retryable": false,
    "details": null
  }
}
```

Keine uneinheitlichen Rückgaben wie:

```json
{"detail": "error"}
```

an einer Stelle und:

```json
{"message": "failed"}
```

an einer anderen Stelle, sofern ein zentrales Fehlerformat vorgesehen ist.

---

## 38. Frontend-Regeln

Das Frontend darf keine Backendregeln duplizieren.

Das Frontend kann Werte vorvalidieren, aber das Backend bleibt verbindlich.

API-Aufrufe gehören in zentrale Services oder Clients.

Nicht zulässig:

* dieselbe API-Logik in mehreren Komponenten
* direkte URLs in vielen Dateien
* uneinheitliche Fehlerauswertung
* unkontrollierter globaler Zustand

Modellstatus, Ladefortschritt und Importfortschritt sollen über zentrale Stores verwaltet werden.

---

## 39. Keine unkontrollierten globalen Zustände

Globale Singleton-Objekte sind nur zulässig, wenn ihr Lebenszyklus bewusst verwaltet wird.

Besonders kritisch:

* geladenes Modell
* Datenbanksession
* Event-Loop
* Executor
* Queue
* Cache

Diese Komponenten sollen über den Application-Lifespan initialisiert und sauber beendet werden.

---

## 40. Anwendungsstart und Beendigung

Beim Start:

1. Konfiguration laden,
2. Logging initialisieren,
3. Datenbankverbindung prüfen,
4. Migrationen prüfen,
5. Standardwerte anlegen,
6. Standard-Prompts anlegen,
7. Event-System starten,
8. Queue und Worker starten,
9. Modellregistry laden,
10. optional aktives Modell laden.

Beim Beenden:

1. neue Anfragen stoppen,
2. laufende Aufgaben kontrolliert beenden,
3. Streams schließen,
4. Modell entladen,
5. Executor beenden,
6. Queue schließen,
7. Datenbankverbindungen schließen,
8. Logs abschließen.

---

## 41. Änderungen an bestehendem Code

Vor jeder Änderung muss der Agent prüfen:

* welche Aufrufer existieren?
* welche Tests sind betroffen?
* welche Schemas sind betroffen?
* welche Datenbankmigration ist nötig?
* welche Dokumentation muss angepasst werden?
* kann die Änderung bestehende Konfigurationen beschädigen?

Refactorings dürfen das Verhalten nicht unbeabsichtigt verändern.

Wenn Verhalten geändert wird, muss dies ausdrücklich benannt werden.

---

## 42. Verbotene Schnelllösungen

Nicht zulässig:

* Fehler durch pauschale `try/except`-Blöcke verstecken
* Typfehler mit dauerhaftem `# type: ignore` unterdrücken
* Linterfehler ohne Begründung deaktivieren
* Tests löschen, weil sie fehlschlagen
* feste Pfade eintragen
* Zugangsdaten in den Quellcode schreiben
* Datenbanktabellen beim Start löschen
* Modellzustände nur in globalen Variablen speichern
* blockierende Inferenz direkt im Event-Loop ausführen
* Benutzerrechte nur im Frontend prüfen
* ungesicherte Shell-Ausführung ergänzen
* beliebige Dateien aus externen Quellen ausführen
* unbekannte Daten mit `pickle` laden
* SQL-Abfragen aus Benutzereingaben zusammensetzen

---

## 43. Sicherheitskritische Dateiformate

Unsichere Serialisierungsformate sind kritisch zu behandeln.

Insbesondere `pickle`, unsichere PyTorch-Dateien und unbekannte Modellartefakte können ausführbaren Code enthalten.

Sicherere Formate haben Vorrang:

* GGUF
* Safetensors
* JSON
* klar validierte Textformate

Dateien aus unbekannten Quellen dürfen nicht automatisch ausgeführt oder unsicher deserialisiert werden.

---

## 44. Dokumentation nach Änderungen

Nach relevanten Änderungen sind gegebenenfalls anzupassen:

* `README.md`
* `CHANGELOG.md`
* `ROADMAP.md`
* API-Dokumentation
* Datenbankschema
* Architekturübersicht
* Beispielkonfiguration
* `.env.example`
* Installationsanleitung
* Migrationshinweise

Neue Einstellungen müssen dokumentiert werden mit:

* Kategorie
* Schlüssel
* Datentyp
* Standardwert
* zulässige Werte
* Wirkung
* Neustart- oder Reload-Anforderung

---

## 45. Änderungsprotokoll

Jede abgeschlossene Änderung soll nachvollziehbar beschrieben werden.

Eine sinnvolle Zusammenfassung enthält:

```text
Geänderte Dateien
Umgesetzte Funktion
Architekturentscheidung
Datenbankänderungen
Neue Abhängigkeiten
Ausgeführte Tests
Offene Einschränkungen
```

Keine Behauptung, dass Tests erfolgreich seien, wenn sie nicht ausgeführt wurden.

Wenn Tests nicht ausgeführt werden konnten, muss dies offen angegeben werden.

---

## 46. Arbeitsweise eines Agenten

Ein Agent soll bei größeren Aufgaben in dieser Reihenfolge arbeiten:

```text
1. Aufgabe verstehen
2. Repository analysieren
3. bestehende Regeln lesen
4. betroffene Module bestimmen
5. Lösung entwerfen
6. kleine, nachvollziehbare Änderungen durchführen
7. Typprüfung ausführen
8. Tests ausführen
9. Fehler korrigieren
10. Dokumentation aktualisieren
11. Änderungen zusammenfassen
```

Keine großflächige Neuerstellung des Projekts, wenn gezielte Änderungen ausreichen.

---

## 47. Umgang mit Unsicherheit

Wenn Informationen fehlen, darf ein Agent nicht stillschweigend riskante Annahmen treffen.

Bei kleineren Unsicherheiten ist die sicherste bestehende Konvention zu verwenden.

Bei architekturrelevanten Unsicherheiten soll der Agent:

* die Annahme ausdrücklich dokumentieren,
* eine reversible Lösung wählen,
* keine produktiven Daten gefährden,
* keine neue Parallelarchitektur schaffen.

---

## 48. Prioritäten bei Konflikten

Bei widersprüchlichen Zielen gilt folgende Priorität:

```text
1. Sicherheit
2. Datenintegrität
3. korrekte Funktion
4. bestehende Architektur
5. Wartbarkeit
6. Testbarkeit
7. Performance
8. Entwicklungsaufwand
9. Bequemlichkeit
```

Performanceoptimierungen dürfen Sicherheit und Datenintegrität nicht verschlechtern.

---

## 49. Definition of Done

Eine Aufgabe gilt erst als abgeschlossen, wenn:

* der Code fachlich umgesetzt ist,
* die Architektur eingehalten wurde,
* Typannotationen vorhanden sind,
* Fehlerfälle behandelt werden,
* Tests ergänzt oder angepasst wurden,
* relevante Tests erfolgreich ausgeführt wurden,
* Datenbankänderungen migriert wurden,
* Dokumentation aktualisiert wurde,
* keine Zugangsdaten enthalten sind,
* keine offensichtlichen Sicherheitsprobleme entstanden sind,
* die Änderung verständlich zusammengefasst wurde.

---

## 50. Mindestprüfung vor Abschluss

Vor Abschluss einer Änderung muss der Agent mindestens prüfen:

```text
Sind direkte SQL-Zugriffe in API-Routen entstanden?
Wurde ein Pfad hart codiert?
Wurde blockierende Logik in async-Code eingefügt?
Wurden Rechteprüfungen vergessen?
Wurde eine Migration benötigt?
Wurde bestehende Logik dupliziert?
Wurden Tests tatsächlich ausgeführt?
Wurden sensible Daten protokolliert?
Wurde eine neue Abhängigkeit begründet?
Ist die Lösung unter Windows und Linux plausibel?
```

---

## 51. Projektbezogene Standardentscheidung

Wenn keine andere Entscheidung dokumentiert ist, gelten folgende Standards:

```text
Python:
3.12 oder die im Projekt festgelegte Version

Backend:
FastAPI

Validierung:
Pydantic 2

ORM:
SQLAlchemy 2

Migrationen:
Alembic

Entwicklungsdatenbank:
SQLite

Produktivdatenbank:
PostgreSQL

Vektorsuche:
pgvector oder konfigurierbarer lokaler Index

Lokales erstes Modell-Backend:
llama-cpp-python

Dateipfade:
pathlib.Path

Tests:
pytest

Codeformatierung:
Ruff

Typprüfung:
mypy oder pyright gemäß Projektkonfiguration

Frontend:
React und TypeScript
```

Diese Standards dürfen geändert werden, wenn eine dokumentierte technische Begründung vorliegt.

---

## 52. Gültigkeit

Diese Regeln sind verbindlich.

Ein Agent darf sie nicht:

* umgehen,
* stillschweigend abschwächen,
* teilweise ignorieren,
* durch eine eigene Parallelregel ersetzen.

Abweichungen sind nur zulässig, wenn:

1. sie technisch notwendig sind,
2. die Gründe dokumentiert werden,
3. Sicherheit und Datenintegrität erhalten bleiben,
4. die Abweichung möglichst klein bleibt.

Bei Zweifeln ist die konservativere und besser überprüfbare Lösung zu wählen.
