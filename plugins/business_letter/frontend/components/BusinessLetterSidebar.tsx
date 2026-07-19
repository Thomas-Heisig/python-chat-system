import type { PendingConfirmation } from "../services/businessLetterApi";
import type { BusinessLetterResultSummary } from "../services/types";

type SidebarConfig = {
  label: string;
  category: string;
  requiresPositions: boolean;
  supportsEInvoice: boolean;
};

type SidebarTotals = {
  net: number;
  tax: number;
  gross: number;
};

type BusinessLetterSidebarProps = {
  config: SidebarConfig;
  positionsCount: number;
  totals: SidebarTotals;
  currentUserId?: number;
  draftStatus: string;
  draftMessage: string;
  saveDraftNow: () => Promise<void>;
  reloadDraftNow: () => Promise<void>;
  attachPdf: boolean;
  attachXml: boolean;
  validateBeforeSend: boolean;
  saveDocument: boolean;
  setAttachPdf: (value: boolean) => void;
  setAttachXml: (value: boolean) => void;
  setValidateBeforeSend: (value: boolean) => void;
  setSaveDocument: (value: boolean) => void;
  error: string;
  pendingConfirmation: PendingConfirmation | null;
  running: boolean;
  confirmPendingExecution: () => Promise<void>;
  result: unknown;
  resultSummary: BusinessLetterResultSummary | null;
  showTechnicalResponse: boolean;
};

const money = new Intl.NumberFormat("de-DE", {
  style: "currency",
  currency: "EUR",
});

