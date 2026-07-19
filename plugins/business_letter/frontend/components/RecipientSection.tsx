export type RecipientValue = {
  name: string;
  street: string;
  postalCode: string;
  city: string;
  email: string;
};

type RecipientSectionProps = {
  value: RecipientValue;
  onChange: (field: keyof RecipientValue, value: string) => void;
};

export function RecipientSection({ value, onChange }: RecipientSectionProps) {
  return (
    <section className="bl-card">
      <div className="bl-section-heading">
        <span>3</span>
        <div>
          <h2>Empfänger</h2>
          <p>Kundendaten für das Dokument.</p>
        </div>
      </div>
      <div className="bl-grid bl-grid-2">
        <label className="bl-span-2">
          Name / Firma
          <input value={value.name} onChange={(event) => onChange("name", event.target.value)} />
        </label>
        <label className="bl-span-2">
          Straße
          <input value={value.street} onChange={(event) => onChange("street", event.target.value)} />
        </label>
        <label>
          PLZ
          <input value={value.postalCode} onChange={(event) => onChange("postalCode", event.target.value)} />
        </label>
        <label>
          Ort
          <input value={value.city} onChange={(event) => onChange("city", event.target.value)} />
        </label>
        <label className="bl-span-2">
          E-Mail
          <input type="email" value={value.email} onChange={(event) => onChange("email", event.target.value)} />
        </label>
      </div>
    </section>
  );
}
