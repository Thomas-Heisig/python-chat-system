# Fremdgewerke & Schnittstellen – Trainingsdaten v1.4.0

Dieses Paket trainiert einen deutschsprachigen Fachassistenten für einen Natursteinbetrieb.

## Inhalte

- Abgrenzung zu Sanitär, Elektro, Estrich, Rohbau, Abdichtung, Statik und Planung
- mehrstufige Dialoge und gezielte Rückfragen
- höfliche Fehlerkorrektur und Prämissen-Hinterfragung
- Umgang mit unklaren Laienbegriffen
- Tagesberichte, Leistungsnachweise, Mängelmeldungen und Fotodokumentation
- interne Kommunikation und Teamarbeit
- Materialbestellungen und Bestellvorbereitungen
- Arbeitsanweisungen für Werkstatt, Transport und Montage
- Terminplanung mit Vorbehalten und Abhängigkeiten
- Kapazitätsprüfung ohne erfundene Personal- oder Betriebsdaten

## Dateien

- `training.jsonl`: ausschließlich für das Training
- `validation.jsonl`: ausschließlich für die Validierung
- `test.jsonl`: ausschließlich für den abschließenden Test
- `manifest.json`: Version, Themen, Regeln, Prüfsummen und Dateigrößen

## Wichtige Modellregeln

Das Modell darf keine Lagerbestände, Lieferzeiten, Personalkapazitäten, Fertigstellungstermine, Maße, Mengen, Qualifikationen oder Freigaben erfinden. Bei fehlenden Angaben soll es gezielt nachfragen oder offene Felder sichtbar kennzeichnen. Bestellvorbereitungen und Terminbewertungen sind als prüfbare Entwürfe zu formulieren, nicht als bereits ausgelöste Bestellung oder verbindliche Zusage.

Die Datensplits dürfen nicht vermischt werden.
