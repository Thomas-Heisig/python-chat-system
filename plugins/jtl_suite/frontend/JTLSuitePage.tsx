import React, { FormEvent, useCallback, useMemo, useRef, useState } from 'react';
import { usePluginDraft } from '../../shared/frontend/usePluginDraft';
import './JTLSuitePage.css';

type JsonObject = Record<string, unknown>;

type ExecutePayload = {
  pluginId: string;
  pluginInput?: JsonObject;
  pluginSettings?: JsonObject;
  userId?: number;
};

type PluginAction = {
  id: string;
  label: string;
  description?: string;
  openTab?: 'manual' | 'settings';
  pluginInput?: JsonObject;
};

type PluginSection = {
  id: string;
  title: string;
  description?: string;
  actions?: PluginAction[];
};

type PluginMeta = {
  name?: string;
  description?: string;
  icon?: string;
  pluginFrontend?: {
    title?: string;
    description?: string;
    sections?: PluginSection[];
  };
};

type Props = {
  currentUserId?: number;
  executePlugin?: (payload: ExecutePayload) => Promise<unknown>;
  pluginMeta?: PluginMeta;
  onClose?: () => void;
  onOpenSettings?: () => void;
};

type Draft = {
  lastActionId?: string;
  lastParams?: JsonObject;
  savedAt?: string;
};

const PLUGIN_ID = 'jtl_suite';

function fieldValue(value: unknown): string {
  if (value == null) return '';
  if (typeof value === 'object') return JSON.stringify(value, null, 2);
  return String(value);
}

function parseFieldValue(original: unknown, value: string): unknown {
  if (typeof original === 'number') return Number(value);
  if (typeof original === 'boolean') return value === 'true';
  if (typeof original === 'object' && original !== null) {
    try {
      return JSON.parse(value);
    } catch {
      return value;
    }
  }
  return value;
}

