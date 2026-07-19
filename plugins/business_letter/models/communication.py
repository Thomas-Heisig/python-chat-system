from __future__ import annotations

from typing import Any, cast

from plugins.business_letter.constants import EMAIL_RE, PLACEHOLDER_PATTERNS


def normalize_letter_type(value: Any, aliases: dict[str, str]) -> str:
    raw = str(value or "allgemein").strip().lower()
    return aliases.get(raw, raw)


def resolve_body_paragraphs(data: dict[str, Any], company: dict[str, str]) -> list[str]:
    content = str(data.get("content") or "").strip()
    if content:
        paragraphs = [item.strip() for item in content.split("\n") if item.strip()]
        if paragraphs:
            return paragraphs

    letter_type = str(data.get("letter_type") or "allgemein").strip().lower()
    intro = company["base_intro_text"]

    if letter_type in {"angebot", "angebot_treppe", "preisangebot", "kostenvoranschlag"}:
        paragraphs = [intro, "auf Grundlage Ihrer Anfrage erstellen wir ein unverbindliches Entwurfsangebot."]
        offer_valid_until = str(data.get("offer_valid_until") or "").strip()
        if offer_valid_until:
            paragraphs.append(f"Dieses Angebot ist gültig bis {offer_valid_until}.")
        delivery_date = str(data.get("delivery_date") or "").strip()
        if delivery_date:
            paragraphs.append(f"Geplanter Lieferzeitraum: {delivery_date}.")
        not_included = [str(item).strip() for item in cast(list[Any], data.get("not_included") or []) if str(item).strip()]
        if not_included:
            paragraphs.append("Nicht enthaltene Leistungen: " + ", ".join(not_included) + ".")
        return paragraphs

    templates: dict[str, list[str]] = {
        "anfrage": [intro, "vielen Dank für Ihre Anfrage. Wir prüfen Ihr Anliegen und melden uns mit den nächsten Schritten."],
        "angebotsanfrage": [intro, "vielen Dank für Ihre Angebotsanfrage. Auf Basis Ihrer Angaben bereiten wir ein passendes Angebot vor."],
        "angebotserinnerung": [intro, "wir erinnern freundlich an das noch offene Angebot und stehen für Rückfragen bereit."],
        "angebotsaenderung": [intro, "wir bestätigen die abgestimmte Änderung Ihres Angebots und fassen die aktualisierten Inhalte zusammen."],
        "angebotsstornierung": [intro, "wir bestätigen die Stornierung des vorliegenden Angebots."],
        "auftragsbestaetigung": [intro, "hiermit bestätigen wir den Eingang Ihres Auftrags gemäß den vorliegenden Angaben."],
        "bestellbestaetigung": [intro, "hiermit bestätigen wir den Eingang Ihrer Bestellung und den vorgesehenen Bearbeitungsbeginn."],
        "auftragsaenderung": [intro, "wir bestätigen die besprochene Änderung des laufenden Auftrags."],
        "auftragsstornierung": [intro, "wir bestätigen die Stornierung des laufenden Auftrags."],
        "bestellung": [intro, "hiermit erteilen wir die Bestellung gemäß den abgestimmten Konditionen."],
        "bestellaenderung": [intro, "wir teilen die Änderung einer bestehenden Bestellung mit."],
        "bestellstornierung": [intro, "wir bestätigen die Stornierung der bestehenden Bestellung."],
        "terminbestaetigung": [intro, "hiermit bestätigen wir den mit Ihnen abgestimmten Termin."],
        "terminverschiebung": [intro, "leider müssen wir den vorgesehenen Termin verschieben und schlagen einen Ersatztermin vor."],
        "lieferankuendigung": [intro, "wir kündigen die Lieferung bzw. Montage für den vereinbarten Zeitraum an."],
        "teillieferschein": [intro, "anbei erhalten Sie den Teillieferschein zu den bereits ausgelieferten Positionen."],
        "sammellieferschein": [intro, "anbei erhalten Sie den Sammellieferschein zu den zusammengefassten Lieferungen."],
        "versandanzeige": [intro, "wir informieren Sie über den Versand der beauftragten Ware oder Leistung."],
        "fertigstellungsanzeige": [intro, "die beauftragten Leistungen sind fertiggestellt."],
        "abnahme": [intro, "die Leistungen stehen zur gemeinsamen Abnahme bereit."],
        "abnahmeprotokoll": [intro, "anbei erhalten Sie das Protokoll zur durchgeführten Abnahme."],
        "rechnung_begleitschreiben": [intro, "anbei erhalten Sie die Rechnung zu den erbrachten Leistungen."],
        "zahlungserinnerung": [intro, "wir erinnern freundlich an die noch offene Zahlung."],
        "mahnung_1": [intro, "trotz Fälligkeit konnten wir bislang keinen Zahlungseingang feststellen."],
        "mahnung_2": [intro, "leider liegt weiterhin kein Zahlungseingang vor. Wir bitten um umgehende Ausgleichung."],
        "mahnung_3": [intro, "trotz mehrfacher Erinnerung liegt weiterhin kein Zahlungseingang vor. Bitte begleichen Sie den offenen Betrag letztmalig fristgerecht."],
        "inkassouebergabe": [intro, "wir kündigen die Übergabe des Vorgangs an ein Inkassoverfahren an, sofern kein Zahlungsausgleich erfolgt."],
        "verzugszinsberechnung": [intro, "anbei erhalten Sie die Berechnung der angefallenen Verzugszinsen zum offenen Vorgang."],
        "proformarechnung": [intro, "anbei erhalten Sie die Proformarechnung zu Ihrer weiteren Verwendung."],
        "anzahlungsanforderung": [intro, "anbei erhalten Sie die Anzahlungsanforderung zum vereinbarten Auftrag."],
        "belastungsanzeige": [intro, "anbei erhalten Sie die Belastungsanzeige zum betreffenden Vorgang."],
        "zahlungsavis": [intro, "anbei erhalten Sie das Zahlungsavis zum dokumentierten Zahlungsvorgang."],
        "kontoauszug": [intro, "anbei erhalten Sie den Kontoauszug bzw. die Kontenübersicht zum Vorgang."],
        "zahlungsbestaetigung": [intro, "wir bestätigen hiermit den Eingang bzw. die Ausführung der Zahlung."],
        "reklamation_eingang": [intro, "wir bestätigen den Eingang Ihrer Reklamation und prüfen den Vorgang."],
        "reklamation_antwort": [intro, "wir nehmen Bezug auf Ihre Reklamation und teilen Ihnen unser Prüfergebnis mit."],
        "reklamation": [intro, "hiermit dokumentieren wir eine Reklamation und bitten um Abstimmung der weiteren Bearbeitung."],
        "lieferantenreklamation": [intro, "hiermit zeigen wir gegenüber dem Lieferanten einen festgestellten Mangel bzw. eine Abweichung an."],
        "maengelanzeige": [intro, "hiermit zeigen wir festgestellte Mängel an und bitten um Abstimmung der Nachbesserung."],
        "nachbesserung": [intro, "wir bestätigen die geplanten Nachbesserungsmaßnahmen."],
        "stornobestaetigung": [intro, "wir bestätigen die Stornierung des Vorgangs."],
        "vertragsaenderung": [intro, "wir bestätigen die abgestimmte Vertragsänderung."],
        "vertragsbegleitschreiben": [intro, "anbei erhalten Sie die begleitenden Unterlagen zum Vertrag bzw. zur Vertragsänderung."],
        "fehlende_angaben": [intro, company["base_missing_info_text"]],
        "dokumentenanforderung": [intro, "für die weitere Bearbeitung benötigen wir noch ergänzende Unterlagen."],
        "servicebericht": [intro, "anbei erhalten Sie den Servicebericht zur durchgeführten Leistung."],
        "montagebericht": [intro, "anbei erhalten Sie den Montagebericht zur ausgeführten Arbeit."],
        "wartungsprotokoll": [intro, "anbei erhalten Sie das Wartungsprotokoll zur dokumentierten Leistung."],
        "retourenschein": [intro, "anbei erhalten Sie den Retourenschein für die abgestimmte Rücksendung."],
        "anschreiben": [intro, "anbei erhalten Sie das gewünschte Anschreiben zum Vorgang."],
        "serienbrief": [intro, "anbei erhalten Sie den vorbereiteten Serienbrief."],
        "kuendigung": [intro, "hiermit erklären wir die Kündigung des betreffenden Vertrags- oder Leistungsgegenstands."],
        "empfangsbestaetigung": [intro, "wir bestätigen den Eingang der übermittelten Unterlagen bzw. Lieferung."],
    }

    return templates.get(letter_type, [intro, "für die weitere Bearbeitung stimmen wir die nächsten Schritte gerne mit Ihnen ab."])


