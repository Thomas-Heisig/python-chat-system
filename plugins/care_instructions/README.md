# 📋 Care Instructions Plugin

**ID:** `care_instructions`  
**Kategorie:** 🏢 Spezial (Naturstein)  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Plugin liefert **Pflegeanleitungen für Naturstein** – Reinigung, Versiegelung, Schutz und Fleckenentfernung für die gängigsten Steinarten:

- Granit
- Marmor
- Quarzit
- Schiefer
- Travertin
- Kalkstein

Es basiert auf einer **lokalen Wissensdatenbank** und benötigt keine externe API.

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(pflege|reinigung|versiegelung|schutz|flecken|naturstein pflegen)\b
```

**Beispiele:**

- _"Wie reinige ich Granit richtig?"_
- _"Welche Versiegelung braucht Marmor?"_
- _"Wie entferne ich Flecken aus Travertin?"_

---

## ⚙️ Konfiguration

Das Plugin ist **sofort einsatzbereit**, es sind keine Umgebungsvariablen erforderlich.

---

## 📦 Input-Schema

```json
{
  "stone": "Granit",
  "category": "daily_cleaning" // optional
}
```

**Kategorien:**

- `daily_cleaning` – Tägliche Reinigung
- `deep_cleaning` – Grundreinigung
- `sealing` – Versiegelung
- `protection` – Schutzmaßnahmen
- `stain_removal` – Fleckenentfernung

---

## 📤 Output-Schema

```json
{
  "stone": "Granit",
  "instructions": {
    "daily_cleaning": "Reinigen Sie mit warmem Wasser und einem milden pH-neutralen Spülmittel. Verwenden Sie ein weiches Tuch oder einen Mopp.",
    "deep_cleaning": "Bei hartnäckigen Flecken: Speziellen Granitreiniger oder eine Mischung aus Wasser und etwas Alkohol verwenden. Keine säurehaltigen Mittel.",
    "sealing": "Versiegelung alle 1–2 Jahre mit einem hochwertigen Granit-Versiegelungsmittel. Vor der Versiegelung gründlich reinigen und trocknen.",
    "protection": "Verwenden Sie Untersetzer für Gläser und heiße Töpfe. Säurehaltige Substanzen (Zitronensaft, Essig) sofort aufwischen.",
    "stain_removal": "Ölflecken: mit Spezialsteinpaste oder Backpulver abdecken, einwirken lassen und abwischen."
  }
}
```

**Bei Fehlern:**

```json
{
  "error": "Keine Pflegeanleitung für 'Blabla' gefunden. Verfügbare Steine: Granit, Marmor, Quarzit, Schiefer, Travertin, Kalkstein"
}
```

---

## 🧪 Beispiele

### 1. Vollständige Pflegeanleitung für Granit

**Input:**

```json
{
  "stone": "Granit"
}
```

**Output (gekürzt):** siehe oben.

### 2. Nur Versiegelung für Marmor

**Input:**

```json
{
  "stone": "Marmor",
  "category": "sealing"
}
```

**Output:**

```json
{
  "stone": "Marmor",
  "instructions": {
    "sealing": "Versiegelung alle 6–12 Monate mit Marmor-Versiegelung. Marmor ist porös, daher wichtig für Fleckenschutz."
  }
}
```

### 3. Fleckenentfernung für Travertin

**Input:**

```json
{
  "stone": "Travertin",
  "category": "stain_removal"
}
```

**Output:**

```json
{
  "stone": "Travertin",
  "instructions": {
    "stain_removal": "Flecken mit einer Mischung aus Wasser und Backpulver behandeln, einwirken lassen und abwischen."
  }
}
```

### 4. Teilübereinstimmung

**Input:**

```json
{
  "stone": "Marmo"
}
```

**Output:** Findet automatisch "Marmor".

---

## 📁 Datei-Struktur

```
packages/plugins/care_instructions/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Erweiterbarkeit

Die Wissensdatenbank kann einfach um weitere Steine oder Kategorien erweitert werden:

```python
_CARE_DB["neuer_stein"] = {
    "name": "Neuer Stein",
    "daily_cleaning": "...",
    "deep_cleaning": "...",
    # ...
}
```

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Wie pflege ich meine Granit-Arbeitsplatte?"_
>
> **Elisa:** _"Granit sollte täglich mit warmem Wasser und mildem Spülmittel gereinigt werden. Verwenden Sie keine säurehaltigen Mittel. Alle 1–2 Jahre ist eine Versiegelung empfehlenswert. Möchten Sie detaillierte Anleitungen für Reinigung, Versiegelung oder Fleckenentfernung?"_

---

## 📚 Siehe auch

- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
