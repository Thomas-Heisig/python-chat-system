# Security Documentation Overview

Diese Uebersichtsseite beschreibt den zentralen Einstieg in die Security-Dokumentation unter `docs/security/`.

## Dokumente

- [authentication.md](authentication.md): Authentifizierungs-Mindeststandard (Bearer-Token, Token-Validierung, aktive Benutzer)
- [authorization.md](authorization.md): Verbindliche Autorisierungsregeln und Guard-Konvention fuer administrative Endpunkte
- [admin-actions.md](admin-actions.md): Katalog und Vorgaben fuer geschuetzte Admin-Aktionen, inkl. Cleanup-Endpunkt
- [audit-logging.md](audit-logging.md): Mindeststandard fuer Audit-Events bei sicherheitskritischen Aktionen
- [secret-leak-playbook.md](secret-leak-playbook.md): Vorgehen bei Secret-Funden, Rotation, Bereinigung, Allowlist-Regeln und Abschlusskriterien

## Operativer Secret-Review

- Wiederholbarer Review-Lauf: `python scripts/review_secret_scan.py`
- Strenger Modus (CI-geeignet): `python scripts/review_secret_scan.py --strict`
- Report-Ausgabe: `docs/security/reports/secret-scan-review-YYYYMMDD.md`
- Pflichtkommentare fuer Allowlist-Aenderungen: `config/secret-scan-change-comments.json` (`reason` + `reference` je `new`/`removed`-Regel)

## Empfohlene Reihenfolge fuer Implementierung

1. authentication.md
2. authorization.md
3. admin-actions.md
4. audit-logging.md
5. secret-leak-playbook.md

Begruendung:

- Zuerst Identitaet und Session/Token sicherstellen.
- Danach Rollen- und Rechtepruefung zentralisieren.
- Anschliessend konkrete Admin-Aktionen auf die Guard-Regeln heben.
- Danach revisionsfaehiges Audit-Logging fuer diese Aktionen durchgaengig aktivieren.
- Anschliessend Secret-Leak-Response und Allowlist-Governance als operativen Teamprozess verankern.

## Empfohlene Reihenfolge fuer Reviews

1. authentication.md
2. authorization.md
3. admin-actions.md
4. audit-logging.md
5. secret-leak-playbook.md

Review-Checkpunkte je Schritt:

- Authentifizierung: 401-Pfade fuer fehlende/ungueltige Tokens, aktive Benutzerpruefung.
- Autorisierung: keine ad-hoc-Rollenpruefung in Routen, stattdessen zentrale Guard-Dependency.
- Admin-Aktionen: 403-Pfade fuer Nicht-Admins/deaktivierte Benutzer, konsistente Fehlersemantik.
- Audit-Logging: Pflichtfelder vollstaendig, Dry-Run und Execute klar unterscheidbar, keine sensiblen Daten in Logs.
- Secret-Leak-Playbook: Rotation/Revoke eindeutig, kein echtes Secret in Allowlist, Abschluss erst nach gruener Scan-Wiederholung.

## Referenz-Endpunkt

Der Endpunkt `POST /api/settings/chat/cleanup-obsolete` ist der aktuelle Referenzfall fuer diese Sicherheitsstandards.
