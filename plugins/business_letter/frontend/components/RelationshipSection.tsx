const money = new Intl.NumberFormat("de-DE", {
  style: "currency",
  currency: "EUR",
});

export type RelationshipConversionOption = {
  value: string;
  label: string;
  sourceKind?: string;
  targetKind?: string;
};

export type RelationshipReferencePosition = {
  lineId: string;
  name: string;
  description: string;
  quantity: number;
  unitCode: string;
  priceNet: number;
};

export type RelationshipReferenceDocument = {
  id: string;
  number: string;
  kind: string;
  subject: string;
  projectId: string;
  customerId: string;
  customerName: string;
  totalAmount: string;
  positions: RelationshipReferencePosition[];
};

export type RelationshipProjectCase = {
  statusView: {
    documentCount: number;
    statuses: Record<string, number>;
  };
  timeline: Array<{
    documentId: string;
    documentNumber: string;
    documentKind: string;
    status: string;
    createdAt: string;
    payableAmount: string;
  }>;
  quantityChain: {
    followUpDocuments: number;
    lines: Array<{
      lineId: string;
      name: string;
      deliveredQuantity: string;
      invoicedQuantity: string;
      openQuantity: string;
    }>;
    totals: {
      deliveredQuantity: string;
      invoicedQuantity: string;
      openQuantity: string;
    };
  };
};

export type RelationshipFields = {
  sourceDocumentId: string;
  sourceDocumentNumber: string;
  sourceDocumentKind: string;
  projectId: string;
  customerId: string;
  revisionOf: string;
  cancelsDocumentId: string;
};

type RelationshipFieldKey = keyof RelationshipFields;

type RelationshipSectionProps = {
  conversionOptions: RelationshipConversionOption[];
  conversionAction: string;
  selectedReferenceId: string;
  referenceDocuments: RelationshipReferenceDocument[];
  selectedReference: RelationshipReferenceDocument | null;
  selectedSourceLineIds: string[];
  sourcePositionQuantities: Record<string, string>;
  projectCase: RelationshipProjectCase | null;
  projectCaseLoading: boolean;
  fields: RelationshipFields;
  onConversionActionChange: (value: string) => void;
  onSelectedReferenceChange: (value: string) => void;
  onApplyReferenceSelection: () => void;
  onLoadProjectCaseOverview: () => void;
  onToggleSourceLineSelection: (lineId: string, checked: boolean) => void;
  onUpdateSourceQuantity: (lineId: string, value: string) => void;
  onRelationshipFieldChange: (field: RelationshipFieldKey, value: string) => void;
};

