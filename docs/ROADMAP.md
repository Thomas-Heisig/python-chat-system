# Roadmap

- Nach Aktivierung des direkten SQL-Zugriffs im `jtl_suite`-Plugin: produktive Query-Bibliothek fuer typische JTL-Auswertungen (Artikel, Auftragsstatus, Lagerbewegungen) pro Service bereitstellen und versionieren.
- Plugins-Frontend wurde um einen direkten Solo-Lauf ergaenzt, sodass Plugin-Executions (insb. `business_letter`) im Gastsystem direkt unter `Plugins` testbar sind.
- Plugins-Frontend wurde als Widget-Flaeche erweitert: Logo-gestuetzte Plugin-Karten und direkter Zugriff auf die jeweiligen Plugin-Settings sind jetzt im `Plugins`-Bereich verfuegbar; naechster Schritt sind je Plugin eigene, spezialisierte Frontend-Teilansichten.
- Die Plugin-Kachel-Logik nutzt jetzt dynamische Logo-Discovery aus `frontend/src/assets/plugin-logos/` (statt fester Mapping-Liste); naechster Schritt ist ein optionales Plugin-Metadatenfeld fuer Logos als Primaerquelle mit Asset-Discovery als Fallback.
- Plugin-Bedienstandard ist jetzt vereinheitlicht: Settings-Symbol auf der Karte, Popup/Dialog als zentrale Detailflaeche und dedizierte Aktion `Plugin oeffnen` fuer die manuelle Plugin-Oberflaeche; naechster Schritt sind plugin-spezifische Manual-UIs innerhalb dieses Popup-Rahmens.
- Plugin-Settings sind jetzt durchgaengig sichtbar (alle definierten Felder), gruppenweise einklappbar und kennzeichnen feldabhaengige Optionen visuell (`abhaengig von ...`) sowohl in `Einstellungen > Plugins` als auch im Plugin-Popup; naechster Schritt ist eine noch differenziertere Bedingungsdarstellung (z. B. `= Wert` bzw. `in [...]`) fuer komplexere Regeln.
- Plugin-Konfigurationen werden in `Einstellungen > Plugins` jetzt als eigenstaendige Karten mit Kurzmetadaten dargestellt; naechster Schritt ist die weitere fachliche Verdichtung je Plugin-Karte (z. B. Status, letzter Test, Schnellaktionen).
- Auch die Plugin-Untergruppen werden jetzt innerhalb der Plugin-Karten als eigene Boxen dargestellt; naechster Schritt ist die visuelle Priorisierung wichtiger Gruppen statt rein gleicher Rastergewichte.
- Die Bearbeitung von Plugin-Untergruppen erfolgt jetzt gross im Popup, waehrend die Karten nur noch kompakte Vorschauinformationen tragen; naechster Schritt ist eine noch klarere Unterscheidung zwischen Vorschau- und Bearbeitungszustand.
- Die Popup-Interaktion gilt jetzt fuer die komplette Plugin-Settings-Hierarchie (Kategorie -> Plugin -> Untergruppe); naechster Schritt ist die Navigation zwischen Ebenen im Modal ohne Ruecksprung in die Ausgangsansicht.
- Die modalbasierte Detailbearbeitung wurde auf Projekte, Bibliothek, Termine und Chats erweitert; naechster Schritt ist die Vereinheitlichung der Modal-Navigation auch fuer die restlichen allgemeinen Settings-Gruppen ausserhalb des Plugin-Bereichs.
- Die allgemeinen Settings-Gruppen laufen jetzt ebenfalls ueber eine gemeinsame Modal-Huelle; naechster Schritt ist die Feinnavigation innerhalb dieser Modals (z. B. Breadcrumbs, Vor/Zurueck, Kontextwechsel ohne Fokusverlust) und die weitere Vereinheitlichung mit der Plugin-Hierarchie.
- Breadcrumbs, Vor/Zurueck und direkte Auswahl sind jetzt in den Settings-Modals vorhanden; naechster Schritt ist eine staerkere Fokusfalle/Fokus-Rueckgabe beim Schliessen sowie konsistente Modal-Navigation fuer weitere Spezialdialoge.
- Die Settings-Ansicht oeffnet jetzt sofort modal und nutzt auf der obersten Ebene quadratische Auswahlkarten; naechster Schritt ist die weitere Verdichtung dieser Karten (z. B. Status, ungespeicherte Aenderungen, Schnellaktionen) ohne Ueberladung.
- Die Workspace-Regression ist behoben: `Einstellungen` und `Plugins` laufen wieder als zentrales Overlay ueber der Chatflaeche statt als normale Ausgabeseite; naechster Schritt ist eine durchgaengige Accessibility-Haertung (Fokusfalle, Fokus-Rueckgabe, Tastaturnavigation) fuer alle Overlay-Ebenen.
- Die Kachelstruktur wurde im Plugin-Settings-Pfad bis in die tieferen Ebenen erweitert (Kategorie/Plugin/Untergruppe) und um Symbol-/Erwartungstexte ergaenzt; naechster Schritt ist eine gezielte E2E-Absicherung dieses hierarchischen Tile-Flows.
- Die Plugin-Popups nutzen jetzt dynamische Viewport-Hoehen und die letzte Untergruppen-Ebene besitzt getrennte Scrollbereiche fuer Kacheln/Felder; naechster Schritt ist Feintuning der Hoehenverteilung je Breakpoint und Inhaltstiefe.
- Die Integrationen-Settings besitzen jetzt eine Darstellungswahl (`Inline`/`Popup`) mit direktem Gruppen-Popup; naechster Schritt ist die persistente Speicherung dieses View-Profils pro Benutzer.
- Die Darstellungswahl ist jetzt in `Einstellungen / Darstellung` zentral verfuegbar und wird pro Benutzer lokal gespeichert; naechster Schritt ist optional eine serverseitige Profil-Synchronisation ueber Geraete hinweg.
- Plugins koennen jetzt ein eigenes Frontend ueber Metadaten an die UI melden; naechster Schritt ist die Ausweitung dieses Schemas von statischen Schnellaktionen auf reichhaltigere Plugin-spezifische Formulare.
- `business_letter` nutzt dieses Plugin-Frontend-Schema jetzt bereits mit fachlichen Schnellzugaengen; naechster Schritt ist die Weiterentwicklung von Preset-Aktionen zu vollwertigen dokumenttyp-spezifischen Formularoberflaechen.
- Die generische Plugin-Frontpage zeigt jetzt auch automatisch alle deklarierten Plugin-Funktionen; naechster Schritt ist ein kontextreicheres Mapping von Aktionsparametern (nicht nur `action`) in formularartige Einstiege.
- Plugin-Frontends koennen jetzt neben Aktionssektionen auch echte plugin-definierte Seiten (`pluginFrontend.page`) ausliefern; naechster Schritt ist die Ausweitung dieses Schemas auf weitere Kernplugins.
- `business_letter` besitzt jetzt zusaetzlich eine echte Frontend-Komponente im Projekt, die direkt im Popup gerendert wird; naechster Schritt ist die Rueckfuehrung weiterer Plugin-Frontends in denselben komponentenbasierten Pfad.
- Der `business_letter`-Frontend-Flow ist jetzt entkoppelt vom reinen Session-State: plugin-lokale Entwuerfe werden persistent in den Plugin-Settings gehalten (Load + Autosave + manuelles Save/Reload); naechster Schritt ist die optionale Trennung in mehrere benannte Entwurfs-Slots pro Benutzer.
- Der Entwurfs-Persistenzpfad wurde plugin-uebergreifend vereinheitlicht: Zuordnung erfolgt dynamisch aus dem Aufrufkontext (`pluginId`) und ist jetzt fuer `business_letter` und `calculator` aktiv; naechster Schritt ist die Extraktion in einen gemeinsamen Frontend-Helper fuer weitere Plugin-Frontpages.
- Die Extraktion ist abgeschlossen: `plugins/shared/frontend/usePluginDraft.ts` kapselt den einheitlichen Draft-Flow fuer Plugin-Frontpages; naechster Schritt ist die schrittweise Uebernahme durch weitere plugin-spezifische Frontends.
- `calculator` ist jetzt ebenfalls als echte plugin-spezifische Frontend-Komponente im Popup verfuegbar (statt nur generischer Runner); naechster Schritt ist die Ausweitung auf weitere Kernplugins mit fachlichen Frontpages und konsistenten Laufzeitmetadaten.
- Der `calculator`-Parser ist jetzt auf eine strengere AST-Whitelist gehaertet (keine Bool-Konstanten, keine Keyword-Args, nur direkte Allowlist-Calls) und um wissenschaftliche Funktionen (`min`/`max`, `asin`/`acos`/`atan`, `sinh`/`cosh`/`tanh`) erweitert; naechster Schritt ist die UX-seitige Sichtbarkeit dieser Funktionen in Presets/Hilfetexten der Manual-Frontpage.
- `calculator` ist jetzt strukturell am `business_letter`-Muster ausgerichtet (Modulstruktur + ausgelagerter Service/Settings/Constants) und zeigt ein eigenes Logo im Manual-Frontend; naechster Schritt ist die fachliche Befuellung der derzeitigen Platzhalterbereiche `models/` und `renderers/` mit echten Domaintypen/formatierter Ergebnisdarstellung.
- Das manuelle `business_letter`-Frontend liegt jetzt inklusive lokaler README direkt im vorgesehenen Plugin-Frontend-Ordner; naechster Schritt ist die fachliche Vertiefung des Payload-Mappings pro Dokumenttyp.
- Die Dokumenttypen-Matrix fuer `business_letter` ist jetzt breit integriert; naechster Schritt ist die noch feinere fachliche Differenzierung pro Typ in `buildPayload()`, Ergebnissicht und typbezogenen Pflicht-/Hilfsfeldern.
- Die zentrale Dokumenttyp-Konfiguration fuer `business_letter` ist jetzt eingefuehrt (Frontend + Backend-Regelmatrix); naechster Schritt ist die Ausweitung derselben Konfigurationsidee auf weitere komplexe Plugins mit eigener Frontpage.
- Fuer `business_letter` verschiebt sich der Hauptmehrwert jetzt von reinen Dokumenttypen hin zu Produktivitaets- und Workflow-Themen: Vorlagenverwaltung, Assistentenfluss, Vorschau, Kunden-/Artikelstamm, Historie, Signaturen, QR-Codes, Wiedervorlagen, Dashboard sowie Naturstein-spezifische Projektdaten bilden den naechsten grossen Ausbaupfad.
- Nach der Einfuehrung der zentralen Typmatrix liegt der naechste `business_letter`-Architekturblock bei drei Achsen: 1. dokumentuebergreifende Beziehungen und Konvertierungsaktionen, 2. strukturierte Service-/Baustellen- und Naturstein-Felder, 3. testgetriebene Absicherung der Matrix inklusive Freigabe-/Workflow-Vorbereitung.
- Ein erster Vertikalschnitt fuer `business_letter` ist jetzt umgesetzt: Dokumentbeziehungen, einfache Konvertierungsaktionen und optionale natursteinspezifische `stone_details` laufen bereits durch Frontend und Plugin-Vertrag; naechster Schritt ist die fachliche Vertiefung mit echten Folgebeleg-Uebernahmen und strengeren Beziehungsregeln.
- Die fachliche Vertiefung des Folgebeleg-Blocks ist jetzt umgesetzt: zentrale Konvertierungsregeln, Quellbeleg-Referenzmodell, Positionsuebernahme mit Teilmengen und erweiterte Referenzvalidierungen laufen im Plugin-Ende-zu-Ende-Pfad; naechster Schwerpunkt ist die tiefe Auswertung von `stone_details` bis in Ausgabe-/Artefaktpfade.
- Lifecycle-Fortschritt abgeschlossen: Restmengenlogik fuer `Lieferschein -> Rechnung`, negative Werte fuer `Rechnung -> Gutschrift/Stornorechnung` sowie Offene-Posten-Berechnung fuer `Rechnung -> Zahlungserinnerung` sind im Konvertierungspfad aktiv; naechster Schwerpunkt ist die projektweite Zusammenfuehrung als echte Projektakte mit Status-/Timeline-Sicht.
- Die projektweite Zusammenfuehrung ist jetzt umgesetzt: `project_case_overview` liefert Timeline + Statussicht auf Projektebene und zeigt im Folgedokument-Flow die persistente Mengenkette (`geliefert`/`fakturiert`/`offen`); naechster Schwerpunkt ist die Ausweitung auf strengere Prozessregeln (z. B. Mahnstufen-/Freigabeketten) und UI-Filter fuer grosse Projektakten.
- Follow-up-Hardening umgesetzt: persistente Referenzsuche ist jetzt nicht mehr nur sessionbasiert, sondern loest Quelldokumente bei fehlender Referenzangabe aus der DB ueber Projekt-/Kundenkontext plus erwarteten Quelltyp auf; naechster Schwerpunkt ist ein expliziter serverseitiger Referenz-Selector (inkl. Eindeutigkeitsregeln/Priorisierung) fuer Mehrtreffer-Faelle.
- Prozess-/Status-Gates wurden pro Folgedokumentpfad verschaerft (inkl. Blockern fuer unzulaessige Quellstatus, fehlende Restmenge und fehlenden offenen Betrag); naechster Schwerpunkt ist die fachliche Erweiterung um Mahnstufen-Kettenlogik und Storno-/Gutschrift-Grenzen auf Belegebene.
- Die `business_letter`-Manual-Frontpage nutzt jetzt den policy-faehigen Funktionsendpunkt (`/api/plugins/execute-function`) fuer Erstellung und Projektakte statt des generischen Execute-Pfads; naechster Schritt ist die durchgaengige Migration verbleibender plugin-spezifischer Frontends auf denselben Vertragsweg.
- Frontend-Hardening fuer den Folgebeleg-Flow ist aktiv: numerische Feldvalidierung, Teilmengen-Grenzen und Referenztyp/Konvertierungs-Konsistenz werden bereits clientseitig erzwungen; naechster Schritt ist die Spiegelung aller kritischen Regeln als explizite serverseitige Fehlercodes fuer UI-Fehlermapping.
- CSS-Leakage und Layout-Inkonsistenzen in der `business_letter`-Frontpage sind behoben (Scope + Grid); die erste Entzerrungswelle ist umgesetzt (Header + Sidebar-Komponenten, ausgelagerter Execution-Hook), naechster Schritt ist die Extraktion der grossen Formularsektionen (Dokument, Beziehungen, Positionen, Texte) in weitere Subcomponents/Hooks.
- Der naechste Refactor-Block ist gestartet: `DocumentSection`, `RecipientSection` und `TextSection` sind bereits aus der Manual-Page ausgelagert und ueber strukturierte Props verdrahtet; die direkte Folge ist jetzt `PositionSection`, danach der komplexe Relationship-Bereich.
- Der Refactor-Block ist jetzt abgeschlossen: auch `PositionSection` sowie der komplexe `RelationshipSection`-Bereich sind ausgelagert; als naechster Schritt folgt die interne Entzerrung der Parent-Seite (z. B. lokale Reducer/Handler-Gruppierung fuer Relationship- und Positionszustand).
- TypeScript-Aufloesung fuer ausgelagerte Plugin-Frontends (`../plugins/*/frontend`) ist jetzt stabilisiert; naechster Schritt ist die kontrollierte Bereinigung der verbleibenden Frontend-Typfehler in `frontend/src` ohne Regression im bestehenden Plugin-Flow.
- Den Settings-Layer weiter absichern: globale und benutzerspezifische Scopes sind jetzt auth-gebunden, sensible Werte werden maskiert; als naechster Schritt fehlt vor allem ein echtes Team-Mitgliedschaftsmodell fuer feinere Team-Berechtigungen statt des aktuellen Admin-Fallbacks.
- Die neue SQLite-Persistenz fuer Dokumente, Artefakte und Nummernkreise als belastbaren Archivpfad ausbauen; transaktionale Kopplung ist umgesetzt, als naechster Schritt folgen Betriebsmetriken, Rollback-Diagnostik und Migrationspfade.
- Die zweite Ausgabespur des Modells im Dokumentmodell sauber abbilden, damit Brief, E-Mail und strukturierte Exportpfade aus demselben Datenkern gespeist werden; PDF ist jetzt als nativer Baseline-Renderer angebunden.
- Zielgerichtete Integritaets-Regressionen fuer Nummernkreise, Persistenzabbrueche und E-Invoice-Minimalausgabe dauerhaft im Testlauf halten, damit die neue Identitaets- und Exportlogik nicht wieder driftet.
- E-Invoice von erweiterter Strukturvalidierung auf volle Normkonformitaet bringen: UBL-`cbc`/`cac`-Ausgabe, CII-/UNCEFACT-Ausgabe, offizielle XSD/Schematron-Ausfuehrung, KoSIT-Referenzfaelle aus der offiziellen Testsuite (valid + offiziell abgeleitete invalid) und das Priority-3-Fachmapping fuer Reverse Charge, Steuerbefreiung, Abschlag/Schluss, Gutschrift/Storno, Rundung und Preisbasismengen sind fuer beide Syntaxpfade verdrahtet; als naechster Schritt folgen weitere Pflichtstrukturen und tiefere Profilregeln, insbesondere fuer komplexe CII- und CreditNote-Faelle.
- ZUGFeRD-Pfad auf Compliance-Haertung weiterfuehren: XML-Einbettung, XMP-Baseline, veraPDF-Gate, gepinnte Validator-Assets mit SHA-Checks und CI-Artefakt-Export sind aktiv; als naechster Schritt folgen dauerhafte Freigabekriterien und Langzeitstabilitaet gegen Upstream-Validator-Updates.

