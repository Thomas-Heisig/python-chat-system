# 📄 Product Catalog Plugin

**ID:** `product_catalog`  
**Kategorie:** 🛒 E-Commerce & Preis  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Product Catalog Plugin ermöglicht die **Suche im internen Produktkatalog** für Natursteinprodukte. Es unterstützt:

- **Volltextsuche** (Name, Material, Variante, Beschreibung, Tags)
- **Filter** (Material, Kategorie, Variante, Preisbereich, Verfügbarkeit)
- **Sortierung** (Name, Preis, Lagerbestand)
- **Währungsumrechnung** (EUR, USD, CHF, GBP)

Der Katalog wird in einer JSON-Datei gespeichert (`./catalog.json`) und kann über die Admin-UI oder manuell bearbeitet werden.

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(katalog|produkt|fliesen|platte|arbeitsplatte|stein|bestellen|angebot)\b
```

**Beispiele:**

- _"Suche nach Nero Assoluto Fliesen."_
- _"Zeige mir alle Granit-Produkte."_
- _"Welche Marmor-Platten sind auf Lager?"_
- _"Finde Arbeitsplatten unter 500 €."_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable               | Beschreibung               | Standard         |
| ---------------------- | -------------------------- | ---------------- |
| `CATALOG_STORAGE_PATH` | Pfad zur JSON-Katalogdatei | `./catalog.json` |

---

## 📦 Input-Schema

```json
{
  "query": "Nero Assoluto",
  "material": "granit",
  "category": "fliese",
  "variant": "nero assoluto",
  "min_price": 100,
  "max_price": 250,
  "in_stock": true,
  "limit": 10,
  "sort_by": "price",
  "sort_order": "asc",
  "currency": "EUR"
}
```

| Feld         | Typ     | Beschreibung                                                                  |
| ------------ | ------- | ----------------------------------------------------------------------------- |
| `query`      | string  | Suchbegriff (erforderlich)                                                    |
| `material`   | string  | Material (z.B. Granit, Marmor)                                                |
| `category`   | string  | Kategorie (`fliese`, `platte`, `arbeitsplatte`, `boden`, `fassade`, `treppe`) |
| `variant`    | string  | Variante/Name des Steins                                                      |
| `min_price`  | number  | Mindestpreis                                                                  |
| `max_price`  | number  | Maximalpreis                                                                  |
| `in_stock`   | boolean | Nur verfügbare Produkte (Standard: `true`)                                    |
| `limit`      | integer | Max. Ergebnisse (1–50, Standard: `10`)                                        |
| `sort_by`    | string  | `name`, `price`, `stock` (Standard: `name`)                                   |
| `sort_order` | string  | `asc`, `desc` (Standard: `asc`)                                               |
| `currency`   | string  | `EUR`, `USD`, `CHF`, `GBP` (Standard: `EUR`)                                  |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "total": 3,
  "message": "3 Produkte gefunden.",
  "results": [
    {
      "id": "P001",
      "name": "Nero Assoluto Granit Fliese 60x60",
      "category": "fliese",
      "material": "granit",
      "variant": "nero assoluto",
      "format": "60x60",
      "thickness": "2cm",
      "finish": "polished",
      "price": 185.0,
      "currency": "EUR",
      "unit": "qm",
      "stock": 120,
      "description": "Edle schwarze Granitfliese, poliert, für Böden und Arbeitsplatten.",
      "tags": ["granit", "schwarz", "fliese", "innen"]
    }
  ]
}
```

---

## 🧪 Beispiele

### 1. Suche nach Nero Assoluto

**Input:**

```json
{
  "query": "Nero Assoluto",
  "category": "fliese"
}
```

### 2. Granit-Produkte filtern

**Input:**

```json
{
  "query": "Granit",
  "in_stock": true,
  "sort_by": "price",
  "sort_order": "asc"
}
```

### 3. Preisbereich und Verfügbarkeit

**Input:**

```json
{
  "query": "Marmor",
  "min_price": 200,
  "max_price": 350,
  "limit": 5
}
```

### 4. Währung umrechnen

**Input:**

```json
{
  "query": "Quarzit",
  "currency": "USD"
}
```

---

## 📁 Datei-Struktur

```text
packages/plugins/product_catalog/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 📁 Speicherort des Katalogs

Standardmäßig wird der Katalog in einer JSON-Datei gespeichert:

```text
./catalog.json
```

Das Format entspricht dem `_CATALOG_DB` im Code. Es kann über die Admin-UI oder manuell bearbeitet werden.

---

## 🔧 Erweiterbarkeit

Der Katalog kann einfach um neue Produkte erweitert werden:

```python
{
    "id": "P011",
    "name": "Neues Produkt",
    "category": "fliese",
    "material": "granit",
    "variant": "new_variant",
    "format": "60x60",
    "thickness": "2cm",
    "finish": "polished",
    "price": 199.0,
    "currency": "EUR",
    "unit": "qm",
    "stock": 50,
    "description": "Beschreibung",
    "tags": ["tag1", "tag2"],
    "image_url": "/images/product.jpg"
}
```

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Suche nach Nero Assoluto Fliesen."_
>
> **Elisa:** _"Ich habe 3 Produkte gefunden:_
>
> 1. _Nero Assoluto Granit Fliese 60x60 – 185,00 €/qm (120 verfügbar)_
> 2. _Nero Assoluto Granit Arbeitsplatte 240x60cm – 320,00 €/qm (8 verfügbar)_
> 3. _..._
>    _Möchtest du Details zu einem Produkt?"_

---

## 📚 Siehe auch

- [Price Finder Plugin](../pricefinder)
- [Offer Generator Plugin](../offer_generator)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
