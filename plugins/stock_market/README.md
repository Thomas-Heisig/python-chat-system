# 📄 Stock Market Plugin

**ID:** `stock_market`  
**Kategorie:** 📊 Business & Analytics  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Stock Market Plugin ermöglicht die **Abfrage von Aktienkursen und Börsendaten** über die **Alpha Vantage API**. Es unterstützt:

- **Aktuelle Kurse** (Quote) – Preis, Veränderung, Volumen, Tagesspanne
- **Aktiensuche** – Suche nach Symbolen und Unternehmensnamen
- **Tägliche historische Daten** – Schlusskurse, Volumen (angepasst)
- **Intraday-Daten** – Echtzeitkurse in verschiedenen Intervallen
- **Unternehmensübersicht** – Branche, Marktkapitalisierung, KGV, Dividende

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(aktie|kurs|börse|dax|nasdaq|s&p|markt|wertpapier|stock|share)\b
```

**Beispiele:**

- _"Wie steht die Apple Aktie?"_
- _"Kurs von Microsoft."_
- _"Suche nach Aktien von Tesla."_
- _"Zeige mir den DAX."_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable                | Beschreibung          | Erforderlich |
| ----------------------- | --------------------- | ------------ |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API-Key | ✅           |

### Alpha Vantage API-Key erhalten

1. Registriere dich auf [alphavantage.co](https://www.alphavantage.co/support/#api-key)
2. Erhalte einen kostenlosen API-Key
3. Setze den Key als `ALPHA_VANTAGE_API_KEY` in der Umgebung.

> **Hinweis:** Der kostenlose Key erlaubt 5 Anfragen pro Minute und 500 pro Tag.

---

## 📦 Input-Schema

### Quote (aktueller Kurs)

```json
{
  "action": "quote",
  "symbol": "AAPL"
}
```

### Search (Aktiensuche)

```json
{
  "action": "search",
  "keywords": "Apple"
}
```

### Daily (historische Tagesdaten)

```json
{
  "action": "daily",
  "symbol": "AAPL",
  "outputsize": "compact"
}
```

### Intraday (Echtzeit-Daten)

```json
{
  "action": "intraday",
  "symbol": "AAPL",
  "interval": "5min",
  "outputsize": "compact"
}
```

### Overview (Unternehmensübersicht)

```json
{
  "action": "overview",
  "symbol": "AAPL"
}
```

---

## 📤 Output-Schema

### Quote

```json
{
  "success": true,
  "symbol": "AAPL",
  "price": 215.5,
  "change": 3.25,
  "change_percent": 1.53,
  "volume": 45678900,
  "high": 216.0,
  "low": 212.5,
  "open": 212.75,
  "previous_close": 212.25,
  "timestamp": "2026-06-28 10:00:00"
}
```

### Search

```json
{
  "success": true,
  "results": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "type": "Equity",
      "region": "United States",
      "currency": "USD"
    }
  ]
}
```

### Daily

```json
{
  "success": true,
  "symbol": "AAPL",
  "results": [
    {
      "date": "2026-06-27",
      "open": 212.0,
      "high": 216.0,
      "low": 211.5,
      "close": 215.5,
      "adjusted_close": 215.5,
      "volume": 45678900
    }
  ]
}
```

### Intraday

```json
{
  "success": true,
  "symbol": "AAPL",
  "interval": "5min",
  "results": [
    {
      "timestamp": "2026-06-28 10:00:00",
      "open": 215.0,
      "high": 216.0,
      "low": 214.5,
      "close": 215.5,
      "volume": 12345
    }
  ]
}
```

### Overview

```json
{
  "success": true,
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "description": "Apple Inc. designs, manufactures, and markets smartphones...",
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "market_cap": "3,200,000,000,000",
  "pe_ratio": "28.5",
  "dividend_yield": "0.45",
  "eps": "6.15",
  "book_value": "12.80"
}
```

---

## 🧪 Beispiele

### 1. Aktuellen Kurs abrufen

**Input:**

```json
{
  "action": "quote",
  "symbol": "AAPL"
}
```

### 2. Aktie suchen

**Input:**

```json
{
  "action": "search",
  "keywords": "Microsoft"
}
```

### 3. Historische Daten (30 Tage)

**Input:**

```json
{
  "action": "daily",
  "symbol": "AAPL",
  "outputsize": "compact"
}
```

### 4. Echtzeit-Daten (5-Minuten-Intervall)

**Input:**

```json
{
  "action": "intraday",
  "symbol": "AAPL",
  "interval": "5min",
  "outputsize": "compact"
}
```

### 5. Unternehmensübersicht

**Input:**

```json
{
  "action": "overview",
  "symbol": "AAPL"
}
```

---

## 📁 Datei-Struktur

```text
packages/plugins/stock_market/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 📊 Preise (Alpha Vantage)

| Tier          | Anfragen/Minute | Anfragen/Tag | Preis     |
| ------------- | --------------- | ------------ | --------- |
| **Kostenlos** | 5               | 500          | 0 €       |
| **Premium**   | 75              | 10.000       | $50/Monat |

---

## 🔧 Fehlerbehebung

### Fehler: "Ungültiger API-Key"

**Lösung:** Prüfe `ALPHA_VANTAGE_API_KEY` in der Umgebung. Der Key muss korrekt und aktiv sein.

### Fehler: "Rate-Limit überschritten"

**Lösung:** Alpha Vantage erlaubt 5 Anfragen pro Minute. Warte eine Minute und versuche es erneut.

### Fehler: "Keine Daten für Symbol gefunden"

**Lösung:** Prüfe, ob das Symbol korrekt ist (z.B. `AAPL`, `MSFT`, `DAX`). Verwende `search`, um das richtige Symbol zu finden.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Wie steht die Apple Aktie?"_
>
> **Elisa:** _"Apple (AAPL): 215,50 € (+3,25 €, +1,53%). High: 216,00 €, Low: 212,50 €. Volumen: 45.678.900."_

> **Nutzer:** _"Suche nach Aktien von Tesla."_
>
> **Elisa:** _"Tesla (TSLA) – NASDAQ – USD."_

> **Nutzer:** _"Zeige mir die letzten 10 Tage von Microsoft."_
>
> **Elisa:** _"Microsoft (MSFT): 10 Tage historische Daten [Tabelle]."_

---

## 📚 Siehe auch

- [Alpha Vantage API Dokumentation](https://www.alphavantage.co/documentation/)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