- Gesamt-CI als Release-Gate absichern: Backend-Lint, komplette Backend-/Frontend-Suiten, TypeScript-Check und Build laufen nun im Standard-Workflow; als naechster Schritt folgen Laufzeit-Optimierung und gezielte Flake-Reduktion.

## Ziel und Abgrenzung

- Nach dem Fallback-Hardening fuer modell-spezifische Chat-Settings: weitere `model_<id>_*`-Defaults und Migrationsfaelle im Settings-Layer systematisch absichern.

- Diese Datei enthaelt nur geplante Ausbaustufen und Ziele.
- Bereits implementierte Punkte stehen ausschliesslich im Changelog.
- Konkrete naechste Arbeitspakete mit Prioritaet stehen im TODO.
- Spaetere Enterprise-Themen stehen im Backlog.

## V1 Stabilisierung und Produktreife lokal

- Secret-Hygiene im Regelbetrieb halten: projektspezifische Scan-Regeln/Allowlists (`.gitleaks.toml`, `config/secret-scan-allowlist.json`) und das Security-Playbook (`docs/security/secret-leak-playbook.md`) kontinuierlich gegen neue Provider/Dateipfade nachpflegen.
- Secret-Hygiene zyklisch pruefen: monatliche Allowlist-Reviews mit Report-Output (`python scripts/review_secret_scan.py`) als festen Betriebsrhythmus beibehalten und Findings trendbasiert auswerten.
- Nach Trend-Auswertung und Snapshot-Diff im Secret-Review: Pflichtkommentare (`reason` + `reference`) fuer neue/entfernte Allowlist-Regeln dauerhaft als Audit-Standard im Betriebsprozess halten.
- CI-Governance aktiv halten: `Secret Scan` laesst den strict Review-Lauf gegen Snapshot verpflichtend laufen und blockiert ohne aktive Kommentarpflicht den Build.
- Nach Einfuehrung der Integrations-Settings fuer API-Schluessel: optional sichere Maskierung, getrennte Rollenrechte und spaetere Secret-Backends (z. B. OS-Secret-Store) evaluieren.
- Nach Erweiterung der Integrations-Settings auf viele Provider (inkl. Wetter/Web/Kommunikation): provider-spezifische Verfuegbarkeitschecks, Test-Buttons und klare Nutzungspfade pro Plugin/Backend im UI ausbauen.
- Nach Einfuehrung direkter `Key holen`-Links je Integrationsfeld: optionale provider-spezifische Health-Checks im selben Feld (Ampelstatus + letzter erfolgreicher Testzeitpunkt) ergaenzen.
- Nach Einfuehrung von `Key testen` je Integrations-Key (Weather/Search) und serverseitiger Re-Validation-Persistenz: Ergebnisexport/Copy-Funktion fuer Support sowie optionales Verlaufsaudit pro Provider evaluieren.
- Nach Umsetzung von `Alle Keys testen` mit Ergebnis `OK/Fehler/uebersprungen`: Sammeltest um Zeitstempel, Laufdauer und optionale Export-/Copy-Funktion fuer Support erweitern.
- Nach eingefuehrtem Skip-Verhalten fuer leere Integrations-Keys: Re-Validation-Berichte um `getestet` vs. `uebersprungen` differenzieren, damit Teilkonfigurationen transparent bleiben.
- Nach Umstellung auf kompakten Target-Button (`↗`) je Integrationsfeld: optional Tooltip-/Status-Muster fuer Key-Quelle, letzter Test und Fehlerdiagnose vereinheitlichen.
- Nach Einfuehrung von Integrationen-Tabs und einklappbaren Gruppen: nutzerbezogene Persistenz fuer aktiven Tab/Klappzustand sowie Rollensteuerung pro Sensitivitaetsklasse der Keys evaluieren.
- Nach Einfuehrung gruppierter Plugin-Settings-Accordion: die offene Kategorien-/Plugin-Persistenz ist umgesetzt; als naechster Schritt eine schnelle Direktnavigation zu einzelnen Plugins ergaenzen.
- Nach Einfuehrung von `custom_provider_keys` (JSON): standardisierte Adapter-Konvention fuer dynamische Provider-Aktivierung im Plugin-/Tool-Layer definieren.
- Nach Laufzeitverdrahtung fuer `weather` und `websearch`: denselben Integrationspfad schrittweise auf weitere API-Plugins (z. B. `news`, `translator`, `stock_market`) ausrollen.
- Nach aktivierter Secret-Maskierung im Settings-GET-Endpoint: rollenbasierte Secret-Freigaben und selektive Entschluesselung/Offenlegung fuer Admin-Werkzeuge evaluieren.
- Nach Einfuehrung des OpenAI-/ChatGPT-Backends: Modellkatalog, Verbindungsdiagnosen und klare Runtime-Hinweise fuer `.env` vs. `.env.example` weiter produktivieren.
- Nach Umstellung der Modell-Einstellungen auf Untertabs und Standard-Klappgruppen: persoenliche UI-Persistenz fuer offenen Gruppenstatus und Filterkombinationen evaluieren.
- Nach browserseitiger Persistenz fuer Modellfilter und Gruppenstatus: optional serverseitige Synchronisation pro Benutzer/Geraet evaluieren.
- Python-Laufzeit konsolidieren: `.venv-chat` (Python 3.12) als primaere Umgebung fuer Chat/Loader/Training etablieren und Interpreter-Drift zwischen lokalen Starts vermeiden.
- Nach erfolgreicher `.venv-chat`-Migration: GPU-Paritaet der neuen Hauptumgebung vervollstaendigen (CUDA-Torch final angleichen und gegen Transformers/Vision/Training live pruefen).
- Nach projektlokaler Pyright/Pylance-Venv-Fixierung: CI-gestuetzten Typcheck (pyright) als optionalen Qualitaetsgate-Job fuer Backend-Pfade evaluieren.
- Nach aktivierter Markdown-Strictness Phase 1 fuer `docs/**/*.md`: Rule-Haertung in kleinen Batches auf weitere Doku-Bereiche (z. B. Plugin-READMEs) ausweiten und je Batch mit gezielten Korrekturen absichern.
- Nach umgesetzter Markdown-Strictness Phase 2 fuer ausgewaehlte Plugin-READMEs: verbleibende Legacy-Plugin-Dokus mit Sonderformaten (z. B. Wrapper-Fences) schrittweise auf regelkonforme H1/Fence-Struktur migrieren, um weitere globale Ausnahmen abzubauen.

