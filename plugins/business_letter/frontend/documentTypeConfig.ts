export type DocumentKind =
  | "anfrage"
  | "angebotsanfrage"
  | "angebot"
  | "preisangebot"
  | "angebotsaenderung"
  | "angebotsstornierung"
  | "bestellbestaetigung"
  | "auftragsbestaetigung"
  | "auftragsaenderung"
  | "auftragsstornierung"
  | "lieferschein"
  | "teillieferschein"
  | "sammellieferschein"
  | "versandanzeige"
  | "proformarechnung"
  | "anzahlungsanforderung"
  | "rechnung"
  | "abschlagsrechnung"
  | "schlussrechnung"
  | "gutschrift"
  | "stornorechnung"
  | "belastungsanzeige"
  | "zahlungsavis"
  | "kontoauszug"
  | "zahlungsbestaetigung"
  | "zahlungserinnerung"
  | "mahnung_1"
  | "mahnung_2"
  | "mahnung_3"
  | "inkassouebergabe"
  | "verzugszinsberechnung"
  | "bestellung"
  | "bestellaenderung"
  | "bestellstornierung"
  | "wareneingang"
  | "lieferantenreklamation"
  | "kostenvoranschlag"
  | "servicebericht"
  | "montagebericht"
  | "abnahmeprotokoll"
  | "wartungsprotokoll"
  | "reklamation"
  | "retourenschein"
  | "anschreiben"
  | "serienbrief"
  | "vertragsbegleitschreiben"
  | "kuendigung"
  | "empfangsbestaetigung";

export type FrontendFieldKey =
  | "subject"
  | "buyerReference"
  | "paymentReference"
  | "offerValidUntil"
  | "deliveryDate"
  | "dueDate"
  | "invoiceNumber"
  | "invoiceDate"
  | "invoiceAmount"
  | "originalInvoiceNumber"
  | "orderNumber"
  | "projectReference"
  | "serviceDescription"
  | "siteLocation"
  | "technician"
  | "acceptanceResult"
  | "defectList"
  | "responseDeadline"
  | "desiredResolution";

export type DocumentTypeConfig = {
  label: string;
  category: string;
  hint: string;
  requiresPositions: boolean;
  supportsEInvoice: boolean;
  requiresOfferValidity?: boolean;
  requiresDueDate?: boolean;
  requiresDeliveryDate?: boolean;
  requiresPaymentData?: boolean;
  requiredFields: FrontendFieldKey[];
  visibleFields: FrontendFieldKey[];
  defaultOutput: {
    attachPdf: boolean;
    attachXml: boolean;
    validateBeforeSend: boolean;
    saveDocument: boolean;
  };
};

const DEFAULT_OUTPUT = {
  attachPdf: true,
  attachXml: false,
  validateBeforeSend: true,
  saveDocument: true,
};

