# Support

## Unterstuetzungsumfang

Dieses Projekt befindet sich in aktiver Entwicklung. Unterstuetzung erfolgt im Rahmen der verfuegbaren Zeit und kann nicht innerhalb einer bestimmten Frist garantiert werden.

Unterstuetzt wird grundsaetzlich nur:

- der aktuelle Stand des Branches `main`
- die neueste veroeffentlichte Version
- die in der README beschriebenen Installationswege
- nachvollziehbare Fehler unter einer unterstuetzten Umgebung
- unveraenderte oder eindeutig dokumentierte Projektstaende

Aeltere Commits, private Forks und stark veraenderte Installationen koennen in der Regel nur eingeschraenkt beurteilt werden.

## Geeigneter Meldeweg

Verwenden Sie GitHub Issues fuer:

- reproduzierbare Fehler
- Funktionswuensche
- Verbesserungsvorschlaege
- unklare oder fehlerhafte Dokumentation
- Installations- und Konfigurationsprobleme
- Kompatibilitaetsprobleme
- nachvollziehbare Modell- oder Trainingsfehler

Fuer kleinere Rueckfragen sollte zunaechst die vorhandene Dokumentation geprueft werden.

## Klare Einordnung von Anfragen

Zur schnelleren Bearbeitung ordnen Sie Ihr Anliegen im Issue-Titel und in der Beschreibung eindeutig einem Typ zu:

- `bug`: technischer Defekt mit reproduzierbarem Fehlverhalten
- `question`: Bedienungsfrage oder unklarer Ablauf ohne klaren Defekt
- `feature`: Erweiterungswunsch oder Produktverbesserung
- `security`: vermutete Sicherheitsluecke (nicht oeffentlich melden, siehe Abschnitt Sicherheit)

Empfohlene Titelpraefixe:

- `[BUG] ...`
- `[QUESTION] ...`
- `[FEATURE] ...`
- `[DOCS] ...`

## Vor dem Erstellen eines Issues

Bitte pruefen Sie zunaechst:

1. Gibt es bereits ein passendes Issue?
2. Tritt das Problem im aktuellen Stand von `main` weiterhin auf?
3. Wurden die Schritte aus [README.md](../README.md) befolgt?
4. Wurde die Konfiguration mit [.env.example](../.env.example) verglichen?
5. Sind Python-, Node- und GPU-Abhaengigkeiten kompatibel?
6. Kann das Problem nach einem sauberen Neustart reproduziert werden?
7. Handelt es sich moeglicherweise um ein Problem des verwendeten Modells oder einer Drittanbieterbibliothek?

Bei Abhaengigkeitsproblemen kann eine neue virtuelle Umgebung sinnvoller sein als die Reparatur einer aelteren Umgebung.

## Fehlerbericht

Ein Fehlerbericht sollte moeglichst folgende Angaben enthalten:

- kurze und eindeutige Beschreibung
- erwartetes Verhalten
- tatsaechlich beobachtetes Verhalten
- vollstaendige Schritte zur Reproduktion
- betroffene Version oder Commit-SHA
- Betriebssystem und Version
- Python-Version
- Node.js- und npm-Version
- verwendeter Startbefehl
- verwendetes Modellformat und Backend
- relevante Konfiguration
- Fehlermeldungen und bereinigte Logs
- Information, ob der Fehler regelmaessig oder nur gelegentlich auftritt

Beispiel:

```text
Betriebssystem: Windows 11
Commit: 0123456789abcdef
Python: 3.12.x
Node.js: 22.x
npm: 10.x
GPU: NVIDIA RTX 3060 12 GB
Backend: llama.cpp
Modellformat: GGUF
Startbefehl: python start.py --reload
```

## Diagnosebefehle

### Python-Version

```bash
python --version
```

### Installierte Python-Pakete

```bash
python -m pip list
```

### Node.js und npm

```bash
node --version
npm --version
```

### Backend-Tests

```bash
pip install -r requirements-dev.txt
pytest
```

### Python-Pruefung

```bash
ruff check .
```

### Frontend-Tests

```bash
cd frontend
npm ci
npm run test:run
```

### Frontend-Build

```bash
cd frontend
npm run build
```

Bitte geben Sie an, welcher Befehl fehlgeschlagen ist und an welcher Stelle der Fehler auftrat.

## Logs und vertrauliche Informationen

Logs und Screenshots muessen vor der Veroeffentlichung geprueft und bereinigt werden.

Veroeffentlichen Sie insbesondere keine:

- Passwoerter
- API-Schluessel
- Zugriffstokens
- Cookies oder Sitzungsdaten
- privaten Schluessel
- vollstaendigen `.env`-Dateien
- Datenbankinhalte
- personenbezogenen Daten
- interne Hostnamen oder Netzwerkdetails
- vertraulichen Chatverlaeufe
- vollstaendigen Modell- oder Dataset-Pfade, wenn diese sensible Angaben enthalten
- proprietaeren Trainingsdaten

Teilen Sie moeglichst nur den fuer die Fehleranalyse erforderlichen Ausschnitt.

## Modellprobleme

Bei Problemen mit einem Modell sollten zusaetzlich angegeben werden:

