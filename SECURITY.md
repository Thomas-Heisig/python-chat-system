# Sicherheitsrichtlinie

## Unterstützte Versionen

Das Projekt befindet sich derzeit in aktiver Entwicklung vor Version `1.0.0`.

Sicherheitskorrekturen werden grundsätzlich nur für den aktuellen Stand des Branches `main` und die neueste veröffentlichte Version bereitgestellt.

| Version | Sicherheitsupdates |
|---|---:|
| aktueller Stand von `main` | ✅ |
| neueste veröffentlichte Version | ✅ |
| ältere Versionen und Commits | ❌ |
| Forks und veränderte Installationen | ❌ |

Für ältere Stände werden keine separaten Sicherheitsupdates garantiert. Anwender sollten vor einer Meldung prüfen, ob das Problem auch im aktuellen Stand von `main` besteht.

## Sicherheitslücke vertraulich melden

Bitte veröffentlichen Sie vermutete Sicherheitslücken nicht als öffentliches GitHub-Issue, nicht als öffentliche Diskussion und nicht als Pull Request mit einem funktionsfähigen Exploit.

Verwenden Sie bevorzugt GitHubs Funktion für private Sicherheitsmeldungen:

[Private Sicherheitslücke melden](https://github.com/Thomas-Heisig/python-chat-system/security/advisories/new)

Falls diese Funktion nicht verfügbar ist, eröffnen Sie bitte zunächst ein öffentliches Issue ohne technische Details und bitten dort um einen vertraulichen Kontaktweg.

Veröffentlichen Sie dabei insbesondere keine:

- Passwörter oder Zugangsdaten
- API-Schlüssel oder Tokens
- privaten Schlüssel
- personenbezogenen Daten
- vollständigen Datenbankinhalte
- internen Netzwerkadressen
- Modell- oder Dataset-Inhalte mit vertraulichen Daten
- ausführbaren Exploits gegen öffentlich erreichbare Systeme

## Benötigte Angaben

Eine Sicherheitsmeldung sollte möglichst folgende Informationen enthalten:

- betroffene Version oder Commit-SHA
- betroffene Datei, Komponente oder API-Route
- Art der Schwachstelle
- notwendige Voraussetzungen
- nachvollziehbare Schritte zur Reproduktion
- erwartetes und tatsächliches Verhalten
- mögliche Auswirkungen
- vorgeschlagene Gegenmaßnahme, falls bekannt
- verwendetes Betriebssystem und relevante Laufzeitversionen
- Information, ob die Schwachstelle bereits öffentlich bekannt ist

Ein minimaler Proof of Concept ist hilfreich, sofern er keine fremden Systeme, Konten oder Daten gefährdet.

## Bearbeitung einer Meldung

Nach Eingang einer ausreichend vollständigen Meldung wird nach Möglichkeit:

1. der Eingang bestätigt,
2. die Schwachstelle reproduziert und bewertet,
3. der betroffene Umfang bestimmt,
4. eine Korrektur vorbereitet und getestet,
5. eine Veröffentlichung oder Sicherheitswarnung vorbereitet,
6. die meldende Person über das Ergebnis informiert.

Aufgrund des aktuellen Projektumfangs kann keine verbindliche Reaktions- oder Behebungsfrist zugesichert werden. Kritische und aus der Ferne ausnutzbare Schwachstellen werden vorrangig behandelt.

## Bewertung

Bei der Bewertung werden insbesondere berücksichtigt:

- Möglichkeit einer Ausnutzung aus der Ferne
- erforderliche Authentifizierung und Benutzerrechte
- Vertraulichkeit, Integrität und Verfügbarkeit
- Zugriff auf lokale Dateien oder interne Netzwerke
- mögliche Offenlegung von Zugangsdaten
- Einfluss auf Modell-, Dataset- und Trainingsartefakte
- Reproduzierbarkeit unter einer unterstützten Konfiguration

Die endgültige Einstufung kann von der ursprünglichen Einschätzung der meldenden Person abweichen.

## Koordinierte Offenlegung

Bitte veröffentlichen Sie technische Details erst, nachdem:

- eine Korrektur verfügbar ist,
- betroffene Anwender angemessen reagieren konnten oder
- eine gemeinsame Veröffentlichung vereinbart wurde.

Es wird versucht, die meldende Person vor einer Veröffentlichung über den geplanten Ablauf zu informieren. Ein Anspruch auf namentliche Erwähnung oder Vergütung besteht nicht.

## Nicht abgedeckte Bereiche

In der Regel nicht als Sicherheitslücke dieses Projekts behandelt werden:

- Probleme, die nur in veralteten Commits auftreten
- Schwachstellen in unveränderten Drittanbieter-Abhängigkeiten ohne projektspezifische Auswirkung
- fehlende Härtung bei absichtlich unsicherer Konfiguration
- öffentlich erreichbare Entwicklungsserver ohne Reverse Proxy oder Zugriffsschutz
- kompromittierte Betriebssysteme, Python-Umgebungen oder Administratorenkonten
- Social Engineering und Phishing
- Denial-of-Service durch rein theoretische oder nicht reproduzierbare Lastannahmen
- Ergebnisse automatischer Scanner ohne betroffenen Codepfad oder nachvollziehbaren Nachweis
- lokale Angriffe, die bereits vollständige Administratorrechte voraussetzen

Abhängigkeitsschwachstellen können dennoch gemeldet werden, wenn ein konkreter, im Projekt erreichbarer Angriffsweg besteht.

## Sicherheitsrelevante Betriebsgrenzen

Das Projekt ist derzeit nicht als ungeprüfte, direkt öffentlich erreichbare Produktionsanwendung vorgesehen.

Beim Betrieb sind mindestens folgende Maßnahmen erforderlich:

- eigenen sicheren `SECRET_KEY` setzen
- `.env`, Datenbanken und Zugangsdaten nicht versionieren
- Zugriff auf Backend und Frontend begrenzen
- für Internetbetrieb HTTPS und einen Reverse Proxy verwenden
- CORS auf tatsächlich benötigte Origins beschränken
- Firewall- und Dateisystemrechte prüfen
- Entwicklungsmodus und automatisches Reloading deaktivieren
- Abhängigkeiten und Basissystem regelmäßig aktualisieren
- Modelle und Datasets nur aus vertrauenswürdigen Quellen verwenden
- Upload-, Import- und Trainingsverzeichnisse schützen
- Backups getrennt und zugriffsgeschützt aufbewahren

Der Vite-Entwicklungsserver und `uvicorn --reload` sind nicht für einen ungeschützten öffentlichen Produktionsbetrieb vorgesehen.

## Automatisierte Sicherheitsprüfungen

Das Repository verwendet unter anderem:

- CodeQL
- GitHub Dependency Review
- Dependabot
- CI-Tests
- `npm audit`

Automatisierte Prüfungen können Schwachstellen übersehen oder Fehlalarme erzeugen. Ein erfolgreicher Scan ist daher kein Nachweis vollständiger Sicherheit.

## Grundsätze für Sicherheitsprüfungen

Sicherheitsprüfungen dürfen nur an eigenen Installationen oder mit ausdrücklicher Erlaubnis des Betreibers durchgeführt werden.

Nicht gestattet sind insbesondere:

- Zugriffe auf fremde Konten oder Daten
- dauerhafte Beeinträchtigung laufender Systeme
- Veränderung oder Löschung fremder Daten
- Installation von Schadsoftware
- Veröffentlichung vertraulicher Informationen
- Angriffe auf Systeme außerhalb des ausdrücklich freigegebenen Umfangs