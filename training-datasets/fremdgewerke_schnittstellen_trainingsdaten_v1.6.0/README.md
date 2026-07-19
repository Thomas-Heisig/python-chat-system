# Fremdgewerke & Schnittstellen – Trainingsdaten v1.6.0

Dieses Paket trainiert einen deutschsprachigen Fachassistenten für einen Natursteinbetrieb.

## Inhalte

- Abgrenzung zu Sanitär, Elektro, Estrich, Rohbau, Abdichtung, Statik und Planung
- mehrstufige Dialoge, Fehlerkorrektur und Umgang mit Laienbegriffen
- Tagesberichte, Leistungsnachweise, Mängelmeldungen und Fotodokumentation
- interne Kommunikation, Materialbestellung, Arbeitsanweisung, Termin- und Kapazitätsplanung
- Notfälle: Materialschäden, Witterung, Personalausfall und Lieferverzug
- rechtlich zurückhaltende Orientierung zu Gewährleistung, Haftung, Vorbehalten und Rechnungsprüfung

## Rechtliche Antwortlogik

1. Vertragsgrundlage und konkrete Dokumente prüfen: BGB, wirksam vereinbarte VOB/B, Individualvereinbarungen, Auftrag und Nachträge.
2. Abnahme, Leistungsart und Leistungsumfang klären, bevor Fristen genannt werden.
3. Keine pauschale Haftungszuweisung oder verbindliche Rechtsberatung geben.
4. Erkennbare Bedenken konkret, schriftlich und nachweisbar dokumentieren.
5. Bei Rechnungsabweichungen Bestellung, Auftragsbestätigung, Lieferschein, Leistungsnachweis und Rechnung abgleichen.
6. Ungeklärte Beträge nicht freigeben; Erläuterung, Korrektur oder Gutschrift anfordern.
7. Bei hohem Streitwert, unklarer Vertragslage oder Haftungsrisiko eine rechtliche beziehungsweise kaufmännische Prüfung empfehlen.

## Dateien

- `training.jsonl`: ausschließlich für das Training
- `validation.jsonl`: ausschließlich für die Validierung
- `test.jsonl`: ausschließlich für den abschließenden Test
- `manifest.json`: Version, Themen, Regeln, Quellen, Prüfsummen und Dateigrößen

Die Datensplits dürfen nicht vermischt werden. Das Modell darf keine Rechtslage, Vertragsklauseln, Fristen, Haftungsanerkenntnisse, Zahlungsfreigaben oder Tatsachen erfinden.
