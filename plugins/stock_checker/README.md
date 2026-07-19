# 📄 Stock Checker Plugin

**ID:** `stock_checker`  
**Kategorie:** 🛒 E-Commerce & Preis  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Stock Checker Plugin ermöglicht die **Lagerbestandsabfrage** für Natursteinprodukte. Es unterstützt:

- **Suche nach Produkt-ID** (exakt)
- **Suche nach Produktname** (Teilsuche)
- **Lagerort-Filter**
- **Anzeige von reservierten und verfügbaren Beständen**
- **Warnung bei Unterschreitung des Mindestbestands**

Die Lagerdaten werden in einer JSON-Datei gespeichert (`./stock.json`) und können über die Admin-UI oder manuell bearbeitet werden.

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(lager|bestand|verfügbar|lieferbar|vorrat|stock)\b
```

**Beispiele:**

- _"Wie viel Lagerbestand haben wir von Nero Assoluto?"_
- _"Ist Produkt P001 verfügbar?"_
- _"Zeige mir den Bestand von Granit-Fliesen."_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable             | Beschreibung             | Standard       |
| -------------------- | ------------------------ | -------------- |
| `STOCK_STORAGE_PATH` | Pfad zur JSON-Lagerdatei | `./stock.json` |

---

## 📦 Input-Schema

```json
{
  "product_id": "P001",
  "product_name": "Nero Assoluto",
  "location": "Lager A",
  "all_locations": false
}
```

| Feld            | Typ     | Beschreibung                                           |
| --------------- | ------- | ------------------------------------------------------ |
| `product_id`    | string  | Produkt-ID (erforderlich, wenn kein product_name)      |
| `product_name`  | string  | Produktname (Teilsuche)                                |
| `location`      | string  | Lagerort (optional)                                    |
| `all_locations` | boolean | Bestände aller Standorte anzeigen (nur mit product_id) |

---

## 📤 Output-Schema

### Bei Produkt-ID

```json
{
  "success": true,
  "product_id": "P001",
  "product_name": "Nero Assoluto Granit Fliese 60x60",
  "stock": 120,
  "reserved": 15,
  "available": 105,
  "location": "Lager A",
  "min_stock": 20,
  "message": "105 verfügbar (Lager: 120, reserviert: 15)"
}
```

### Bei Produktname-Suche

```json
{
  "success": true,
  "results": [
    {
      "product_id": "P001",
      "product_name": "Nero Assoluto Granit Fliese 60x60",
      "stock": 120,
      "reserved": 15,
      "available": 105,
      "location": "Lager A"
    }
  ],
  "message": "1 Produkte gefunden."
}
```

**Bei Fehlern:**

```json
{
  "success": false,
  "error": "Produkt mit ID 'P001' nicht gefunden."
}
```

---

## 🧪 Beispiele

### 1. Bestand nach Produkt-ID abfragen

**Input:**

```json
{
  "product_id": "P001"
}
```

**Output:**

```json
{
  "success": true,
  "product_id": "P001",
  "product_name": "Nero Assoluto Granit Fliese 60x60",
  "stock": 120,
  "reserved": 15,
  "available": 105,
  "location": "Lager A",
  "min_stock": 20,
  "message": "105 verfügbar (Lager: 120, reserviert: 15)"
}
```

### 2. Bestand nach Produktname suchen

**Input:**

```json
{
  "product_name": "Nero Assoluto"
}
```

### 3. Bestand mit Lagerort-Filter

**Input:**

```json
{
  "product_id": "P001",
  "location": "Lager B"
}
```

**Output:** Fehler, wenn Produkt nicht am Lagerort verfügbar ist.

---

## 📁 Datei-Struktur

```text
packages/plugins/stock_checker/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 📁 Speicherort der Lagerdaten

Standardmäßig werden die Lagerdaten in einer JSON-Datei gespeichert:

```text
./stock.json
```

**Format:**

```json
{
  "P001": {
    "name": "Nero Assoluto Granit Fliese 60x60",
    "stock": 120,
    "reserved": 15,
    "location": "Lager A",
    "min_stock": 20
  }
}
```

---

## 🔧 Erweiterbarkeit

Die Lagerdatenbank kann einfach um neue Produkte erweitert werden:

```python
_STOCK_DB["P011"] = {
    "name": "Neues Produkt",
    "stock": 50,
    "reserved": 5,
    "location": "Lager B",
    "min_stock": 10,
}
```

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Wie viel Lagerbestand haben wir von Nero Assoluto?"_
>
> **Elisa:** _"Nero Assoluto Granit Fliese 60x60: 105 verfügbar (Lager: 120, reserviert: 15)."_

> **Nutzer:** _"Ist Produkt P002 verfügbar?"_
>
> **Elisa:** _"Produkt P002 (Bianco Sardo Marmor Fliese 40x40): 80 verfügbar (Lager: 85, reserviert: 5)."_

---

## 📚 Siehe auch

- [Product Catalog Plugin](../product_catalog)
- [Price Finder Plugin](../pricefinder)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