- Modellname
- Modellquelle
- Modellformat
- Quantisierung
- Dateigroesse
- verwendetes Backend
- CPU- oder GPU-Ausfuehrung
- verfuegbarer RAM und VRAM
- relevante Modell-Einstellungen
- Ergebnis des Modellscans
- genaue Fehlermeldung bei Laden oder Aktivieren

Grosse Modelldateien sollen nicht an ein Issue angehaengt werden. Ein Link zur urspruenglichen oeffentlichen Quelle ist ausreichend.

Fuer Modelle aus nicht oeffentlich zugaenglichen oder rechtlich unklaren Quellen kann keine vollstaendige Unterstuetzung zugesichert werden.

## Trainingsprobleme

Bei Problemen mit der Training Workbench sollten zusaetzlich angegeben werden:

- verwendeter Trainer
- Basismodell und Modellformat
- Dataset-Format
- Anzahl der Trainingsbeispiele
- relevante Hyperparameter
- Ergebnis des Preflight-Checks
- Jobstatus
- letzter erfolgreicher Trainingsschritt
- CUDA- und GPU-Konfiguration
- Information, ob 4-Bit-Laden aktiviert wurde
- Information, ob CPU-Training erlaubt wurde

Trainingsdaten duerfen nur in anonymisierter und rechtlich zulaessiger Form veroeffentlicht werden.

## Funktionswuensche

Ein Funktionswunsch sollte moeglichst erklaeren:

- welches konkrete Problem geloest werden soll
- wer die Funktion benoetigt
- wie der derzeitige Ablauf aussieht
- welches Verhalten erwartet wird
- welche Alternativen bereits geprueft wurden
- ob Auswirkungen auf API, Datenbank, Frontend oder Modell-Backends zu erwarten sind

Eine vorgeschlagene technische Umsetzung ist hilfreich, aber nicht erforderlich.

Die Annahme eines Vorschlags bedeutet nicht, dass oder wann er umgesetzt wird.

## Dokumentationsprobleme

Bei einem Dokumentationsproblem sollten angegeben werden:

- betroffene Datei oder Seite
- unklare oder falsche Passage
- beobachtete Abweichung zum tatsaechlichen Verhalten
- gewuenschte Korrektur

Kleinere Korrekturen koennen auch als Pull Request eingereicht werden.

## Sicherheitsprobleme

Vermutete Sicherheitsluecken duerfen nicht als oeffentliches Issue veroeffentlicht werden.

Verwenden Sie das in [SECURITY.md](SECURITY.md) beschriebene vertrauliche Meldeverfahren.

Dazu gehoeren insbesondere:

- Umgehung der Authentifizierung
- Zugriff auf fremde Daten
- SSRF
- Path Traversal
- Remote Code Execution
- Offenlegung von Zugangsdaten
- unzulaessiger Zugriff auf lokale Dateien
- Schwachstellen beim Upload oder Dataset-Import
- sicherheitsrelevante Fehler in Modell- oder Trainingspfaden

Allgemeine Konfigurationsfragen und nicht sicherheitsrelevante Fehler gehoeren weiterhin in die oeffentlichen Issues.

## Verhaltensmeldungen

Belaestigung, persoenliche Angriffe und andere Verstoesse gegen den Verhaltenskodex sind keine technischen Sicherheitsluecken.

Das Meldeverfahren ist in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) beschrieben.

## Reaktionszeiten

Es gibt keine garantierten Reaktions- oder Loesungszeiten.

Orientierende Priorisierung:

- Sicherheitsmeldungen ueber den vertraulichen Kanal: moeglichst zeitnah
- reproduzierbare `bug`-Meldungen mit klaren Schritten und Logs: bevorzugt
- `question`- und `feature`-Anfragen: nach Verfuegbarkeit

Fehlende Reproduktion, unvollstaendige Angaben oder nicht bereinigte Logs koennen die Bearbeitung deutlich verzoegern.

## Nicht zugesicherte Unterstuetzung

In der Regel nicht abgedeckt sind:

- allgemeine Python-, JavaScript- oder Linux-Schulungen
- Einrichtung fremder Reverse Proxys oder Cloud-Plattformen
- Betrieb nicht dokumentierter Forks
- Fehler in veralteten Projektstaenden
- Beschaffung oder Lizenzpruefung von KI-Modellen
- individuelle Modell- oder Dataset-Beratung ohne reproduzierbares Projektproblem
- Leistungszusagen fuer bestimmte Hardware
- Wiederherstellung beschaedigter Datenbanken oder Trainingsartefakte
- Rechtsberatung zu Modellen, Datasets oder generierten Inhalten
- garantierte Reaktions- oder Loesungszeiten

Hinweise zu solchen Themen koennen freiwillig gegeben werden, begruenden aber keinen dauerhaften Supportanspruch.

## Pull Requests

Wenn Sie selbst eine Korrektur einreichen moechten, beachten Sie bitte:

- [Beitragsrichtlinien](CONTRIBUTING.md)
- [Verhaltenskodex](CODE_OF_CONDUCT.md)
- vorhandene Architektur- und Projektdokumentation
- relevante Tests und Qualitaetspruefungen

Bei groesseren Aenderungen sollte vor der Umsetzung ein Issue zur Abstimmung eroeffnet werden.
