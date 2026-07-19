# JTL Suite Plugin (Enterprise)

**ID:** `jtl_suite`
**Kategorie:** 📊 Business & Analytics
**Status:** ✅ Implementiert

---

## Beschreibung

Das **JTL Suite Plugin** ist die ultimative Schnittstelle zwischen Ihrem Chat-System und der gesamten JTL-Produktwelt. Es bietet einen einheitlichen Zugriff auf:

- **JTL-Wawi** – ERP & Warenwirtschaft
- **JTL-Shop** – Online-Shop
- **JTL-WMS** – Warehouse Management
- **JTL-eazyAuction** – Marketplace-Integration

Das Plugin unterstützt **vollständige CRUD-Operationen** (Create, Read, Update, Delete) für alle Geschäftsobjekte sowie **intelligentes Hybrid-Routing** – einfache Abfragen werden über die REST-API, komplexe Analysen automatisch über die Datenbank ausgeführt. Mit **vordefinierten Business-Reports** und **direktem SQL-Zugriff** wird das Plugin zur zentralen Business-Intelligence-Schnittstelle.

---

## 🔧 Konfiguration

### Umgebungsvariablen

| Variable | Beschreibung | Erforderlich |
| --- | --- | --- |
| `JTL_WAWI_BASE_URL` | Base URL der JTL-Wawi API | für WaWi-Aktionen |
| `JTL_WAWI_API_KEY` | API-Key für JTL-Wawi | für WaWi-Aktionen |
| `JTL_SHOP_BASE_URL` | Base URL der JTL-Shop API | für Shop-Aktionen |
| `JTL_SHOP_API_KEY` | API-Key für JTL-Shop | für Shop-Aktionen |
| `JTL_WMS_BASE_URL` | Base URL der JTL-WMS API | für WMS-Aktionen |
| `JTL_WMS_API_KEY` | API-Key für JTL-WMS | für WMS-Aktionen |
| `JTL_EAZYAUCTION_BASE_URL` | Base URL der JTL-eazyAuction API | für eazyAuction-Aktionen |
| `JTL_EAZYAUCTION_API_KEY` | API-Key für JTL-eazyAuction | für eazyAuction-Aktionen |
| `JTL_DB_HOST` | SQL Server Host | für DB-Aktionen |
| `JTL_DB_PORT` | SQL Server Port (Standard 1433) | für DB-Aktionen |
| `JTL_DB_USER` | SQL Server Benutzer (Standard `sa`) | für DB-Aktionen |
| `JTL_DB_PASSWORD` | SQL Server Passwort (Standard `sa`) | für DB-Aktionen |
| `JTL_DB_DRIVER` | ODBC Driver Name (z.B. `ODBC Driver 18 for SQL Server`) | für DB-Aktionen |
| `JTL_WAWI_DB_NAME` | Datenbankname WaWi (Standard `eazybusiness`) | für DB-Aktionen |
| `JTL_SHOP_DB_NAME` | Datenbankname Shop | optional |
| `JTL_WMS_DB_NAME` | Datenbankname WMS | optional |
| `JTL_EAZYAUCTION_DB_NAME` | Datenbankname eazyAuction | optional |
| `JTL_DB_ENCRYPT` | SQL Encrypt (`true`/`false`) | optional |
| `JTL_DB_TRUST_SERVER_CERTIFICATE` | Zertifikat vertrauen (`true`/`false`) | optional |
| `JTL_DB_TIMEOUT_SECONDS` | SQL Timeout in Sekunden (Standard 20) | optional |

### Plugin-Settings (Überschreiben Umgebungsvariablen)

Alle oben genannten Werte können auch über die Plugin-Settings gesetzt werden (Präfix `jtl_*`). Zusätzlich stehen folgende **erweiterte Einstellungen** zur Verfügung:

| Setting | Typ | Standard | Beschreibung |
| --- | --- | --- | --- |
| `request_timeout_seconds` | Zahl | 20 | HTTP-Timeout für API-Aufrufe |
| `verify_tls` | Boolean | true | TLS-Zertifikatsprüfung aktivieren |
| `max_pagination_pages` | Zahl | 10 | Maximale Seiten bei `fetch_all` |
| `retry_max_attempts` | Zahl | 3 | Wiederholungen bei API-Fehlern |
| `retry_backoff_factor` | Zahl | 1.0 | Exponentieller Backoff-Faktor |
| `api_read_timeout` | Zahl | 30 | Separater Timeout für Lese-APIs |
| `api_write_timeout` | Zahl | 60 | Separater Timeout für Schreib-APIs (PDF, etc.) |
| `sql_query_timeout_seconds` | Zahl | 60 | SQL-Query-Timeout (überschreibt `jtl_db_timeout_seconds`) |
| `db_pool_size` | Zahl | 5 | SQL Connection Pool Size |
| `allow_cross_database_joins` | Boolean | false | Cross-DB-Joins erlauben |
| `jtl_mandant_filter` | Zahl | 0 | Standard-Mandant für SQL-Queries (0 = deaktiviert) |
| `analytics_default_limit` | Zahl | 50 | Standard-Limit für Analytics-Reports |
| `analytics_use_db` | Boolean | false | Analytics immer via DB (sonst hybrid) |

