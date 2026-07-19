# 📄 Installation Guide Plugin

**ID:** `installation_guide`  
**Kategorie:** 🏢 Spezial (Naturstein)  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Installation Guide Plugin liefert **Verlegeanleitungen für Naturstein** – für verschiedene Steinarten und Anwendungen wie:

- Küchenarbeitsplatten
- Böden
- Fassaden
- Treppen
- Außenbereiche

Es basiert auf einer **lokalen Wissensdatenbank** und benötigt keine externe API.

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(verlegung|einbau|montage|anleitung|installieren|verlegen)\b
```

**Beispiele:**

- _"Wie verlege ich Granit richtig?"_
- _"Anleitung für Marmorboden."_
- _"Verlegung von Schiefer-Fassade."_

---

## ⚙️ Konfiguration

Das Plugin ist **sofort einsatzbereit**, es sind keine Umgebungsvariablen erforderlich.

---

## 📦 Input-Schema

```json
{
  "stone": "Granit",
  "application": "Küchenarbeitsplatte"
}
```

| Feld          | Typ    | Beschreibung                                                             |
| ------------- | ------ | ------------------------------------------------------------------------ |
| `stone`       | string | Steinname (z.B. Granit, Marmor, Quarzit, Schiefer, Travertin, Kalkstein) |
| `application` | string | Anwendungsbereich (Standard: `küchenarbeitsplatte`)                      |

**Unterstützte Anwendungen:**

- `küchenarbeitsplatte`
- `boden`
- `fassade`
- `treppe`
- `außenbereich`

---

## 📤 Output-Schema

```json
{
  "stone": "Granit",
  "application": "küchenarbeitsplatte",
  "title": "Granit-Küchenarbeitsplatte verlegen",
  "steps": [
    "Untergrund prüfen: Sauber, eben, tragfähig...",
    "Ausschnitt für Spüle und Herd vorbereiten...",
    "..."
  ],
  "materials": [
    "Granitplatte",
    "Montagekleber",
    "Fugenmasse",
    "Gummihammer",
    "Wasserwaage"
  ],
  "tips": [
    "Trage die Platten zu zweit – Granit ist schwer.",
    "Verwende einen Saugheber für präzises Ausrichten."
  ]
}
```

**Bei Fehlern:**

```json
{
  "error": "Keine Verlegeanleitung für 'Blabla' gefunden. Verfügbare Steine: Granit, Marmor, Quarzit, Schiefer, Travertin, Kalkstein"
}
```

---

## 🧪 Beispiele

### 1. Granit-Küchenarbeitsplatte

**Input:**

```json
{
  "stone": "Granit",
  "application": "Küchenarbeitsplatte"
}
```

**Output:** (siehe oben)

### 2. Marmorboden

**Input:**

```json
{
  "stone": "Marmor",
  "application": "Boden"
}
```

### 3. Schiefer-Fassade

**Input:**

```json
{
  "stone": "Schiefer",
  "application": "Fassade"
}
```

### 4. Teilübereinstimmung

**Input:**

```json
{
  "stone": "Gran"
}
```

**Output:** Findet automatisch "Granit".

---

## 📁 Datei-Struktur

```
packages/plugins/installation_guide/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Erweiterbarkeit

Die Wissensdatenbank kann einfach um weitere Steine, Anwendungen oder detailliertere Schritte erweitert werden:

```python
_INSTALLATION_DB["neuer_stein"] = {
    "name": "Neuer Stein",
    "applications": {
        "anwendung": {
            "title": "Titel",
            "steps": ["Schritt 1", "Schritt 2"],
            "materials": ["Material 1"],
            "tips": ["Tipp 1"]
        }
    }
}
```

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Wie verlege ich eine Granit-Küchenarbeitsplatte?"_
>
> **Elisa:** _"Granit-Küchenarbeitsplatte verlegen:_
>
> 1. _Untergrund prüfen..._
> 2. _Ausschnitt vorbereiten..._
>    ...
>    _Benötigte Materialien: Granitplatte, Montagekleber, Fugenmasse..._"

---

## 📚 Siehe auch

- [Care Instructions Plugin](../care_instructions)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