- Einheitliche API-Fehlerstruktur mit Fehlercode, Retry-Hinweis und Details bereitstellen.
- Nach vereinheitlichtem HTTP- und SSE-Error-Envelope: zentrale Client-Error-Utility fuer Toasts, Retry-Hinweise und Telemetrie standardisieren.
- Speech-API-Vertragsstabilitaet ausbauen: Request-Varianten fuer `POST /api/speech/synthesize` (snake_case/camelCase, optionale `null`-Felder) als feste API- und Integrationstests absichern.
- Speech-Runtime-Hardening erweitern: modellfamilien-spezifische TTS-Ladepfade (u. a. Kokoro ohne `model_type` in `config.json`) als dauerhafte Runtime-/Integrationstests absichern.
- Speech-Runtime-Kompatibilitaet stabil halten: Kokoro-Laufzeit gegen API-Aenderungen (z. B. Generator-Result-Typen und lokale Modellpfade unter Windows) mit versionsnahen Regressionstests absichern.
- Nach aktivierter deutscher Kokoro-Sprachauswahl (`de`/`de-de`): optionales Voice-Profiling fuer deutschsprachige Standardsprecher (z. B. `bf_emma`, `bm_george`) in der UI als Presets ergaenzen.
- Qwen3-TTS produktivieren: validierten Runtime-Stack mit CPU-Smoke und Causal-Mask-Bridge als optionales, konfliktfreies Deployment-Profil kapseln und per Regressionstest stabil halten.
- VAD-Preprocessing weiter ausbauen: nach serverseitigem STT-Precut (Silero-VAD) als naechsten Schritt Segment-Merging-/Padding-Strategien je Sprache und Mikrofonprofil evaluieren.
- Polling weiter optimieren: sichtbarkeitsbasierten Refresh um Fokus-/Idle-Strategie erweitern, um Hintergrundlast weiter zu senken.
- Konversations-Lifecycle weiter haerten: Rename/Delete/Create-Endpunkte konsistent gegen Async- und DB-Randfaelle absichern.
- Nach Settings-Fallback-Hardening fuer `model_<id>_*`: End-to-End-Tests fuer modell-spezifische Prompt-/Parameterauflosung ueber mehrere Benutzerkonten ausbauen.
- Modellpfade mit Path-Traversal-Schutz und Basisverzeichnis-Pruefung haerten.
- Nach Modellpfad-Haertung: bestehende `ModelConfig`-Datensaetze per Migrations-/Health-Check auf unerlaubte Pfade pruefen und bereinigen.
- Nach umgestellter Startup-Repair-Strategie fuer invalide Settings: optionalen Admin-Repair-Trigger (on-demand) und einen strukturierten Reparaturreport fuer Betrieb/Support ergaenzen.
- Runtime-Warnungsstrategie verfeinern: umgebungsabhaengige Log-Level (dev/staging/prod) fuer Betriebsmeldungen konsistent ueber weitere Startup-Checks ausrollen.
- Nach erfolgreichem Volltestlauf (`43 passed`): verbleibende SQLAlchemy-Connection-Lifecycle-Warnung (`non-checked-in connection`) in Integrationstests systematisch beheben.
- Nach Polling-Deduplikation: Fokus-/Idle-basierte Polling-Intervalle dynamisch staffeln, um Last unter aktiver Nutzung weiter zu optimieren.
- Nach TanStack-Query-Konsolidierung: Cache-Invalidierung und Mutation-Flows fuer Einstellungen/Chataktionen weiter standardisieren.
- Nach zentralen Settings-Query-Helfern: verbleibende Chat-Mutationen schrittweise in denselben einheitlichen Invalidation-/Optimistic-Update-Pfad ueberfuehren.
- Nach Strict-Mode-Regressionstests: Polling-Testabdeckung auf Fokus-/Idle-Intervallstaffelung und Sichtbarkeitswechsel erweitern.
- Nach bereinigter Pylance-Typdiagnostik in den Training-Repositories: Strict-Typisierung fuer weitere Training-Pfade (`services`, `routes`) systematisch nachziehen und als festen Qualitaetscheck verankern.
- Prompt-Persistenz im Modellprofil weiter haerten: UI-Race-Conditions beim Modellwechsel/Speichern eliminieren und globalen Fallback (`prompt.system_prompt`) als sichtbaren Standardpfad absichern.
- API-/Integrationstests fuer Startup-Restore und Modellpfad-Gueltigkeit gegen Datenbank-Bestandsdaten ausbauen.
- Nach retrieval-basierten Kontextmetriken: externe Datenanteile von Metadaten-Kontext auf inhaltsbasierte Chunk-Selektion (inkl. Embedding-/Hybrid-Ranking) weiterentwickeln.
- Nach lokalem Prompt-Diagnosemodus und API-Endpunkt: optionalen redigierten Export (Datei/Snapshot) fuer reproduzierbare Prompt-/Retrieval-Analysen ergaenzen.
- Nach modell-spezifischer Prompt-/Decoding-Steuerung: einheitliche Parameterunterstuetzung fuer weitere Backends (neben llama.cpp) und capability-gesteuerte UI-Enablement-Regeln einfuehren.
- Modellstil gezielt steuerbar machen: pro Modell/Profilebene robuste Ausgabe-Templates (Kurzantwort/Analyse/Schrittfolge) und automatische Halluzinations-Checks fuer bekannte Domainthemen (z. B. Charta von Venedig) integrieren.
- Nach interpreter-aware Loaderdiagnostik fuer `llama_cpp`: Installationspfad fuer Python-3.13/Windows (Long-Path- und Wheel-Strategie) als dokumentierten Ops-Runbook-Schritt standardisieren.

