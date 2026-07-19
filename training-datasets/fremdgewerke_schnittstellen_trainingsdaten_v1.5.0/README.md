# Fremdgewerke & Schnittstellen – Trainingsdaten v1.5.0

Dieses Paket trainiert einen deutschsprachigen Fachassistenten für einen Natursteinbetrieb.

## Inhalte

- Abgrenzung zu Sanitär, Elektro, Estrich, Rohbau, Abdichtung, Statik und Planung
- mehrstufige Dialoge und gezielte Rückfragen
- höfliche Fehlerkorrektur und Prämissen-Hinterfragung
- Umgang mit unklaren Laienbegriffen
- Tagesberichte, Leistungsnachweise, Mängelmeldungen und Fotodokumentation
- interne Kommunikation, Materialbestellung, Arbeitsanweisung, Termin- und Kapazitätsplanung
- Notfälle und Ausnahmesituationen: Materialschäden, Witterung, Personalausfall und Lieferverzug
- sichere Sofortmaßnahmen, neutrale Ereignisdokumentation, Eskalation und Wiederanlauf nach Prüfung

## Dateien

- `training.jsonl`: ausschließlich für das Training
- `validation.jsonl`: ausschließlich für die Validierung
- `test.jsonl`: ausschließlich für den abschließenden Test
- `manifest.json`: Version, Themen, Regeln, Prüfsummen und Dateigrößen

## Notfall-Reaktionslogik

1. Unmittelbare Gefahren stoppen und Arbeitsbereich sichern.
2. Personen-, Material- und Folgeschäden begrenzen.
3. Beobachteten Zustand mit Zeitpunkt, Ort, Fotos und betroffenen Leistungen dokumentieren.
4. Zuständige interne oder externe Stelle informieren.
5. Auswirkungen auf Qualität, Ablauf und Termin prüfen.
6. Erst nach fachlicher Klärung, sicherer Neuplanung oder Freigabe weiterarbeiten.

Das Modell darf keine Schadensursachen, Schuldzuweisungen, Ersatzliefertermine, Personalverfügbarkeiten, Freigaben oder verbindlichen Fertigstellungstermine erfinden. Sicherheit und Schadensbegrenzung haben Vorrang vor Termin- oder Produktivitätsdruck. Die Datensplits dürfen nicht vermischt werden.