export function BusinessLetterSidebar({
  config,
  positionsCount,
  totals,
  currentUserId,
  draftStatus,
  draftMessage,
  saveDraftNow,
  reloadDraftNow,
  attachPdf,
  attachXml,
  validateBeforeSend,
  saveDocument,
  setAttachPdf,
  setAttachXml,
  setValidateBeforeSend,
  setSaveDocument,
  error,
  pendingConfirmation,
  running,
  confirmPendingExecution,
  result,
  resultSummary,
  showTechnicalResponse,
}: BusinessLetterSidebarProps) {
  return (
    <aside className="business-letter-sidebar">
      <section className="bl-card bl-summary-card">
        <h2>Zusammenfassung</h2>
        <dl>
          <div>
            <dt>Dokument</dt>
            <dd>{config.label}</dd>
          </div>
          <div>
            <dt>Kategorie</dt>
            <dd>{config.category}</dd>
          </div>
          <div>
            <dt>Positionen</dt>
            <dd>{config.requiresPositions ? positionsCount : 0}</dd>
          </div>
          <div>
            <dt>Netto</dt>
            <dd>{money.format(totals.net)}</dd>
          </div>
          <div>
            <dt>Steuer</dt>
            <dd>{money.format(totals.tax)}</dd>
          </div>
          <div className="bl-total">
            <dt>Brutto</dt>
            <dd>{money.format(totals.gross)}</dd>
          </div>
        </dl>
      </section>

      <section className="bl-card">
        <h2>Plugin-Entwurf</h2>
        <p className="bl-muted">Formulardaten werden plugin-lokal als Entwurf gespeichert.</p>
        <div className="bl-inline-actions">
          <button type="button" className="bl-button bl-button-secondary" onClick={() => void saveDraftNow()} disabled={currentUserId == null || draftStatus === "saving"}>
            Entwurf speichern
          </button>
          <button type="button" className="bl-button bl-button-secondary" onClick={() => void reloadDraftNow()} disabled={currentUserId == null || draftStatus === "loading"}>
            Entwurf laden
          </button>
        </div>
        {currentUserId == null ? <p className="bl-muted">Entwurfs-Persistenz ist ohne Benutzerkontext deaktiviert.</p> : null}
        {draftMessage ? <p className={`bl-muted ${draftStatus === "error" ? "bl-error-text" : ""}`}>{draftMessage}</p> : null}
      </section>

      <section className="bl-card">
        <h2>Ausgabe</h2>
        <label className="bl-check">
          <input type="checkbox" checked={attachPdf} onChange={(event) => setAttachPdf(event.target.checked)} />
          <span>PDF erzeugen</span>
        </label>
        {config.supportsEInvoice ? <label className="bl-check">
          <input type="checkbox" checked={attachXml} onChange={(event) => setAttachXml(event.target.checked)} />
          <span>E-Rechnungs-XML erzeugen</span>
        </label> : null}
        <label className="bl-check">
          <input type="checkbox" checked={validateBeforeSend} onChange={(event) => setValidateBeforeSend(event.target.checked)} />
          <span>Vor Ausgabe validieren</span>
        </label>
        <label className="bl-check">
          <input type="checkbox" checked={saveDocument} onChange={(event) => setSaveDocument(event.target.checked)} />
          <span>Dokument speichern</span>
        </label>
      </section>

      {error ? (
        <div className="bl-message bl-message-error" role="alert">
          {error}
        </div>
      ) : null}
      {pendingConfirmation ? (
        <section className="bl-card" role="status">
          <h2>Bestätigung erforderlich</h2>
          <p>
            Dieser Aufruf wartet auf eine explizite Freigabe. Die serverseitig geprüfte Anfrage wird mit
            derselben Bestätigungs-ID ausgeführt.
          </p>
          <div className="bl-inline-actions">
            <button type="button" className="bl-button bl-button-primary" onClick={() => void confirmPendingExecution()} disabled={running || currentUserId == null}>
              Jetzt bestätigen
            </button>
          </div>
          <p className="bl-muted">Bestätigungs-ID: {pendingConfirmation.confirmation_id}</p>
        </section>
      ) : null}
      {result !== null ? (
        <section className="bl-card bl-result">
          <h2>Plugin-Ergebnis</h2>
          {resultSummary ? (
            <div className="bl-result-summary">
              <dl>
                <div><dt>Dokumenttyp</dt><dd>{resultSummary.documentType}</dd></div>
                <div><dt>Dokumentnummer</dt><dd>{resultSummary.documentNumber}</dd></div>
                <div><dt>Status</dt><dd>{resultSummary.status}</dd></div>
                <div><dt>Quelldokument</dt><dd>{resultSummary.sourceDocumentNumber || "-"}</dd></div>
                <div><dt>Konvertierung</dt><dd>{resultSummary.conversionAction || "-"}</dd></div>
                <div><dt>Folgebelege</dt><dd>{resultSummary.followUpDocuments || 0}</dd></div>
                <div><dt>Offener Betrag</dt><dd>{resultSummary.openAmount || "-"}</dd></div>
                <div><dt>PDF</dt><dd>{resultSummary.pdfFile || "-"}</dd></div>
                <div><dt>XML</dt><dd>{config.supportsEInvoice ? (resultSummary.xmlFile || "-") : "nicht relevant"}</dd></div>
                <div><dt>Validierung</dt><dd>{resultSummary.validationStatus}</dd></div>
                <div><dt>Speicherort</dt><dd>{resultSummary.storageLocation || "-"}</dd></div>
                <div><dt>Versandstatus</dt><dd>{resultSummary.dispatchStatus || "-"}</dd></div>
                <div><dt>Archivstatus</dt><dd>{resultSummary.archiveStatus || "-"}</dd></div>
              </dl>
              {resultSummary.warnings.length > 0 ? (
                <div className="bl-result-warnings">
                  <strong>Warnungen</strong>
                  {resultSummary.warnings.map((warning) => (
                    <span key={warning}>{warning}</span>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
          {showTechnicalResponse ? (
            <details>
              <summary>Technische Antwort</summary>
              <pre>{JSON.stringify(result, null, 2)}</pre>
            </details>
          ) : null}
        </section>
      ) : null}

      <button type="submit" className="bl-button bl-button-primary bl-submit" disabled={running}>
        {running ? "Dokument wird erstellt …" : `${config.label} erstellen`}
      </button>
    </aside>
  );
}