## V2 Funktionsausbau Chat, Settings und Wissensbasis

- Nach eingefuehrter Zykluspruefung und Parent-Validierung in der Projekt-Hierarchie (`Mandant -> Benutzer -> Bereich -> Projekt`): als naechsten Schritt Mehrbenutzer-Ownership ueber Teams und tenantweite Konsistenzregeln weiter ausbauen.
- Nach Einfuehrung tieferabhaengiger Quellenzuordnung (Quellen auf Knotenebene + vererbte Sicht entlang der Parent-Kette): Retrieval- und Bibliotheksansicht um direkte Kennzeichnung `direkt` vs. `geerbt` mit Filterung je Ebene erweitern.
- Nach aktivierter Scope-Aufloesung im Chat-Retrieval und abgeschlossener Legacy-Quellenmigration: optionalen Strict-Mode (`nur zugewiesene Projektquellen`) je Mandant/Team einfuehren und Scope-Drift fortlaufend per Validierungschecks ueberwachen.
- Nach produktiver Persistenz und gehaerteter Reparenting-Logik (inkl. Child-Umbindung bei Delete): Drag-and-drop Baumansicht und Batch-Reparenting fuer groessere Projektlandschaften einfuehren.
- Nach Einfuehrung des Plugin-Doku-Index (`docs/plugins/index.md`): Querverweise aus Entwickler-Startseiten/README systematisch auf den zentralen Einstiegspunkt ausrichten, um Doku-Streuung weiter zu reduzieren.
- Nach abgeschlossener `/api/plugins/execute`-Vertrags-/E2E-Absicherung: denselben Shared-Validator im naechsten Schritt auf Chat-Orchestrierungs-E2E-Pfade und weitere Kommunikations-Plugins ausweiten.

- Nach Einfuehrung des Workspace-Neustarts (`Chats & Projekte loeschen`): optionalen Sicherheitsdialog mit Export-/Backup-Hinweis und feinere Reset-Scopes (nur Chats, nur Projekte, beides) ergaenzen.
- Nach eingefuehrter Admin-Rechtepruefung fuer den globalen Neustart: optionalen Scope-Parameter (`user`, `global`) und zusaetzliches 4-Augen-Freigabemuster evaluieren.

