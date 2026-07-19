# Fremdgewerke & Schnittstellen – Trainingsdaten

Version: 1.3.0  
Sprache: Deutsch  
Format: JSONL im Chat-Nachrichtenformat

## Inhalt

Das Paket trainiert einen Fachassistenten für einen Natursteinbetrieb in vier Bereichen:

1. Abgrenzung zu Sanitär, Elektro, Bauphysik und anderen Gewerken
2. Mehrstufige Dialoge und kontextbezogene Rückfragen
3. Höfliche Fehlerkorrektur, Prämissen-Hinterfragung und Klärung von Laienbegriffen
4. Dokumentation und Nachvollziehbarkeit auf Baustellen

Neu in Version 1.3.0 sind Beispiele zu:

- Tagesberichten
- Leistungsnachweisen
- internen Mängelmeldungen
- Behinderungs- und Feststellungsvermerken
- Foto- und Zustandsdokumentation
- neutraler, beweissicherer Formulierung ohne erfundene Angaben oder ungeklärte Schuldzuweisungen

## Dateien

- `training.jsonl`: ausschließlich für das Training
- `validation.jsonl`: ausschließlich für die Validierung
- `test.jsonl`: ausschließlich für die abschließende Prüfung
- `manifest.json`: Version, Prüfsummen, Datensatzumfang und Regeln

## Dokumentationsprinzipien

Das Modell soll:

- nur bekannte Tatsachen dokumentieren,
- fehlende Angaben markieren oder gezielt erfragen,
- Beobachtung, Leistung, Behinderung, Mangel und Maßnahme trennen,
- keine Mengen, Zeiten, Ursachen, Verantwortlichkeiten oder Freigaben erfinden,
- ungeklärte Schuldzuweisungen vermeiden,
- Fotos eindeutig nach Baustelle, Datum, Bereich und Bauteil zuordnen,
- Datenschutz und betriebliche Vorgaben berücksichtigen.

## Split-Regel

Die drei JSONL-Dateien dürfen nicht vermischt werden. Testdaten sind erst nach Abschluss von Training und Validierung zu verwenden.
