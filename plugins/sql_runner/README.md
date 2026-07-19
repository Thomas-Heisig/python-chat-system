# 📄 SQL Runner Plugin

**ID:** `sql_runner`  
**Kategorie:** 🔧 Developer Tools  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das SQL Runner Plugin ermöglicht die **Ausführung von SQL-Abfragen** auf einer Datenbank. Es unterstützt:

- **SELECT-Abfragen** (sicherheitsbeschränkt)
- **Parameterisierung** (sicher vor SQL-Injection)
- **Zeilenlimit** (standardmäßig 100)
- **Timeout** (standardmäßig 10 Sekunden)
- **Verschiedene Datenbanken** (PostgreSQL, SQLite, MySQL, etc.)

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(sql|datenbank|abfrage|select|query|run sql)\b
```

**Beispiele:**

- _"Führe SELECT_ FROM kunden LIMIT 10 aus."\*
- _"SQL-Abfrage auf der Datenbank."_
- _"Zeige mir die letzten 5 Bestellungen."_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable                | Beschreibung                | Erforderlich |
| ----------------------- | --------------------------- | ------------ |
| `SQL_CONNECTION_STRING` | Datenbank-Connection-String | ✅           |

**Beispiele:**

- PostgreSQL: `postgresql://user:pass@localhost:5432/db`
- SQLite: `sqlite:///./data.db`
- MySQL: `mysql+pymysql://user:pass@localhost:3306/db`

---

## 📦 Input-Schema

```json
{
  "query": "SELECT name, email FROM customers WHERE active = true LIMIT 10",
  "params": {},
  "limit": 50,
  "timeout": 15,
  "connection_string": "postgresql://user:pass@localhost:5432/db"
}
```

| Feld                | Typ     | Beschreibung                                  |
| ------------------- | ------- | --------------------------------------------- |
| `query`             | string  | SQL-Abfrage (nur SELECT) (erforderlich)       |
| `params`            | object  | Parameter für parametrisierte Abfragen        |
| `limit`             | integer | Max. Zeilen (1–1000, Standard: 100)           |
| `timeout`           | integer | Timeout in Sekunden (1–60, Standard: 10)      |
| `connection_string` | string  | Überschreibt die Umgebungsvariable (optional) |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "columns": ["name", "email"],
  "rows": [
    ["Max Mustermann", "max@mustermann.de"],
    ["Anna Schmidt", "anna@schmidt.de"]
  ],
  "row_count": 2,
  "execution_time_ms": 12.34,
  "message": "Abfrage erfolgreich ausgeführt. 2 Zeilen zurückgegeben."
}
```

**Bei Fehlern:**

```json
{
  "success": false,
  "error": "Nur SELECT-Abfragen sind erlaubt."
}
```

---

## 🧪 Beispiele

### 1. Einfache SELECT-Abfrage

**Input:**

```json
{
  "query": "SELECT * FROM customers LIMIT 5"
}
```

### 2. Parametrisierte Abfrage

**Input:**

```json
{
  "query": "SELECT * FROM customers WHERE name LIKE :name LIMIT 10",
  "params": {
    "name": "%Mustermann%"
  }
}
```

### 3. Mit eigenem Connection-String

**Input:**

```json
{
  "query": "SELECT * FROM orders WHERE date > '2026-01-01'",
  "connection_string": "sqlite:///./sales.db"
}
```

---

## 🔒 Sicherheitsmaßnahmen

| Maßnahme                  | Beschreibung                                                |
| ------------------------- | ----------------------------------------------------------- |
| **Nur SELECT**            | DDL/DML (INSERT, UPDATE, DELETE, DROP, etc.) sind blockiert |
| **Parameterisierung**     | Verhindert SQL-Injection                                    |
| **Zeilenlimit**           | Maximal 1000 Zeilen (Standard 100)                          |
| **Timeout**               | Maximal 60 Sekunden (Standard 10)                           |
| **Keine Multistatements** | Semikolon-getrennte Abfragen werden blockiert               |

---

## 📁 Datei-Struktur

```text
packages/plugins/sql_runner/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "Keine Datenbankverbindung konfiguriert"

**Lösung:** Setze `SQL_CONNECTION_STRING` in der Umgebung:

```bash
export SQL_CONNECTION_STRING="postgresql://user:pass@localhost:5432/db"
```

### Fehler: "Nur SELECT-Abfragen sind erlaubt"

**Lösung:** Verwende nur SELECT-Abfragen. Andere Operationen sind blockiert.

### Fehler: "Datenbankfehler"

**Lösung:** Prüfe, ob die Datenbank läuft und der Connection-String korrekt ist.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Zeige mir die ersten 10 Kunden aus der Datenbank."_
>
> **Elisa:** _"Abfrage erfolgreich. 10 Kunden gefunden: [Liste]."_

---

## 📚 Siehe auch

- [SQLAlchemy Dokumentation](https://docs.sqlalchemy.org/)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
