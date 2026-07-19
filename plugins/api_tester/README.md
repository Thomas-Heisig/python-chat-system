# 📄 API Tester Plugin – README

**ID:** `api_tester`  
**Kategorie:** 🔧 Developer Tools  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das API Tester Plugin führt **HTTP-Requests** an beliebige URLs aus und gibt die Antwort zurück. Es unterstützt:

- **Verschiedene HTTP-Methoden**: GET, POST, PUT, DELETE, PATCH, HEAD
- **Benutzerdefinierte Header**
- **Request-Body** (als String oder JSON-Objekt)
- **Follow Redirects** (automatische Weiterleitung)
- **Zeitmessung** (Latenz in ms)

Es ist ideal für:

- API-Entwicklung und -Tests
- Integration mit externen Diensten
- Debugging von Webhooks und Endpunkten

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(api|teste|request|http|get|post|put|delete)\b
```

**Beispiele:**

- _"Teste die API unter <https://api.example.com/health>."_
- _"Sende einen POST-Request an ..."_
- _"Führe einen GET-Request auf ... aus."_

---

## ⚙️ Konfiguration

Das Plugin ist **sofort einsatzbereit** – es sind keine Umgebungsvariablen erforderlich.

---

## 📦 Input-Schema

```json
{
  "url": "https://api.example.com/users",
  "method": "GET",
  "headers": {
    "Authorization": "Bearer token123",
    "Content-Type": "application/json"
  },
  "body": {
    "name": "Max Mustermann"
  }
}
```

| Feld      | Typ           | Standard | Beschreibung                                       |
| --------- | ------------- | -------- | -------------------------------------------------- |
| `url`     | string        | –        | Ziel-URL (erforderlich)                            |
| `method`  | string        | `GET`    | HTTP-Methode (GET, POST, PUT, DELETE, PATCH, HEAD) |
| `headers` | object        | –        | HTTP-Header als Key-Value-Objekt                   |
| `body`    | string/object | –        | Request-Body (JSON-Objekt oder String)             |

---

## 📤 Output-Schema

### Erfolg

```json
{
  "status_code": 200,
  "headers": {
    "content-type": "application/json",
    "content-length": "1234"
  },
  "body": "{\"data\": {...}}",
  "elapsed_ms": 42.5
}
```

### Fehler

```json
{
  "error": "HTTP-Fehler: 404",
  "status_code": 404
}
```

---

## 🧪 Beispiele

### 1. GET-Request mit Headers

**Input:**

```json
{
  "url": "https://api.github.com/users/octocat",
  "headers": {
    "User-Agent": "Mozilla/5.0"
  }
}
```

**Output:**

```json
{
  "status_code": 200,
  "headers": {...},
  "body": "{\"login\":\"octocat\",\"id\":1,...}",
  "elapsed_ms": 234.5
}
```

### 2. POST-Request mit JSON-Body

**Input:**

```json
{
  "url": "https://jsonplaceholder.typicode.com/posts",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "title": "foo",
    "body": "bar",
    "userId": 1
  }
}
```

**Output:**

```json
{
  "status_code": 201,
  "body": "{\"title\":\"foo\",\"body\":\"bar\",\"userId\":1,\"id\":101}",
  "elapsed_ms": 156.3
}
```

### 3. PUT-Request

**Input:**

```json
{
  "url": "https://jsonplaceholder.typicode.com/posts/1",
  "method": "PUT",
  "body": "{\"title\":\"updated\"}"
}
```

### 4. HEAD-Request

**Input:**

```json
{
  "url": "https://api.example.com",
  "method": "HEAD"
}
```

**Output:**

```json
{
  "status_code": 200,
  "headers": {
    "server": "nginx/1.18.0",
    "content-type": "text/html"
  },
  "body": "",
  "elapsed_ms": 12.8
}
```

---

## 📁 Datei-Struktur

```
packages/plugins/api_tester/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "URL ist erforderlich"

**Lösung:** Gib eine gültige URL an (mit `http://` oder `https://`).

### Fehler: "Zeitüberschreitung (Timeout)"

**Lösung:** Der Timeout beträgt 15 Sekunden. Reduziere die Antwortgröße oder erhöhe das Timeout (falls konfigurierbar).

### Fehler: "HTTP-Fehler: 4xx"

**Lösung:** Prüfe die URL, die Header und den Body. Der Fehler kommt vom Zielserver.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Teste die API unter <https://api.heishg-naturstein.de/health>."_
>
> **Elisa:** _"API-Test durchgeführt: Status 200 OK. Antwortzeit: 42 ms. Antwort: {\"status\":\"healthy\"}."_

---

## 📚 Siehe auch

- [WebSearch Plugin](../websearch)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
