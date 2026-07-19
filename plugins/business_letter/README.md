# Geschaeftsbrief-Plugin

**Plugin-ID:** `business_letter`
**Kategorie:** Dokumente
**Status:** Implementiert, produktionsnah
**Schwerpunkt:** Geschaeftskommunikation, kaufmaennische Dokumente, E-Rechnung und revisionsnahe Persistenz

## Kurzueberblick

Das Geschaeftsbrief-Plugin erzeugt strukturierte Geschaeftskommunikation und kaufmaennische Dokumente fuer Brief, E-Mail, HTML, PDF, E-Rechnung und Datenbankpersistenz.

Es verbindet:

* Kommunikationslogik fuer Brief und E-Mail
* kaufmaennische Dokumentmodelle
* Positions-, Summen- und Steuerberechnung
* konfigurierbare Dokumentnummern
* Template- und Artefakterzeugung
* XRechnung- und ZUGFeRD-Ausgabe
* XSD- und Schematron-Validierung
* PDF/A-nahe PDF-Erzeugung mit eingebettetem XML
* transaktionale Persistenz
* optionale Spiegelung in eine Gastsystem-Datenbank
* globale, teambezogene und benutzerbezogene Plugin-Settings

Das Plugin kann sowohl reine Kommunikationsdokumente als auch strukturierte kaufmaennische Dokumente erzeugen.

---

## Architektur

Die Implementierung ist in klar getrennte Schichten aufgeteilt.

### Zentrale Orchestrierung

* `plugin.py`

  * Eingaben normalisieren
  * Settings aufloesen
  * Dokumentmodell erzeugen
  * fachliche Validierung ausfuehren
  * Renderer und E-Rechnungsdienste aufrufen
  * Status bestimmen
  * Persistenz koordinieren
  * Ergebnisobjekt zusammenbauen

### Modelle

* `models/parties.py`

  * Absender
  * Empfaenger
  * Unternehmensdaten
  * Ansprechpartner
  * Bank- und Rechtsangaben

* `models/communication.py`

  * Brief- und E-Mail-Kommunikation
  * Betreff
  * Anrede
  * Anlagen
  * Versandinformationen

* `models/commercial.py`

  * kaufmaennische Dokumente
  * Positionen
  * Steuern
  * Rabatte und Zuschlaege
  * Summen
  * Zahlungsinformationen

### Services

* `services/calculation.py`

  * Positionsberechnung
  * Nettosummen
  * Steueraufschluesselung
  * Bruttosummen
  * Zuschlaege und Nachlaesse

* `services/numbering.py`

  * Nummernkreise
  * Sequenzen
  * Jahreswechsel
  * Pattern-Aufloesung
  * parallele Nummernvergabe

* `services/persistence.py`

  * transaktionale Speicherung
  * Dokumentversionen
  * Artefakte
  * Events
  * optionale Gastsystem-Spiegelung

* `services/artifacts.py`

  * Dokumentartefakte
  * Dateinamen
  * MIME-Typen
  * Metadaten

* `services/templates.py`

  * Briefvorlagen
  * E-Mail-Vorlagen
  * Dokumentprofile
  * Template-Auswahl

### Renderer

* `renderers/text.py`
* `renderers/email.py`
* `renderers/html.py`
* `renderers/pdf.py`

### E-Rechnung

* `einvoice/xrechnung.py`

  * XML-Erzeugung
  * UBL-Mapping
  * XRechnung-Ausgabe

* `einvoice/zugferd.py`

  * ZUGFeRD-/Factur-X-Paket
  * XML-Einbettung
  * Profilmetadaten

* `einvoice/validation.py`

  * interne fachliche Regeln
  * Codelistenpruefung
  * strukturierte Validierungsfehler

* `einvoice/official_validation.py`

  * XSD-Ausfuehrung
  * Schematron-Ausfuehrung
  * externe Validatorintegration
  * Validierungsreports

### Settings

* `settings.py`

  * Scope-Merging
  * Plugin-Defaults
  * Nummernkreis-Einstellungen
  * Dokument-Overrides

---

## Intent-Erkennung

Das Plugin kann unter anderem durch folgende Begriffe erkannt werden:

```text
\b(brief|geschaeftsbrief|angebotsschreiben|auftragsbestaetigung|reklamation|abnahme|mahnung|rechnung)\b
```

Die Intent-Erkennung dient nur der Plugin-Auswahl. Der konkrete Dokumenttyp wird ueber `letter_type` beziehungsweise `document_kind` festgelegt.

---

## Unterstuetzte Dokumentarten

### Kommunikationsdokumente