def normalize_attachments(raw_attachments: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_attachments, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in cast(list[Any], raw_attachments):
        if isinstance(item, str):
            value = item.strip()
            if value:
                normalized.append({"name": value, "file_name": "", "document_type": "", "required": False, "included": True})
            continue
        if isinstance(item, dict):
            item_dict = cast(dict[str, Any], item)
            name = str(item_dict.get("name") or "").strip()
            if not name:
                continue
            normalized.append(
                {
                    "name": name,
                    "file_name": str(item_dict.get("file_name") or "").strip(),
                    "document_type": str(item_dict.get("document_type") or "").strip(),
                    "required": bool(item_dict.get("required")) if isinstance(item_dict.get("required"), bool) else False,
                    "included": bool(item_dict.get("included")) if isinstance(item_dict.get("included"), bool) else True,
                }
            )
    return normalized


def contains_placeholder(recipient: dict[str, str], company: dict[str, str], data: dict[str, Any]) -> bool:
    fields = [
        recipient.get("company") or "",
        recipient.get("name") or "",
        recipient.get("street") or "",
        recipient.get("city") or "",
        company.get("name") or "",
        company.get("street") or "",
        company.get("city") or "",
        company.get("vat_id") or "",
        str(data.get("subject") or ""),
    ]
    for value in fields:
        for pattern in PLACEHOLDER_PATTERNS:
            if pattern.search(value):
                return True
    return False


def is_email_valid(value: str) -> bool:
    return bool(EMAIL_RE.match(value))
