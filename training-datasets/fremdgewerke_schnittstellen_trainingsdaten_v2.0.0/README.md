# Fremdgewerke & Schnittstellen – Trainingsdaten v2.0.0

Dieses Paket enthält diversifizierte deutschsprachige Chat-Trainingsdaten für einen Natursteinbetrieb.

## Dateien
- `training.jsonl`: 204 Datensätze
- `validation.jsonl`: 40 Datensätze
- `test.jsonl`: 40 Datensätze
- `manifest.json`: Metadaten, Prüfsummen und Regeln

## Qualitätsmerkmale
- unterschiedliche Rollen: Privatkunde, Architekt, Bauleitung, Montage, Verkauf, Buchhaltung und Einsatzleitung
- einfache, mittlere und schwierige Praxisfälle
- kurze, mittlere und ausführliche Antworten
- Einzelfragen und mehrstufige Dialoge
- höfliche Korrektur falscher Annahmen
- Rückfragen und Arbeitsstopps bei fehlenden Freigaben
- klare Trennung von Naturstein-, Sanitär-, Elektro-, Planungs- und Fremdgewerksleistungen
- Dokumentation, interne Kommunikation, Notfälle sowie rechtlich zurückhaltende Orientierung

## Format
Jede Zeile ist ein eigenständiges JSON-Objekt im Chat-Format mit `messages` und `metadata`.

## Split-Regel
Training, Validierung und Test dürfen nicht vermischt werden. Der Testsplit ist ausschließlich für die abschließende Bewertung vorgesehen.

## Rechtlicher Hinweis
Die Datensätze ersetzen keine Rechtsberatung. Vertragsgrundlage, Abnahme, Leistungsumfang und aktuelle Rechtslage müssen im Einzelfall geprüft werden.