export const DOCUMENT_TYPE_CONFIG: Record<DocumentKind, DocumentTypeConfig> = {
  anfrage: {
    label: "Anfrage",
    category: "Vertrieb",
    hint: "Allgemeiner Einstieg ohne Positions- und Rechnungslogik.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiredFields: ["subject"],
    visibleFields: ["subject", "responseDeadline"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  angebotsanfrage: {
    label: "Angebotsanfrage (RFQ)",
    category: "Vertrieb",
    hint: "Angebotsanfrage mit Gültigkeit und Projektbezug.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiresOfferValidity: true,
    requiredFields: ["subject", "offerValidUntil"],
    visibleFields: ["subject", "offerValidUntil", "projectReference", "responseDeadline"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  angebot: {
    label: "Angebot",
    category: "Vertrieb",
    hint: "Klassisches Angebot mit Positionen und Gültigkeit.",
    requiresPositions: true,
    supportsEInvoice: false,
    requiresOfferValidity: true,
    requiredFields: ["subject", "offerValidUntil"],
    visibleFields: ["subject", "offerValidUntil", "projectReference", "buyerReference", "paymentReference"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  preisangebot: {
    label: "Preisangebot (Kurzangebot)",
    category: "Vertrieb",
    hint: "Kompaktes Preisangebot mit Positionen und Gültigkeit.",
    requiresPositions: true,
    supportsEInvoice: false,
    requiresOfferValidity: true,
    requiredFields: ["subject", "offerValidUntil"],
    visibleFields: ["subject", "offerValidUntil", "projectReference"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  angebotsaenderung: {
    label: "Angebotsänderung",
    category: "Vertrieb",
    hint: "Änderung eines vorhandenen Angebots.",
    requiresPositions: true,
    supportsEInvoice: false,
    requiresOfferValidity: true,
    requiredFields: ["subject", "offerValidUntil"],
    visibleFields: ["subject", "offerValidUntil", "projectReference"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  angebotsstornierung: {
    label: "Angebotsstornierung",
    category: "Vertrieb",
    hint: "Storniert ein bestehendes Angebot ohne Positionspflicht.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiredFields: ["subject"],
    visibleFields: ["subject"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  bestellbestaetigung: {
    label: "Bestellbestätigung",
    category: "Auftragsabwicklung",
    hint: "Bestätigt einen Auftrag mit Positionen und Auftragsnummer.",
    requiresPositions: true,
    supportsEInvoice: false,
    requiredFields: ["subject", "orderNumber"],
    visibleFields: ["subject", "orderNumber", "projectReference", "deliveryDate"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  auftragsbestaetigung: {
    label: "Auftragsbestätigung",
    category: "Auftragsabwicklung",
    hint: "Bestätigt den Auftrag verbindlich.",
    requiresPositions: true,
    supportsEInvoice: false,
    requiredFields: ["subject", "orderNumber"],
    visibleFields: ["subject", "orderNumber", "projectReference", "deliveryDate"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  auftragsaenderung: {
    label: "Auftragsänderung",
    category: "Auftragsabwicklung",
    hint: "Änderungsdokument für bestehende Aufträge.",
    requiresPositions: true,
    supportsEInvoice: false,
    requiredFields: ["subject", "orderNumber"],
    visibleFields: ["subject", "orderNumber", "projectReference", "deliveryDate"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  auftragsstornierung: {
    label: "Auftragsstornierung",
    category: "Auftragsabwicklung",
    hint: "Stornierung eines bestehenden Auftrags.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiredFields: ["subject", "orderNumber"],
    visibleFields: ["subject", "orderNumber"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  lieferschein: {
    label: "Lieferschein",
    category: "Auftragsabwicklung",
    hint: "Lieferbeleg mit Positionen und Lieferdatum, ohne E-Rechnung.",
    requiresPositions: true,
    supportsEInvoice: false,
    requiresDeliveryDate: true,
    requiredFields: ["subject", "deliveryDate"],
    visibleFields: ["subject", "deliveryDate", "projectReference", "orderNumber"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  teillieferschein: {
    label: "Teillieferschein",
    category: "Auftragsabwicklung",
    hint: "Lieferschein für Teilmengen mit Lieferdatum.",
    requiresPositions: true,
    supportsEInvoice: false,
    requiresDeliveryDate: true,
    requiredFields: ["subject", "deliveryDate"],
    visibleFields: ["subject", "deliveryDate", "orderNumber", "projectReference"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  sammellieferschein: {
    label: "Sammellieferschein",
    category: "Auftragsabwicklung",
    hint: "Zusammenfassung mehrerer Lieferpositionen.",
    requiresPositions: true,
    supportsEInvoice: false,
    requiresDeliveryDate: true,
    requiredFields: ["subject", "deliveryDate"],
    visibleFields: ["subject", "deliveryDate", "orderNumber"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  versandanzeige: {
    label: "Versandanzeige",
    category: "Auftragsabwicklung",
    hint: "Kommuniziert Versand-/Liefertermin ohne Rechnungslogik.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiresDeliveryDate: true,
    requiredFields: ["subject", "deliveryDate"],
    visibleFields: ["subject", "deliveryDate", "orderNumber"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  proformarechnung: {
    label: "Proformarechnung",
    category: "Rechnungswesen",
    hint: "Proforma mit Positionen, aber ohne E-Rechnungszwang.",
    requiresPositions: true,
    supportsEInvoice: false,
    requiredFields: ["subject"],
    visibleFields: ["subject", "buyerReference", "paymentReference"],
    defaultOutput: { ...DEFAULT_OUTPUT, attachXml: false },
  },
  anzahlungsanforderung: {
    label: "Anzahlungsanforderung",
    category: "Rechnungswesen",
    hint: "Zahlungsanforderung mit Fälligkeit und Positionen.",
    requiresPositions: true,
    supportsEInvoice: false,
    requiresDueDate: true,
    requiresPaymentData: true,
    requiredFields: ["subject", "dueDate"],
    visibleFields: ["subject", "dueDate", "buyerReference", "paymentReference"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  rechnung: {
    label: "Rechnung",
    category: "Rechnungswesen",
    hint: "Faktura mit Zahlungsziel und optionaler E-Rechnung.",
    requiresPositions: true,
    supportsEInvoice: true,
    requiresDueDate: true,
    requiresPaymentData: true,
    requiredFields: ["subject", "dueDate"],
    visibleFields: ["subject", "dueDate", "buyerReference", "paymentReference", "invoiceNumber"],
    defaultOutput: { ...DEFAULT_OUTPUT, attachXml: true },
  },
  abschlagsrechnung: {
    label: "Abschlagsrechnung",
    category: "Rechnungswesen",
    hint: "Teilrechnung mit Zahlungsziel und optionaler E-Rechnung.",
    requiresPositions: true,
    supportsEInvoice: true,
    requiresDueDate: true,
    requiresPaymentData: true,
    requiredFields: ["subject", "dueDate"],
    visibleFields: ["subject", "dueDate", "buyerReference", "paymentReference"],
    defaultOutput: { ...DEFAULT_OUTPUT, attachXml: true },
  },
  schlussrechnung: {
    label: "Schlussrechnung",
    category: "Rechnungswesen",
    hint: "Abschlussrechnung mit Zahlungsziel und optionaler E-Rechnung.",
    requiresPositions: true,
    supportsEInvoice: true,
    requiresDueDate: true,
    requiresPaymentData: true,
    requiredFields: ["subject", "dueDate"],
    visibleFields: ["subject", "dueDate", "buyerReference", "paymentReference"],
    defaultOutput: { ...DEFAULT_OUTPUT, attachXml: true },
  },
  gutschrift: {
    label: "Gutschrift",
    category: "Rechnungswesen",
    hint: "Gutschrift mit E-Rechnungsfähigkeit.",
    requiresPositions: true,
    supportsEInvoice: true,
    requiresDueDate: true,
    requiresPaymentData: true,
    requiredFields: ["subject", "dueDate"],
    visibleFields: ["subject", "dueDate", "originalInvoiceNumber", "paymentReference"],
    defaultOutput: { ...DEFAULT_OUTPUT, attachXml: true },
  },
  stornorechnung: {
    label: "Stornorechnung",
    category: "Rechnungswesen",
    hint: "Erfordert Referenz auf die Ursprungsrechnung.",
    requiresPositions: true,
    supportsEInvoice: true,
    requiresDueDate: true,
    requiresPaymentData: true,
    requiredFields: ["subject", "dueDate", "originalInvoiceNumber"],
    visibleFields: ["subject", "dueDate", "originalInvoiceNumber", "paymentReference"],
    defaultOutput: { ...DEFAULT_OUTPUT, attachXml: true },
  },
  belastungsanzeige: {
    label: "Belastungsanzeige",
    category: "Rechnungswesen",
    hint: "Finanzielle Nachbelastung mit Positionen und Zahlungsziel.",
    requiresPositions: true,
    supportsEInvoice: false,
    requiresDueDate: true,
    requiresPaymentData: true,
    requiredFields: ["subject", "dueDate"],
    visibleFields: ["subject", "dueDate", "paymentReference"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  zahlungsavis: {
    label: "Zahlungsavis",
    category: "Rechnungswesen",
    hint: "Kommuniziert Zahlungszuordnung ohne Positionen.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiresPaymentData: true,
    requiredFields: ["subject", "paymentReference"],
    visibleFields: ["subject", "paymentReference"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  kontoauszug: {
    label: "Kontoauszug",
    category: "Rechnungswesen",
    hint: "Finanzübersicht ohne Rechnungs-/Positionspflicht.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiredFields: ["subject"],
    visibleFields: ["subject"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  zahlungsbestaetigung: {
    label: "Zahlungsbestätigung",
    category: "Rechnungswesen",
    hint: "Bestätigt einen Zahlungseingang oder eine Zahlungsausführung.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiresPaymentData: true,
    requiredFields: ["subject", "paymentReference"],
    visibleFields: ["subject", "paymentReference"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  zahlungserinnerung: {
    label: "Zahlungserinnerung",
    category: "Mahnwesen",
    hint: "Vorstufe zur Mahnung mit Rechnungs- und Fälligkeitsbezug.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiresDueDate: true,
    requiredFields: ["subject", "invoiceNumber", "invoiceDate", "invoiceAmount", "dueDate"],
    visibleFields: ["subject", "invoiceNumber", "invoiceDate", "invoiceAmount", "dueDate", "responseDeadline", "paymentReference"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  mahnung_1: {
    label: "1. Mahnung",
    category: "Mahnwesen",
    hint: "Erste Mahnstufe mit Zahlungsfrist.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiresDueDate: true,
    requiredFields: ["subject", "invoiceNumber", "invoiceDate", "invoiceAmount", "dueDate"],
    visibleFields: ["subject", "invoiceNumber", "invoiceDate", "invoiceAmount", "dueDate", "responseDeadline", "paymentReference"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  mahnung_2: {
    label: "2. Mahnung",
    category: "Mahnwesen",
    hint: "Zweite Mahnung mit neuer Frist und Mahngebühr.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiresDueDate: true,
    requiredFields: ["subject", "invoiceNumber", "invoiceDate", "invoiceAmount", "dueDate", "responseDeadline"],
    visibleFields: ["subject", "invoiceNumber", "invoiceDate", "invoiceAmount", "dueDate", "responseDeadline", "paymentReference"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  mahnung_3: {
    label: "3. Mahnung / Letzte Mahnung",
    category: "Mahnwesen",
    hint: "Letzte Mahnstufe vor Eskalation.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiresDueDate: true,
    requiredFields: ["subject", "invoiceNumber", "invoiceDate", "invoiceAmount", "dueDate", "responseDeadline"],
    visibleFields: ["subject", "invoiceNumber", "invoiceDate", "invoiceAmount", "dueDate", "responseDeadline", "paymentReference"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  inkassouebergabe: {
    label: "Inkassoübergabe",
    category: "Mahnwesen",
    hint: "Übergabehinweis mit offener Rechnung und Fristdaten.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiresDueDate: true,
    requiredFields: ["subject", "invoiceNumber", "invoiceDate", "invoiceAmount", "dueDate"],
    visibleFields: ["subject", "invoiceNumber", "invoiceDate", "invoiceAmount", "dueDate", "responseDeadline"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  verzugszinsberechnung: {
    label: "Verzugszinsberechnung",
    category: "Mahnwesen",
    hint: "Dokumentiert Verzugszinsen zum offenen Vorgang.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiresDueDate: true,
    requiredFields: ["subject", "invoiceNumber", "invoiceDate", "invoiceAmount", "dueDate"],
    visibleFields: ["subject", "invoiceNumber", "invoiceDate", "invoiceAmount", "dueDate", "responseDeadline"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  bestellung: {
    label: "Bestellung",
    category: "Einkauf",
    hint: "Beschaffungsvorgang mit Positionen und Lieferdaten.",
    requiresPositions: true,
    supportsEInvoice: false,
    requiresDeliveryDate: true,
    requiredFields: ["subject", "deliveryDate"],
    visibleFields: ["subject", "deliveryDate", "orderNumber"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  bestellaenderung: {
    label: "Bestelländerung",
    category: "Einkauf",
    hint: "Ändert eine bestehende Bestellung.",
    requiresPositions: true,
    supportsEInvoice: false,
    requiresDeliveryDate: true,
    requiredFields: ["subject", "deliveryDate", "orderNumber"],
    visibleFields: ["subject", "deliveryDate", "orderNumber"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  bestellstornierung: {
    label: "Bestellstornierung",
    category: "Einkauf",
    hint: "Storniert eine bestehende Bestellung.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiredFields: ["subject", "orderNumber"],
    visibleFields: ["subject", "orderNumber"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  wareneingang: {
    label: "Wareneingang",
    category: "Einkauf",
    hint: "Erfasst eingegangene Ware mit Positionen und Datum.",
    requiresPositions: true,
    supportsEInvoice: false,
    requiresDeliveryDate: true,
    requiredFields: ["subject", "deliveryDate"],
    visibleFields: ["subject", "deliveryDate", "orderNumber"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  lieferantenreklamation: {
    label: "Lieferantenreklamation",
    category: "Einkauf",
    hint: "Reklamation gegenüber dem Lieferanten mit Fehlerbeschreibung.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiredFields: ["subject", "serviceDescription", "desiredResolution"],
    visibleFields: ["subject", "serviceDescription", "desiredResolution", "orderNumber"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  kostenvoranschlag: {
    label: "Kostenvoranschlag",
    category: "Service",
    hint: "Service-/Projektangebot mit Positionen und Gültigkeit, aber ohne Zahlungsfälligkeit.",
    requiresPositions: true,
    supportsEInvoice: false,
    requiresOfferValidity: true,
    requiredFields: ["subject", "offerValidUntil"],
    visibleFields: ["subject", "offerValidUntil", "projectReference", "siteLocation"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  servicebericht: {
    label: "Servicebericht",
    category: "Service",
    hint: "Bericht über ausgeführte Servicearbeiten.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiresDeliveryDate: true,
    requiredFields: ["subject", "deliveryDate", "serviceDescription", "technician", "siteLocation"],
    visibleFields: ["subject", "deliveryDate", "serviceDescription", "technician", "siteLocation"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  montagebericht: {
    label: "Montagebericht",
    category: "Service",
    hint: "Montagedokumentation mit Mitarbeiter, Datum und Baustelle.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiresDeliveryDate: true,
    requiredFields: ["subject", "deliveryDate", "serviceDescription", "technician", "siteLocation"],
    visibleFields: ["subject", "deliveryDate", "serviceDescription", "technician", "siteLocation"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  abnahmeprotokoll: {
    label: "Abnahmeprotokoll",
    category: "Service",
    hint: "Abnahme mit Ergebnis, Mängeln und Beteiligten.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiresDeliveryDate: true,
    requiredFields: ["subject", "deliveryDate", "acceptanceResult", "defectList"],
    visibleFields: ["subject", "deliveryDate", "acceptanceResult", "defectList", "siteLocation"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  wartungsprotokoll: {
    label: "Wartungsprotokoll",
    category: "Service",
    hint: "Protokolliert Wartungsarbeiten mit Datum und Beschreibung.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiresDeliveryDate: true,
    requiredFields: ["subject", "deliveryDate", "serviceDescription", "technician"],
    visibleFields: ["subject", "deliveryDate", "serviceDescription", "technician", "siteLocation"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  reklamation: {
    label: "Reklamation",
    category: "Service",
    hint: "Reklamationsdokument mit Fehlerbeschreibung und gewünschter Lösung.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiredFields: ["subject", "serviceDescription", "desiredResolution"],
    visibleFields: ["subject", "serviceDescription", "desiredResolution", "siteLocation"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  retourenschein: {
    label: "Retourenschein",
    category: "Service",
    hint: "Retourendokument mit Rücksendedatum und Artikelbezug.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiresDeliveryDate: true,
    requiredFields: ["subject", "deliveryDate"],
    visibleFields: ["subject", "deliveryDate", "serviceDescription"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  anschreiben: {
    label: "Anschreiben",
    category: "Allgemein",
    hint: "Freies Anschreiben ohne zusätzliche Fachlogik.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiredFields: ["subject"],
    visibleFields: ["subject", "serviceDescription"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  serienbrief: {
    label: "Serienbrief",
    category: "Allgemein",
    hint: "Mehrfachanschreiben mit Standardtexten.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiredFields: ["subject", "serviceDescription"],
    visibleFields: ["subject", "serviceDescription"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  vertragsbegleitschreiben: {
    label: "Vertragsbegleitschreiben",
    category: "Allgemein",
    hint: "Begleitschreiben für Vertragsunterlagen.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiredFields: ["subject", "serviceDescription"],
    visibleFields: ["subject", "serviceDescription"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  kuendigung: {
    label: "Kündigung",
    category: "Allgemein",
    hint: "Kündigungsschreiben mit Begründung/Inhalt.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiredFields: ["subject", "serviceDescription"],
    visibleFields: ["subject", "serviceDescription", "responseDeadline"],
    defaultOutput: DEFAULT_OUTPUT,
  },
  empfangsbestaetigung: {
    label: "Empfangsbestätigung",
    category: "Allgemein",
    hint: "Bestätigt den Eingang von Unterlagen oder Lieferungen.",
    requiresPositions: false,
    supportsEInvoice: false,
    requiredFields: ["subject"],
    visibleFields: ["subject", "deliveryDate"],
    defaultOutput: DEFAULT_OUTPUT,
  },
};

export const DOCUMENT_KIND_ORDER: DocumentKind[] = Object.keys(DOCUMENT_TYPE_CONFIG) as DocumentKind[];