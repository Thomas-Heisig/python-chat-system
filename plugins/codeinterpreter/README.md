# 📄 Code Interpreter Plugin

**ID:** `codeinterpreter`  
**Kategorie:** 🔧 Developer Tools  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Code Interpreter Plugin führt **Python-Code** in einer sicheren Sandbox aus. Es unterstützt zwei Modi:

- **Lokale Sandbox** (Standard): Ausführung in einem temporären Verzeichnis mit Zeitlimit
- **Docker-Sandbox** (optional): Vollständige Isolierung mit Netzwerkabschaltung, Speicher- und CPU-Limits

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

````regex
```python|code|python|ausführen
````

**Beispiele:**

- _"Führe diesen Python-Code aus: `python print('Hallo')`"_
- _"Kannst du mir helfen, diesen Python-Code zu testen?"_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable             | Beschreibung                 | Standard           | Erforderlich              |
| -------------------- | ---------------------------- | ------------------ | ------------------------- |
| `CODE_SANDBOX_IMAGE` | Docker-Image für die Sandbox | `python:3.11-slim` | ❌ (nur für Docker-Modus) |

---

## 📦 Input-Schema

```json
{
  "code": "print('Hallo Welt')",
  "timeout": 10,
  "sandbox_mode": "local"
}
```

| Feld           | Typ     | Standard | Beschreibung                                                      |
| -------------- | ------- | -------- | ----------------------------------------------------------------- |
| `code`         | string  | –        | Der auszuführende Python-Code (kann Markdown-Codeblock enthalten) |
| `timeout`      | integer | 10       | Maximale Laufzeit in Sekunden                                     |
| `sandbox_mode` | string  | `local`  | `local` oder `docker`                                             |

---

## 📤 Output-Schema

```json
{
  "output": "Hallo Welt",
  "duration_ms": 12.34
}
```

**Bei Fehlern:**

```json
{
  "error": "Zeitüberschreitung (10 Sekunden)."
}
```

---

## 🧪 Beispiele

### 1. Einfacher Code (lokal)

**Input:**

```json
{
  "code": "print('Hallo Welt')",
  "timeout": 5
}
```

**Output:**

```json
{
  "output": "Hallo Welt",
  "duration_ms": 8.23
}
```

### 2. Code mit Fehler

**Input:**

```json
{
  "code": "raise ValueError('Testfehler')"
}
```

**Output:**

```json
{
  "output": "⚠️ Fehler:\nTraceback (most recent call last):\n  File ...\nValueError: Testfehler"
}
```

### 3. Markdown-Codeblock

**Input:**

````json
{
  "code": "```python\nprint('Hello')\n```"
}
````

**Output:** (wie oben)

### 4. Docker-Sandbox

**Input:**

```json
{
  "code": "import os\nprint(os.getcwd())",
  "sandbox_mode": "docker"
}
```

**Output:** (Gibt den Pfad im Container aus)

---

## 🔒 Sicherheit

| Maßnahme                        | Beschreibung                                                                                                                                |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Lokaler Modus**               | Ausführung in einem temporären Verzeichnis, kein Netzwerkzugriff, Zeitlimit                                                                 |
| **Docker-Modus**                | Vollständig isolierter Container, Netzwerk deaktiviert, Speicherlimit 256 MB, CPU-Limit 0.5 Kerne, Zeitlimit                                |
| **Zeitlimit**                   | Standard 10 Sekunden, konfigurierbar                                                                                                        |
| **Keine gefährlichen Builtins** | Das Skript kann keine Systembefehle ausführen (weil `subprocess` etc. nicht importiert sind, sofern der Nutzer sie nicht selbst importiert) |

> **Hinweis:** Der lokale Modus ist **nicht produktionssicher**, da er direkten Zugriff auf das Dateisystem hat. Verwenden Sie für produktive Umgebungen den **Docker-Modus**.

---

## 📁 Datei-Struktur

```
packages/plugins/codeinterpreter/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Berechne die Fibonacci-Zahlen bis 10."_
>
> **Elisa:** _"Ich führe den Code aus:_
>
> ```python
> a, b = 0, 1
> result = []
> for _ in range(10):
>     result.append(a)
>     a, b = b, a+b
> print(result)
> ```
>
> _Ergebnis: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]"_

---

## 🔧 Fehlerbehebung

### Fehler: "Docker ist nicht verfügbar."

**Lösung:** Installiere Docker und starte den Dienst. Oder wechsle in den lokalen Modus.

### Fehler: "Timeout"

**Lösung:** Erhöhe den Timeout-Wert oder optimiere den Code.

---

## 🚀 Nächste Erweiterungen (geplant)

- [ ] Unterstützung für mehrere Sprachen (JavaScript, Bash, etc.)
- [ ] Netzwerkzugriff im Docker-Modus (optional)
- [ ] Speicherung von Ausgaben (Datei-Output)

---

## 📚 Siehe auch

- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
