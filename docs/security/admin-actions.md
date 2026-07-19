# Geschuetzte Admin-Aktionen

Dieses Dokument beschreibt sicherheitskritische Admin-Aktionen und die verbindlichen Mindestanforderungen fuer Zugriffsschutz, Dry-Run und Auditierbarkeit.

## Geltungsbereich

Folgende Aktionsklassen gelten als administrativ und muessen zentral abgesichert werden:

- geschuetzte Cleanup-Endpunkte
- Benutzer- und Rollenverwaltung
- Plugin-Einstellungen mit globaler Wirkung
- Trainingsdaten-Loeschung
- Modellregistrierung und Modell-Lifecycle-Eingriffe
- systemweite Konfigurationsaenderungen
- Wartungs- und Reparaturaktionen

## Cleanup von Systemeinstellungen

Der Cleanup-Endpunkt darf ausschliesslich von authentifizierten, aktiven Admin-Benutzern ausgefuehrt werden.

Betroffener Endpunkt:

- POST /api/settings/chat/cleanup-obsolete

### Zugriffskontrolle

- Kein Bearer-Token: HTTP 401
- Ungueltiger oder abgelaufener Token: HTTP 401
- Authentifizierter Benutzer ohne Admin-Rolle: HTTP 403
- Deaktivierter Admin-Benutzer: HTTP 403
- Aktiver Admin-Benutzer: Zugriff erlaubt

### Dry-Run

Der Endpunkt unterstuetzt einen Dry-Run-Modus.

Im Dry-Run werden passende Datensaetze ermittelt, aber nicht geloescht.

### Audit-Anforderungen

Jede Ausfuehrung sollte mindestens folgende Daten protokollieren:

- actor_user_id
- actor_role
- action
- dry_run
- matched_count
- deleted_count
- remaining_count
- timestamp
- request_id
- result
- error_message

### Ergebnis- und Fehlersemantik

- Erfolgreicher Dry-Run liefert Statistik ohne Datenmutation.
- Erfolgreiche Ausfuehrung liefert Statistik nach Loeschlauf.
- Fehlerantworten muessen den gleichen Sicherheitsstandard wie andere Admin-Endpunkte einhalten und duerfen keine sensitiven Interna offenlegen.

## Weitere geschuetzte Admin-Aktionen (Mindeststandard)

Die folgenden Bereiche muessen dieselben Schutzprinzipien verwenden wie der Cleanup-Endpunkt:

- Benutzer- und Rollenverwaltung
- globale Plugin-Konfigurationen
- Trainingsdaten-Loeschung und irreversible Datenbereinigungen
- Modellregistrierung, Aktivierung, Deaktivierung und Loeschung
- globale Reset- und Reparaturaktionen