export function RelationshipSection({
  conversionOptions,
  conversionAction,
  selectedReferenceId,
  referenceDocuments,
  selectedReference,
  selectedSourceLineIds,
  sourcePositionQuantities,
  projectCase,
  projectCaseLoading,
  fields,
  onConversionActionChange,
  onSelectedReferenceChange,
  onApplyReferenceSelection,
  onLoadProjectCaseOverview,
  onToggleSourceLineSelection,
  onUpdateSourceQuantity,
  onRelationshipFieldChange,
}: RelationshipSectionProps) {
  return (
    <section className="bl-card">
      <div className="bl-section-heading">
        <span>2</span>
        <div>
          <h2>Beziehungen & Konvertierung</h2>
          <p>Folgedokumente, Projekt- und Kundenbezug sowie Storno-/Revisionsketten festhalten.</p>
        </div>
      </div>
      <div className="bl-grid bl-grid-2">
        {conversionOptions.length > 0 ? (
          <label className="bl-span-2">
            Konvertierungsaktion
            <select value={conversionAction} onChange={(event) => onConversionActionChange(event.target.value)}>
              <option value="">Keine</option>
              {conversionOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        <label className="bl-span-2">
          Referenzdokument auswählen
          <select value={selectedReferenceId} onChange={(event) => onSelectedReferenceChange(event.target.value)}>
            <option value="">Kein gespeichertes Referenzdokument</option>
            {referenceDocuments.map((entry) => (
              <option key={entry.id} value={entry.id}>
                {entry.number || entry.id} · {entry.kind || "unbekannt"} · {entry.subject || "ohne Betreff"}
              </option>
            ))}
          </select>
        </label>
        {selectedReference ? (
          <>
            <div className="bl-reference-panel bl-span-2">
              <div className="bl-reference-panel__header">
                <strong>Referenzdaten (schreibgeschützt)</strong>
                <div className="bl-reference-actions">
                  <button type="button" className="bl-button bl-button-secondary" onClick={onApplyReferenceSelection}>
                    Folgedokument erstellen
                  </button>
                  <button type="button" className="bl-button bl-button-secondary" onClick={onLoadProjectCaseOverview} disabled={projectCaseLoading}>
                    {projectCaseLoading ? "Projektakte lädt ..." : "Projektakte laden"}
                  </button>
                </div>
              </div>
              <dl>
                <div><dt>Dokumentnummer</dt><dd>{selectedReference.number || "-"}</dd></div>
                <div><dt>Dokumenttyp</dt><dd>{selectedReference.kind || "-"}</dd></div>
                <div><dt>Kunde</dt><dd>{selectedReference.customerName || "-"}</dd></div>
                <div><dt>Projekt-ID</dt><dd>{selectedReference.projectId || "-"}</dd></div>
                <div><dt>Kunden-ID</dt><dd>{selectedReference.customerId || "-"}</dd></div>
                <div><dt>Betrag</dt><dd>{selectedReference.totalAmount || "-"}</dd></div>
              </dl>
            </div>
            {selectedReference.positions.length > 0 ? (
              <div className="bl-reference-positions bl-span-2">
                <strong>Übernommene Positionen (mit gezielter Abwahl und Teilmengen)</strong>
                {selectedReference.positions.map((position) => {
                  const selected = selectedSourceLineIds.includes(position.lineId);
                  return (
                    <div className="bl-reference-position" key={position.lineId}>
                      <label className="bl-reference-position__toggle">
                        <input
                          type="checkbox"
                          checked={selected}
                          onChange={(event) => onToggleSourceLineSelection(position.lineId, event.target.checked)}
                        />
                        <span>{position.lineId} · {position.description || position.name}</span>
                      </label>
                      <div className="bl-reference-position__meta">
                        <span>Quelle: {position.quantity} {position.unitCode} · {money.format(position.priceNet)}</span>
                        <label>
                          Übernahme-Menge
                          <input
                            type="number"
                            min="0"
                            step="0.001"
                            value={sourcePositionQuantities[position.lineId] || String(position.quantity)}
                            onChange={(event) => onUpdateSourceQuantity(position.lineId, event.target.value)}
                            disabled={!selected}
                          />
                        </label>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : null}
            {projectCase ? (
              <div className="bl-chain-panel bl-span-2">
                <div className="bl-chain-panel__header">
                  <strong>Teilmengen-/Restmengen-Kette</strong>
                  <span>Folgebelege: {projectCase.quantityChain.followUpDocuments}</span>
                </div>
                {projectCase.quantityChain.lines.length > 0 ? (
                  <div className="bl-chain-table">
                    <div className="bl-chain-row bl-chain-row-head">
                      <span>Position</span>
                      <span>Geliefert</span>
                      <span>Fakturiert</span>
                      <span>Offen</span>
                    </div>
                    {projectCase.quantityChain.lines.map((line) => (
                      <div className="bl-chain-row" key={line.lineId}>
                        <span>{line.lineId} · {line.name || "Position"}</span>
                        <span>{line.deliveredQuantity}</span>
                        <span>{line.invoicedQuantity}</span>
                        <span>{line.openQuantity}</span>
                      </div>
                    ))}
                    <div className="bl-chain-row bl-chain-row-total">
                      <span>Gesamt</span>
                      <span>{projectCase.quantityChain.totals.deliveredQuantity}</span>
                      <span>{projectCase.quantityChain.totals.invoicedQuantity}</span>
                      <span>{projectCase.quantityChain.totals.openQuantity}</span>
                    </div>
                  </div>
                ) : (
                  <p>Keine Positionskette vorhanden.</p>
                )}
              </div>
            ) : null}
          </>
        ) : null}
        <label>
          Quelldokument-ID
          <input value={fields.sourceDocumentId} onChange={(event) => onRelationshipFieldChange("sourceDocumentId", event.target.value)} />
        </label>
        <label>
          Quelldokument-Nummer
          <input value={fields.sourceDocumentNumber} onChange={(event) => onRelationshipFieldChange("sourceDocumentNumber", event.target.value)} />
        </label>
        <label>
          Quelldokument-Typ
          <input value={fields.sourceDocumentKind} onChange={(event) => onRelationshipFieldChange("sourceDocumentKind", event.target.value)} />
        </label>
        <label>
          Projekt-ID
          <input value={fields.projectId} onChange={(event) => onRelationshipFieldChange("projectId", event.target.value)} />
        </label>
        <label>
          Kunden-ID
          <input value={fields.customerId} onChange={(event) => onRelationshipFieldChange("customerId", event.target.value)} />
        </label>
        <label>
          Revision von
          <input value={fields.revisionOf} onChange={(event) => onRelationshipFieldChange("revisionOf", event.target.value)} />
        </label>
        <label>
          Storniert Dokument-ID
          <input value={fields.cancelsDocumentId} onChange={(event) => onRelationshipFieldChange("cancelsDocumentId", event.target.value)} />
        </label>
      </div>
      {projectCase ? (
        <div className="bl-timeline-panel">
          <div className="bl-timeline-panel__header">
            <strong>Projektakte / Timeline</strong>
            <span>{projectCase.statusView.documentCount} Dokumente</span>
          </div>
          <div className="bl-status-chips">
            {Object.entries(projectCase.statusView.statuses).map(([statusKey, count]) => (
              <span key={statusKey} className="bl-status-chip">{statusKey}: {count}</span>
            ))}
          </div>
          {projectCase.timeline.length > 0 ? (
            <div className="bl-timeline-list">
              {projectCase.timeline.map((entry) => (
                <div key={entry.documentId || `${entry.documentNumber}-${entry.createdAt}`} className="bl-timeline-item">
                  <div>
                    <strong>{entry.documentNumber || entry.documentId || "-"}</strong>
                    <span>{entry.documentKind || "unbekannt"} · {entry.status || "-"}</span>
                  </div>
                  <div>
                    <span>{entry.createdAt || ""}</span>
                    <span>{entry.payableAmount ? `${entry.payableAmount} EUR` : ""}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p>Für die Projektakte wurden noch keine Dokumente gefunden.</p>
          )}
        </div>
      ) : null}
    </section>
  );
}
