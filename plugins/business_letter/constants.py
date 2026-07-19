from __future__ import annotations

import re
from decimal import Decimal

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PLACEHOLDER_PATTERNS = [
    re.compile(r"(?i)musterstra(?:s|ß)e"),
    re.compile(r"(?i)max\s+mustermann"),
    re.compile(r"(?i)DE123456789"),
]

MONEY_QUANT = Decimal("0.01")
QUANTITY_QUANT = Decimal("0.001")
SUPPORTED_DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y")

COMMUNICATION_DOCUMENT_TYPES = {
    "allgemein",
    "anfrage",
    "angebotsanfrage",
    "angebotserinnerung",
    "angebotsstornierung",
    "bestellbestaetigung",
    "auftragsaenderung",
    "auftragsstornierung",
    "terminbestaetigung",
    "terminverschiebung",
    "lieferankuendigung",
    "versandanzeige",
    "fertigstellungsanzeige",
    "abnahme",
    "abnahmeprotokoll",
    "rechnung_begleitschreiben",
    "zahlungserinnerung",
    "mahnung_1",
    "mahnung_2",
    "mahnung_3",
    "inkassouebergabe",
    "verzugszinsberechnung",
    "reklamation_eingang",
    "reklamation_antwort",
    "reklamation",
    "maengelanzeige",
    "nachbesserung",
    "stornobestaetigung",
    "vertragsaenderung",
    "vertragsbegleitschreiben",
    "fehlende_angaben",
    "dokumentenanforderung",
    "zahlungsavis",
    "kontoauszug",
    "zahlungsbestaetigung",
    "servicebericht",
    "montagebericht",
    "wartungsprotokoll",
    "retourenschein",
    "lieferantenreklamation",
    "anschreiben",
    "serienbrief",
    "kuendigung",
    "empfangsbestaetigung",
}

COMMERCIAL_DOCUMENT_TYPES = {
    "angebot",
    "angebot_treppe",
    "preisangebot",
    "angebotsaenderung",
    "auftragsbestaetigung",
    "kostenvoranschlag",
    "lieferschein",
    "teillieferschein",
    "sammellieferschein",
    "abschlagsrechnung",
    "anzahlungsanforderung",
    "schlussrechnung",
    "rechnung",
    "proformarechnung",
    "gutschrift",
    "stornorechnung",
    "belastungsanzeige",
    "bestellung",
    "bestellaenderung",
    "bestellstornierung",
    "wareneingang",
}

TEMPLATE_MODES = {"auto", "brief", "email", "both", "document"}
