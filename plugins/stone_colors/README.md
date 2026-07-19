# 📄 Stone Colors Plugin

**ID:** `stone_colors`  
**Kategorie:** 🏢 Spezial (Naturstein)  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Stone Colors Plugin liefert **Farbinformationen für Natursteine** – Granit, Marmor, Quarzit, Schiefer, Travertin. Es enthält:

- **Farbnamen** und **Hex-Codes**
- **Beschreibung** und **Stimmung** (z.B. "edel, modern")
- **Verwendungshinweise** (z.B. "Küchenarbeitsplatten", "Böden")
- **Varianten** (z.B. "Nero Assoluto Zimbabwe")
- **RGB-Werte**

Die Datenbank wird in einer JSON-Datei gespeichert (`./stone_colors.json`) und kann über die Admin-UI oder manuell bearbeitet werden.

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(farbe|ton|muster|optik|farbpalette|stein farbe|schwarz|weiß|grau|beige|braun|rot|grün|blau)\b
```

**Beispiele:**

- _"Welche Farbe hat Nero Assoluto?"_
- _"Zeige mir die Farbpalette von Marmor."_
- _"Welche Farben gibt es bei Granit?"_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable             | Beschreibung                | Standard              |
| -------------------- | --------------------------- | --------------------- |
| `COLOR_STORAGE_PATH` | Pfad zur JSON-Farbdatenbank | `./stone_colors.json` |

---

## 📦 Input-Schema

```json
{
  "stone_name": "Nero Assoluto",
  "stone_type": "granit",
  "color": "schwarz",
  "limit": 10
}
```

| Feld         | Typ     | Beschreibung                                                                                                    |
| ------------ | ------- | --------------------------------------------------------------------------------------------------------------- |
| `stone_name` | string  | Name des Steins (erforderlich)                                                                                  |
| `stone_type` | string  | Steinart (`granit`, `marmor`, `quarzit`, `schiefer`, `travertin`, `kalkstein`)                                  |
| `color`      | string  | Farbe (`schwarz`, `weiß`, `grau`, `beige`, `braun`, `rot`, `grün`, `blau`, `gelb`, `orange`, `violett`, `rosa`) |
| `limit`      | integer | Anzahl der Ergebnisse (1–50, Standard: 10)                                                                      |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "stone": {
    "name": "Nero Assoluto",
    "type": "Granit",
    "color": "Schwarz",
    "hex": "#1a1a1a",
    "description": "Tiefschwarzer Granit mit feiner, gleichmäßiger Körnung. Sehr elegant und zeitlos.",
    "suitable_for": ["Küchenarbeitsplatten", "Böden", "Fassaden", "Grabsteine"],
    "mood": "edel, modern, zeitlos",
    "rgb": [26, 26, 26],
    "variants": ["Nero Assoluto Zimbabwe", "Nero Assoluto Brazil"]
  },
  "message": "Informationen zu Nero Assoluto gefunden."
}
```

---

## 🧪 Beispiele

### 1. Farbe von Nero Assoluto

**Input:**

```json
{
  "stone_name": "Nero Assoluto"
}
```

**Output:**

```json
{
  "success": true,
  "stone": {
    "name": "Nero Assoluto",
    "type": "Granit",
    "color": "Schwarz",
    "hex": "#1a1a1a",
    "description": "Tiefschwarzer Granit mit feiner, gleichmäßiger Körnung. Sehr elegant und zeitlos.",
    "suitable_for": ["Küchenarbeitsplatten", "Böden", "Fassaden", "Grabsteine"],
    "mood": "edel, modern, zeitlos",
    "rgb": [26, 26, 26],
    "variants": ["Nero Assoluto Zimbabwe", "Nero Assoluto Brazil"]
  },
  "message": "Informationen zu Nero Assoluto gefunden."
}
```

### 2. Alle weißen Marmore

**Input:**

```json
{
  "stone_type": "marmor",
  "color": "weiß",
  "limit": 10
}
```

### 3. Farbpalette von Granit

**Input:**

```json
{
  "stone_type": "granit",
  "limit": 20
}
```

---

## 📁 Datei-Struktur

```text
packages/plugins/stone_colors/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 📁 Speicherort der Datenbank

Standardmäßig wird die Farbdatenbank in einer JSON-Datei gespeichert:

```text
./stone_colors.json
```

---

## 🔧 Erweiterbarkeit

Die Datenbank kann um neue Steine, Farben und Varianten erweitert werden:

```python
_COLOR_DB["neuer_stein"] = {
    "name": "Neuer Stein",
    "type": "Granit",
    "color": "Blau",
    "hex": "#1a2a5a",
    "description": "Beschreibung",
    "suitable_for": ["Küche", "Boden"],
    "mood": "modern",
    "rgb": [26, 42, 90],
    "variants": ["Variante 1"],
}
```

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Welche Farbe hat Nero Assoluto?"_
>
> **Elisa:** _"Nero Assoluto ist schwarz (Hex: #1a1a1a). Der Stein ist sehr edel und modern und eignet sich für Küchenarbeitsplatten, Böden, Fassaden und Grabsteine."_

---

## 📚 Siehe auch

- [Stone Knowledge Plugin](../stone_knowledge)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