* `allgemein`
* `anfrage`
* `angebotsanfrage`
* `angebotserinnerung`
* `angebotsstornierung`
* `bestellbestaetigung`
* `auftragsaenderung`
* `auftragsstornierung`
* `terminbestaetigung`
* `terminverschiebung`
* `lieferankuendigung`
* `versandanzeige`
* `fertigstellungsanzeige`
* `abnahme`
* `abnahmeprotokoll`
* `rechnung_begleitschreiben`
* `zahlungserinnerung`
* `mahnung_1`
* `mahnung_2`
* `mahnung_3`
* `inkassouebergabe`
* `verzugszinsberechnung`
* `reklamation_eingang`
* `reklamation_antwort`
* `reklamation`
* `maengelanzeige`
* `nachbesserung`
* `stornobestaetigung`
* `vertragsaenderung`
* `vertragsbegleitschreiben`
* `fehlende_angaben`
* `dokumentenanforderung`
* `zahlungsavis`
* `kontoauszug`
* `zahlungsbestaetigung`
* `servicebericht`
* `montagebericht`
* `wartungsprotokoll`
* `retourenschein`
* `lieferantenreklamation`
* `anschreiben`
* `serienbrief`
* `kuendigung`
* `empfangsbestaetigung`

### Kaufmaennische Dokumente

* `angebot`
* `angebot_treppe`
* `preisangebot`
* `angebotsaenderung`
* `auftragsbestaetigung`
* `kostenvoranschlag`
* `lieferschein`
* `teillieferschein`
* `sammellieferschein`
* `abschlagsrechnung`
* `anzahlungsanforderung`
* `schlussrechnung`
* `rechnung`
* `proformarechnung`
* `gutschrift`
* `stornorechnung`
* `belastungsanzeige`
* `bestellung`
* `bestellaenderung`
* `bestellstornierung`
* `wareneingang`

Nicht jede Dokumentart ist automatisch eine E-Rechnung. Eine strukturierte E-Rechnung wird nur für die fakturarelevanten Typen `rechnung`, `abschlagsrechnung`, `schlussrechnung`, `gutschrift` und `stornorechnung` erzeugt, wenn die E-Rechnungsoptionen dies zulassen.

---

## Alias-Normalisierung

Eingaben werden vor der Verarbeitung normalisiert.

Beispiele:

* Umlautvarianten von `auftragsbestaetigung` werden auf `auftragsbestaetigung` abgebildet
* Umlautvarianten von `lieferankuendigung` werden auf `lieferankuendigung` abgebildet
* Umlautvarianten von `stornobestaetigung` werden auf `stornobestaetigung` abgebildet
* Umlautvarianten von `vertragsaenderung` werden auf `vertragsaenderung` abgebildet
* Umlautvarianten von `maengelanzeige` werden auf `maengelanzeige` abgebildet

Dadurch bleiben API-Aufrufe auch bei unterschiedlichen Schreibweisen kompatibel.

---

## Minimale Eingaben

Pflichtfelder:

* `letter_type`
* `subject`

Je nach Kommunikationskanal und Dokumentart koennen weitere Pflichtfelder entstehen.

Beispiel:

```json
{
  "letter_type": "angebot",
  "subject": "Angebot fuer Natursteinarbeiten"
}
```

---

## Erweiterte Eingaben

### Kommunikation

* `communication_channel`

  * `letter`
  * `email`
  * `both`

* `recipient_email`
* `buyer_electronic_address`
* `buyer_electronic_address_scheme`
* `seller_electronic_address`
* `seller_electronic_address_scheme`

* `cc`

* `bcc`

* `salutation`

* `signatory_name`

* `signatory_position`

* `ready_for_sending`

### Dokument

* `document_kind`
* `document_number`
* `issue_date`
* `delivery_date`
* `service_period`
* `buyer_reference`
* `order_reference`
* `contract_reference`
* `project_reference`
* `delivery_note_reference`
* `original_invoice_number`
* `billing_reference_document_number`

### Positionen

* `positions`

  * Beschreibung
  * Menge
  * Einheit
  * Einzelpreis
  * Steuersatz
  * Steuerkategorie
  * Preisbasismenge
  * Preisbasismengen-Einheit
  * Steuerbefreiungsgrund
  * Steuerbefreiungs-Code
  * Nachlaesse
  * Zuschlaege

### Dokumentweite Anpassungen

* `document_allowances`
* `document_charges`
* `shipping_costs`
* `rounding_amount`
* `prepaid_amount`
* `reverse_charge`
* `tax_exemption_reason`
* `tax_exemption_reason_code`

### Templates und Artefakte

* `company_logo_file`

  * `url`
  * `data_url`
  * `content_base64`

* `template_mode`

  * `auto`
  * `brief`
  * `email`
  * `both`
  * `document`

* `template_profile`

* `generate_templates`

* `persist_to_database`

### E-Rechnung-

* `einvoice.enabled`
* `einvoice.standard`
* `einvoice.profile`
* `einvoice.syntax`

Beispiel:

```json
{
  "einvoice": {
    "enabled": true,
    "standard": "xrechnung",
    "profile": "en16931",
    "syntax": "ubl"
  }
}
```

---

## Admin-Settings

Die Settings werden ueber `settingsFields` an das Frontend ausgeliefert und dort typisiert dargestellt.

Im Workspace werden die Plugin-Settings jetzt pro Fachbereich gruppiert und einklappbar dargestellt. Abhaengige Felder werden nur eingeblendet, wenn ihr Steuerfeld aktiv ist, zum Beispiel:

