# Authorization

Dieses Dokument definiert verbindliche Autorisierungsregeln fuer API-Endpunkte.

## Grundprinzip

Rechtepruefungen muessen konsistent, wiederverwendbar und zentral implementiert sein.

## Regel fuer administrative Endpunkte

Administrative Endpunkte duerfen keine eigene Rollenpruefung ad hoc implementieren.

Sie muessen einen zentralen Auth-Guard oder eine gemeinsame Dependency verwenden, beispielsweise:

- require_authenticated_user
- require_active_user
- require_admin_user

## Verbindliche Anforderungen

- Kein Duplizieren semantisch gleicher Prueflogik in mehreren Routen.
- Einheitliche Antwortcodes fuer Auth- und Rechteverletzungen.
- Trennung zwischen Authentifizierung und Autorisierung.
- Admin-Pruefung immer nach erfolgreicher Token- und Aktivstatuspruefung.

## HTTP-Semantik

- 401 fuer fehlende, ungueltige oder abgelaufene Authentifizierung.
- 403 fuer authentifizierte Benutzer ohne ausreichende Rechte oder deaktivierte Benutzer.

## Umsetzungshinweise

- Guards bevorzugt in gemeinsamen Utilities oder Dependencies kapseln.
- Routen sollen Guard-Ergebnis konsumieren, nicht selbst Sicherheitsentscheidungen duplizieren.
- Tests muessen mindestens 401, 403 und erfolgreichen Admin-Zugriff abdecken.
