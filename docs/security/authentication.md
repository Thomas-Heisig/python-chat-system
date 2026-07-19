# Authentication

Dieses Dokument beschreibt den Mindeststandard fuer Authentifizierung in API-Endpunkten.

## Token-basierte Authentifizierung

- API-Zugriffe auf geschuetzte Endpunkte erfolgen ueber Bearer-Token.
- Tokens muessen auf Gueltigkeit und Ablauf geprueft werden.
- Der Token muss auf einen existierenden Benutzer aufloesbar sein.

## Mindestpruefungen

- Bearer-Token vorhanden.
- Bearer-Token gueltig und nicht abgelaufen.
- Benutzer aus Token existiert.
- Benutzerkonto ist aktiv.

## Fehlercodes

- 401 bei fehlendem oder ungueltigem Token.
- 403 bei deaktiviertem Benutzerkonto.

## Zusammenspiel mit Autorisierung

Nach erfolgreicher Authentifizierung folgt die rollenbasierte Autorisierung gemaess docs/security/authorization.md.
