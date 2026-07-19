import type { FrontendFieldKey } from "../documentTypeConfig";

export type TextSectionValue = {
  introText: string;
  closingText: string;
  serviceDescription: string;
  siteLocation: string;
  technician: string;
  acceptanceResult: string;
  defectList: string;
  responseDeadline: string;
  desiredResolution: string;
};

type TextSectionProps = {
  value: TextSectionValue;
  visibleFields: FrontendFieldKey[];
  onChange: (field: keyof TextSectionValue, value: string) => void;
};

function isVisible(fieldKey: FrontendFieldKey, visibleFields: FrontendFieldKey[]): boolean {
  return visibleFields.includes(fieldKey);
}

export function TextSection({ value, visibleFields, onChange }: TextSectionProps) {
  return (
    <section className="bl-card">
      <div className="bl-section-heading">
        <span>5</span>
        <div>
          <h2>Texte</h2>
          <p>Einleitung, Abschluss und typbezogene Zusatzfelder.</p>
        </div>
      </div>
      <div className="bl-grid">
        <label>
          Einleitung
          <textarea rows={4} value={value.introText} onChange={(event) => onChange("introText", event.target.value)} />
        </label>
        <label>
          Abschlusstext
          <textarea rows={4} value={value.closingText} onChange={(event) => onChange("closingText", event.target.value)} />
        </label>
        {isVisible("serviceDescription", visibleFields) ? <label>
          Leistungs- / Fehlerbeschreibung
          <textarea rows={4} value={value.serviceDescription} onChange={(event) => onChange("serviceDescription", event.target.value)} />
        </label> : null}
        {isVisible("siteLocation", visibleFields) ? <label>
          Baustelle / Einsatzort
          <input value={value.siteLocation} onChange={(event) => onChange("siteLocation", event.target.value)} />
        </label> : null}
        {isVisible("technician", visibleFields) ? <label>
          Monteur / Mitarbeiter
          <input value={value.technician} onChange={(event) => onChange("technician", event.target.value)} />
        </label> : null}
        {isVisible("acceptanceResult", visibleFields) ? <label>
          Abnahmeergebnis
          <input value={value.acceptanceResult} onChange={(event) => onChange("acceptanceResult", event.target.value)} placeholder="z. B. freigegeben / mit Maengeln" />
        </label> : null}
        {isVisible("defectList", visibleFields) ? <label>
          Mängelliste
          <textarea rows={3} value={value.defectList} onChange={(event) => onChange("defectList", event.target.value)} />
        </label> : null}
        {isVisible("responseDeadline", visibleFields) ? <label>
          Neue Frist / Rückmeldung bis
          <input type="date" value={value.responseDeadline} onChange={(event) => onChange("responseDeadline", event.target.value)} />
        </label> : null}
        {isVisible("desiredResolution", visibleFields) ? <label>
          Gewünschte Lösung
          <textarea rows={3} value={value.desiredResolution} onChange={(event) => onChange("desiredResolution", event.target.value)} />
        </label> : null}
      </div>
    </section>
  );
}
