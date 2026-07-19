# Fremdgewerke & Schnittstellen – Trainingsdaten

Version 1.2.0

Dieses Paket trainiert einen deutschsprachigen Fachassistenten für einen Natursteinbetrieb. Im Mittelpunkt stehen die Abgrenzung zu Fremdgewerken, mehrstufige Dialoge sowie die höfliche Korrektur falscher oder unvollständiger Prämissen.

## Dateien

- `training.jsonl`: Trainingsdaten
- `validation.jsonl`: unabhängige Validierungsdaten
- `test.jsonl`: zurückgehaltene Testdaten
- `manifest.json`: Version, Regeln, Themen und Prüfsummen

## Methodische Schwerpunkte

- Einzelfragen und mehrstufige Gespräche
- klare Zuständigkeitsgrenzen zu Sanitär, Elektro, Estrich, Rohbau, Abdichtung, Statik und Planung
- höfliche Fehlerkorrektur ohne Bloßstellung
- Hinterfragen falscher Prämissen statt ungeprüfter Zustimmung
- Klärung ungenauer Laienbegriffe durch gezielte Rückfragen
- keine pauschale Zusicherung von Materialeigenschaften ohne eindeutige Sorten- und Produktangabe
- Verweis auf Auftrag, Leistungsverzeichnis, Planung, Herstellerunterlagen oder Bauleitung, wenn die Zuständigkeit nicht eindeutig ist

## Antwortmuster bei falschen Annahmen

1. Annahme respektvoll relativieren: „Das lässt sich so pauschal nicht sagen.“
2. Fachlich korrekten Kern nennen.
3. Risiken oder fehlende Angaben erklären.
4. Eine konkrete Rückfrage oder den zuständigen Ansprechpartner nennen.
5. Keine fremden Leistungen, Prüfungen oder Freigaben übernehmen.

## Datentrennung

Die drei Splits dürfen nicht vermischt werden. Testdaten sind ausschließlich für die abschließende Bewertung vorgesehen. Inhaltlich ähnliche Fälle wurden mit anderen Formulierungen, Objekten und Dialogverläufen angelegt.

## Format

Jede JSONL-Zeile enthält `messages` und `metadata`. Mehrstufige Datensätze enthalten mehrere abwechselnde User- und Assistant-Nachrichten.