* Steuerbefreiungsgrund und -code nur bei aktivierter Standard-Steuerbefreiung
* Reverse-Charge-Hinweis nur bei aktiviertem Reverse Charge
* E-Rechnungsprofil, Syntax und Validatoroptionen nur bei aktiver E-Rechnung
* Gastsystempfad und Dual-Save-Fehlerverhalten nur bei aktivem Dual-Save

Die Settings-API selbst ist jetzt scopesensitiv abgesichert:

* globale Settings nur fuer Administratoren
* reine Team-Settings derzeit nur fuer Administratoren, solange kein separates Team-Mitgliedschaftsmodell vorhanden ist
* benutzerbezogene Settings nur fuer den jeweiligen Benutzer oder Administratoren
* sensible Werte bleiben im normalen Settings-Read maskiert; `settings.resolved` maskiert zusaetzlich pluginseitige Passwort-/Secret-/Token-Felder

### Firmendaten

* `company_logo_url`
* `company_name`
* `company_street`
* `company_zip`
* `company_city`
* `company_country`
* `company_postbox`
* `company_phone`
* `company_mobile`
* `company_fax`
* `company_email`
* `company_electronic_address`
* `company_electronic_address_scheme`
* `company_email_reply_to`
* `company_email_bcc`
* `company_website`
* `company_manager`
* `company_profession`
* `company_chamber`
* `company_agb`
* `company_privacy`

### Rechtliche Angaben

* `company_tax_id`
* `company_vat_id`
* `company_legal_form`
* `company_registry_number`
* `company_registry_court`
* `company_responsible_content`

### Bankverbindung

* `company_bank_name`
* `company_iban`
* `company_bic`
* `company_account_holder`

### Kommunikation-

* `default_language`
* `default_tone`
* `default_salutation`
* `default_email_greeting`
* `default_email_signature`
* `default_email_disclaimer`
* `default_confidentiality_notice`
* `default_signatory_name`
* `default_signatory_position`
* `base_intro_text`
* `base_closing_text`
* `base_missing_info_text`
* `default_cc`
* `default_email_subject_template`
* `default_reply_to_address`
* `default_email_html_enabled`
* `default_attach_pdf`
* `default_attach_xml`
* `default_filename_pattern`
* `default_reminder_text_level_1`
* `default_reminder_text_level_2`

Diese Versandfelder greifen jetzt im Laufzeitpfad:

* `default_email_subject_template` wird mit Platzhaltern wie `document_kind`, `document_number`, `customer_company`, `customer_name` und `subject` aufgeloest.
* `default_cc` sowie `company_email_bcc` werden als Default-Empfaenger ausgewertet; vorhandene explizite Empfaenger bleiben erhalten.
* `default_reply_to_address` faellt vor `company_email_reply_to` auf die Antwortadresse zurueck.
* `default_email_html_enabled=false` unterdrueckt die HTML-Mail-Ausgabe und laesst nur den Textkoerper aktiv.
* `default_attach_pdf` und `default_attach_xml` erzeugen automatische Mail-Anhaenge fuer das generierte PDF bzw. das E-Rechnungs-XML.
* `validate_before_send` plus `block_send_on_validation_error` blockieren den E-Mail-Versandpfad bei fehlschlagender E-Rechnungsvalidierung und setzen den Status auf `needs_review`.

Fuer dokumenttypspezifische Abweichungen werden dieselben Schluessel auch mit Suffix ausgewertet, etwa `default_email_subject_template_rechnung`, `default_cc_mahnung` oder `company_email_bcc_angebot`.

### Dokument-Defaults

* `default_currency`
* `default_payment_terms`
* `default_payment_method_code`
* `default_payment_days`
* `default_invoice_type_code`
* `default_country_code`
* `default_unit_code`
* `default_tax_rate`
* `default_tax_category`
* `default_reverse_charge_enabled`
* `default_tax_exemption_enabled`
* `default_tax_exemption_reason`
* `default_tax_exemption_reason_code`
* `default_reverse_charge_note`
* `default_buyer_reference`
* `default_payment_reference`
* `default_delivery_terms`
* `default_place_of_supply`
* `default_jurisdiction`
* `default_offer_validity_days`

Zur Laufzeit werden diese Defaults bereits fuer BuyerReference, PaymentReference, Angebotsgueltigkeit sowie Positions-Fallbacks fuer Einheitencode, Steuerkategorie, Steuersatz und Steuerbefreiungsdaten angewendet.

### Bank & Zahlung

* `default_payment_recipient`
* `default_sepa_creditor_id`
* `default_sepa_mandate_reference`
* `default_payment_purpose_template`
* `default_cash_discount_percent`
* `default_cash_discount_days`
* `default_dunning_fee`
* `default_late_interest_rate`

### E-Rechnung--

* `default_einvoice_enabled`
* `default_einvoice_standard`
* `default_einvoice_profile`
* `default_einvoice_syntax`
* `xrechnung_version`
* `zugferd_version`
* `default_einvoice_profile_invoice`
* `default_einvoice_profile_credit_note`
* `validator_profile`
* `validate_on_save`
* `validate_before_send`
* `require_pdfa_check`
* `block_send_on_validation_error`
* `store_xml_artifact`
* `archive_validation_report`

