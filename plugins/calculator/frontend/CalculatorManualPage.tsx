import { FormEvent, useCallback, useMemo, useRef, useState } from "react";
import "./CalculatorManualPage.css";
import { usePluginDraft } from "../../shared/frontend/usePluginDraft";
import calculatorLogo from "../assets/logo.svg";

type ExecutePayload = {
  pluginId: string;
  pluginInput?: Record<string, unknown>;
  pluginSettings?: Record<string, unknown>;
  userId?: number;
};

type Props = {
  currentUserId?: number;
  executePlugin?: (payload: ExecutePayload) => Promise<unknown>;
};

type HistoryEntry = {
  id: string;
  expression: string;
  result: number;
  angleMode: "rad" | "deg";
  precision: number;
};

type CalculationSummary = {
  result: number;
  expression: string;
  angleMode: "rad" | "deg";
  precision: number;
  action: string;
};

type CalculatorDraft = {
  expression: string;
  angleMode: "rad" | "deg";
  precision: number;
  history: HistoryEntry[];
  savedAt: string;
};

const CALCULATOR_PLUGIN_ID = "calculator";

type KeypadButton = {
  label: string;
  value: string;
};

const keypadRows: KeypadButton[][] = [
  [
    { label: "7", value: "7" },
    { label: "8", value: "8" },
    { label: "9", value: "9" },
    { label: "/", value: " / " },
    { label: "sqrt", value: "sqrt(" },
  ],
  [
    { label: "4", value: "4" },
    { label: "5", value: "5" },
    { label: "6", value: "6" },
    { label: "*", value: " * " },
    { label: "pow", value: "**" },
  ],
  [
    { label: "1", value: "1" },
    { label: "2", value: "2" },
    { label: "3", value: "3" },
    { label: "-", value: " - " },
    { label: "pi", value: "pi" },
  ],
  [
    { label: "0", value: "0" },
    { label: ".", value: "." },
    { label: "%", value: " % " },
    { label: "+", value: " + " },
    { label: "e", value: "e" },
  ],
];

const presets: Array<{ id: string; label: string; expression: string; angleMode?: "rad" | "deg" }> = [
  { id: "preset-basic", label: "Brutto aus Netto", expression: "1250 * 1.19" },
  { id: "preset-discount", label: "Rabatt 15%", expression: "249 * 0.85" },
  { id: "preset-circle", label: "Kreisflaeche r=12", expression: "pi * 12**2" },
  { id: "preset-trig", label: "Trigonometrie", expression: "sin(30) + cos(60)", angleMode: "deg" },
  { id: "preset-log", label: "Log-Mix", expression: "log(1000) + ln(e**2)" },
];

function parseSummary(raw: unknown): CalculationSummary | null {
  if (typeof raw !== "object" || raw == null) {
    return null;
  }
  const envelope = raw as Record<string, unknown>;
  const payload =
    typeof envelope.plugin_response === "object" && envelope.plugin_response != null
      ? (envelope.plugin_response as Record<string, unknown>)
      : envelope;

  if (typeof payload.result !== "number" || !Number.isFinite(payload.result)) {
    return null;
  }

  const expression = typeof payload.expression === "string" ? payload.expression : "";
  const angleMode = payload.angle_mode === "deg" ? "deg" : "rad";
  const precision = typeof payload.precision === "number" && Number.isFinite(payload.precision)
    ? Math.max(0, Math.min(12, Math.trunc(payload.precision)))
    : 8;
  const action = typeof payload.action === "string" ? payload.action : "evaluate";

  return {
    result: payload.result,
    expression,
    angleMode,
    precision,
    action,
  };
}