- Nach Einfuehrung von `Ollama Local` und `Ollama Cloud` in der Modellauswahl: optionalen Katalog-Refresh, Download-Fortschritt und gefilterte Darstellung nach Modellfamilie/Faehigkeiten im UI ausbauen.
- Nach abgesicherter API-/UI-Regression fuer Ollama-Scan/Aktivierung und Pull-Abbruch/Retry: serverseitige Historie fuer fehlgeschlagene Downloads und Support-Diagnostik weiter standardisieren.
- Nach lokalem Filterset im Modellmanager (`Tools`, `Thinking`, `Vision`, Modellfamilie`): serverseitige Persistenz fuer Nutzerfilter und kombinierte Sortierprofile evaluieren.

- Nach eingefuehrter Plugin-Runtime-API (`/api/plugins`, `/api/plugins/execute`, `/api/plugins/execute-from-markup`): UI-Orchestrierung fuer Plugin-Schritte (`plugin_call` -> warten -> `plugin_response` -> Antwort) als gefuehrten Chat-Laufpfad produktivieren.
- Nach Einfuehrung des dynamischen Discovery-Layers (`/api/plugins/capabilities`, `/api/plugins/{plugin_id}/manifest`, `/api/plugins/{plugin_id}/functions/{function_name}`, `/api/plugins/execute-function`): plugin-spezifische Metadaten (`capabilities`, `usage_rules`, `examples`, Funktions-Metadaten inkl. Side-Effect-Infos) systematisch pro Kernplugin kuratieren, damit die Tool-Auswahl nicht nur aus `input_schema.action` abgeleitet wird.
- Status 2026-07-18: `business_letter` und `calculator` liefern jetzt explizite Discovery- und Funktionsmetadaten; der naechste Ausbauzyklus fokussiert `email`, `calendar`, CRM und Dateiverarbeitung.
- Nach produktiver Chat-Orchestrierung mit `chat.plugin_orchestration_enabled`: Konversations-UX um sichtbare Tool-Statusanzeige und Debug-Ansicht fuer Plugin-Ketten erweitern.
- Nach aktivierter zweistufiger Discovery-Orchestrierung im Chat (`plugin_search` -> `plugin_manifest` -> optional `plugin_function` -> `plugin_call`): sichtbare Zwischenstufen in der UI (Kandidaten, geladenes Manifest, validierte Funktion) als nachvollziehbaren Debug-/Transparenzpfad ausbauen.
- Fallback-Haertung umgesetzt: bei erkannten Dokumentanfragen wird bei fehlendem Tool-Tag einmalig automatische Discovery (`plugin_search_response`) nachgeschoben, damit der Flow nicht bei einer rein textlichen Erstantwort abbricht.
- Zweite Fallback-Stufe umgesetzt: wenn selbst nach der Discovery kein Tool-Tag folgt, wird fuer klare Dokumentanfragen `business_letter` direkt mit einem Basis-Payload ausgefuehrt, damit Angebots-/Rechnungsanfragen nicht in generischen Beispielantworten enden.
- Direktrouting umgesetzt: fuer starke Dokument-Intents kann der Chat jetzt schon vor dem Modelllauf intern in den `business_letter`-Pfad verzweigen und nur noch das Ergebnis zurueckmelden.
- Ergebnislieferung erweitert: direkte Dokumentantworten koennen jetzt echte persistierte Artefaktlinks (z. B. PDF) in die Chatantwort einbetten statt nur Dateinamen anzuzeigen.
- Direkt-Routing ist jetzt auch vertragssauber gegen den gemeinsamen Communication-Contract: interne Chat-Payloads fuer `business_letter` vermeiden ungueltige String-Felder an den Plugin-Boundaries.
- Artefakt-Links im Direktpfad sind jetzt an die reale Persistenzstruktur des Plugins angepasst (`plugin_storage.artifacts`) und koennen dadurch im Chat sichtbar werden.
- Die Chat-Ergebnislieferung ist jetzt einen Schritt weiter: `business_letter`-Antworten koennen eine strukturierte Ergebnisbox mit authentifizierten PDF-/JSON-Downloadaktionen anzeigen, statt nur Dateinamen oder offene Direktlinks auszugeben.
- Download-Governance erweitert: Artefaktdownloads werden jetzt als Dokumentevents auditiert, und das Tenant-Modell fuer Chat-generierte Dokumente kennt neben `user:{id}` auch `team:{id}` und `shared` als vorbereitete Sichtpfade.
- Branding-Konsistenz verbessert: `business_letter` kann bei fehlendem Firmenlogo auf das Kernschmiede-Systemlogo zurueckfallen, sodass generierte Dokumente auch ohne kundenspezifisches Logo nicht mehr ungebremst ohne Branding laufen.
- PDF-Paritaet verbessert: wenn nur das SVG-Systemlogo vorhanden ist, zeigt der PDF-Pfad jetzt mindestens eine Kernschmiede-Wortmarke als sichtbaren Branding-Fallback statt eines komplett logolosen Headers.
- Der Direktpfad fuer Dokumentanfragen ist jetzt fachlich angereichert: einfache Preisrecherchen fuer Angebotsfaelle koennen ueber `pricefinder` vorgelagert aufgeloest und in das erzeugte Dokument-Payload uebernommen werden.
- Plugin-Governance ausbauen: pro Team/Benutzer erlaubte Plugins und API-Key-Verfuegbarkeit serverseitig erzwingen (Allow-/Deny-Policy + Audit).
- Status 2026-07-18: Basisschicht ist umgesetzt (zentrales `PluginExecutionPolicy`-Gate inkl. Scope/Permission/Confirmation/Idempotency/Input-Schema). Als Folgeschritt bleiben Team-Allowlist-Administration, API-Key-Presence-Gate je Provider-Plugin und Audit-Auswertung.
- Status 2026-07-18 (Governance-Block 2): Confirmation-Flow ist persistent (`pending_confirmation` + Confirm/Reject-API) und fuehrt den serverseitig gespeicherten, geprueften Aufruf exakt aus; zusaetzliches Hardening ist aktiv (Alembic-Migration, Team-Bindung, atomarer Claim `pending -> executing`, Idempotency-Lease gegen verwaiste `in_progress`-Eintraege).
- Nach integrierter Template-Generierung, Logo-Bildupload und kaufmaennischen Positionsdaten im `business_letter`-Plugin: echte Persistenz der erzeugten Artefakte sowie DOCX/PDF-Exporter und eRechnungsformate weiter ausbauen.
- Nach eingefuehrter plugin-spezifischer Feldvalidierung und feldgenauer Save-Fehlerrueckmeldung auf Basis von `settings_fields`: als naechsten Schritt Rechte-/Sichtbarkeitsregeln, Cross-Field-Validierung und API-/UI-Regressionstests pro Plugin ausbauen.
- Nach abgesicherter UI- und API-E2E-Regression fuer Plugin-Settings-Persistenz: Scope-Matrix fuer `global/team/user` ist jetzt als API- plus Frontend-Service-Regression verdrahtet; als naechsten Schritt folgen teambezogene UI-Workflows im End-to-End-Lauf.
- Nach ergaenzter semantischer `business_letter`-Settings-Validierung (Nummernpattern, Laufweite, Zahlungsziel, Mirror-Pfad): den Validierungsumfang auf Mandanten-/Team-Scope-Regeln und abhaengige UI-Feldlogik erweitern.
- Nach erweitertem `business_letter`-Settingskatalog (Dokument-Defaults, E-Rechnung, Nummernkreis/Persistenz) als naechsten Schritt pluginuebergreifende Feldkonventionen und zentrale Settings-Profile fuer Massen-Rollout standardisieren.
- `business_letter` hat jetzt eine persistente Dispatch-Queue mit Idempotenzschutz, Retry-Status und Versandhistorie sowie eine Versandausfuehrung ueber den bestehenden `email`-Pluginpfad; naechster Schritt ist ein dedizierter Worker fuer asynchrone Queue-Abarbeitung inkl. Monitoring/Alerting.
- Nach abgeschlossener Execute-Runtime-Absicherung des `business_letter`-Plugins: denselben Fallkatalog auf API- und Orchestrierungs-Ebene als End-to-End-Regressionssuite verankern.
- Nach Harmonisierung von `email`, `whatsapp` und `translator` auf gemeinsame Boundary-Vertraege (`delivery`/`content`, `validate_only`, strukturiertes `validation`): kanaluebergreifende Kommunikations-Suite als verbindlichen API-/Orchestrierungs-Regressionstest ausbauen.
- Nach Einfuehrung des kanonischen Kommunikations-Contracts (`docs/plugins/communication-contract.md`) samt Schema (`app/plugins/contracts/communication.schema.json`): auf Runtime aufsetzende API-/Frontend-Nutzung (Formulare, Contract-Tests, Fehlermapping) schrittweise vervollstaendigen.
- Nach Einfuehrung strukturierter Empfaenger-/Referenz-/Anlagenfelder im `business_letter`-Plugin: PDF/DOCX-Template-Renderer auf dieselbe Datenstruktur harmonisieren, damit Brief und Mail aus identischen Dokumentdaten erzeugt werden.
- Training robuster fuer Modellwechsel machen: architekturbezogene Auto-Profile fuer `target_modules` in den Preflight-Report aufnehmen (inkl. erkannter Module und Fallback-Hinweisen).
- Preflight-Qualitaet vertiefen: `target_modules`-Vorschau optional durch leichtgewichtige Modell-Introspektion (ohne Full-Load) validieren und pro Modellfamilie mit Confidence kennzeichnen.

- Nach Einfuehrung von `/api/models/capabilities`: Frontend-Modelleinstellungen und Ladeentscheidungen schrittweise auf capability-basierte Validierung umstellen.
- Nach Erweiterung von `GET /api/models` um Capability-Metadaten: persistente Favoriten/Irrelevanz-Labels (`favorite`/`irrelevant`) und nutzerbezogene Gruppierungs-Praeferenzen ergaenzen.
- Nach Einfuehrung persistenter Relevanzflags: Team-/rollenbezogene Relevanzansichten (pro Nutzer vs. globales Teamprofil) und Bulk-Markierung im Modellmanager ausbauen.
- Nach Einfuehrung des plugin-basierten Custom-Loader-Registrysystems: weitere benutzerdefinierte Architektur-Plugins (neben Supra-A2A) standardisiert ueber dieselbe Registry integrieren.
- Nach Trust-Gating fuer Custom-Code: dedizierte UI-Interaktion fuer sichere Freigabe/Widerruf und differenzierte Risiko-Hinweise im Modellmanager ausbauen.
- Nach Einfuehrung des `custom_pytorch`-Runtime-Backends: multimodalen Request-Pfad (Text+Bild) in Chat-API/Service fuer `vision_text_generation` ist umgesetzt; als naechster Schritt bleibt die Ausweitung auf weitere Modalitaeten (`any_to_any`, Audio-Pfade).
- Nach erfolgreicher SmolVLM2-Liveaktivierung inkl. JPEG-Smoke-Test: Vision-Postprocessing weiter verbessern, damit Antworten nicht mehr Prompt-/History-Echo enthalten und modelltypisch kompakt ausgegeben werden.
- Nach Frontend-Umstellung auf Markdown-Rendering: optionale Safe-Plugins (z. B. GFM) und feinere Typografie fuer Tabellen/Codebloecke evaluieren, ohne Sicherheit und Lesbarkeit zu verschlechtern.
- Nach produktiver Einfuehrung und Stabilisierung von `Allgemein`-Settings: verbleibende Frontend-Texte auf durchgaengige i18n-Struktur umstellen (statt partieller DE/EN-Inline-Texte in einzelnen Komponenten).
- Nach produktiver Verdrahtung der Settings-Gruppen `Chat`, `Wissen` und `Logs`: verbleibende Gruppen (`Darstellung`, `Datenbank`, `System`) schrittweise von Platzhaltern auf echte Persistenz-/Validierungsfluesse umstellen.
- Nach Breadcrumb-Anzeige fuer verschachtelte Chat-Projekte: E2E-Regressionen fuer Assign/Unassign in Projektbaeumen und konsistente Labels in weiteren Ansichten ausbauen.
- Nach Entkopplung des Owner-Gates fuer Chat-Projektzuordnung: Berechtigungsmodell fuer sichtbare Fremdchats in Mutationspfaden weiter haerten und mit UI-Tests absichern.
- Nach Quellenfilterung auf die aktive Chat-Projektlinie: Persistenz/Anzeige fuer projektbezogene Quellenzuordnung in der Quellenansicht weiter verfeinern.
- Nach Projektpfad- und Scope-Anzeige pro Quelle: optionale Filter/Aktionen direkt an Quelle und Ebene aus der Chat-UI heraus weiter vereinheitlichen.
- Nach Verlagerung der Chat-Projektzuordnung ins Hamburger-Menue: Bedienung und Tastaturzugang dort weiter verfeinern, statt den Header erneut zu belasten.
- Nach Entkopplung von Projektfilter und Chatliste: klare Aktivierungsanzeige fuer Auswahlzustand, Filterreset und Projektwechsel weiter polieren.
- Nach Entfernen des `selectedProjectLocked`-Pfads: verbleibende Sidebar-States in reine Selector-Helfer auslagern und komponentenweit wiederverwenden.
- Nach hierarchischem Quellenbaum im rechten Panel: Quelle/Abschnitt-Auswahl pro Baumknoten und Filter fuer tiefer verschachtelte Pfade weiter ausbauen.
- Nach Entkopplung und Startup-Cleanup der alten globalen Antwortstil-Keys: chattypische Presets weiter ausbauen (z. B. Streaming-Default, pluginbezogene Sicherheitsstufen, konversationsbezogene Startprofile) ohne erneute Vermischung mit modellspezifischen Generierungsparametern.
- Nach abgesichertem On-Demand-Cleanup im Settings-Bereich: Audit-Trail fuer Wartungsaktionen (`cleanup-obsolete`, Reset-/Repair-Tasks) zentralisieren.
- Nach Einfuehrung der zentralen Security-Dokumente unter `docs/security/`: verbleibende Admin-Endpunkte schrittweise auf gemeinsame Guard-Dependencies und einheitliche Audit-Events migrieren.
- Security-Rollout operationalisieren: `docs/security/README.md` als verbindliche Reihenfolge- und Review-Checkliste fuer neue und bestehende Admin-Endpunkte verwenden.
- Nach Selbstwissen-Erweiterung im Chat-Systemprompt: steuerbare Auspraegung festlegen, welche Benutzer-/Team-Einstellungen als Prompt-Kontext zwingend oder optional einbezogen werden.
- Nach Umstellung des Standardstils auf natuerlichen Fliesstext: umschaltbare Ausgabeprofile (Klartext, strukturiert, technisch) pro Nutzer/Modell im Settings-Flow ergaenzen.
- Nach eingefuehrter Live-Denkblase fuer `<think>`-Streaming: pro Benutzer konfigurierbar machen, ob Reasoning nur live sichtbar oder zusaetzlich in redigierter Form persistiert werden soll.
- Nach integrierter In-Scan-Bereinigung von Datei-vs-Ordner-Dubletten: optionalen expliziten Maintenance-/Migrationspfad fuer historische Sonderfaelle ausserhalb regulärer Scan-Laeufe standardisieren.
- Nach Runtime-Probes und produktiver Loader-Aufloesung: echte Inferenzpfade je Task-Typ (Embedding/Reranker/Speech/OCR/Bild) hinter denselben Loader-IDs weiter vertiefen und benchmarken.
- Chat-Template-Strategie backenduebergreifend weiter haerten: GGUF/llama.cpp-Template-Verhalten gegen reale Modellmetadaten und Sonderfaelle (fehlendes Chat-Template) systematisch validieren.
- Nach gehaerteter GGUF-Dateiauswahl (Gewichte statt `mmproj`): automatische Regressionstests fuer Ordner mit mehreren `.gguf`-Artefakten (inkl. Vision-Projektordateien) im Modellaktivierungsflow verankern.
- Trainings-Kompatibilitaet vertiefen: neben `peft_lora` weitere Trainer-spezifische Regeln und hardwareabhaengige Constraints (VRAM/CUDA/Quantisierung) serverseitig auswerten.
- Geschaeftskorrespondenz-Training weiter haerten: einheitliches JSON-Zielformat pro Dokumenttyp (`geschaeftsbrief`, `angebot`, ...) als verbindlichen Structured-Output-Standard etablieren und in Preflight/Evaluation verankern.
- Nach API-Erweiterung um optionale Testdateien und `imported`-Default: Dataset-Verwaltung auf rollenbasierte Dateimodelle (`source`/`canonical`/`training`/`validation`/`test`) umstellen und UI entlang dieser Rollen strukturieren.
- Nach eingefuehrter Rollen-UI, ZIP-Bundle-Import und normalisierten Tabellen (`training_dataset_files`, `training_artifacts`): End-to-End-Monitoring und Detailansichten auf den neuen Tabellen aufbauen (statt primaer auf JSON-Metadaten).
- Nach neuer Job-Provenance (`result.dataset.files` + UI-Anzeige): naechster Schritt ist die Erweiterung um Dateihashes, Record-Counts und ggf. Snapshot-Versionen fuer vollstaendig reproduzierbare Laufhistorien.
- Nach den neuen Bereichs-Toggles im Trainingscenter: Nutzerpraeferenzen fuer sichtbare Panels (Training/Dateien/Jobs) pro Benutzer speichern und beim erneuten Oeffnen wiederherstellen.
- Nach eingefuehrten Run-Profilen (`A`/`B`/`C`) und strukturierter Artefaktablage pro Dataset/Version: vergleichsbasierte Run-Auswertung (Metrikmatrix + Topic-Abdeckung) als Standardprozess etablieren.
- Nach eingefuehrtem A-F-Experimentskript (`scripts/run_training_experiment_plan.py`): automatische Zusammenfuehrung mehrerer Run-Reports in eine vergleichbare Leaderboard-Ansicht (Base vs Adapter, Delta je Schritt) ausbauen.
- Nach Einfuehrung versionierter Konversations-Generierungsprofile: Versionsvergleich und schnelle Wiederherstellung (Diff/Restore) im UI erweitern.
- Projektverwaltung weiter ausbauen: projektbezogene Filter und Bulk-Aktionen fuer Konversationen, Termine und Wissensquellen konsistent machen.
- Quellenfluss produktivieren: nach `sources/upload` echte Inhaltsverarbeitung (Parsing/Chunking/Indexierung) fuer `pdf/md/txt/docx` aufbauen, damit Retrieval auf Dokumentinhalt statt Dateimetadaten basiert.
- Projektzuordnung robuster machen: stale Projekt-IDs in Konversations-Create-/Assign-Flows automatisch erkennen, ruecksetzen und mit klarer UX-Rueckmeldung recovern.
- Chat-Feedback und Regeneration einzelner Antworten einfuehren.
- Multi-User-Chat-Darstellung verfeinern: Benutzerlabels je Nachricht mit klarer visueller Unterscheidung.
- KI-Teilnahmemodus je Konversation steuern ("KI redet mit"), inklusive Intent-gesteuerter Zurueckhaltung.
- Intent-Marker konfigurierbar machen: Default pro Benutzer plus optionale Ueberschreibung pro Team-Chat.
- Bedienhilfe uebergreifend vereinheitlichen: aussagekraeftige Hover-Hinweise fuer verbleibende Header-/Sidebar-Aktionen vervollstaendigen.
- Einstellungen exportieren, importieren und zuruecksetzen.
- Dokumentversionierung und kontrollierte Neuindizierung bei Embedding-Wechsel.
- Kaskadenloeschung fuer Dokumente, Chunks und Embeddings durchgaengig absichern.
- Strukturierte Request-, Conversation- und Trace-IDs durchgaengig loggen.
- Virtuelle Nachrichtenliste fuer sehr lange Chats im Frontend einfuehren.
- Frontend Error Boundary fuer robuste Fehlerisolierung ergaenzen.
- Navigation mit React Router und Deep Links fuer Chats, Projekte und Dokumente.
- Teststrategie mit kleinen lokalen Testmodellen fuer CI und lokale Entwicklung.

## V3 Teamfaehigkeit und Betriebsstabilitaet

- Teambezogene Sichtbarkeit fuer Konversationen abschliessen (internal statt global).
- Nach UI-Ownership-Guards: Conversation-API-Semantik fuer Teamchats finalisieren (sichtbar vs. bearbeitbar/loeschbar) und konsistente `403`-Antworten fuer fehlende Rechte statt generischer `404` evaluieren.
- Nach interner Default-Sichtbarkeit Team-/Rollenregeln pro Konversation durchsetzen (internal nicht mehr global fuer alle Nutzer).
- Rollen- und Rechtekonzept fuer Projekte, Dokumente und Konversationen erweitern.
- Admin-Benutzerverwaltung weiter haerten: serverseitige Admin-Autorisierung von `admin_user_id` auf echte Session-/Token-Pruefung umstellen.
- Admin-Benutzerverwaltung erweitern: Audit-Log fuer Benutzer-Aenderungen (wer, was, wann) inklusive Rueckverfolgbarkeit im UI bereitstellen.
- Auth-Layer weiterentwickeln: token-basierte Anmeldung um Refresh-/Logout-Invalidierung, robuste Token-Rehydration nach Reload/HMR und optionales Rolling-Session-Konzept ergaenzen.
- Admin-Lifecycle vervollstaendigen: nach Kick-Entsperren jetzt Soft-Delete-Events in der Admin-Historie visualisieren und Reaktivierung geloeschter Konten ergaenzen.
- Teamchat-UX weiterentwickeln: Teilnahme-Schalter und Kollaborationshinweise einheitlich ueber Desktop/Tablet/Mobil verhalten (inkl. klarer Disabled-Zustaende).
- Teamchat-Flow ausbauen: nach User-only-Sendepfad optional konfigurierbar machen, ob bei deaktivierter KI automatisch ein rein menschlicher Modus aktiv ist.
- Hintergrundjobs fuer Import, Embeddings und Reindizierung stabilisieren.
- Hybridsuche aus Volltext und Vektor inklusive Quellen-Nachvollziehbarkeit verfeinern.
- Betriebsmetriken fuer Queue, Modellzustand und Antwortlatenz standardisieren.
- Produktiven Internet-Betrieb standardisieren: Reverse-Proxy-Referenzkonfiguration inkl. TLS, Forwarded-Headern und sicheren CORS-Vorgaben bereitstellen.
- Nutzerpraesenz von Heartbeat-Polling auf push-basierte Echtzeitpraesenz (WebSocket/SSE-Presence-Events) weiterentwickeln.
- Secret-Handling standardisieren: Zugangsdaten und API-Secrets ausschliesslich ueber sichere, nicht versionierte Secret-Speicher verwalten.
- Release-Haertung fuer oeffentliche Repositories ausbauen: standardisierte Pre-Publish-Checks fuer Secret-Scan und Ignore-Regeln vor jedem Public Push etablieren.
- GitHub-Repository-Governance weiter ausbauen: Label-Strategie, Auto-Triage und semantische Release-Notes entlang PR-Kategorien weiter verfeinern.
- Frontend-Devtool-Sicherheit dauerhaft absichern: Vite/Vitest/esbuild-Updates regelmaessig einplanen und Dependabot-PRs zeitnah mergen.
- Nach Major-Upgrades (React/TypeScript/jsdom) verbindliche Kompatibilitaetspruefung ueber CI + UI-Regressionspfade etablieren.
- Backend-Security weiter vertiefen: zentralisiertes Error-Redaction-Pattern fuer alle API-Routen vereinheitlichen und testbar machen.
- Workflow-Stack kontinuierlich haerten: Trigger, Berechtigungen und Secret-Policy regelmaessig ueberpruefen.
- Code-Scanning-Strategie konsolidieren: genau einen produktiven CodeQL-Pfad (Default Setup oder Advanced Setup) verbindlich festlegen und dokumentieren, um SARIF-Konflikte dauerhaft zu vermeiden.
- README-Badge-Pflege standardisieren: fuer jeden aktiven Workflow in `.github/workflows` eine eindeutige Badge-Strategie hinterlegen.
- Support-Prozess standardisieren: Issue-Typisierung (`bug`/`question`/`feature`/`security`) mit reproduzierbaren Mindestangaben und Log-Redaktionsregeln in Templates abbilden.
- Repository-Governance weiter festigen: Lizenz-, Security- und Issue-Template-Konventionen als verbindlichen Maintainer-Check vor Releases verankern.
- Rebranding konsistent halten: sichtbare Produktbezeichnungen, Logos und API-Metadaten bei Namensaenderungen zentral und synchron aktualisieren.
- Design-Konsistenz ausbauen: Branding-Assets (Logo, Farben, Typografie) in Login, Header, Sidebar und Favicon zentral versionieren und validieren.
- Finale Logo-Produktivfassung vorbereiten: Wortmarke fuer absolute Render-Konsistenz optional in Pfade konvertieren und als offizielle Masterdatei versionieren.
- Trainings-URL-Import langfristig produktivieren: Host-Allowlist aus Settings verwalten (statt statischer Basen) und mit dedizierten Security-Tests absichern.
- Chat-Updates von Polling auf push-basiertes Eventing (SSE/WebSocket) umstellen, um geraeteuebergreifend niedrigere Latenz zu erreichen.
- Statische Typqualitaet im Backend weiter schaerfen (Pylance strict): unbekannte Typen in Service-/Repository-Pfaden systematisch eliminieren.

## V4 Training Workbench und Modellverbesserung

- Plugin-Training operationalisieren: bereitgestelltes Datenset (`plugins_agent_training_v1.0.0.jsonl`) in den Evaluationsfluss ueberfuehren und das Interaktionsmuster `<plugin_call>/<plugin_input>/<plugin_response>` mit Gateway-Checks absichern.
- Nach produktiver Chat-Orchestrierung: Trainingsdaten gegen die reale Zwei-Runden-Logik validieren und Plugin-Fehlerpfade als eigene Beispielsammlung erfassen.

- Trainingsdomane als allgemeines `training`-Subsystem aufbauen (statt enger `finetuning`-Bezeichnung), damit neben Fine-Tuning auch LoRA/QLoRA, DPO/PPO, Reranker und Reward-Model-Pfade erweiterbar bleiben.
- Trainings-Preflight fuer lokales Basismodell und Dataset weiter ausbauen (inkl. klarer Fehlerklassifizierung und Recovery-Hinweisen).
- Lifecycle-Konsolidierung abschliessen: `running` als Oberstatus gegen granulare Trainingsstatus/Phasen sauber abloesen.
- Realen PEFT-Smoke-Run als wiederholbaren Verifikationspfad weiter standardisieren (automatisierte Ausfuehrung, reproduzierbare Artefaktpruefung, klare Abbruchsignale).
- Nach fruehem Trainer-Heartbeat und explizitem Validierungsdatei-Support: Trainingsbeobachtbarkeit im UI weiter ausbauen (sichtbare Phase vor Schritt 1, Datensatzgroessen, Tokenizer-/Pad-Checks im Report).
- Nach erfolgreichem Adapter-Artefaktcheck: Trainingsartefakte in den Modellmanager rueckfuehren (registrieren, vergleichen, kurze Testinferenz mit/ohne Adapter).
- Nach direkter Fortschrittsanzeige in der Job-Liste: Runtime-Metriken im selben Job-Panel weiter verdichten (Loss/LR/ETA) und als stabile Beobachtungsansicht standardisieren.
- Nach aktiviertem Live-Polling fuer Trainingsjobs: naechster Schritt ist ein serverseitiges Event-Streaming fuer Job-Progress, um Polling-Last weiter zu reduzieren.
- Nach OOM-Hinweisintegration und Dateifallback fuer Alt-Jobs: automatische Retry-Assistenten mit hardwareabhaengigen Hyperparameter-Empfehlungen aufbauen.
- Nach aktivem CUDA-OOM-CPU-Fallback im PEFT-Trainer: Fallback-Transparenz im UI ausbauen (Kennzeichnung, Dauer, Ressourcenverbrauch) und intelligentes Offload-Tuning je Hardwareprofil einfuehren.
- Nach verbesserter 409-/Preflight-Fehlertransparenz: Jobstart-Dialog um gefuehrte Korrekturschritte (Modell/Trainer/Datensatzstatus) erweitern.
- Nach Parsing verschachtelter API-Fehlerdetails: einheitliche Fehlerdarstellung ueber alle Routen (nicht nur Training) inkl. konsistenter UX-Typen (Hinweis/Warnung/Blocker) einfuehren.
- Nach Freigabe von `imported`-Datasets fuer den Jobstart-Preflight: Statusmodell vereinheitlichen, sodass technische Import-Stati und fachliche Trainingsbereitschaft klar getrennt sind.
- Queue-first Jobstart weiter absichern: Konflikte auf echte technische Blocker begrenzen (Preflight), während Dataset-Lifecycle-Stati den Submit-Pfad nicht unnoetig blockieren.
- API-Robustheit im Trainingspfad ausbauen: ORM-Serialisierung nach Commit standardisieren (Reload-Pattern), um asynchrone Lazy-Load-Fehler in Response-Mapping zu verhindern.
- Dataset-Lebenszyklus weiter schaerfen: harte Loeschung nur fuer unbenutzte Datasets erlauben, genutzte Datasets bewusst archivieren statt referenzierte Trainingshistorie zu zerstören.
- Async-ORM-Antworten nach Commit generell vermeiden oder gezielt neu laden, damit Archivieren/Unarchivieren und andere Training-CRUD-Aktionen keine expired-attribute Fehler erzeugen.
- Trainingsordner als Batch-Quelle: Ordnerbasierte Datensaetze gesammelt in die Queue schieben und erfolgreiche Ergebnisse automatisch archivieren.
- Trainer ueber Interface abstrahieren (Unsloth, Axolotl, TRL, MLX, FutureTrainer), damit Backendwechsel ohne Umbau in Services/API moeglich ist.
- Dataset-Domane mit Versionierung und reproduzierbaren Metadaten ausbauen (Quelle, Split, Tokenizer, Promptformat, Lizenz, Sprache, Checksum, Ersteller, Projektbezug).
- Trainingsdaten und Artefakte langfristig normalisieren: eigene DB-Tabellen fuer Dataset-Dateien und Job-Artefakte einfuehren statt ausschliesslich JSON-Felder zu verwenden.
- Nach Einfuehrung der Tabellen `training_dataset_files` und `training_artifacts`: API-Responses schrittweise auf table-first umstellen und JSON-Felder auf Kompatibilitaetsrolle reduzieren.
- Nach Split-Leakage-Checks im Preflight: ergaenzende Hash-/Checksum-basierte Quellintegritaetspruefung in den Manifest-Flow integrieren.
- Nach eingefuehrtem Business-Letter-Linter: Qualitaetsgates in den Trainingssubmit integrieren (Schema-Validitaet, verbotene Muster, Dokumenttyp-Konsistenz), sodass fehlerhafte Assistant-Targets bereits vor Jobstart abgelehnt werden.
- Nach Datei-/URL-Import fuer Trainingsdatasets: Metadatenfluss fuer Manifest/README/Checksummen automatisch auslesen und bei Importen direkt am Dataset hinterlegen.
- Nach universellem Dataset-MVP: Parser-/Validator-/Exporter-Plugins fuer weitere Formate und unternehmensspezifische Schemata standardisieren, inklusive Auto-Split (train/val/test), Qualitaetsbewertung und Benchmark-Generierung aus demselben kanonischen Datensatz.
- Exporter und Validator als Pflichtbausteine einfuehren: Datenqualitaet/Schema/Tokenlaengen/Rollen/Duplikate validieren und Daten aus Chats/Bibliothek/Dokumenten/Bewertungen/Projekten exportieren.
- Job-Lifecycle fuer Training weiter granularisieren (`created`, `queued`, `preparing`, `validating`, `tokenizing`, `training`, `saving`, `registering`, `completed`, `cancelled`, `failed`) und im UI transparent machen.
- Promotions-Gate verpflichtend machen: Training -> Evaluation -> Healthcheck -> Benchmark -> Registrierung -> Aktivierbar.
- Evaluationsmodul nach jedem Training automatisch ausfuehren (Perplexity, Testsatz, Qualitaet, Benchmark, Regression).
- Nach erweitertem `evaluation-report.json` (Base-vs-Adapter + Konfusionsmatrizen): Labelschema fuer Intent/Agent/Tool standardisieren, damit die Metriken nicht mehr von frei formatierten Completion-JSONs abhaengen.
- Experiment-Tracking und Trainingshistorie persistieren (Hyperparameter, Seed, Commit, Dataset-/Trainer-Versionen, CUDA, Loss/LR/Epoch/ETA/Checkpoint, GPU/VRAM/RAM).
- GPU-Scheduler mit klaren Prioritaeten einfuehren: Chat (1), Embedding (2), Training (3).
- Referenzarchitektur laufend pflegen in [docs/training-workbench.md](docs/training-workbench.md).

## Technische Leitplanken

### API-Kompatibilitaet zwischen Client und Server

- Capability-Modell nach Einfuehrung von `/api/meta/capabilities` auf weitere Featurebereiche ausdehnen (z. B. Uploads, Teamfunktionen, Streaming-Varianten).
- Persistente Frontend-Sessions gegen geloeschte oder ungueltige Benutzer robust validieren (klare Re-Auth statt stiller Fehlerpfade).

### Modellstatus und Tests

- Passiver Modellstatus wird regelmaessig geprueft.
- Aktive Test-Inferenz erfolgt nach dem Laden.
- Erneute Test-Inferenz erfolgt nur bei konkretem Fehlerverdacht.

### OOM-Wiederherstellung

1. Anfrage abbrechen.
2. Backendzustand pruefen.
3. Modell bei Bedarf entladen.
4. Speicher freigeben.
5. Modell kontrolliert neu laden.
6. Erst danach neue Anfragen zulassen.

### Modell-Cache

- Optionaler Mehrmodell-Cache nur bei ausreichend RAM/VRAM.
- Standard bleibt ein gleichzeitig geladenes Modell.

### Zustandsarchitektur Frontend

- TanStack Query verwaltet Serverdaten: Conversations, Messages, Models, Projects, Documents.
- Zentraler UI-Store verwaltet nur Oberflaechenzustand: Sidebars, Theme, aktiver Tab, Fokusmodus, Composer.

### Retry-Strategie API-Client

- GET: begrenzte Retries erlaubt.
- POST, PUT, DELETE: nur mit Idempotency-Key oder explizit als sicher markiert.

### Migration und Seeding

- Migrationen verwalten ausschliesslich Datenbankschema.
- Standardwerte und Standard-Prompts werden idempotent ueber Seed-Service bereitgestellt.
