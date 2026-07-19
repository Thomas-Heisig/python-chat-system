# 📅 Calendar Plugin

**ID:** `calendar`  
**Kategorie:** 📱 Social & Communication  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Calendar-Plugin ermöglicht die **Terminplanung und Kalenderverwaltung**. Es unterstützt:

- **Lokale Terminverwaltung** (ohne externe API) – perfekt für Entwicklung und Test
- **Google Calendar-Integration** (über Google Calendar API) – für den Produktivbetrieb
- **Termine anzeigen, erstellen und löschen**

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(termin|kalender|beratung|besichtigung|vorort|meeting|appointment)\b
```

**Beispiele:**

- _"Ich möchte einen Termin vereinbaren."_
- _"Zeige mir meine Termine für heute."_
- _"Kannst du einen Besichtigungstermin für nächste Woche erstellen?"_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable                     | Beschreibung                              | Standard                 | Erforderlich                |
| ---------------------------- | ----------------------------------------- | ------------------------ | --------------------------- |
| `CALENDAR_STORAGE_PATH`      | Pfad zur lokalen JSON-Speicherdatei       | `./calendar_events.json` | ❌                          |
| `GOOGLE_CALENDAR_API_KEY`    | Google Calendar API-Key                   | –                        | ❌ (für Google-Integration) |
| `GOOGLE_CALENDAR_ID`         | Google Calendar-ID (z.B. `primary`)       | `primary`                | ❌                          |
| `GOOGLE_OAUTH_CLIENT_ID`     | OAuth2-Client-ID (für Schreibzugriff)     | –                        | ❌                          |
| `GOOGLE_OAUTH_CLIENT_SECRET` | OAuth2-Client-Secret (für Schreibzugriff) | –                        | ❌                          |

> **Hinweis:** Für Lesezugriff auf Google Calendar reicht ein API-Key. Für Schreibzugriff (Termine erstellen/löschen) wird OAuth2 benötigt.

---

## 📦 Input-Schema

```json
{
  "action": "list | create | delete",
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "title": "Termintitel",
  "description": "Beschreibung (optional)",
  "duration_minutes": 60,
  "event_id": "ID des zu löschenden Termins"
}
```

### Aktionen im Detail

| Aktion       | Erforderliche Felder    | Beschreibung                                  |
| ------------ | ----------------------- | --------------------------------------------- |
| **`list`**   | `date` (optional)       | Zeigt alle Termine für ein Datum (oder heute) |
| **`create`** | `date`, `time`, `title` | Erstellt einen neuen Termin                   |
| **`delete`** | `event_id`              | Löscht einen Termin anhand seiner ID          |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "message": "1 Termin(e) für 2026-06-28:",
  "events": [
    {
      "id": "local_1234567890",
      "date": "2026-06-28",
      "time": "14:00",
      "title": "Beratung Heishg Naturstein",
      "description": "Besprechung zur Küchenarbeitsplatte",
      "duration_minutes": 60,
      "created_at": "2026-06-28T10:00:00"
    }
  ],
  "event_id": "local_1234567890"
}
```

**Bei Fehlern:**

```json
{
  "success": false,
  "error": "Ungültiges Datumsformat. Verwende YYYY-MM-DD."
}
```

---

## 🧪 Beispiele

### 1. Termine für heute anzeigen

**Input:**

```json
{
  "action": "list"
}
```

**Output (lokal):**

```
✅ 2 Termin(e) für 2026-06-28:
- 10:00 - Angebotserstellung Müller (60 Min)
- 14:00 - Besichtigung Mustermann (90 Min)
```

### 2. Termin erstellen (lokal)

**Input:**

```json
{
  "action": "create",
  "date": "2026-06-30",
  "time": "15:00",
  "title": "Beratung Heishg Naturstein",
  "description": "Küchenarbeitsplatte Granit",
  "duration_minutes": 60
}
```

**Output:**

```
✅ Termin 'Beratung Heishg Naturstein' am 2026-06-30 um 15:00 erstellt.
ID: local_1234567890
```

### 3. Google Calendar Termine abrufen

**Input:**