---

## 🚀 Aktionen (Übersicht)

### Basis-Aktionen (kompatibel)

| Aktion | Service | Zweck |
| --- | --- | --- |
| `list_products` | Wawi | Produkte abrufen (mit Suchfilter) |
| `get_product` | Wawi | Einzelnes Produkt abrufen |
| `list_customers` | Wawi | Kunden abrufen |
| `create_customer` | Wawi | Kunden anlegen |
| `list_orders` | Wawi | Aufträge abrufen |
| `create_order` | Wawi | Auftrag anlegen |
| `update_order_status` | Wawi | Auftragsstatus aktualisieren |
| `sync_stock_to_shop` | Shop | Bestand an Shop synchronisieren |
| `list_shop_orders` | Shop | Shop-Bestellungen abrufen |
| `list_wms_picklists` | WMS | Picklisten abrufen |
| `list_marketplace_listings` | eazyAuction | Marketplace-Listings abrufen |
| `db_test_connection` | SQL | Datenbankverbindung testen |
| `db_query` | SQL | Direkte SQL-Select-Abfrage |
| `custom_request` | flexibel | Beliebigen API-Endpunkt aufrufen |

### Erweiterte Aktionen

#### Rechnungen & Angebote

| Aktion | Service | Zweck |
| --- | --- | --- |
| `list_invoices` | Wawi | Rechnungen abrufen |
| `get_invoice` | Wawi | Einzelne Rechnung abrufen |
| `create_invoice_from_order` | Wawi | Rechnung aus Auftrag erstellen |
| `download_invoice_pdf` | Wawi | Rechnung als PDF (Base64) herunterladen |
| `list_quotes` | Wawi | Angebote abrufen |
| `get_quote` | Wawi | Einzelnes Angebot abrufen |
| `update_quote` | Wawi | Angebot aktualisieren |
| `convert_quote_to_order` | Wawi | Angebot in Auftrag umwandeln |

#### Lager & Bestand

| Aktion | Service | Zweck |
| --- | --- | --- |
| `list_warehouses` | Wawi | Lager abrufen |
| `get_stock` | Wawi | Bestand eines Produkts abrufen |
| `adjust_stock` | Wawi | Bestand manuell anpassen |
| `list_stock_movements` | Wawi | Bestandsbewegungen anzeigen |

#### Versand & Zahlungen

| Aktion | Service | Zweck |
| --- | --- | --- |
| `list_shipments` | Wawi | Versandaufträge abrufen |
| `get_shipment` | Wawi | Einzelnen Versandauftrag abrufen |
| `create_shipment` | Wawi | Versandauftrag erstellen |
| `list_payments` | Wawi | Zahlungen abrufen |
| `get_payment` | Wawi | Einzelne Zahlung abrufen |
| `create_payment` | Wawi | Zahlung manuell buchen |

#### Auftragsverwaltung

| Aktion | Service | Zweck |
| --- | --- | --- |
| `add_order_comment` | Wawi | Kommentar zu Auftrag hinzufügen |
| `cancel_order` | Wawi | Auftrag stornieren |

#### CRUD-Operationen (generisch)

| Aktion | Service | Zweck |
| --- | --- | --- |
| `create_product` | Wawi | Neues Produkt anlegen |
| `update_product` | Wawi | Produkt aktualisieren |
| `delete_product` | Wawi | Produkt löschen |
| `update_customer` | Wawi | Kunde aktualisieren |
| `delete_customer` | Wawi | Kunde löschen |
| `update_order` | Wawi | Auftrag aktualisieren |
| `delete_order` | Wawi | Auftrag löschen |

#### Analytics & Business-Reports

| Aktion | Service | Zweck |
| --- | --- | --- |
| `analytics` | SQL | Vordefinierte Business-Reports ausführen |

**Verfügbare Report-Typen:**
- `sales_overview` – Umsatzübersicht (Bestellungen, Umsatz, Ø-Wert)
- `top_selling_products` – Bestseller nach Umsatz
- `customer_lifetime_value` – Kunden mit höchstem Lifetime-Wert
- `slow_moving_inventory` – Langsamdreher im Lager
- `order_fulfillment_kpi` – Durchlaufzeiten & Erfüllungsquote
- `invoice_payment_behavior` – Zahlungsverhalten (Tage bis Zahlung)

