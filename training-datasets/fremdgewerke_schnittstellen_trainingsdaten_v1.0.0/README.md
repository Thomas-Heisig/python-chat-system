# Trainingsdaten: Fremdgewerke & Schnittstellen

Dieses Paket enthält deutschsprachige Trainingsdaten zur Abgrenzung der Zuständigkeiten eines Natursteinbetriebs gegenüber anderen Gewerken.

## Ziel

Das Modell soll:

- die eigene Leistung des Natursteinbetriebs benennen,
- Sanitär-, Elektro-, Abdichtungs-, Statik-, Estrich- und Rohbauleistungen sauber abgrenzen,
- notwendige Vorleistungen und Abstimmungen nennen,
- bei erkennbaren Mängeln auf Prüf- und Hinweispflichten verweisen,
- keine vertraglichen Zuständigkeiten, Freigaben oder Qualifikationen erfinden,
- bei Unklarheit auf Auftrag, Leistungsverzeichnis, Planung, Herstellerangaben, Bauleitung oder Fachgewerk verweisen.

## Dateien

- `training.jsonl`: 24 Datensätze für das Training
- `validation.jsonl`: 6 Datensätze für die Validierung
- `test.jsonl`: 6 Datensätze für den abschließenden Test
- `manifest.json`: Metadaten, Dateigrößen und SHA-256-Prüfsummen

## Themen

- Sanitär
- Elektro
- Bauphysik, Abdichtung und Tragfähigkeit
- Zusammenarbeit und Vorleistungen anderer Gewerke

## Format

Jede Zeile ist ein eigenständiges JSON-Objekt mit `messages` und `metadata`. Die Aufteilung darf nicht vermischt werden.

## Fachlicher Hinweis

Die Antworten beschreiben typische Zuständigkeitsgrenzen. Der konkrete Leistungsumfang ergibt sich immer aus Vertrag, Leistungsverzeichnis, Planung, Herstellerangaben und den Gegebenheiten des jeweiligen Projekts. Die Daten ersetzen keine rechtliche, statische oder fachplanerische Prüfung.
