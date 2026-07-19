# 📋 HubSpot CRM Plugin

**ID:** `crm_hubspot`  
**Kategorie:** 📊 Business & Analytics  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das HubSpot CRM Plugin ermöglicht die **Integration Ihres Chat-Systems mit HubSpot CRM**. Es unterstützt:

- **Kontaktverwaltung** – Erstellen, Anzeigen, Suchen und Aktualisieren von Kontakten
- **Deal-Management** – Erstellen und Anzeigen von Deals
- **Aufgabenverwaltung** – Erstellen und Anzeigen von Aufgaben (Tasks)

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(kunde|kontakt|adresse|telefon|email|crm|hubspot|deal|unternehmen)\b
```

**Beispiele:**

- _"Erstelle einen neuen Kontakt für Max Mustermann."_
- _"Suche nach Kunde mit der E-Mail <max@mustermann.de>."_
- _"Erstelle einen neuen Deal für Granit-Angebot."_
- _"Zeige mir alle offenen Aufgaben."_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable          | Beschreibung                     | Erforderlich |
| ----------------- | -------------------------------- | ------------ |
| `HUBSPOT_API_KEY` | HubSpot Private App Access Token | ✅           |

### HubSpot API-Key erstellen

1. Gehe zu **HubSpot** → **Einstellungen** → **Integrationen** → **Private Apps**
2. Erstelle eine neue Private App mit folgenden Scopes:
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
   - `crm.objects.deals.read`
   - `crm.objects.deals.write`
   - `crm.objects.tasks.read`
   - `crm.objects.tasks.write`
3. Kopiere den **Access Token** und setze ihn als `HUBSPOT_API_KEY` in der Umgebung.

---

## 📦 Input-Schema

Das Plugin unterstützt verschiedene Aktionen. Hier sind die wichtigsten:

### Aktionen im Überblick

| Aktion                | Beschreibung               | Erforderliche Felder                                                    |
| --------------------- | -------------------------- | ----------------------------------------------------------------------- |
| **`list_contacts`**   | Listet alle Kontakte       | `limit` (optional)                                                      |
| **`get_contact`**     | Ruft einen Kontakt ab      | `contact_id`                                                            |
| **`create_contact`**  | Erstellt einen Kontakt     | `firstname`, `lastname`, `email`, `phone`, `company` (mindestens eines) |
| **`update_contact`**  | Aktualisiert einen Kontakt | `contact_id` + mindestens ein Feld                                      |
| **`search_contacts`** | Sucht Kontakte             | `query` oder `email`                                                    |
| **`list_deals`**      | Listet alle Deals          | `limit` (optional)                                                      |
| **`create_deal`**     | Erstellt einen Deal        | `deal_name`                                                             |
| **`list_tasks`**      | Listet alle Aufgaben       | `limit` (optional)                                                      |
| **`create_task`**     | Erstellt eine Aufgabe      | `task_title`                                                            |

---

## 📤 Output-Schema

**Erfolg:**

```json
{
  "success": true,
  "message": "Kontakt erstellt.",
  "contact": { ... }
}
```

**Fehler:**

```json
{
  "success": false,
  "error": "HubSpot API-Key nicht konfiguriert."
}
```

---

## 🧪 Beispiele

### 1. Kontakt erstellen

**Input:**

```json
{
  "action": "create_contact",
  "firstname": "Max",
  "lastname": "Mustermann",
  "email": "max@mustermann.de",
  "phone": "+49 170 1234567",
  "company": "Steinwelt GmbH"
}
```

**Output:**

```json
{
  "success": true,
  "message": "Kontakt erstellt.",
  "contact": {
    "id": "123456",
    "properties": {
      "firstname": "Max",
      "lastname": "Mustermann",
      "email": "max@mustermann.de",
      "phone": "+49 170 1234567",
      "company": "Steinwelt GmbH"
    }
  }
}
```

### 2. Kontakt suchen

**Input:**

```json
{
  "action": "search_contacts",
  "email": "max@mustermann.de"
}
```

**Output:**

```json
{
  "success": true,
  "data": [
    {
      "id": "123456",
      "properties": {
        "firstname": "Max",
        "lastname": "Mustermann",
        "email": "max@mustermann.de"
      }
    }
  ],
  "total": 1
}
```

### 3. Deal erstellen

**Input:**

```json
{
  "action": "create_deal",
  "deal_name": "Granit-Angebot für Mustermann",
  "deal_amount": 2500,
  "deal_stage": "qualifiedtobuy"
}
```

**Output:**

```json
{
  "success": true,
  "message": "Deal erstellt.",
  "deal": {
    "id": "789012",
    "properties": {
      "dealname": "Granit-Angebot für Mustermann",
      "amount": 2500,
      "dealstage": "qualifiedtobuy"
    }
  }
}
```

### 4. Aufgabe erstellen

**Input:**

```json
{
  "action": "create_task",
  "task_title": "Beratungstermin Heishg Naturstein",
  "task_description": "Beratung für Küchenarbeitsplatte Granit",
  "task_due_date": "2026-07-05"
}
```

**Output:**

```json
{
  "success": true,
  "message": "Aufgabe erstellt.",
  "task": {
    "id": "345678",
    "properties": {
      "hs_task_subject": "Beratungstermin Heishg Naturstein",
      "hs_task_body": "Beratung für Küchenarbeitsplatte Granit",
      "hs_task_due_date": "2026-07-05",
      "hs_task_status": "NOT_STARTED"
    }
  }
}
```

---

## 📁 Datei-Struktur

```
packages/plugins/crm_hubspot/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── plugin copy.py     # Backup (optional)
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "Ungültiger API-Key"

**Lösung:** Prüfe `HUBSPOT_API_KEY` in der Umgebung. Stelle sicher, dass der Key gültig ist und die richtigen Scopes hat.

### Fehler: "Rate-Limit überschritten"

**Lösung:** Warte einige Minuten und versuche es erneut. HubSpot erlaubt 100 Requests pro 10 Sekunden.

### Fehler: "Ressource nicht gefunden"

**Lösung:** Prüfe die `contact_id` oder `deal_id`. Die ID muss existieren.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Erstelle einen neuen Kontakt für Max Mustermann mit E-Mail <max@mustermann.de> und Telefon 0170 1234567."_
>
> **Elisa:** _"✅ Kontakt erstellt: Max Mustermann (<max@mustermann.de>) wurde in HubSpot hinzugefügt."_

> **Nutzer:** _"Erstelle einen Deal für Granit-Angebot an Mustermann mit 2500 €."_
>
> **Elisa:** _"✅ Deal erstellt: Granit-Angebot für Mustermann (2500 €) wurde in HubSpot hinzugefügt."_

---

## 📚 Siehe auch

- [HubSpot API Dokumentation](https://developers.hubspot.com/docs/api)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