#### Bulk-Fetch (alle Seiten abrufen)

| Aktion | Service | Zweck |
| --- | --- | --- |
| `fetch_all_products` | Wawi | Alle Produkte (mehrere Seiten) abrufen |
| `fetch_all_customers` | Wawi | Alle Kunden abrufen |
| `fetch_all_orders` | Wawi | Alle Aufträge abrufen |
| `fetch_all_invoices` | Wawi | Alle Rechnungen abrufen |
| `fetch_all_quotes` | Wawi | Alle Angebote abrufen |

**Alternativ:** Bei jeder `list_*`-Aktion kann `"fetch_all": true` gesetzt werden.

#### Datenbank-Helfer

| Aktion | Service | Zweck |
| --- | --- | --- |
| `db_tables` | SQL | Alle Tabellen der Datenbank auflisten |
| `db_describe_table` | SQL | Spaltenstruktur einer Tabelle anzeigen |

---

## 💡 Beispiele

### 1. Rechnungen abrufen (mit Filter)
```json
{
  "action": "list_invoices",
  "limit": 10,
  "query": "2026-01"
}
```

### 2. Rechnung als PDF herunterladen
```json
{
  "action": "download_invoice_pdf",
  "item_id": "12345"
}
```
**Antwort:**
```json
{
  "success": true,
  "action": "download_invoice_pdf",
  "data": {
    "invoice_id": "12345",
    "pdf_base64": "JVBERi0xLjQKMSAwIG9iago8PC..."
  }
}
```

### 3. Angebot in Auftrag umwandeln
```json
{
  "action": "convert_quote_to_order",
  "item_id": "67890"
}
```

### 4. Business-Report: Bestseller
```json
{
  "action": "analytics",
  "report_type": "top_selling_products",
  "date_from": "2026-01-01",
  "date_to": "2026-06-30",
  "limit": 10
}
```

### 5. Alle Kunden abrufen (mehrere Seiten)
```json
{
  "action": "list_customers",
  "fetch_all": true,
  "limit": 100
}
```

### 6. SQL-Tabellen auflisten
```json
{
  "action": "db_tables",
  "db_service": "wawi"
}
```

### 7. SQL-Spaltenstruktur anzeigen
```json
{
  "action": "db_describe_table",
  "db_service": "wawi",
  "table_name": "tArtikel"
}
```

### 8. Direkte SQL-Abfrage mit Parametern
```json
{
  "action": "db_query",
  "db_service": "wawi",
  "sql": "SELECT TOP (:limit) kArtikel, cName, fPreis FROM tArtikel WHERE cName LIKE :search ORDER BY kArtikel DESC",
  "sql_params": {
    "limit": 20,
    "search": "%Granit%"
  }
}
```

### 9. Bestand an Shop synchronisieren
```json
{
  "action": "sync_stock_to_shop",
  "stock_updates": [
    {"sku": "ABC-001", "quantity": 50},
    {"sku": "ABC-002", "quantity": 0}
  ]
}
```

### 10. Custom Request (flexibler Endpunkt)
```json
{
  "action": "custom_request",
  "service": "wawi",
  "method": "GET",
  "endpoint": "/api/v2/special/report",
  "params": {"date": "2026-07-01"}
}
```

---

## 🧠 Hybrid-Routing (API vs. SQL)

Das Plugin entscheidet automatisch, ob eine Anfrage über die REST-API oder direkt über die Datenbank ausgeführt wird:

| Kriterium | Routing |
| --- | --- |
| Einfache Liste ohne Filter | → **API** (schnell, entlastet DB) |
| Mit Suchfilter (`query`) | → **API** |
| Mit Datumsfilter (`date_from`/`date_to`) | → **SQL** (flexiblere Filterung) |
| Mit Gruppierung (`group_by`) | → **SQL** |
| Analytics-Reports | → **SQL** |
| Schreibzugriffe (Create/Update/Delete) | → **API** (transaktionssicher) |
| `analytics_use_db = true` | → **immer SQL** |

---

## 🔒 Direkter Datenbankzugriff

Das Plugin unterstützt **lesende SQL-Abfragen** (`SELECT` und `WITH`) gegen alle JTL-Datenbanken.

### Unterstützte Services
- `wawi` (Standard: `eazybusiness`)
- `shop`
- `wms`
- `eazyauction`

### Sicherheitsmechanismen
- ✅ Nur `SELECT` und `WITH` erlaubt
- ✅ Parametrisierte Queries (Schutz vor SQL-Injection)
- ✅ Optionaler Mandantenfilter (`kMandant`)
- ✅ Connection-Pooling für Performance
- ✅ Timeout-Kontrolle (`sql_query_timeout_seconds`)