export function CalculatorManualPage({ currentUserId, executePlugin }: Props) {
  const applyingDraftRef = useRef(false);

  const [expression, setExpression] = useState<string>("(1250 * 0.19) + sqrt(81)");
  const [angleMode, setAngleMode] = useState<"rad" | "deg">("rad");
  const [precision, setPrecision] = useState<number>(6);
  const [result, setResult] = useState<CalculationSummary | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [running, setRunning] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  const numberFormatter = useMemo(
    () => new Intl.NumberFormat("de-DE", { maximumFractionDigits: Math.max(0, Math.min(12, precision)) }),
    [precision],
  );

  const draftSnapshot = useMemo<CalculatorDraft>(
    () => ({
      expression,
      angleMode,
      precision,
      history,
      savedAt: new Date().toISOString(),
    }),
    [expression, angleMode, precision, history],
  );

  const applyDraft = useCallback((draft: CalculatorDraft) => {
    applyingDraftRef.current = true;
    setExpression(draft.expression);
    setAngleMode(draft.angleMode);
    setPrecision(Math.max(0, Math.min(12, Number(draft.precision) || 0)));
    setHistory(Array.isArray(draft.history) ? draft.history.slice(0, 8) : []);
    setResult(null);
  }, []);

  const normalizeCalculatorDraft = useCallback((raw: unknown): CalculatorDraft | null => {
    if (typeof raw !== "object" || raw == null) {
      return null;
    }
    const row = raw as Partial<CalculatorDraft>;
    return {
      expression: String(row.expression || "(1250 * 0.19) + sqrt(81)"),
      angleMode: row.angleMode === "deg" ? "deg" : "rad",
      precision: Math.max(0, Math.min(12, Number(row.precision) || 6)),
      history: Array.isArray(row.history)
        ? row.history
            .filter((entry) => typeof entry === "object" && entry != null)
            .map((entry) => {
              const item = entry as Partial<HistoryEntry>;
              return {
                id: String(item.id || crypto.randomUUID()),
                expression: String(item.expression || ""),
                result: Number(item.result || 0),
                angleMode: item.angleMode === "deg" ? "deg" : "rad",
                precision: Math.max(0, Math.min(12, Number(item.precision) || 6)),
              } satisfies HistoryEntry;
            })
            .filter((entry) => Number.isFinite(entry.result))
            .slice(0, 8)
        : [],
      savedAt: String(row.savedAt || ""),
    };
  }, []);

  const { draftStatus, draftMessage, saveDraftNow, reloadDraftNow } = usePluginDraft<CalculatorDraft>({
    pluginId: CALCULATOR_PLUGIN_ID,
    currentUserId,
    draftSnapshot,
    applyDraft,
    normalizeDraft: normalizeCalculatorDraft,
    applyingDraftRef,
    autosaveDelayMs: 600,
  });

  const appendToken = (token: string) => {
    setExpression((current) => `${current}${token}`);
  };

  const applyPreset = (presetId: string) => {
    const selected = presets.find((item) => item.id === presetId);
    if (!selected) {
      return;
    }
    setExpression(selected.expression);
    if (selected.angleMode) {
      setAngleMode(selected.angleMode);
    }
    setError("");
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setRunning(true);
    try {
      const payload: ExecutePayload = {
        pluginId: CALCULATOR_PLUGIN_ID,
        userId: currentUserId,
        pluginInput: {
          action: "evaluate",
          expression,
          angle_mode: angleMode,
          precision,
        },
        pluginSettings: {
          angle_mode: angleMode,
          precision,
        },
      };

      let response: unknown;
      if (executePlugin) {
        response = await executePlugin(payload);
      } else {
        const fetchResponse = await fetch("/api/plugins/execute", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            plugin_id: payload.pluginId,
            plugin_input: payload.pluginInput,
            plugin_settings: payload.pluginSettings,
            user_id: payload.userId ?? null,
          }),
        });
        const body = await fetchResponse.json().catch(() => null);
        if (!fetchResponse.ok) {
          throw new Error((body as { detail?: string } | null)?.detail || `Plugin-Aufruf fehlgeschlagen (${fetchResponse.status}).`);
        }
        response = body;
      }

      const summary = parseSummary(response);
      if (!summary) {
        throw new Error("Keine berechenbare Antwort erhalten.");
      }

      setResult(summary);
      setHistory((current) => [
        {
          id: crypto.randomUUID(),
          expression: summary.expression || expression,
          result: summary.result,
          angleMode: summary.angleMode,
          precision: summary.precision,
        },
        ...current,
      ].slice(0, 8));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unbekannter Fehler.");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="calculator-page">
      <header className="calculator-header">
        <div className="calculator-branding">
          <img
            src={calculatorLogo}
            alt="Calculator Logo"
            className="calculator-logo"
            loading="lazy"
          />
          <div>
          <span className="calculator-eyebrow">Calculator</span>
          <h1>Interaktive Rechenoberflaeche</h1>
          <p>Direkte Berechnung ueber den Plugin-Contract mit Presets, Keypad und Ergebnis-Historie.</p>
          </div>
        </div>
      </header>

      <div className="calculator-layout">
        <form className="calculator-main" onSubmit={submit}>
          <section className="calculator-card">
            <div className="calculator-card__header">
              <h2>Ausdruck</h2>
              <div className="calculator-card__actions">
                <button type="button" className="calc-btn calc-btn--secondary" onClick={() => setExpression("")}>Leeren</button>
                <button type="button" className="calc-btn calc-btn--secondary" onClick={() => setExpression((current) => current.slice(0, -1))}>Rueckschritt</button>
              </div>
            </div>
            <textarea
              className="calculator-expression"
              value={expression}
              onChange={(event) => setExpression(event.target.value)}
              placeholder="Beispiel: (12 + 8) * 1.19"
              spellCheck={false}
              rows={4}
            />
            <div className="calculator-preset-grid">
              {presets.map((preset) => (
                <button
                  key={preset.id}
                  type="button"
                  className="calc-chip"
                  onClick={() => applyPreset(preset.id)}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </section>

          <section className="calculator-card">
            <h2>Keypad</h2>
            <div className="calculator-keypad">
              {keypadRows.map((row, rowIndex) => (
                <div key={`row:${rowIndex}`} className="calculator-keypad__row">
                  {row.map((button) => (
                    <button
                      key={`${rowIndex}:${button.label}`}
                      type="button"
                      className="calc-key"
                      onClick={() => appendToken(button.value)}
                    >
                      {button.label}
                    </button>
                  ))}
                </div>
              ))}
              <div className="calculator-keypad__row calculator-keypad__row--wide">
                <button type="button" className="calc-key" onClick={() => appendToken("(")}> ( </button>
                <button type="button" className="calc-key" onClick={() => appendToken(")")}> ) </button>
                <button type="button" className="calc-key" onClick={() => appendToken("sin(")}>sin</button>
                <button type="button" className="calc-key" onClick={() => appendToken("cos(")}>cos</button>
                <button type="button" className="calc-key" onClick={() => appendToken("tan(")}>tan</button>
                <button type="button" className="calc-key" onClick={() => appendToken("log(")}>log</button>
                <button type="button" className="calc-key" onClick={() => appendToken("ln(")}>ln</button>
              </div>
            </div>
          </section>

          <section className="calculator-card calculator-card--runtime">
            <h2>Laufzeit</h2>
            <div className="calculator-runtime-grid">
              <label>
                <span>Winkelmodus</span>
                <select value={angleMode} onChange={(event) => setAngleMode(event.target.value === "deg" ? "deg" : "rad")}>
                  <option value="rad">Radiant</option>
                  <option value="deg">Grad</option>
                </select>
              </label>
              <label>
                <span>Praezision ({precision})</span>
                <input
                  type="range"
                  min={0}
                  max={12}
                  step={1}
                  value={precision}
                  onChange={(event) => setPrecision(Math.max(0, Math.min(12, Number(event.target.value) || 0)))}
                />
              </label>
              <button type="submit" className="calc-btn calc-btn--primary" disabled={running}>
                {running ? "Berechne..." : "Berechnen"}
              </button>
            </div>
            {error ? <div className="calculator-message calculator-message--error">{error}</div> : null}
          </section>
        </form>

        <aside className="calculator-sidebar">
          <section className="calculator-card calculator-card--result">
            <h2>Ergebnis</h2>
            {result ? (
              <div className="calculator-result">
                <span className="calculator-result__value">{numberFormatter.format(result.result)}</span>
                <dl>
                  <div>
                    <dt>Ausdruck</dt>
                    <dd>{result.expression || expression}</dd>
                  </div>
                  <div>
                    <dt>Modus</dt>
                    <dd>{result.angleMode}</dd>
                  </div>
                  <div>
                    <dt>Aktion</dt>
                    <dd>{result.action}</dd>
                  </div>
                </dl>
              </div>
            ) : (
              <p>Noch keine Berechnung ausgefuehrt.</p>
            )}
          </section>

          <section className="calculator-card">
            <h2>Verlauf</h2>
            {history.length > 0 ? (
              <ul className="calculator-history">
                {history.map((entry) => (
                  <li key={entry.id}>
                    <button
                      type="button"
                      onClick={() => {
                        setExpression(entry.expression);
                        setAngleMode(entry.angleMode);
                        setPrecision(entry.precision);
                      }}
                    >
                      <strong>{new Intl.NumberFormat("de-DE", { maximumFractionDigits: 12 }).format(entry.result)}</strong>
                      <span>{entry.expression}</span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p>Der Verlauf fuellt sich nach den ersten Berechnungen.</p>
            )}
          </section>

          <section className="calculator-card">
            <h2>Plugin-Entwurf</h2>
            <p className="calculator-muted">Frontpage-Daten werden plugin-lokal gespeichert.</p>
            <div className="calculator-inline-actions">
              <button
                type="button"
                className="calc-btn calc-btn--secondary"
                onClick={() => void saveDraftNow()}
                disabled={currentUserId == null || draftStatus === "saving"}
              >
                Entwurf speichern
              </button>
              <button
                type="button"
                className="calc-btn calc-btn--secondary"
                onClick={() => void reloadDraftNow()}
                disabled={currentUserId == null || draftStatus === "loading"}
              >
                Entwurf laden
              </button>
            </div>
            {currentUserId == null ? <p className="calculator-muted">Entwurfs-Persistenz ist ohne Benutzerkontext deaktiviert.</p> : null}
            {draftMessage ? <p className={`calculator-muted ${draftStatus === "error" ? "calculator-muted--error" : ""}`}>{draftMessage}</p> : null}
          </section>
        </aside>
      </div>
    </div>
  );
}