export function JTLSuitePage({ currentUserId, executePlugin, pluginMeta, onClose, onOpenSettings }: Props) {
  const applyingDraftRef = useRef(false);
  const sections = useMemo(() => pluginMeta?.pluginFrontend?.sections ?? [], [pluginMeta]);
  const allActions = useMemo(() => sections.flatMap((section) => section.actions ?? []), [sections]);
  const [selectedAction, setSelectedAction] = useState<PluginAction | null>(null);
  const [actionParams, setActionParams] = useState<JsonObject>({});
  const [result, setResult] = useState<unknown>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');

  const draftSnapshot = useMemo<Draft>(() => ({
    lastActionId: selectedAction?.id,
    lastParams: actionParams,
    savedAt: new Date().toISOString(),
  }), [selectedAction, actionParams]);

  const normalizeDraft = useCallback((raw: unknown): Draft | null => {
    if (!raw || typeof raw !== 'object') return null;
    const value = raw as Draft;
    return {
      lastActionId: value.lastActionId,
      lastParams: value.lastParams ?? {},
      savedAt: value.savedAt,
    };
  }, []);

  const applyDraft = useCallback((draft: Draft) => {
    applyingDraftRef.current = true;
    const action = allActions.find((candidate) => candidate.id === draft.lastActionId);
    if (action) setSelectedAction(action);
    setActionParams(draft.lastParams ?? action?.pluginInput ?? {});
  }, [allActions]);

  const { draftStatus, draftMessage, saveDraftNow, reloadDraftNow } = usePluginDraft({
    pluginId: PLUGIN_ID,
    currentUserId,
    draftSnapshot,
    applyDraft,
    normalizeDraft,
    applyingDraftRef,
    autosaveDelayMs: 600,
  });

  const chooseAction = (action: PluginAction) => {
    if (action.openTab === 'settings') {
      onOpenSettings?.();
      return;
    }
    setSelectedAction(action);
    setActionParams({ ...(action.pluginInput ?? {}) });
    setResult(null);
    setError('');
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedAction) return;
    setRunning(true);
    setError('');
    try {
      const payload: ExecutePayload = {
        pluginId: PLUGIN_ID,
        userId: currentUserId,
        pluginInput: { ...(selectedAction.pluginInput ?? {}), ...actionParams },
      };
      if (executePlugin) {
        setResult(await executePlugin(payload));
      } else {
        const response = await fetch('/api/plugins/execute', {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            plugin_id: payload.pluginId,
            plugin_input: payload.pluginInput,
            user_id: payload.userId ?? null,
          }),
        });
        const body = await response.json().catch(() => null);
        if (!response.ok) throw new Error(body?.detail ?? `Plugin-Aufruf fehlgeschlagen (${response.status})`);
        setResult(body);
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unbekannter Fehler');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="jtl-suite-page">
      <header className="jtl-suite-header">
        <div className="jtl-suite-brand">
          <img src={pluginMeta?.icon ?? '/api/plugins/jtl_suite/assets/logo.svg'} alt="" />
          <div>
            <h1>{pluginMeta?.pluginFrontend?.title ?? pluginMeta?.name ?? 'JTL Suite'}</h1>
            <p>{pluginMeta?.pluginFrontend?.description ?? pluginMeta?.description}</p>
          </div>
        </div>
        {onClose && <button className="jtl-suite-close" type="button" onClick={onClose} aria-label="Plugin schließen">×</button>}
      </header>

      <div className="jtl-suite-layout">
        <nav className="jtl-suite-navigation" aria-label="JTL Aktionen">
          {sections.map((section) => (
            <section key={section.id}>
              <h2>{section.title}</h2>
              {section.description && <p>{section.description}</p>}
              <div className="jtl-suite-actions">
                {(section.actions ?? []).map((action) => (
                  <button
                    key={action.id}
                    type="button"
                    className={selectedAction?.id === action.id ? 'is-active' : ''}
                    onClick={() => chooseAction(action)}
                  >
                    <strong>{action.label}</strong>
                    {action.description && <span>{action.description}</span>}
                  </button>
                ))}
              </div>
            </section>
          ))}
        </nav>

        <main className="jtl-suite-workspace">
          {!selectedAction ? (
            <div className="jtl-suite-empty">Wähle links eine Aktion aus.</div>
          ) : (
            <form onSubmit={submit}>
              <div className="jtl-suite-form-header">
                <div><h2>{selectedAction.label}</h2><p>{selectedAction.description}</p></div>
                <button type="submit" disabled={running}>{running ? 'Wird ausgeführt …' : 'Ausführen'}</button>
              </div>
              <div className="jtl-suite-fields">
                {Object.entries(actionParams).map(([key, value]) => (
                  <label key={key}>
                    <span>{key}</span>
                    {typeof value === 'boolean' ? (
                      <select value={String(value)} onChange={(event) => setActionParams((current) => ({ ...current, [key]: event.target.value === 'true' }))}>
                        <option value="true">Ja</option><option value="false">Nein</option>
                      </select>
                    ) : typeof value === 'object' && value !== null ? (
                      <textarea value={fieldValue(value)} rows={6} onChange={(event) => setActionParams((current) => ({ ...current, [key]: parseFieldValue(value, event.target.value) }))} />
                    ) : (
                      <input type={typeof value === 'number' ? 'number' : 'text'} value={fieldValue(value)} onChange={(event) => setActionParams((current) => ({ ...current, [key]: parseFieldValue(value, event.target.value) }))} />
                    )}
                  </label>
                ))}
              </div>
            </form>
          )}

          {error && <div className="jtl-suite-error">{error}</div>}
          {result !== null && <section className="jtl-suite-result"><h2>Ergebnis</h2><pre>{JSON.stringify(result, null, 2)}</pre></section>}
          <footer className="jtl-suite-draft">
            <button type="button" onClick={() => void saveDraftNow()} disabled={currentUserId == null || draftStatus === 'saving'}>Entwurf speichern</button>
            <button type="button" onClick={() => void reloadDraftNow()} disabled={currentUserId == null || draftStatus === 'loading'}>Entwurf laden</button>
            {draftMessage && <span>{draftMessage}</span>}
          </footer>
        </main>
      </div>
    </div>
  );
}

export default JTLSuitePage;