### Voraussetzungen
- ODBC-Treiber (z.B. `ODBC Driver 18 for SQL Server`)
- `pyodbc` Python-Paket
- SQL Server-Zugang (Standard: `sa` / `sa` – **in Produktion ändern!**)

---

## 📋 Frontend-Sektionen

Das Plugin bietet ein strukturiertes Frontend mit folgenden Sektionen:

| Sektion | Inhalt |
| --- | --- |
| **JTL-Wawi** | Produkte, Kunden, Aufträge, Rechnungen, Angebote |
| **Shop und WMS** | Shop-Aufträge, Picklisten, Marketplace-Listings |
| **Analytics & Reports** | Umsatzübersicht, Bestseller, Kundenwert |
| **SQL und Verbindung** | DB-Test, SQL-Query, Tabellen auflisten, Settings |

---

## ⚠️ Hinweise

### API-Endpunkte
Die konkreten Endpunkte (`/api/v1/...`) können je nach JTL-Setup variieren. Falls Ihre Installation andere Pfade verwendet, nutzen Sie:

- `custom_request` für flexible API-Aufrufe
- Oder passen Sie die Endpunkte in `ENTITY_CONFIG` an

### SQL-Zugriff
- Für SQL-Zugriff muss **pyodbc** und der **SQL Server ODBC-Treiber** auf dem Host installiert sein.
- Standardzugang ist `sa` / `sa` – **bitte für Produktion ändern!**
- Cross-DB-Joins sind standardmäßig deaktiviert (`allow_cross_database_joins = false`)

### Bulk-Fetch
- `fetch_all` durchläuft maximal `max_pagination_pages` Seiten (Standard: 10)
- Bei großen Datenmengen kann dies zu erhöhter Latenz führen

### Timeouts
- Lese-APIs: `api_read_timeout` (Standard 30s)
- Schreib-APIs: `api_write_timeout` (Standard 60s)
- SQL-Queries: `sql_query_timeout_seconds` (Standard 60s)
- HTTP-Generell: `request_timeout_seconds` (Standard 20s)

### Retry-Logik
- Bei temporären Fehlern (5xx, 429) wird automatisch wiederholt
- Maximal `retry_max_attempts` (Standard 3)
- Exponentieller Backoff mit `retry_backoff_factor` (Standard 1.0)

---

## 🔧 Fehlersuche

| Problem | Lösung |
| --- | --- |
| "Base URL fehlt" | `JTL_WAWI_BASE_URL` setzen |
| "API-Key fehlt" | `JTL_WAWI_API_KEY` setzen |
| "Nur SELECT/WITH erlaubt" | Keine Schreib-SQLs verwenden |
| "SQL-Fehler: pyodbc" | ODBC-Treiber installieren |
| "Timeout" | `request_timeout_seconds` oder `sql_query_timeout_seconds` erhöhen |
| "TLS-Zertifikat" | `verify_tls = false` (nur für Testumgebungen!) |
| "Mandant nicht gefiltert" | `jtl_mandant_filter` setzen |

---

## 📦 Updates & Migration

### Von der Basis-Version zur Enterprise-Version
1. **Plugin austauschen** – die neue `plugin.py` ersetzt die alte
2. **Einstellungen prüfen** – neue Settings wie `sql_query_timeout_seconds`, `db_pool_size` etc. können übernommen werden
3. **Keine Änderungen in der API** – alle alten Aktionen funktionieren unverändert
4. **Neue Aktionen** – stehen sofort zur Verfügung

### Abwärtskompatibilität
- ✅ `list_products`, `get_product`, `list_customers`, `create_customer`, `list_orders`, `create_order`, `update_order_status`, `sync_stock_to_shop`, `list_shop_orders`, `list_wms_picklists`, `list_marketplace_listings`, `db_test_connection`, `db_query`, `custom_request`
- ✅ Alle bestehenden Aufrufe funktionieren unverändert
- ✅ Neue Aktionen ergänzen, ersetzen nichts

---

## 🎯 Zusammenfassung

Das **JTL Suite Plugin (Enterprise)** bietet:

- **100% Abwärtskompatibilität** zu bestehenden Integrationen
- **Vollständige CRUD-Operationen** für alle Geschäftsobjekte
- **Rechnungen, Angebote, Versand, Zahlungen** aus einer Hand
- **Intelligentes Hybrid-Routing** für maximale Performance
- **Vordefinierte Analytics-Reports** für schnelle Business-Einblicke
- **Flexibler SQL-Zugriff** mit Sicherheitsmechanismen
- **Retry-Logik, Connection-Pooling** und **erweiterte Timeout-Kontrolle**
- **Strukturiertes Frontend** für schnellen Zugriff

---

*Bei Fragen oder individuellen Anpassungen kontaktieren Sie den Plugin-Entwickler.*