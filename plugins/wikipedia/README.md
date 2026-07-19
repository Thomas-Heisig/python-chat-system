````markdown
# Wikipedia Plugin

**ID:** `wikipedia`  
**Kategorie:** 🌐 Core / Web  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Wikipedia Plugin ruft **Artikel aus der deutschsprachigen Wikipedia** ab. Es liefert:

- Die **Einleitung** des Artikels (erster Absatz)
- **Reine Textausgabe** (ohne HTML- oder Wiki-Markup)
- Automatische **Weiterleitungsauflösung**

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(wikipedia|wiki|lexikon)\b
```
````

**Beispiele:**

- _"Suche auf Wikipedia nach Granit."_
- _"Was sagt Wikipedia zu Marmor?"_
- _"Wiki-Artikel zu Nero Assoluto."_

---

## ⚙️ Konfiguration

Das Plugin ist **sofort einsatzbereit** – es sind keine Umgebungsvariablen erforderlich.

---

## 📦 Input-Schema

```json
{
  "title": "Granit"
}
```

| Feld    | Typ    | Beschreibung                                |
| ------- | ------ | ------------------------------------------- |
| `title` | string | Titel des Wikipedia-Artikels (erforderlich) |

---

## 📤 Output-Schema

```json
{
  "extract": "Granit ist ein massives, sehr hartes und verwitterungsbeständiges Gestein..."
}
```

**Bei Fehlern:**

```json
{
  "extract": "Seite nicht gefunden."
}
```

---

## 🧪 Beispiele

### 1. Artikel abrufen

**Input:**

```json
{
  "title": "Granit"
}
```

**Output:**

```json
{
  "extract": "Granit ist ein massives, sehr hartes und verwitterungsbeständiges Gestein..."
}
```

### 2. Artikel mit Weiterleitung

**Input:**

```json
{
  "title": "Naturstein"
}
```

**Output:** Der Artikel wird automatisch aufgelöst und die Einleitung zurückgegeben.

### 3. Nicht gefundener Artikel

**Input:**

```json
{
  "title": "NichtExistierenderArtikel"
}
```

**Output:**

```json
{
  "extract": "Seite nicht gefunden."
}
```

---

## 📁 Datei-Struktur

```
packages/plugins/wikipedia/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "Seite nicht gefunden"

**Ursache:** Der angegebene Titel existiert nicht auf der deutschen Wikipedia.

**Lösung:** Prüfe die Schreibweise oder verwende den exakten Titel. Bei Unsicherheit hilft die Wikipedia-Suche.

### Fehler: "Timeout"

**Ursache:** Die Wikipedia-API kann bei hoher Last langsamer sein.

**Lösung:** Wiederhole die Anfrage später.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Was sagt Wikipedia zu Nero Assoluto?"_
>
> **Elisa:** _"Nero Assoluto ist ein schwarzer Granit aus Indien. Er zeichnet sich durch seine feine Körnung und hohe Härte aus..."_

> **Nutzer:** _"Wiki-Artikel zu Marmor."_
>
> **Elisa:** _"Marmor ist ein metamorphes Gestein, das durch Umwandlung von Kalkstein entsteht..."_

---

## 🌍 Andere Sprachen

Möchten Sie die Wikipedia-API auf eine andere Sprache umstellen?

```python
# Englische Wikipedia
"https://en.wikipedia.org/w/api.php"
# Französische Wikipedia
"https://fr.wikipedia.org/w/api.php"
# etc.
```

---

## 📚 Siehe auch

- [Wikipedia API Dokumentation](https://www.mediawiki.org/wiki/API:Main_page)
- [WebSearch Plugin](../websearch)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28

```

```
