import {
  DOCUMENT_KIND_ORDER,
  DOCUMENT_TYPE_CONFIG,
  type DocumentKind,
  type FrontendFieldKey,
} from "../documentTypeConfig";

export type DocumentSectionValue = {
  documentKind: DocumentKind;
  subject: string;
  buyerReference: string;
  paymentReference: string;
  offerValidUntil: string;
  deliveryDate: string;
  dueDate: string;
  invoiceNumber: string;
  invoiceDate: string;
  invoiceAmount: string;
  originalInvoiceNumber: string;
  orderNumber: string;
  projectReference: string;
};

type DocumentSectionProps = {
  value: DocumentSectionValue;
  visibleFields: FrontendFieldKey[];
  hint: string;
  onDocumentKindChange: (value: DocumentKind) => void;
  onChange: (field: Exclude<keyof DocumentSectionValue, "documentKind">, value: string) => void;
};

function isVisible(fieldKey: FrontendFieldKey, visibleFields: FrontendFieldKey[]): boolean {
  return visibleFields.includes(fieldKey);
}

export function DocumentSection({ value, visibleFields, hint, onDocumentKindChange, onChange }: DocumentSectionProps) {
  return (
    <section className="bl-card">
      <div className="bl-section-heading">
        <span>1</span>
        <div>
          <h2>Dokument</h2>
          <p>Art und Grunddaten festlegen.</p>
        </div>
      </div>
      <div className="bl-grid bl-grid-2">
        <label>
          Dokumenttyp
          <select value={value.documentKind} onChange={(event) => onDocumentKindChange(event.target.value as DocumentKind)}>
            {DOCUMENT_KIND_ORDER.map((entry) => (
              <option key={entry} value={entry}>
                {DOCUMENT_TYPE_CONFIG[entry].label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Betreff
          <input value={value.subject} onChange={(event) => onChange("subject", event.target.value)} placeholder="z. B. Angebot Natursteinarbeiten" />
        </label>
        {isVisible("buyerReference", visibleFields) ? <label>
          Käuferreferenz
          <input value={value.buyerReference} onChange={(event) => onChange("buyerReference", event.target.value)} placeholder="optional" />
        </label> : null}
        {isVisible("paymentReference", visibleFields) ? <label>
          Zahlungsreferenz
          <input value={value.paymentReference} onChange={(event) => onChange("paymentReference", event.target.value)} placeholder="optional" />
        </label> : null}
        {isVisible("offerValidUntil", visibleFields) ? <label>
          Angebotsgültigkeit
          <input type="date" value={value.offerValidUntil} onChange={(event) => onChange("offerValidUntil", event.target.value)} />
        </label> : null}
        {isVisible("deliveryDate", visibleFields) ? <label>
          Liefer- / Leistungsdatum
          <input type="date" value={value.deliveryDate} onChange={(event) => onChange("deliveryDate", event.target.value)} />
        </label> : null}
        {isVisible("dueDate", visibleFields) ? <label>
          Fälligkeitsdatum
          <input type="date" value={value.dueDate} onChange={(event) => onChange("dueDate", event.target.value)} />
        </label> : null}
        {isVisible("invoiceNumber", visibleFields) ? <label>
          Rechnungsnummer
          <input value={value.invoiceNumber} onChange={(event) => onChange("invoiceNumber", event.target.value)} />
        </label> : null}
        {isVisible("invoiceDate", visibleFields) ? <label>
          Rechnungsdatum
          <input type="date" value={value.invoiceDate} onChange={(event) => onChange("invoiceDate", event.target.value)} />
        </label> : null}
        {isVisible("invoiceAmount", visibleFields) ? <label>
          Rechnungsbetrag
          <input value={value.invoiceAmount} onChange={(event) => onChange("invoiceAmount", event.target.value)} />
        </label> : null}
        {isVisible("originalInvoiceNumber", visibleFields) ? <label>
          Ursprungsrechnung
          <input value={value.originalInvoiceNumber} onChange={(event) => onChange("originalInvoiceNumber", event.target.value)} />
        </label> : null}
        {isVisible("orderNumber", visibleFields) ? <label>
          Auftragsnummer
          <input value={value.orderNumber} onChange={(event) => onChange("orderNumber", event.target.value)} />
        </label> : null}
        {isVisible("projectReference", visibleFields) ? <label>
          Projektreferenz
          <input value={value.projectReference} onChange={(event) => onChange("projectReference", event.target.value)} />
        </label> : null}
        <div className="bl-span-2 bl-info-box" role="note" aria-label="Dokumenthinweis">
          {hint}
        </div>
      </div>
    </section>
  );
}
