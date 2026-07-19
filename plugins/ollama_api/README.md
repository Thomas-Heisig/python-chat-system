# 📄 OLLAMA API Plugin

**ID:** `ollama_api`  
**Kategorie:** 🔌 Externe APIs  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das OLLAMA API Plugin ermöglicht die **Nutzung von OLLAMA-Modellen** (lokal) für Textgenerierung. Es unterstützt:

- **Viele Modelle** (Llama 2, Mistral, Code Llama, etc.)
- **Streaming** (schrittweise Antwortausgabe)
- **System-Prompt** für Kontextsteuerung
- **Modell-Liste** abrufen
- **Health-Check**

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(ollama|lokal|llama|mistral|code llama)\b
```

**Beispiele:**

- _"Nutze OLLAMA für diese Frage."_
- _"Generiere mit OLLAMA eine Antwort."_
- _"Lokales Modell mit OLLAMA."_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable               | Beschreibung         | Standard                 |
| ---------------------- | -------------------- | ------------------------ |
| `OLLAMA_API_BASE`      | OLLAMA API-Basis-URL | `http://localhost:11434` |
| `OLLAMA_DEFAULT_MODEL` | Standard-Modell      | `llama2`                 |

### OLLAMA installieren

1. Installiere [OLLAMA](https://ollama.ai/)
2. Lade ein Modell herunter: `ollama pull llama2`
3. Starte OLLAMA: `ollama serve`

---

## 📦 Input-Schema

```json
{
  "prompt": "Erkläre Granit.",
  "model": "llama2",
  "temperature": 0.7,
  "max_tokens": 512,
  "stream": true,
  "system_prompt": "Du bist ein Naturstein-Experte.",
  "keep_alive": 300,
  "api_base": "http://localhost:11434"
}
```

| Feld            | Typ     | Standard | Beschreibung                                       |
| --------------- | ------- | -------- | -------------------------------------------------- |
| `prompt`        | string  | –        | Der Prompt (erforderlich)                          |
| `model`         | string  | `llama2` | Modellname (z.B. `llama2`, `mistral`, `codellama`) |
| `temperature`   | number  | `0.7`    | Kreativität (0.0–2.0)                              |
| `max_tokens`    | integer | `512`    | Maximale Antwort-Tokens                            |
| `stream`        | boolean | `true`   | Streaming aktivieren                               |
| `system_prompt` | string  | –        | Optionaler System-Prompt                           |
| `keep_alive`    | integer | `300`    | Modell im Speicher halten (Sekunden)               |
| `api_base`      | string  | –        | API-Basis-URL (überschreibt ENV)                   |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "model": "llama2",
  "response": "Granit ist ein magmatisches Gestein...",
  "tokens": 120,
  "total_duration": 23456789
}
```

**Bei Fehlern:**

```json
{
  "success": false,
  "error": "Modell 'llama2' nicht gefunden. Verfügbare Modelle: ['llama2', 'mistral']"
}
```

---

## 🧪 Beispiele

### 1. Einfache Textgenerierung

**Input:**

```json
{
  "prompt": "Erkläre Granit.",
  "model": "llama2"
}
```

### 2. Mit System-Prompt

**Input:**

```json
{
  "prompt": "Was ist die beste Arbeitsplatte?",
  "system_prompt": "Du bist ein Naturstein-Experte und antwortest auf Deutsch.",
  "temperature": 0.3
}
```

### 3. Streaming deaktivieren

**Input:**

```json
{
  "prompt": "Generiere eine Zusammenfassung.",
  "stream": false
}
```

---

## 📁 Datei-Struktur

```text
packages/plugins/ollama_api/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "OLLAMA nicht verfügbar"

**Lösung:** Stelle sicher, dass OLLAMA läuft:

```bash
ollama serve
```

### Fehler: "Modell nicht gefunden"

**Lösung:** Lade das Modell herunter:

```bash
ollama pull llama2
```

### Fehler: "Connection refused"

**Lösung:** Prüfe die `OLLAMA_API_BASE`-URL und stelle sicher, dass OLLAMA auf dem richtigen Port läuft.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Nutze OLLAMA für eine Erklärung von Granit."_
>
> **Elisa:** _"Granit ist ein magmatisches Gestein, das hauptsächlich aus Quarz, Feldspat und Glimmer besteht..."_

---

## 📚 Siehe auch

- [OLLAMA Dokumentation](https://github.com/ollama/ollama)
- [OLLAMA API](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
