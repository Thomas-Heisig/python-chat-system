# Trainingsdaten: Fremdgewerke & Schnittstellen

Dieses Paket enthält deutschsprachige Trainingsdaten zur Abgrenzung der Zuständigkeiten eines Natursteinbetriebs gegenüber anderen Gewerken.

## Ziel

Das Modell soll:

- die eigene Leistung des Natursteinbetriebs benennen,
- Sanitär-, Elektro-, Abdichtungs-, Statik-, Estrich- und Rohbauleistungen sauber abgrenzen,
- notwendige Vorleistungen und Abstimmungen nennen,
- bei erkennbaren Mängeln auf Prüf- und Hinweispflichten verweisen,
- keine vertraglichen Zuständigkeiten, Freigaben oder Qualifikationen erfinden,
- bei Unklarheit auf Auftrag, Leistungsverzeichnis, Planung, Herstellerangaben, Bauleitung oder Fachgewerk verweisen,
- in mehrstufigen Gesprächen den bisherigen Kontext berücksichtigen und konsistent auf Nachfragen reagieren.

## Dateien

- `training.jsonl`: 32 Datensätze, davon 8 mehrstufige Dialoge
- `validation.jsonl`: 8 Datensätze, davon 2 mehrstufige Dialoge
- `test.jsonl`: 8 Datensätze, davon 2 mehrstufige Dialoge
- `manifest.json`: Metadaten, Dateigrößen und SHA-256-Prüfsummen

## Themen

- Sanitär
- Elektro
- Bauphysik, Abdichtung und Tragfähigkeit
- Zusammenarbeit und Vorleistungen anderer Gewerke

## Mehrstufige Dialoge

Mehrstufige Datensätze enthalten nach der ersten Assistentenantwort mindestens eine weitere Nutzerfrage und eine kontextbezogene Antwort. Sie trainieren insbesondere:

- konsistente Zuständigkeitsabgrenzung bei Nachfragen,
- Unterscheidung zwischen mechanischer Bearbeitung und fachfremdem Anschluss,
- Reaktion auf Mängel, Termindruck und unsichere Vorleistungen,
- Verweis auf Auftrag, Planung, Herstellerangaben oder Fachgewerk,
- Vermeidung widersprüchlicher oder zu weitreichender Zusagen.

## Format

Jede Zeile ist ein eigenständiges JSON-Objekt mit `messages` und `metadata`. In `metadata.dialogue_type` steht `single_turn` oder `multi_turn`. Die Aufteilung in Training, Validierung und Test darf nicht vermischt werden.

## Fachlicher Hinweis

Die Antworten beschreiben typische Zuständigkeitsgrenzen. Der konkrete Leistungsumfang ergibt sich immer aus Vertrag, Leistungsverzeichnis, Planung, Herstellerangaben und den Gegebenheiten des jeweiligen Projekts. Die Daten ersetzen keine rechtliche, statische oder fachplanerische Prüfung.
