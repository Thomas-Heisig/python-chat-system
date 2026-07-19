# Secret Leak Playbook

Dieses Playbook beschreibt den verbindlichen Ablauf bei Secret-Funden durch CI, lokale Hooks oder manuelle Reviews.

## 1. Erkennung

Trigger-Quellen:

- GitHub Workflow `Secret Scan` (`.github/workflows/secret-scan.yml`)
- Lokaler Hook `.githooks/pre-commit`
- Script `scripts/check_example_secrets.py`

Sofortmassnahme:

1. Commit/PR nicht mergen.
2. Fundstelle mit Dateipfad, Zeile und Muster dokumentieren.
3. Verantwortliche Maintainer informieren.

## 2. Triage

Klassifizierung:

1. `echtes secret`: produktiver API-Key, Token, Passwort, private key.
2. `test/placeholder`: absichtlich nicht-produktiver Beispielwert.
3. `false positive`: legitimer String ohne Secret-Risiko.

Bewertung:

- Ist der Wert bereits gepusht?
- Ist der Wert in CI-Logs, Artefakten oder Chatverlaeufen sichtbar?
- Betrifft der Wert externe Konten mit Kosten-/Datenrisiko?

## 3. Sofortreaktion bei echtem Secret

1. Secret unverzueglich beim Provider rotieren/revoken.
2. Neuen Wert nur in sicheren Stores hinterlegen (nicht im Repo).
3. Scope minimieren (least privilege, Ablaufdatum, IP-Bindung falls moeglich).
4. Betroffene Systeme auf Missbrauch pruefen (Provider-Logs, Audit-Trails).

## 4. Repository-Bereinigung

1. Secret aus allen betroffenen Dateien entfernen.
2. Beispiele auf Platzhalter umstellen (`your-...`, `<REPLACE_ME>`).
3. Falls Secret bereits in Historie liegt:
   - Rewriting-Prozess mit Maintainer-Freigabe planen.
   - Nach Rewrite Team auf verpflichtenden re-clone/rebase hinweisen.
4. Scanner erneut ausfuehren bis gruen.

## 5. Allowlist-Regelung

Datei:

- `config/secret-scan-allowlist.json`

Regeln:

1. Nur dokumentierte Platzhalter und bestaetigte False-Positives aufnehmen.
2. Keine echten Secrets in Allowlists eintragen.
3. Jede neue Allowlist-Regel muss begruendet sein (PR-Beschreibung + Reviewer-Freigabe).

## 6. Abschluss und Lernen

1. Incident-Notiz im Changelog/Ticket erfassen (ohne Secret selbst).
2. Ursache festhalten (z. B. Copy/Paste aus lokalem `.env`).
3. Praevention nachziehen:
   - Hook-/CI-Regeln erweitern
   - Setup-Doku verbessern
   - Team-Hinweis in Review-Checkliste aktualisieren

## 7. Verantwortlichkeiten

- Entwickler: Secret entfernen, Rotation anstossen, Fix bereitstellen.
- Reviewer: Keine Merge-Freigabe bis Rotation + Scan gruen.
- Maintainer: Prozessfreigabe, ggf. History-Rewrite koordinieren, Abschluss verifizieren.

## 8. Wiederholbare Allowlist-Review

Ziel:

- False-Positives kontrolliert halten, ohne echte Secrets zu maskieren.

Empfohlene Frequenz:

- mindestens monatlich
- zusaetzlich nach groesseren Doku-/Setup-Aenderungen

Ausfuehrung:

1. Review starten:
   - `python scripts/review_secret_scan.py`
2. Report pruefen:
   - `docs/security/reports/secret-scan-review-YYYYMMDD.md`
   - Abschnitt `Allowlist Trend` auswerten (`new`, `removed`, `unchanged` je Regelgruppe)
   - Abschnitt `Allowlist Entries` als Snapshot fuer den naechsten Vergleich nutzen
3. Bei Bedarf Allowlist anpassen:
   - `config/secret-scan-allowlist.json`
   - `config/secret-scan-change-comments.json` fuer jede neue/entfernte Regel aktualisieren (`reason` + `reference`)
4. Abschlusstest laufen lassen:
   - `python scripts/check_example_secrets.py`

Hinweis zur ersten Ausfuehrung:

- Beim ersten Trend-Report ohne vorherigen Snapshot sind `new`-Werte erwartbar hoch und gelten als Baseline.
- Kommentarpflicht wird erst ab vorhandenem vorherigem Snapshot strikt erzwungen (nicht im Baseline-Lauf).

Strenger CI-geeigneter Modus:

- `python scripts/review_secret_scan.py --strict`
- Schlaegt fehl bei Secret-Findings oder fehlenden Pflichtkommentaren fuer Allowlist-Aenderungen.
