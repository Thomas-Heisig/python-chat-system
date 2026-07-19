# 📄 GitHub Search Plugin

**ID:** `github_search`  
**Kategorie:** 🔧 Developer Tools  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das GitHub Search Plugin ermöglicht die **Suche auf GitHub** über die GitHub REST API. Es unterstützt:

- **Repository-Suche** – Finde Repositories nach Name, Beschreibung, Sprache, Stars
- **Code-Suche** – Suche in Code-Dateien innerhalb von Repositories
- **Issue-Suche** – Finde Issues und Pull Requests
- **User-Suche** – Finde GitHub-Benutzer

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(github|code|repository|repo|issue|pull request|pr|star|fork|commit)\b
```

**Beispiele:**

- _"Suche auf GitHub nach React-Projekten."_
- _"Finde Python-Repositories mit mehr als 1000 Stars."_
- _"Suche nach Issues im Repository 'facebook/react'."_
- _"Finde GitHub-User mit dem Namen 'elisa'."_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable       | Beschreibung                 | Erforderlich |
| -------------- | ---------------------------- | ------------ |
| `GITHUB_TOKEN` | GitHub Personal Access Token | ✅           |

### GitHub Token erstellen

1. Gehe zu **GitHub** → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Klicke auf **Generate new token**
3. Wähle Scopes:
   - `repo` (für private Repositories)
   - `public_repo` (für öffentliche Repositories)
   - `user` (für User-Suche)
4. Kopiere den Token und setze ihn als `GITHUB_TOKEN` in der Umgebung.

> **Hinweis:** Ohne Token ist die GitHub API auf 60 Requests pro Stunde limitiert. Mit Token sind es 5000 Requests pro Stunde.

---

## 📦 Input-Schema

```json
{
  "query": "react",
  "type": "repositories",
  "language": "javascript",
  "repo": "facebook/react",
  "owner": "facebook",
  "sort": "stars",
  "order": "desc",
  "per_page": 10,
  "page": 1
}
```

| Feld       | Typ     | Standard       | Beschreibung                              |
| ---------- | ------- | -------------- | ----------------------------------------- |
| `query`    | string  | –              | Suchbegriff (erforderlich)                |
| `type`     | string  | `repositories` | `repositories`, `code`, `issues`, `users` |
| `language` | string  | –              | Programmiersprache (für Code-Suche)       |
| `repo`     | string  | –              | Repository (für Code-Suche)               |
| `owner`    | string  | –              | Besitzer (für Repository-Suche)           |
| `sort`     | string  | `relevance`    | `stars`, `forks`, `updated`, `relevance`  |
| `order`    | string  | `desc`         | `asc`, `desc`                             |
| `per_page` | integer | `10`           | Ergebnisse pro Seite (1–100)              |
| `page`     | integer | `1`            | Seitennummer                              |

---

## 📤 Output-Schema

### Repository-Suche

```json
{
  "success": true,
  "total_count": 12345,
  "items": [
    {
      "id": 123456,
      "name": "facebook/react",
      "description": "A declarative, efficient, and flexible JavaScript library...",
      "url": "https://github.com/facebook/react",
      "stars": 180000,
      "forks": 37000,
      "language": "JavaScript",
      "owner": "facebook",
      "updated_at": "2026-06-28T10:00:00Z"
    }
  ]
}
```

### Code-Suche

```json
{
  "success": true,
  "total_count": 42,
  "items": [
    {
      "name": "App.js",
      "path": "src/App.js",
      "repository": "facebook/react",
      "url": "https://github.com/facebook/react/blob/main/src/App.js"
    }
  ]
}
```

### Issue-Suche

```json
{
  "success": true,
  "total_count": 150,
  "items": [
    {
      "id": 987654,
      "title": "Bug: Rendering issue in React 18",
      "state": "open",
      "url": "https://github.com/facebook/react/issues/12345",
      "repository": "facebook/react",
      "user": "developer",
      "created_at": "2026-06-28T10:00:00Z"
    }
  ]
}
```

### User-Suche

```json
{
  "success": true,
  "total_count": 5,
  "items": [
    {
      "id": 12345,
      "login": "elisa-dev",
      "name": "Elisa Developer",
      "url": "https://github.com/elisa-dev",
      "avatar_url": "https://avatars.githubusercontent.com/u/12345",
      "repos": 25,
      "followers": 150
    }
  ]
}
```

---

## 🧪 Beispiele

### 1. Repository-Suche (React, nach Stars sortiert)

**Input:**

```json
{
  "query": "react",
  "type": "repositories",
  "sort": "stars",
  "order": "desc",
  "per_page": 5
}
```

### 2. Code-Suche in einem Repository

**Input:**

```json
{
  "query": "useState",
  "type": "code",
  "repo": "facebook/react"
}
```

### 3. Issue-Suche nach offenen Bugs

**Input:**

```json
{
  "query": "type:bug state:open",
  "type": "issues",
  "repo": "facebook/react"
}
```

### 4. User-Suche

**Input:**

```json
{
  "query": "elisa",
  "type": "users"
}
```

---

## 📁 Datei-Struktur

```
packages/plugins/github_search/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "Ungültiger GitHub Token"

**Lösung:** Prüfe `GITHUB_TOKEN` in der Umgebung. Stelle sicher, dass der Token die richtigen Scopes hat.

### Fehler: "Rate-Limit überschritten"

**Lösung:** Warte einige Minuten und versuche es erneut. Mit Token sind 5000 Requests pro Stunde erlaubt.

### Fehler: "Nicht gefunden"

**Lösung:** Prüfe, ob der Suchbegriff korrekt ist und das Repository/der User existiert.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Suche auf GitHub nach React-Projekten mit mehr als 10000 Stars."_
>
> **Elisa:** _"Ich habe 15 Repositories gefunden. Die Top 3: 1. facebook/react (180k Stars), 2. vuejs/vue (50k Stars), 3. angular/angular (20k Stars)."_

> **Nutzer:** _"Finde Issues im Repository 'facebook/react' mit dem Label 'bug'."_
>
> **Elisa:** _"Ich habe 42 offene Issues mit dem Label 'bug' gefunden. Möchtest du die Details?"_

---

## 📚 Siehe auch

- [GitHub REST API Dokumentation](https://docs.github.com/en/rest)
- [GitHub Search Syntax](https://docs.github.com/en/search-github)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
