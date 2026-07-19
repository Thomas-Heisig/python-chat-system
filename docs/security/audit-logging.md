# Audit Logging

Dieses Dokument definiert den Mindeststandard fuer Audit-Logging bei sicherheitskritischen Aktionen.

## Ziel

Administrative und irreversible Aktionen muessen nachvollziehbar, auswertbar und revisionsfaehig protokolliert werden.

## Pflichtfelder fuer sicherheitskritische Aktionen

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

## Logging-Verhalten

- Erfolgsfaelle und Fehlerfaelle protokollieren.
- Dry-Run und Ausfuehrungsmodus klar unterscheiden.
- Keine sensitiven Inhalte (z. B. Secrets, Roh-Token) in Audit-Events persistieren.

## Referenzfall

Fuer den Endpunkt POST /api/settings/chat/cleanup-obsolete gelten die Anforderungen aus docs/security/admin-actions.md.

## Integritaet

- Audit-Eintraege sollten unveraenderbar oder aenderungssicher gespeichert werden.
- Log-Quelle, Zeitstempel und Korrelation ueber request_id muessen konsistent sein.
