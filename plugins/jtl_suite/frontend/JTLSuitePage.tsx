import React, { FormEvent, useCallback, useMemo, useRef, useState } from 'react';
import './JTLSuitePage.css';
import { usePluginDraft } from '../../shared/frontend/usePluginDraft';
// import logo from '../assets/logo.svg'; // falls vorhanden

// Typen (können auch aus einer zentralen Typdefinition kommen)
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

// Die PLUGIN_META muss zur Laufzeit verfügbar sein – wird meist vom Backend geliefert
// Hier als globale Variable angenommen, kann auch per Context oder Prop reingereicht werden
declare const PLUGIN_META: any;

// Typ für eine Action aus der pluginFrontend-Konfiguration
type PluginAction = {
  id: string;
  label: string;
  description?: string;
  pluginInput: Record<string, any>;
};

type PluginSection = {
  id: string;
  title: string;
  description?: string;
  actions: PluginAction[];
};

type Draft = {
  lastActionId?: string;
  lastParams?: Record<string, any>;
  savedAt?: string;
};

const PLUGIN_ID = 'jtl_suite';

export function JTLSuitePage({ currentUserId, executePlugin }: Props) {
  const applyingDraftRef = useRef(false);

  // Zustand für ausgewählte Aktion und Parameter
  const [selectedAction, setSelectedAction] = useState<PluginAction | null>(null);
  const [actionParams, setActionParams] = useState<Record<string, any>>({});
  const [result, setResult] = useState<any>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');

  // Hole die Sections aus PLUGIN_META
  const sections: PluginSection[] = useMemo(
    () => PLUGIN_META?.pluginFrontend?.sections || [],
    []
  );

  // Draft für Autosave (optional)
  const draftSnapshot = useMemo<Draft>(
    () => ({
      lastActionId: selectedAction?.id,
      lastParams: actionParams,
      savedAt: new Date().toISOString(),
    }),
    [selectedAction, actionParams]
  );

  const normalizeDraft = useCallback((raw: unknown): Draft | null => {
    if (typeof raw !== 'object' || raw == null) return null;
    const d = raw as Partial<Draft>;
    return {
      lastActionId: d.lastActionId || undefined,
      lastParams: d.lastParams || {},
      savedAt: d.savedAt || '',
    };
  }, []);

  const applyDraft = useCallback((draft: Draft) => {
    applyingDraftRef.current = true;
    if (draft.lastActionId) {
      // Suche die Aktion in allen Sections
      for (const section of sections) {
        const found = section.actions.find(a => a.id === draft.lastActionId);
        if (found) {
          setSelectedAction(found);
          setActionParams(draft.lastParams || {});
          break;
        }
      }
    }
  }, [sections]);

  const { draftStatus, draftMessage, saveDraftNow, reloadDraftNow } = usePluginDraft<Draft>({
    pluginId: PLUGIN_ID,
    currentUserId,
    draftSnapshot,
    applyDraft,
    normalizeDraft,
    applyingDraftRef,
    autosaveDelayMs: 600,
  });

  // Handler für Action-Klick
  const handleActionClick = (action: PluginAction) => {
    setSelectedAction(action);
    // Setze Parameter aus pluginInput als Vorschlag, aber kopiere sie, damit der Benutzer sie anpassen kann
    setActionParams({ ...action.pluginInput });
    setError('');
    setResult(null);
  };

  // Parameter-Änderung
  const handleParamChange = (key: string, value: any) => {
    setActionParams(prev => ({ ...prev, [key]: value }));
  };

  // Submit des Befehls
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedAction) {
      setError('Bitte wähle zuerst eine Aktion aus.');
      return;
    }

    setError('');
    setRunning(true);
    try {
      const payload: ExecutePayload = {
        pluginId: PLUGIN_ID,
        userId: currentUserId,
        pluginInput: {
          ...selectedAction.pluginInput,
          ...actionParams,  // überschreibt mit benutzerdefinierten Werten
        },
        pluginSettings: {}, // ggf. globale Settings
      };

      let response: unknown;
      if (executePlugin) {
        response = await executePlugin(payload);
      } else {
        const fetchResponse = await fetch('/api/plugins/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            plugin_id: payload.pluginId,
            plugin_input: payload.pluginInput,
            plugin_settings: payload.pluginSettings,
            user_id: payload.userId ?? null,
          }),
        });
        const body = await fetchResponse.json().catch(() => null);
        if (!fetchResponse.ok) {
          throw new Error((body as { detail?: string } | null)?.detail || `Plugin-Aufruf fehlgeschlagen (${fetchResponse.status})`);
        }
        response = body;
      }
      setResult(response);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unbekannter Fehler.');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="jtl-suite-page">
      <header className="jtl-header">
        <div className="jtl-branding">
          {/* Logo optional */}
          <h1>JTL Suite</h1>
          <p className="jtl-subtitle">Maximale JTL-Integration – Wawi, Shop, WMS, eazyAuction</p>
        </div>
      </header>

      <div className="jtl-layout">
        {/* Linke Spalte: Sections und Actions */}
        <div className="jtl-actions-sidebar">
          {sections.map((section) => (
            <div key={section.id} className="jtl-section">
              <h3>{section.title}</h3>
              {section.description && <p className="jtl-section-desc">{section.description}</p>}
              <div className="jtl-action-grid">
                {section.actions.map((action) => (
                  <button
                    key={action.id}
                    className={`jtl-action-btn ${selectedAction?.id === action.id ? 'active' : ''}`}
                    onClick={() => handleActionClick(action)}
                    title={action.description}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Rechte Spalte: Ausführung und Ergebnis */}
        <div className="jtl-execution-panel">
          {selectedAction ? (
            <form onSubmit={submit} className="jtl-exec-form">
              <div className="jtl-exec-header">
                <h2>{selectedAction.label}</h2>
                <p className="jtl-exec-desc">{selectedAction.description}</p>
              </div>

              {/* Dynamische Parameter-Felder */}
              <div className="jtl-params">
                {Object.entries(actionParams).map(([key, value]) => {
                  // Je nach Typ des Wertes entscheiden wir, welches Input-Feld gerendert wird
                  const inputType = typeof value === 'number' ? 'number' : 'text';
                  return (
                    <div key={key} className="jtl-param-row">
                      <label htmlFor={`param-${key}`}>{key}</label>
                      <input
                        id={`param-${key}`}
                        type={inputType}
                        value={value ?? ''}
                        onChange={(e) => {
                          const newVal = inputType === 'number' ? Number(e.target.value) : e.target.value;
                          handleParamChange(key, newVal);
                        }}
                      />
                    </div>
                  );
                })}
              </div>

              <button type="submit" className="jtl-submit-btn" disabled={running}>
                {running ? 'Wird ausgeführt...' : 'Ausführen'}
              </button>

              {error && <div className="jtl-error">{error}</div>}
            </form>
          ) : (
            <div className="jtl-placeholder">
              <p>Wähle eine Aktion aus der linken Liste, um sie auszuführen.</p>
            </div>
          )}

          {/* Ergebnis anzeigen */}
          {result && (
            <div className="jtl-result">
              <h3>Ergebnis</h3>
              <pre>{JSON.stringify(result, null, 2)}</pre>
            </div>
          )}

          {/* Draft-Persistenz (optional) */}
          <div className="jtl-draft-controls">
            <button
              type="button"
              className="jtl-draft-btn"
              onClick={() => void saveDraftNow()}
              disabled={currentUserId == null || draftStatus === 'saving'}
            >
              Entwurf speichern
            </button>
            <button
              type="button"
              className="jtl-draft-btn"
              onClick={() => void reloadDraftNow()}
              disabled={currentUserId == null || draftStatus === 'loading'}
            >
              Entwurf laden
            </button>
            {draftMessage && <span className="jtl-draft-msg">{draftMessage}</span>}
          </div>
        </div>
      </div>
    </div>
  );
}

export default JTLSuitePage;