### Persistenz und Archivierung

* `dual_save_enabled`
* `dual_save_failure_mode`
* `dual_save_retry_attempts`
* `guest_system_database_mode`
* `guest_system_database_path`
* `artifact_directory`
* `retention_days`
* `enable_document_versioning`
* `enable_hash_verification`
* `lock_released_documents`
* `store_validation_reports`
* `archive_pdf_xml_together`

Diese Felder greifen jetzt im Persistenzpfad:

* `dual_save_enabled` schaltet den Gastsystem-Mirror tatsaechlich ein oder aus.
* `dual_save_failure_mode` unterstuetzt `warn`, `queue` und `fail` fuer fehlgeschlagene Gastsystem-Spiegelungen.
* `dual_save_retry_attempts` wird als echte Retry-Anzahl vor dem finalen Fehlerentscheid ausgewertet.
* `artifact_directory` steuert den Storage-Key fuer persistierte Artefakte, Reports und XML-Dateien.
* `store_validation_reports` archiviert vorhandene offizielle Validator-Reports aus dem konfigurierten Report-Verzeichnis als Persistenzartefakte.
* `archive_pdf_xml_together` gruppiert PDF- und XML-Artefakte in derselben Archivgruppe.
* `enable_hash_verification` prueft persistierte Artefakt-Hashes im Plugin-Store nach dem Schreiben.
* `lock_released_documents` markiert freigegebene Dokumente als unveraenderlich und blockiert spaetere inhaltliche Aenderungen desselben `document_id`.
* `retention_days` erzeugt Retention-Metadaten fuer Dokumente und Artefakte.

### Nummernkreise je Dokumentart

Zusaetzlich zum generischen Nummernkreis gibt es jetzt dokumenttypspezifische Felder fuer:

* `angebot`
* `auftragsbestaetigung`
* `lieferschein`
* `rechnung`
* `abschlagsrechnung`
* `schlussrechnung`
* `gutschrift`
* `stornorechnung`
* `mahnung`

Je Dokumentart werden folgende Schluessel unterstuetzt:

* `<art>_document_number_prefix`
* `<art>_document_number_sequence_kind`
* `<art>_document_number_pattern`
* `<art>_document_number_width`
* `<art>_document_number_start_value`
* `<art>_document_number_year_reset`

Diese Felder werden bereits bei der Nummernvergabe aufgeloest. `mahnung_1` und `mahnung_2` teilen sich dabei den Scope `mahnung`, `angebot_treppe` nutzt den Scope `angebot`.

Zusatzverhalten im aktuellen Stand:

* Eigene Startwerte pro Dokumenttyp greifen bei der ersten Reservierung der jeweiligen Sequenz.
* `*_document_number_year_reset=false` fuehrt die Sequenz jahresuebergreifend fort, waehrend der Jahreswert im Format weiter aus dem aktuellen Datum kommt.
* Identische `sequence_kind`-Werte ueber mehrere Dokumenttypen werden beim Speichern als Konflikt abgelehnt.
* Nummernkreis-relevante Felder sind nach erster Verwendung einer Sequenz nicht mehr aenderbar.
* Im Plugin-UI wird eine Vorschau der naechsten Nummer pro Dokumenttyp angezeigt; sie basiert auf dem aktuellen Pattern, Prefix, Startwert und Jahresformat der laufenden Konfiguration.

### Dokumentlayout

* `layout_template`
* `logo_width_mm`
* `logo_position`
* `page_margin_mm`
* `default_font_family`
* `default_font_size_pt`
* `accent_color`
* `footer_text`
* `show_page_numbers`
* `show_bank_details_in_footer`
* `show_legal_details_in_footer`
* `draft_watermark_text`
* `default_pdf_filename_pattern`

Diese Felder greifen jetzt auch im Laufzeitpfad:

* HTML-Dokumente uebernehmen Schriftfamilie, Schriftgroesse, Seitenraender, Akzentfarbe, Logo-Breite, Logo-Position und Entwurfswasserzeichen.
* HTML- und PDF-Ausgabe fuehren Footertext, optionale Bankdaten, optionale rechtliche Angaben und Seitenzahlanzeige zusammen.
* PDF-Artefakte uebernehmen Seitenraender, Schriftgroesse, Footerzeilen, Seitenzahlen und Entwurfswasserzeichen im einfachen PDF-Renderer.
* PDF-Dateinamen werden ueber `default_pdf_filename_pattern` erzeugt; sonstige Artefakte nutzen weiterhin das allgemeine Dateinamenmuster.

### Fachliche Hinweise

* `text_natural_material_notice`
* `text_external_trades_notice`
* `text_measurement_notice`
* `text_installation_notice`
* `text_care_notice`
* `text_color_variation_notice`
* `text_tolerance_notice`
* `text_batch_notice`
* `text_scaffolding_notice`
* `text_disposal_notice`
* `text_warranty_notice`
* `text_material_availability_notice`

