# 💱 Currency Converter Plugin

**ID:** `currency_converter`  
**Kategorie:** 📊 Business & Analytics  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Currency Converter Plugin ermöglicht die **Umrechnung von Währungen** mit Echtzeit-Wechselkursen. Es unterstützt mehrere API-Quellen:

- **Frankfurter** (kostenlos, keine API-Key erforderlich) – Standard
- **Fixer.io** (API-Key erforderlich, mehr Funktionen)
- **ExchangeRate-API** (kostenlos mit API-Key)

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(euro|dollar|umrechnen|wechselkurs|währung|kurs|währungsrechner)\b
```

**Beispiele:**

- _"Wie viel sind 100 Euro in Dollar?"_
- _"Rechne 500 USD in GBP um."_
- _"Was ist der aktuelle Wechselkurs von EUR zu CHF?"_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable               | Beschreibung                 | Erforderlich              |
| ---------------------- | ---------------------------- | ------------------------- |
| `FIXER_API_KEY`        | API-Key für Fixer.io         | ❌ (nur für Fixer-Quelle) |
| `EXCHANGERATE_API_KEY` | API-Key für ExchangeRate-API | ❌                        |

---

## 📦 Input-Schema

```json
{
  "amount": 100.0,
  "from_currency": "EUR",
  "to_currency": "USD",
  "date": "2026-06-28",
  "source": "frankfurter"
}
```

| Feld            | Typ    | Standard      | Beschreibung                                       |
| --------------- | ------ | ------------- | -------------------------------------------------- |
| `amount`        | number | –             | Der umzurechnende Betrag (erforderlich)            |
| `from_currency` | string | `EUR`         | ISO-Währungscode (z.B. EUR, USD, GBP)              |
| `to_currency`   | string | `USD`         | ISO-Währungscode der Zielwährung                   |
| `date`          | string | –             | Historisches Datum (YYYY-MM-DD)                    |
| `source`        | string | `frankfurter` | API-Quelle: `frankfurter`, `fixer`, `exchangerate` |

### Unterstützte Währungen

AED, AUD, BGN, BRL, CAD, CHF, CNY, CZK, DKK, EUR, GBP, HKD, HRK, HUF, IDR, ILS, INR, ISK, JPY, KRW, MXN, MYR, NOK, NZD, PHP, PLN, RON, RUB, SEK, SGD, THB, TRY, USD, ZAR

---

## 📤 Output-Schema

```json
{
  "success": true,
  "amount": 100.0,
  "from_currency": "EUR",
  "to_currency": "USD",
  "converted_amount": 107.22,
  "rate": 1.0722,
  "date": "2026-06-28",
  "source": "frankfurter",
  "message": "100.0 EUR = 107.22 USD (Kurs: 1.0722)"
}
```

**Bei Fehlern:**

```json
{
  "error": "Ungültiger Betrag. Bitte eine Zahl angeben."
}
```

---

## 🧪 Beispiele

### 1. Aktuellen Kurs abfragen

**Input:**

```json
{
  "amount": 100,
  "from_currency": "EUR",
  "to_currency": "USD"
}
```

**Output:**

```json
{
  "success": true,
  "amount": 100.0,
  "from_currency": "EUR",
  "to_currency": "USD",
  "converted_amount": 107.22,
  "rate": 1.0722,
  "date": "2026-06-28",
  "source": "frankfurter",
  "message": "100.0 EUR = 107.22 USD (Kurs: 1.0722)"
}
```

### 2. Historischen Kurs abfragen

**Input:**

```json
{
  "amount": 100,
  "from_currency": "EUR",
  "to_currency": "USD",
  "date": "2023-01-01"
}
```

### 3. CHF in GBP umrechnen

**Input:**

```json
{
  "amount": 250,
  "from_currency": "CHF",
  "to_currency": "GBP"
}
```

### 4. Mit Fixer.io

**Input:**

```json
{
  "amount": 100,
  "from_currency": "EUR",
  "to_currency": "JPY",
  "source": "fixer"
}
```

**Voraussetzung:** `FIXER_API_KEY` in der Umgebung gesetzt.

---

## 📁 Datei-Struktur

```
packages/plugins/currency_converter/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── plugin copy.py     # Backup (optional)
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "API-Key für Fixer.io fehlt"

**Lösung:** Setze `FIXER_API_KEY` in der Umgebung oder verwende eine andere Quelle (`frankfurter`).

### Fehler: "Kein Wechselkurs für EUR → USD gefunden"

**Lösung:** Prüfe, ob die Währungscodes korrekt sind. Die unterstützten Währungen sind oben aufgelistet.

### Fehler: "HTTP-Fehler: 429"

**Lösung:** Rate-Limit überschritten. Warte einige Sekunden und versuche es erneut.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Wie viel sind 100 Euro in Dollar?"_
>
> **Elisa:** _"100.00 EUR sind aktuell 107.22 USD (Kurs: 1.0722)."_

> **Nutzer:** _"Rechne 500 CHF in GBP um."_
>
> **Elisa:** _"500.00 CHF sind 454.80 GBP (Kurs: 0.9096)."_

---

## 📚 Siehe auch

- [Frankfurter API](https://www.frankfurter.app/)
- [Fixer.io](https://fixer.io/)
- [ExchangeRate-API](https://www.exchangerate-api.com/)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
