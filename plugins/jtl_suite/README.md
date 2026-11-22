# JTL Suite Plugin

Zentrale Integration für JTL-Wawi, JTL-Shop, JTL-WMS, JTL-eazyAuction, SQL-Diagnose und Analytics.

## Installation

Den Ordner `jtl_suite` nach `plugins/jtl_suite` kopieren. Die vorhandenen Standalone-Vite-Dateien im alten `frontend`-Ordner werden nicht mehr benötigt.

## Enthalten

- `assets/logo.svg`
- `settings.py` mit Scope-Merging und Umgebungsvariablen
- `plugin.py` mit Plugin-Metadaten, HTTP- und SQL-Ausführung
- `frontend/JTLSuitePage.tsx`
- `frontend/JTLSuitePage.css`

## Benötigte Python-Pakete

- `httpx`
- `sqlalchemy`
- `pyodbc` für SQL-Server-Zugriff

## Sicherheit

`db_query` erlaubt nur `SELECT`- beziehungsweise `WITH`-Abfragen. Secrets werden durch `settings.resolved` nicht an das Frontend ausgegeben.

## Zentrale Frontend-Anbindung

Die konkrete Änderung ist in `WORKSPACE_INTEGRATION.md` im übergeordneten ZIP-Ordner beschrieben.