```json
{
  "action": "list",
  "date": "2026-06-28"
}
```

**Output (Google Calendar):**

```
✅ 3 Termin(e) für 2026-06-28:
- 09:00 - Team Meeting (60 Min)
- 11:00 - Projektbesprechung (90 Min)
- 15:00 - Kundenberatung (60 Min)
```

### 4. Termin löschen

**Input:**

```json
{
  "action": "delete",
  "event_id": "local_1234567890"
}
```

**Output:**

```
✅ Termin local_1234567890 gelöscht.
```

---

## 🏗️ Lokale Speicherung (JSON)

Das Plugin speichert Termine standardmäßig lokal in einer JSON-Datei:

**Speicherort:** `./calendar_events.json` (konfigurierbar über `CALENDAR_STORAGE_PATH`)

**Format:**

```json
[
  {
    "id": "local_1234567890",
    "date": "2026-06-28",
    "time": "14:00",
    "title": "Beratung Heishg Naturstein",
    "description": "Küchenarbeitsplatte Granit",
    "duration_minutes": 60,
    "created_at": "2026-06-28T10:00:00"
  }
]
```

---

## 🔗 Google Calendar-Integration

### Voraussetzungen

1. **Google Cloud Project** erstellen
2. **Google Calendar API** aktivieren
3. **API-Key** generieren (für Lesezugriff)
4. **OAuth2-Credentials** erstellen (für Schreibzugriff)

### Einrichtung

```bash
# Lesezugriff (API-Key)
export GOOGLE_CALENDAR_API_KEY="AIzaSy..."
export GOOGLE_CALENDAR_ID="primary"

# Schreibzugriff (OAuth2)
export GOOGLE_OAUTH_CLIENT_ID="...apps.googleusercontent.com"
export GOOGLE_OAUTH_CLIENT_SECRET="..."
```

### Funktionsumfang

| Funktion          | Lokal | Google Calendar          |
| ----------------- | ----- | ------------------------ |
| Termine anzeigen  | ✅    | ✅                       |
| Termin erstellen  | ✅    | ⚠️ (OAuth2 erforderlich) |
| Termin löschen    | ✅    | ⚠️ (OAuth2 erforderlich) |
| Termin bearbeiten | ⬜    | ⬜ (geplant)             |

---

## 🚀 Nächste Erweiterungen (geplant)

- [ ] Terminbearbeitung (`action: update`)
- [ ] Erinnerungen (Push, E-Mail)
- [ ] Terminbestätigung per Link
- [ ] Wochentag-Ansicht
- [ ] Serientermine

---

## 📁 Datei-Struktur

```
packages/plugins/calendar/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "API-Key ungültig oder keine Berechtigung"

**Lösung:**

1. Prüfe, ob der Google Calendar API-Key korrekt ist.
2. Stelle sicher, dass die Google Calendar API im Cloud Project aktiviert ist.
3. Prüfe, ob die Google Calendar-ID korrekt ist (z.B. `primary` oder die E-Mail-Adresse des Kalenders).

### Fehler: "Kalender nicht gefunden"

**Lösung:**

1. Prüfe `GOOGLE_CALENDAR_ID`.
2. Verwende `primary` für den Hauptkalender oder die E-Mail-Adresse des Kalenders.

### Fehler: "Termin nicht gefunden" (bei Delete)

**Lösung:**

1. Prüfe, ob die `event_id` korrekt ist.
2. Termin existiert möglicherweise nicht mehr oder wurde bereits gelöscht.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Ich möchte einen Beratungstermin für nächsten Mittwoch um 14 Uhr vereinbaren."_
>
> **Elisa:** _"Ich habe einen Termin am 2026-07-05 um 14:00 für dich erstellt. Möchtest du eine Erinnerung per E-Mail?"_

> **Nutzer:** _"Zeige mir meine Termine für heute."_
>
> **Elisa:** _"Du hast heute 2 Termine: 10:00 – Angebotserstellung, 14:00 – Besichtigung."_

---

## 📚 Siehe auch

- [Google Calendar API Dokumentation](https://developers.google.com/calendar/api)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
