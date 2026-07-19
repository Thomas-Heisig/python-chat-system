# 📄 Lead Capture Plugin

**ID:** `lead_capture`  
**Kategorie:** 📱 Social & Communication  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Lead Capture Plugin ermöglicht die **Erfassung und Speicherung von Kundenkontakten** (Leads). Es unterstützt:

- **Lokale Speicherung** in einer JSON-Datei (Standard)
- **Optionale HubSpot-Integration** (wenn API-Key konfiguriert)
- **Flexible Felder** (Name, E-Mail, Telefon, Nachricht, Quelle, Status, Tags, Notizen, Adresse, Firma, Projekt, Interessen)

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(kontakt|adresse|telefon|email|lead|anfrage|interessent|kunde|beratung|termin|besichtigung)\b
```

**Beispiele:**

- _"Speichere den Kunden Max Mustermann mit E-Mail <max@mustermann.de>."_
- _"Erfasse einen neuen Lead für ein Granit-Angebot."_
- _"Speichere die Anfrage von Kunde für Arbeitsplatte."_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable            | Beschreibung                        | Erforderlich                  |
| ------------------- | ----------------------------------- | ----------------------------- |
| `LEAD_STORAGE_PATH` | Pfad zur JSON-Speicherdatei         | ❌ (Standard: `./leads.json`) |
| `HUBSPOT_API_KEY`   | HubSpot API-Key für CRM-Integration | ❌ (nur für HubSpot)          |

---

## 📦 Input-Schema

```json
{
  "name": "Max Mustermann",
  "email": "max@mustermann.de",
  "phone": "+49 170 1234567",
  "message": "Ich interessiere mich für Granit-Arbeitsplatten.",
  "source": "chat",
  "status": "new",
  "tags": ["granit", "küche"],
  "notes": "Kunde sucht schwarzen Granit",
  "address": "Musterstraße 1, 12345 Berlin",
  "company": "Mustermann GmbH",
  "project": "Küchenrenovierung",
  "interest": ["granit", "marmor"]
}
```

| Feld       | Typ    | Beschreibung                                                                         |
| ---------- | ------ | ------------------------------------------------------------------------------------ |
| `name`     | string | Name des Kunden (erforderlich)                                                       |
| `email`    | string | E-Mail-Adresse                                                                       |
| `phone`    | string | Telefonnummer                                                                        |
| `message`  | string | Nachricht oder Anfrage                                                               |
| `source`   | string | Quelle (`chat`, `website`, `email`, `phone`, `referral`, `event`, `social`, `other`) |
| `status`   | string | Status (`new`, `contacted`, `qualified`, `lost`, `converted`)                        |
| `tags`     | array  | Tags für Kategorisierung                                                             |
| `notes`    | string | Zusätzliche Notizen                                                                  |
| `address`  | string | Adresse                                                                              |
| `company`  | string | Firmenname                                                                           |
| `project`  | string | Projektbeschreibung                                                                  |
| `interest` | array  | Interessen des Kunden                                                                |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "lead_id": "abc12345",
  "message": "Lead 'Max Mustermann' wurde erfolgreich erfasst.",
  "lead": {
    "id": "abc12345",
    "name": "Max Mustermann",
    "email": "max@mustermann.de",
    "phone": "+49 170 1234567",
    "message": "Ich interessiere mich für Granit-Arbeitsplatten.",
    "source": "chat",
    "status": "new",
    "tags": ["granit", "küche"],
    "notes": "Kunde sucht schwarzen Granit",
    "address": "Musterstraße 1, 12345 Berlin",
    "company": "Mustermann GmbH",
    "project": "Küchenrenovierung",
    "interest": ["granit", "marmor"],
    "created_at": "2026-06-28T10:00:00Z",
    "updated_at": "2026-06-28T10:00:00Z"
  },
  "hubspot": {
    "status": "success",
    "message": "Lead an HubSpot gesendet."
  }
}
```

**Bei Fehlern:**

```json
{
  "success": false,
  "error": "Name ist erforderlich."
}
```

---

## 🧪 Beispiele

### 1. Einfacher Lead erfassen

**Input:**

```json
{
  "name": "Max Mustermann",
  "email": "max@mustermann.de",
  "phone": "+49 170 1234567",
  "message": "Ich möchte ein Angebot für Granit-Arbeitsplatten."
}
```

### 2. Lead mit Tags und Interessen

**Input:**

```json
{
  "name": "Anna Schmidt",
  "email": "anna@schmidt.de",
  "message": "Suche Marmor für Badezimmer.",
  "tags": ["marmor", "bad"],
  "interest": ["marmor", "travertin"],
  "source": "website"
}
```

### 3. Lead mit HubSpot-Integration

**Input:** (gleiche Felder, aber `HUBSPOT_API_KEY` in der Umgebung gesetzt)

---

## 📁 Datei-Struktur

```
packages/plugins/lead_capture/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 📁 Speicherort der Leads

Standardmäßig werden Leads in einer JSON-Datei gespeichert:

```
./leads.json
```

**Format:**

```json
[
  {
    "id": "abc12345",
    "name": "Max Mustermann",
    "email": "max@mustermann.de",
    "phone": "+49 170 1234567",
    "message": "...",
    "source": "chat",
    "status": "new",
    "tags": ["granit"],
    "notes": "...",
    "created_at": "2026-06-28T10:00:00Z",
    "updated_at": "2026-06-28T10:00:00Z"
  }
]
```

---

## 🔧 HubSpot-Integration (optional)

Wenn `HUBSPOT_API_KEY` in der Umgebung gesetzt ist, wird jeder Lead automatisch an HubSpot gesendet.

### HubSpot API-Key erstellen

1. Gehe zu **HubSpot** → **Einstellungen** → **Integrationen** → **Private Apps**
2. Erstelle eine Private App mit Scopes:
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
3. Kopiere den Access Token als `HUBSPOT_API_KEY`.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Speichere den Kunden Max Mustermann mit E-Mail <max@mustermann.de> und Telefon 0170 1234567 für ein Granit-Angebot."_
>
> **Elisa:** _"✅ Lead 'Max Mustermann' wurde erfolgreich erfasst. (Lead-ID: abc12345)"_

---

## 📚 Siehe auch

- [HubSpot Plugin](../crm_hubspot)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
