# Legacy-Quellenmigration: Mapping fuer `knowledge_documents.project_id = null`

Stand: 2026-07-18

## Ausfuehrungsstatus

- Migration ausgefuehrt am 2026-07-18.
- Datenbank-Backup vor Wartung: `data/backups/chat_system.before-legacy-migration-20260718-112851.db`.
- Ergebnis: `remaining_unassigned = 0`.
- Fuer User 3 wurde `Legacy-Inbox` als Projekt `id=30` angelegt und Dokument `id=5` dorthin gemappt.

## Ziel

Unzugeordnete Wissensdokumente (`project_id = null`) wurden analysiert und auf die vorhandene Mandant/Bereich/Projekt-Hierarchie gemappt, um fachfremde Rueckfaelle im Retrieval zu vermeiden.

## Datengrundlage

- Tabelle `knowledge_documents`: 6 unzugeordnete Dokumente.
- Tabelle `projects`: Zielknoten fuer die Zuordnung.
- Setting `workspace.project_meta_map`: Hierarchie-Info (`scope_kind`, `parent_project_id`, `tenant_key`, `area_key`).

## Analyseergebnis

- Unzugeordnet gesamt: 6
- Status: alle `Bereit`
- Quelle: 4x `Upload`, 2x `upload`
- Nutzer-Verteilung:
  - User 1: 2 Dokumente
  - User 12: 3 Dokumente
  - User 3: 1 Dokument

## Mapping-Entscheidung

| Doc-ID | User | Datei | Ziel-Mandant | Ziel-Bereich | Ziel-Projekt | Ziel `project_id` | Entscheidung |
| -------- | ---: | --- | --- | --- | --- | ---: | --- |
| 1 | 1 | Angebot_Klaener.pdf | heisig-firma | firma | angebote | 15 | Dateiname passt zum Angebotskontext; Projekt 15 ist als Projektknoten unter 13->14->15 modelliert. |
| 2 | 1 | Materialliste_Lemwerder.docx | heisig-firma | firma | angebote | 15 | Materialliste ist fachlich Teil des Angebots-/Auftragskontexts desselben Strangs. |
| 3 | 12 | Angebot_Klaener.pdf | Heisig Naturstein | (noch offen) | (noch offen) | 27 | Fuer User 12 existiert aktuell nur der Tenant-Knoten 27 fuer Naturstein; daher temporaer tenantnah zuordnen. |
| 4 | 12 | Materialliste_Lemwerder.docx | Heisig Naturstein | (noch offen) | (noch offen) | 27 | Gleiches Muster wie Doc 3; fachlich Naturstein, nicht Fussball. |
| 6 | 12 | Charta-von-Venedig_1964.pdf | Heisig Naturstein | (noch offen) | (noch offen) | 27 | Fachquelle fuer Naturstein/Denkmalkontext; ebenfalls Tenant 27 statt Privat/Fussball-Linie. |
| 5 | 3 | knowledge-upload-test.md | (neu anzulegen) | (neu anzulegen) | Legacy-Inbox | TBD | Fuer User 3 existiert kein Projektbaum; zuerst dedizierten Zielknoten anlegen, dann zuordnen. |

## Umsetzungs-SQL (nach Review)

Hinweis: Erst in einer Wartungs-Session auf Backup anwenden.

```sql
-- User 1: Angebotsdokumente in Projekt 15 (heisig-firma -> firma -> angebote)
UPDATE knowledge_documents
SET project_id = 15
WHERE id IN (1, 2)
  AND user_id = 1
  AND project_id IS NULL;

-- User 12: Naturstein-Dokumente vorerst auf Tenant-Knoten 27
UPDATE knowledge_documents
SET project_id = 27
WHERE id IN (3, 4, 6)
  AND user_id = 12
  AND project_id IS NULL;

-- User 3: erst Zielprojekt anlegen, dann Dokument 5 migrieren
-- Beispiel (ID nach INSERT verwenden):
-- INSERT INTO projects (user_id, name, description, created_at, updated_at)
-- VALUES (3, 'Legacy-Inbox', 'Temporarer Zielknoten fuer Altquellen', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
-- UPDATE knowledge_documents
-- SET project_id = <NEUE_PROJECT_ID>
-- WHERE id = 5 AND user_id = 3 AND project_id IS NULL;
```

## Validierung nach Migration

-1. Restmenge pruefen:

```sql
SELECT COUNT(*) AS remaining_unassigned
FROM knowledge_documents
WHERE project_id IS NULL;
```

-2. Fachfremde Leaks pruefen (stichprobenartig):

```sql
SELECT id, user_id, file_name, project_id
FROM knowledge_documents
ORDER BY user_id, id;
```

-3. Retrieval-Scope testen (manuell):

- Konversation auf Naturstein-Projektlinie setzen.
- Pruefen, dass Fussball-Quellen nicht erscheinen.
- Pruefen, dass Naturstein-Dokumente sichtbar sind.

## Offene Restaufgabe

- Optional: fuer User 3 spaeter einen vollstaendigen Mandant/Bereich/Projekt-Baum modellieren und `Legacy-Inbox` bei Bedarf von `scope_kind=project` in die finale Hierarchie einhaengen.
