# Agenten, Datenbanken und Selbstwissen v1.1.0

## Umfang
- training.jsonl: 60
- validation.jsonl: 13
- test.jsonl: 13
- Gesamt: 86

## Zusatzdateien
- permissions_example.json
- action_catalog_example.json
- manifest.json
- quality_check_report.json

## Zentrale Regeln
- Kein erfundener Datenbank- oder Toolzugriff.
- Keine Behauptung einer Abfrage oder Aktion, wenn sie nicht tatsächlich erfolgt ist.
- Dynamische Preise, Bestände und Termine kommen aus aktuellen freigegebenen Quellen.
- Lesen, Vorschlag, Entwurf, Freigabe und Ausführung werden getrennt.
- Kritische und irreversible Aktionen benötigen menschliche Freigabe.
- Audit-Logs, Least Privilege, Fehlerbehandlung und Datenschutz sind berücksichtigt.