### Legacy-Fallbacks

Folgende historische Schluessel bleiben kompatibel:

* `company_registry`
* `company_bank`

Neue Implementierungen sollten die aufgeteilten aktuellen Felder verwenden.

---

## Settings-Scopes

Settings koennen aus mehreren Ebenen stammen.

Die interne Aufloesungsreihenfolge lautet:

1. `system_defaults`
2. globaler beziehungsweise tenantbezogener Scope
3. Team-Scope
4. Benutzer-Scope
5. Standort-Scope
6. Plugin-Scope
7. Dokument-Override

Spaetere und spezifischere Werte ueberschreiben allgemeinere Werte.

API-seitig werden Settings unter anderem ueber folgende Angaben adressiert:

* `category`
* `key`
* optional `team_id`
* optional `user_id`

Der wirksame Stand wird im Plugin-Ergebnis unter `settings.resolved` ausgegeben.

### Aufrufbezogene Overrides

`plugin_settings` gelten nur fuer den aktuellen Plugin-Aufruf und veraendern keine dauerhaft gespeicherten Settings.

Beispiel:

```json
{
  "plugin_settings": {
    "default_currency": "EUR",
    "default_payment_days": 14
  }
}
```

---

## Settings-Validierung

Fuer `category=plugins` und `key=business_letter_profile` gelten typisierte und feldbezogene Regeln.

### Allgemeine Regeln

* Strings werden als Strings validiert
* Textfelder werden als Text validiert
* Boolean-Felder akzeptieren nur gueltige Wahrheitswerte
* Number-Felder werden numerisch validiert
* Select-Felder werden gegen ihre erlaubten Optionen geprueft
* unbekannte Settings-Felder werden abgelehnt

### Business-Letter-spezifische Regeln

#### `document_number_pattern`

* muss `{sequence_text}` enthalten
* darf nur freigegebene Tokens verwenden
* unvollstaendige oder unbekannte Tokens werden abgelehnt

#### `document_number_width`

* muss ganzzahlig sein
* erlaubter Bereich: `1` bis `12`

#### `default_payment_days`

* muss ganzzahlig sein
* erlaubter Bereich: `0` bis `365`

#### `guest_system_database_path`

* muss ein relativer Pfad sein
* darf keine Path-Traversal-Segmente enthalten
* darf nicht auf ein beliebiges absolutes Ziel verweisen
* muss auf `.db` enden

### Fehlerformat

Validierungsfehler werden feldbezogen zurueckgegeben.

```json
{
  "code": "invalid_plugin_settings",
  "field_errors": {
    "document_number_width": "Der Wert muss zwischen 1 und 12 liegen."
  }
}
```

Das Frontend kann diese Fehler direkt dem betroffenen Eingabefeld zuordnen.

---

## Runtime-Defaults

Fehlende Dokumentwerte koennen aus den Settings ergaenzt werden.

Unter anderem:

* Waehrung aus `default_currency`
* Zahlungsbedingungen aus `default_payment_terms`
* Zahlungsart aus `default_payment_method_code`
* Faelligkeitsdatum aus `issue_date + default_payment_days`
* E-Rechnungsaktivierung aus `default_einvoice_enabled`
* Standard aus `default_einvoice_standard`
* Profil aus `default_einvoice_profile`
* Syntax aus `default_einvoice_syntax`

Explizite Dokumentwerte haben Vorrang vor gespeicherten Defaults.

---

## Ausgabe

Das Plugin liefert ein strukturiertes Ergebnisobjekt.

Wesentliche Bloecke:

* `letter`
* `email`
* `content`
* `document`
* `commercial_document`
* `totals`
* `template`
* `artifacts`
* `validation`
* `delivery`
* `metadata`
* `database`
* `settings.resolved`
* optional `einvoice`

### Beispielhafte Struktur

```json
{
  "status": "ready",
  "document": {},
  "commercial_document": {},
  "totals": {},
  "artifacts": [],
  "validation": {
    "status": "valid",
    "errors": [],
    "warnings": []
  },
  "settings": {
    "resolved": {}
  }
}
```

---

## Fachliche Validierung

### Allgemeine Kommunikation

* Empfaengeradresse bei Briefausgabe
* gueltige Empfaenger-E-Mail bei E-Mail-Ausgabe
* gueltige `cc`- und `bcc`-Adressen
* vorhandener Betreff
* vorhandener Unterzeichner
* Warnung bei fehlender Frist
* Warnung bei fehlender Dokument- oder Vorgangsnummer
* Erkennung offensichtlicher Platzhalterdaten

Beispiele fuer erkannte Platzhalter:

* `Musterstrasse`
* `Max Mustermann`
* generische Testadressen

### Kaufmaennische Dokumente-

Kaufmaennische Dokumente benoetigen grundsaetzlich Positionen.

Ausnahmen koennen fuer reine Begleit- oder Erinnerungsschreiben gelten.

### Mahnungen

`mahnung_1` und `mahnung_2` benoetigen mindestens:

* `invoice_number`
* `invoice_date`
* `invoice_amount`
* `due_date`

### Anlagen

Eine Anlage mit:

```json
{
  "required": true,
  "included": false
}
```

erzeugt einen Validierungsfehler.

### Text-Anlagen-Konsistenz

Verweist der Dokumenttext auf Anlagen, obwohl keine Anlagen hinterlegt sind, wird eine Warnung erzeugt.

---

## Statuslogik

Der Dokumentstatus wird aus Validierung, explizitem Status und Versandbereitschaft abgeleitet.

### Prioritaet

1. Bei Validierungsfehlern: `needs_review`
2. Bei explizitem erlaubtem Status: expliziter Status
3. Bei `ready_for_sending=true`: `ready`
4. Sonst: `draft`

### Unterstuetzte explizite Statuswerte

* `approved`
* `queued`
* `sent`
* `delivered`
* `failed`
* `returned`
* `answered`
* `archived`
* `cancelled`

`validation.status` wird separat aus Fehlern, Warnungen und fehlenden Informationen bestimmt.

---

## E-Rechnung---

## XRechnung

Die XRechnung wird aus `commercial_document` erzeugt.

Unterstuetzte Funktionen umfassen:

* UBL-basierte XML-Ausgabe
* CII-/UN/CEFACT-basierte XML-Ausgabe
* Dokumentwaehrung
* Zahlungsart
* Rechnungspositionen
* Mengen und Einheiten
* Steuerkategorien
* Steuersaetze
* Preise
* Summen
* Referenzen
* strukturierte Validierungsreports

### Interne Validierung

Die interne Validierung prueft unter anderem:

* Pflichtfelder
* Summenkonsistenz
* Steuerdaten
* Datumswerte
* Codelisten
* fachliche Dokumentregeln

### Codelisten

Geprueft werden unter anderem:

* ISO 4217 fuer Waehrungen
* UNCL 4461 fuer Zahlungsarten
* UNCL 5305 fuer Steuerkategorien
* UNECE Recommendation 20 fuer Mengeneinheiten

### Offizielle Validierung

Der E-Rechnungspfad unterstuetzt zusaetzlich:

* XSD-Validierung fuer UBL und CII
* Schematron-Validierung fuer UBL und CII
* externe Validatorartefakte
* strukturierte Reports
* CI-seitige Bereitstellung der Reports

XSD-, Schematron- und Validatorversionen sollten fuer produktive Releases fest versioniert und mit Pruefsummen abgesichert werden.

---

## ZUGFeRD und Factur-X

Der ZUGFeRD-Pfad erzeugt ein PDF mit eingebettetem Rechnungs-XML.

Unterstuetzt werden:

* eingebettete XML-Datei
* `factur-x.xml` als Dateiname fuer entsprechende Profile
* `/EmbeddedFiles`
* `/AF`
* `/AFRelationship`
* XMP-Metadaten
* Profil- und Guideline-Metadaten
* PDF/A-3-bezogene Dokumentstrukturen

XML, XMP-Profil, Dateiname und PDF-Metadaten muessen je verwendetem Profil konsistent sein.

Die technische Validierung erfolgt unter anderem mit veraPDF im CI.

---

## Persistenz

## Transaktionale Plugin-Datenbank

Nummernreservierung und Dokumentpersistenz laufen innerhalb eines gemeinsamen transaktionalen Write-Pfads.

Verwendete Tabellen:

* `document_templates`
* `commercial_documents`
* `document_versions`
* `document_artifacts`
* `document_events`
* `number_sequences`

Dadurch wird verhindert, dass eine Dokumentnummer erfolgreich reserviert wird, das zugehoerige Dokument aber nicht gespeichert wird.

### Gespeicherte Inhalte

Je nach Dokument und Konfiguration:

* normalisiertes Dokumentmodell
* kaufmaennische Daten
* Versionen
* Textartefakte
* HTML
* PDF
* XML
* Validierungsinformationen
* Statusereignisse
* Nummernkreis-Metadaten

---

## Dual-Save

Optional kann das Plugin Dokumente in eine zusaetzliche Gastsystem-Datenbank spiegeln.

Konfiguration:

* `guest_system_database_path`

Die Spiegelung kann umfassen:

* Dokument-Payload
* Dokumentmetadaten
* Artefakte
* Statusinformationen

Der Pfad wird aus Sicherheitsgruenden API-seitig validiert.

Fuer produktive Installationen sollte eine klare Fehlerstrategie definiert sein, falls Plugin-Datenbank und Gastsystem-Datenbank unterschiedliche Ergebnisse liefern.

---

## Nummernkreis

Die Dokumentnummer wird aus einem persistenten Nummernkreis erzeugt.

Konfigurierbare Bestandteile:

* `prefix`
* `sequence_kind`
* `year`
* `width`
* `pattern`

Beispiel:

```text
RE-{year}-{sequence_text}
```

Die Nummernvergabe unterstuetzt:

* feste Praefixe
* konfigurierbare Stellenbreite
* Jahresbezug
* unterschiedliche Sequenzarten
* explizit vorgegebene Dokumentnummern
* parallele Zugriffe
* persistente Sequenzen

