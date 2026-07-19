export type PositionSectionPosition = {
  id: string;
  description: string;
  quantity: number;
  unit: string;
  unitPrice: number;
  taxRate: number;
  stoneDetails: {
    materialType: string;
    tradeName: string;
    origin: string;
    color: string;
    surfaceFinish: string;
    thicknessMm: string;
    lengthMm: string;
    widthMm: string;
    edgeProfile: string;
    batch: string;
    blockNumber: string;
    measurementNumber: string;
    installationLocation: string;
  };
};

type PositionField = "description" | "quantity" | "unit" | "unitPrice" | "taxRate";
type StoneField = keyof PositionSectionPosition["stoneDetails"];

type PositionSectionProps = {
  positions: PositionSectionPosition[];
  onAddPosition: () => void;
  onUpdatePosition: (id: string, key: PositionField, value: string | number) => void;
  onUpdateStoneDetail: (id: string, key: StoneField, value: string) => void;
  onRemovePosition: (id: string) => void;
};

export function PositionSection({
  positions,
  onAddPosition,
  onUpdatePosition,
  onUpdateStoneDetail,
  onRemovePosition,
}: PositionSectionProps) {
  return (
    <section className="bl-card">
      <div className="bl-section-heading bl-section-heading-actions">
        <div className="bl-section-heading-copy">
          <span>4</span>
          <div>
            <h2>Positionen</h2>
            <p>Leistungen und Materialien erfassen.</p>
          </div>
        </div>
        <button type="button" className="bl-button bl-button-secondary" onClick={onAddPosition}>
          + Position
        </button>
      </div>
      <div className="bl-positions">
        {positions.map((position, index) => (
          <div className="bl-position" key={position.id}>
            <div className="bl-position-number">{index + 1}</div>
            <label className="bl-position-description">
              Beschreibung
              <input
                value={position.description}
                onChange={(event) => onUpdatePosition(position.id, "description", event.target.value)}
                placeholder="Material oder Leistung"
              />
            </label>
            <label>
              Menge
              <input
                type="number"
                min="0"
                step="0.01"
                value={position.quantity}
                onChange={(event) => onUpdatePosition(position.id, "quantity", Number(event.target.value))}
              />
            </label>
            <label>
              Einheit
              <input value={position.unit} onChange={(event) => onUpdatePosition(position.id, "unit", event.target.value)} />
            </label>
            <label>
              Einzelpreis
              <input
                type="number"
                min="0"
                step="0.01"
                value={position.unitPrice}
                onChange={(event) => onUpdatePosition(position.id, "unitPrice", Number(event.target.value))}
              />
            </label>
            <label>
              Steuer %
              <input
                type="number"
                min="0"
                step="0.01"
                value={position.taxRate}
                onChange={(event) => onUpdatePosition(position.id, "taxRate", Number(event.target.value))}
              />
            </label>
            <div className="bl-position-stone-grid">
              <label>
                Materialart
                <input value={position.stoneDetails.materialType} onChange={(event) => onUpdateStoneDetail(position.id, "materialType", event.target.value)} />
              </label>
              <label>
                Handelsname
                <input value={position.stoneDetails.tradeName} onChange={(event) => onUpdateStoneDetail(position.id, "tradeName", event.target.value)} />
              </label>
              <label>
                Herkunft
                <input value={position.stoneDetails.origin} onChange={(event) => onUpdateStoneDetail(position.id, "origin", event.target.value)} />
              </label>
              <label>
                Farbe
                <input value={position.stoneDetails.color} onChange={(event) => onUpdateStoneDetail(position.id, "color", event.target.value)} />
              </label>
              <label>
                Oberfläche
                <input value={position.stoneDetails.surfaceFinish} onChange={(event) => onUpdateStoneDetail(position.id, "surfaceFinish", event.target.value)} />
              </label>
              <label>
                Stärke (mm)
                <input value={position.stoneDetails.thicknessMm} onChange={(event) => onUpdateStoneDetail(position.id, "thicknessMm", event.target.value)} />
              </label>
              <label>
                Länge (mm)
                <input value={position.stoneDetails.lengthMm} onChange={(event) => onUpdateStoneDetail(position.id, "lengthMm", event.target.value)} />
              </label>
              <label>
                Breite (mm)
                <input value={position.stoneDetails.widthMm} onChange={(event) => onUpdateStoneDetail(position.id, "widthMm", event.target.value)} />
              </label>
              <label>
                Kantenprofil
                <input value={position.stoneDetails.edgeProfile} onChange={(event) => onUpdateStoneDetail(position.id, "edgeProfile", event.target.value)} />
              </label>
              <label>
                Charge
                <input value={position.stoneDetails.batch} onChange={(event) => onUpdateStoneDetail(position.id, "batch", event.target.value)} />
              </label>
              <label>
                Blocknummer
                <input value={position.stoneDetails.blockNumber} onChange={(event) => onUpdateStoneDetail(position.id, "blockNumber", event.target.value)} />
              </label>
              <label>
                Aufmaßnummer
                <input value={position.stoneDetails.measurementNumber} onChange={(event) => onUpdateStoneDetail(position.id, "measurementNumber", event.target.value)} />
              </label>
              <label className="bl-span-2">
                Montageort
                <input value={position.stoneDetails.installationLocation} onChange={(event) => onUpdateStoneDetail(position.id, "installationLocation", event.target.value)} />
              </label>
            </div>
            <button type="button" className="bl-icon-button" aria-label={`Position ${index + 1} entfernen`} onClick={() => onRemovePosition(position.id)}>
              x
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