Dokumentnummern werden nicht aus Python-Hashwerten oder zufaelligen UUIDs erzeugt.

---

## Artefakte und Renderer

Moegliche Ausgabeformate:

* Klartext
* E-Mail-Text
* HTML
* PDF
* XRechnung-XML
* ZUGFeRD-/Factur-X-PDF
* Validierungsreport

Artefakte enthalten je nach Typ:

* Dateiname
* MIME-Typ
* Inhalt oder Speicherreferenz
* Dokumentbezug
* Metadaten
* optional Hash- oder Versionsinformationen

---

## Tests

## Backend

Vorhandene Tests decken unter anderem ab:

* Nummernvergabe
* Jahreswechsel
* parallele Sequenzvergabe
* transaktionale Persistenz
* Settings-Aufloesung
* Settings-API-Persistenz
* kompletter Reload mit neuer App-Session
* semantische Settings-Validierung
* XRechnung-Ausgabe
* ZUGFeRD-Ausgabe
* XML-Embedding
* XSD-Validierung
* Schematron-Validierung
* UBL-Mapping
* Codelisten
* PDF-Strukturmerkmale
* Scope-Matrix fuer global, Team und Benutzer

## Frontend

Vorhandene Regressionen decken unter anderem ab:

* Select-Settings
* Boolean-Settings

### Priority-3 Coverage-Matrix

Die folgende fachliche Mapping-Matrix ist jetzt explizit testgetrieben abgedeckt:

| Bereich | Abdeckung |
| --- | --- |
| Reverse Charge | `AE`-Steuerkategorie inklusive XML-Mapping und Validierung |
| Steuerbefreiung | `E`-Kategorie inklusive `TaxExemptionReason` und `TaxExemptionReasonCode` |
| Abschlagsrechnung | `InvoiceTypeCode 326` |
| Schlussrechnung | `PrepaidAmount` plus Billing-Reference |
| Gutschrift | `InvoiceTypeCode 381` plus Billing-Reference |
| Stornorechnung | `InvoiceTypeCode 381` plus Billing-Reference |
| Preisbasismengen | `cbc:BaseQuantity` im Preisblock |
| Mehrere Steuersaetze | mehrere `cac:TaxSubtotal`-Bloecke |
| Dokumentrabatte/Zuschlaege | `cac:AllowanceCharge` auf Belegebene |
| Versandkosten | separater Zuschlag mit eigener Reason/ReasonCode |
| Rundungsdifferenzen | `cbc:PayableRoundingAmount` |
| Bestell-/Vertrags-/Projekt-/Lieferscheinreferenzen | UBL-Referenzbloecke im XML |
| Elektronische Adressen | `cbc:EndpointID` mit `schemeID` fuer Buyer/Seller |
| CII-Paritaet | analoge Abbildung zentraler Fachfelder im `CrossIndustryInvoice`-Pfad |

* Speichern
* Re-Render
* erneutes Oeffnen
* Erhalt des Settings-Drafts
* API-Service-Aufrufe mit `team_id`
* Fehler-Mapping fuer `invalid_plugin_settings`

---

## CI

Der CI-Pfad umfasst beziehungsweise sollte fuer Releases umfassen:

* Backend-Tests
* Frontend-Tests
* TypeScript-Build
* Lint
* XML-Validierung
* XSD-Validierung
* Schematron-Validierung
* veraPDF
* Upload von Validierungsreports
* Upload von Fehlerartefakten auch bei fehlgeschlagenen Gates

Validatorversionen und externe Artefakte sollten fest gepinnt werden.

---

## Sicherheitsaspekte

### Datenbankpfade

* nur relative Pfade
* keine Traversal-Segmente
* nur freigegebene Dateiendungen
* keine beliebigen absoluten Zielpfade

### Settings-Validierung-

* unbekannte Felder werden abgelehnt
* Select-Werte werden gegen Allow-Lists geprueft
* sensible Werte sollten nicht unmaskiert ueber `settings.resolved` ausgegeben werden

### Mandanten- und Teamtrennung

* Settings muessen nach Scope getrennt bleiben
* globale und teambezogene Schreibvorgaenge benoetigen passende Berechtigungen
* Dokumente und Artefakte duerfen nicht zwischen Mandanten oder Teams vermischt werden

### Dokumentartefakte

* Dateinamen muessen normalisiert werden
* Pfadangaben duerfen keine Traversal-Angriffe erlauben
* Base64- und Data-URL-Inhalte sollten Groessenlimits unterliegen
* MIME-Typen sollten geprueft werden

---

## Bekannte Grenzen

Die technische Integration fuer XSD, Schematron und veraPDF ist vorhanden. Fuer eine vollstaendige produktive Freigabe bleiben jedoch fachliche und betriebliche Haertungen relevant.

Insbesondere:

* vollstaendige Abdeckung aller EN16931-Sonderfaelle
* offizielle KoSIT-Referenzrechnungen fuer UBL und CII als Regressionstest
* weitere komplexe EN16931-Fallkombinationen ueber die bereits abgedeckten Mappings hinaus
* vollstaendige Rechtepruefung fuer alle Settings-Scopes
* reproduzierbare Validator-Updates
* langfristige Archivierungs- und Revisionsanforderungen

---

## Produktionskritische Restarbeiten

### 1. Validatorartefakte reproduzierbar verwalten

* feste Versionen fuer XRechnung und KoSIT
* feste veraPDF-Version
* SHA-256-Pruefsummen
* Versionsmanifest
* dokumentierte Bezugsquellen
* definierter Update- und Rollback-Prozess

### 2. Vollstaendigen Release-CI-Lauf absichern

* keine uebersprungenen Validator-Tests
* komplette Backend-Suite
* komplette Frontend-Suite
* TypeScript-Build
* Lint
* XSD und Schematron als harte Gates
* veraPDF als hartes Gate
* Reports mit `if: always()` archivieren

### 3. Offizielle Referenzfaelle

* gueltige Referenzrechnungen aus `itplr-kosit/xrechnung-testsuite` fuer UBL und CII
* offiziell abgeleitete ungueltige Referenzrechnungen auf Basis derselben KoSIT-Faelle fuer UBL und CII
* erwartete XSD-Fehler
* erwartete Schematron-Regeln
* erwartete KoSIT-Regel-IDs

Aktuell sind im Testbaum feste KoSIT-Fixtures aus `v2026-01-31` hinterlegt, darunter mehrere UBL-Faelle (minimal, umfassend, Business-Case) sowie kleine offizielle CII-/UN/CEFACT-Faelle. Fuer Negativtests werden diese offiziellen Positivfaelle reproduzierbar mutiert, damit konkrete Rule-IDs wie `BR-DE-15`, `PEPPOL-EN16931-R010`, `PEPPOL-EN16931-R020` und `BR-DEX-09` gegen den offiziellen Schematron-Lauf fuer beide Syntaxpfade abgesichert werden koennen.

### 4. Fachliches Mapping erweitern

* vollstaendige elektronische Adressen mit `schemeID`
* Bestellreferenzen
* Vertragsreferenzen
* Projektreferenzen
* Lieferscheinreferenzen
* Zahlungsbedingungen
* Bankdaten
* mehrere Steuerkategorien
* Dokumentrabatte
* Positionsrabatte
* Zuschlaege
* Versandkosten
* Steuerbefreiungen
* Reverse Charge
* Anzahlungen
* Gutschriften
* Stornorechnungen
* Rundungsdifferenzen

### 5. PDF/A-3 weiter haerten

* mehrseitige Dokumente
* Logos und Bilder
* Unicode
* grosse XML-Anhaenge
* verschiedene Dokumenttypen
* konsistente XMP- und XML-Profile

### 6. Settings-Scope im UI vollstaendig testen

* globale Werte
* Team-Overrides
* Benutzer-Overrides
* Teamwechsel
* Benutzerwechsel
* sichtbare Vererbungsquelle
* Berechtigungsfehler
* optional Plugin-Instanz-Scope

### 7. Revisions- und Betriebsanforderungen

* unveraenderliche freigegebene Dokumentversionen
* Hashes fuer Dokument, XML und PDF
* Statushistorie
* Korrektur- und Stornoprozess
* Backup und Restore
* Aufbewahrung
* Monitoring
* strukturierte Fehlerlogs

---

## Empfohlene Release-Checkliste

Vor einem produktiven Release sollten mindestens folgende Punkte erfolgreich sein:

* [ ] gesamte Backend-Test-Suite erfolgreich
* [ ] gesamte Frontend-Test-Suite erfolgreich
* [ ] TypeScript-Build erfolgreich
* [ ] Lint erfolgreich
* [ ] XSD-Validierung erfolgreich
* [ ] Schematron-Validierung erfolgreich
* [ ] veraPDF erfolgreich
* [ ] keine produktionskritischen Tests uebersprungen
* [ ] Validatorversionen gepinnt
* [ ] Checksummen geprueft
* [ ] CI-Reports archiviert
* [ ] Nummernkreis unter Parallelzugriff getestet
* [ ] Settings-Scope und Rechte getestet
* [ ] Backup und Restore getestet
* [ ] fachliche Freigabe erfolgt

---

## Technische Hinweise

* `plugin_settings` ueberschreibt Werte nur fuer den aktuellen Aufruf.
* Persistente Settings werden nicht durch Dokument-Overrides veraendert.
* Aufgeloeste Werte stehen unter `settings.resolved`.
* Dokumentwerte haben Vorrang vor allgemeinen Defaults.
* Dokumentnummern stammen aus persistenten Nummernkreisen.
* Validierungsfehler verhindern den Status `ready`.
* E-Rechnungsreports sollten zusammen mit XML und PDF archiviert werden.
* Externe Validatorartefakte sollten nicht ungeprueft zur Laufzeit heruntergeladen werden.
* Fuer versendete Rechnungen sollten Korrekturen ueber Storno oder Gutschrift erfolgen, nicht durch nachtraegliche Mutation.
