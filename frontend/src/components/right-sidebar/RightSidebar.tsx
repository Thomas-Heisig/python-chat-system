import { useMemo, useState } from "react";
import type { ContextUsageResponse } from "../../services/backend";

export type RightPanelTab = "context" | "info" | "sources" | "logs" | "users";

type RightSidebarProps = {
  collapsed: boolean;
  activeTab: RightPanelTab;
  selectedSourceId: number | null;
  sources: Array<{
    id: number;
    file: string;
    position: string;
    relevance: string;
    projectLabel: string;
    scopeDepth: number | null;
  }>;
  activeProjectLabel: string;
  users: Array<{ id: number; username: string; isAdmin: boolean; isActive: boolean; online: boolean; lastSeenAt: string | null }>;
  currentUserId: number;
  currentUserIsAdmin: boolean;
  locale: string;
  timezone: string;
  contextUsage: ContextUsageResponse | null;
  onToggleCollapse: () => void;
  onChangeTab: (tab: RightPanelTab) => void;
  onContextInspect: (label: string) => void;
  onAdminUpdateUser?: (payload: {
    userId: number;
    username: string;
    isAdmin: boolean;
    isActive: boolean;
    password?: string;
  }) => Promise<void>;
  onAdminKickUser?: (userId: number) => Promise<void>;
  onAdminUnlockUser?: (userId: number) => Promise<void>;
  onAdminDeleteUser?: (userId: number) => Promise<void>;
};

const infoRows: Array<{ label: string; value: string }> = [
  { label: "Backend", value: "llama.cpp" },
  { label: "Modell", value: "Qwen 2.5 7B" },
  { label: "Temperatur", value: "0,7" },
  { label: "Antwortlimit", value: "1.500" },
];

const logRows = [
  "19:42 Modell geladen",
  "19:43 Wissenssuche abgeschlossen",
  "19:43 Antwort erzeugt",
  "19:44 Queue: 0",
];

export function RightSidebar({
  collapsed,
  activeTab,
  selectedSourceId,
  sources,
  activeProjectLabel,
  users,
  currentUserId,
  currentUserIsAdmin,
  locale,
  timezone,
  contextUsage,
  onToggleCollapse,
  onChangeTab,
  onContextInspect,
  onAdminUpdateUser,
  onAdminKickUser,
  onAdminUnlockUser,
  onAdminDeleteUser,
}: RightSidebarProps) {
  const [inspectedLabel, setInspectedLabel] = useState<string | null>(null);
  const [expandedSourceGroups, setExpandedSourceGroups] = useState<Record<string, boolean>>({});
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [editUsername, setEditUsername] = useState("");
  const [editIsAdmin, setEditIsAdmin] = useState(false);
  const [editIsActive, setEditIsActive] = useState(true);
  const [editPassword, setEditPassword] = useState("");
  const [editPending, setEditPending] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  const parseRelevancePercent = (value: string): number => {
    const numeric = Number(value.replace(/[^\d]/g, ""));
    if (!Number.isFinite(numeric)) {
      return 0;
    }
    return Math.max(0, Math.min(100, numeric));
  };

  const sourcesWithRelevance = useMemo(
    () => sources.map((source) => ({ ...source, relevancePercent: parseRelevancePercent(source.relevance) })),
    [sources],
  );

  type SourceTreeEntry = {
    label: string;
    pathKey: string;
    children: Map<string, SourceTreeEntry>;
    sources: typeof sourcesWithRelevance;
  };

  const sourceTree = useMemo(() => {
    const rootNodes = new Map<string, SourceTreeEntry>();

    sourcesWithRelevance.forEach((source) => {
      const projectLabel = source.projectLabel ?? "Unzugeordnet";
      const segments = projectLabel === "Unzugeordnet" ? [projectLabel] : projectLabel.split(" / ");
      let cursor = rootNodes;
      let leafNode: SourceTreeEntry | null = null;

      segments.forEach((segment, index) => {
        const pathKey = segments.slice(0, index + 1).join(" / ");
        const existing = cursor.get(segment);
        const node: SourceTreeEntry =
          existing ?? {
          label: segment,
          pathKey,
          children: new Map<string, SourceTreeEntry>(),
          sources: [],
        };
        cursor.set(segment, node);
        cursor = node.children;
        leafNode = node;
      });

      if (leafNode != null) {
        leafNode.sources.push(source);
      }
    });

    return Array.from(rootNodes.values()).sort((left, right) => left.label.localeCompare(right.label, "de"));
  }, [sourcesWithRelevance]);

  const toggleSourceGroup = (pathKey: string) => {
    setExpandedSourceGroups((current) => ({
      ...current,
      [pathKey]: !(current[pathKey] ?? true),
    }));
  };

  const contextLimitTokens = contextUsage?.context_limit_tokens ?? 8192;
  const usedContextTokens = contextUsage?.used_context_tokens ?? 0;
  const systemPromptTokens = contextUsage?.breakdown.system_prompt_tokens ?? 0;
  const chatHistoryTokens = contextUsage?.breakdown.chat_history_tokens ?? 0;
  const externalDataTokens = contextUsage?.breakdown.external_data_tokens ?? 0;
  const filesTokens = contextUsage?.breakdown.files_tokens ?? 0;
  const answerReserveTokens = contextUsage?.breakdown.output_reserve_tokens ?? 0;

  const contextRows: Array<{ label: string; value: string }> = [
    { label: "System-Prompt", value: `${systemPromptTokens.toLocaleString(locale)} Token` },
    { label: "Chatverlauf", value: `${chatHistoryTokens.toLocaleString(locale)} Token` },
    { label: "Externe Daten", value: `${externalDataTokens.toLocaleString(locale)} Token` },
    { label: "Dateien", value: `${filesTokens.toLocaleString(locale)} Token` },
    { label: "Antwortreserve", value: `${answerReserveTokens.toLocaleString(locale)} Token` },
  ];

  const contextUsagePercent = contextLimitTokens > 0 ? Math.min(100, Math.round((usedContextTokens / contextLimitTokens) * 100)) : 0;
  const contextUsageBucket = Math.min(10, Math.max(0, Math.floor(contextUsagePercent / 10)));

  const renderSourceNode = (node: SourceTreeEntry, depth: number) => {
    const childNodes = Array.from(node.children.values()).sort((left, right) => left.label.localeCompare(right.label, "de"));
    const isExpanded = expandedSourceGroups[node.pathKey] ?? true;
    const hasChildren = childNodes.length > 0 || node.sources.length > 0;

    return (
      <li key={node.pathKey} className="source-tree-node">
        <div className={`source-tree-row source-tree-row--depth-${Math.min(depth, 4)}`}>
          {hasChildren ? (
            <button
              type="button"
              className="source-tree-toggle"
              onClick={() => toggleSourceGroup(node.pathKey)}
              aria-label={`${isExpanded ? "Quellengruppe schliessen" : "Quellengruppe oeffnen"}: ${node.label}`}
              aria-expanded={isExpanded}
            >
              {isExpanded ? "▾" : "▸"}
            </button>
          ) : (
            <span className="source-tree-toggle source-tree-toggle--spacer" aria-hidden="true" />
          )}
          <div className="source-tree-label">
            <strong>{node.label}</strong>
            <span>{node.sources.length} Quelle(n)</span>
          </div>
        </div>

        {isExpanded ? (
          <ul className="source-tree-children" aria-label={`Quellen fuer ${node.label}`}>
            {childNodes.map((childNode) => renderSourceNode(childNode, depth + 1))}
            {node.sources.map((source) => (
              <li key={source.id} className={selectedSourceId === source.id ? "source-entry source-entry--active" : "source-entry"}>
                <strong>{source.file}</strong>
                <div>{source.position}</div>
                <div>Relevanz {source.relevance}</div>
                <div>
                  Projekt {source.projectLabel}
                  {source.scopeDepth != null ? ` | Ebene ${source.scopeDepth}` : ""}
                </div>
                <div className="source-actions">
                  <button type="button" className="ghost-btn">Oeffnen</button>
                  <button type="button" className="ghost-btn">Textabschnitt</button>
                </div>
              </li>
            ))}
          </ul>
        ) : null}
      </li>
    );
  };

  const contextDetail =
    inspectedLabel === "Externe Daten"
      ? (contextUsage?.external_data.selected_sources.length ?? 0) === 0
        ? "Keine externen Datenquellen aktiv."
        : (contextUsage?.external_data.selected_sources ?? [])
            .map((source) => `${source.file} (${source.position}, Relevanz ${source.relevance}, Status ${source.status})`)
            .join(" · ")
      : inspectedLabel === "Dateien"
        ? `${contextUsage?.external_data.selected_count ?? sourcesWithRelevance.length} Datei(en) aus Retrieval aktiv.`
        : inspectedLabel
          ? `${inspectedLabel} ist als Detailansicht geladen.`
          : null;

  if (collapsed) {
    return (
      <aside className="right-sidebar" aria-label="Informationsbereich eingeklappt">
        <div className="right-sidebar__tabs">
          <button type="button" className="icon-btn" onClick={onToggleCollapse} aria-label="Rechte Sidebar öffnen">
            ◀
          </button>
        </div>
      </aside>
    );
  }

  return (
    <aside className="right-sidebar" aria-label="Informationsbereich">
      <div className="right-sidebar__tabs">
        <button
          type="button"
          className={`tab-btn ${activeTab === "context" ? "tab-btn--active" : ""}`}
          onClick={() => onChangeTab("context")}
        >
          Kontext
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === "info" ? "tab-btn--active" : ""}`}
          onClick={() => onChangeTab("info")}
        >
          Infos
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === "sources" ? "tab-btn--active" : ""}`}
          onClick={() => onChangeTab("sources")}
        >
          Quellen
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === "logs" ? "tab-btn--active" : ""}`}
          onClick={() => onChangeTab("logs")}
        >
          Logs
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === "users" ? "tab-btn--active" : ""}`}
          onClick={() => onChangeTab("users")}
        >
          Nutzer
        </button>

        <button type="button" className="icon-btn" onClick={onToggleCollapse} aria-label="Rechte Sidebar einklappen">
          ▶
        </button>
      </div>

      <div className="right-sidebar__content">
        {activeTab === "context" ? (
          <section>
            <h2 className="panel-title">Kontextnutzung</h2>
            <div className="context-meter">
              <div className="kv-list context-summary">
                <div>
                  <span>Gesamtauslastung</span>
                  <strong>
                    {usedContextTokens.toLocaleString(locale)} / {contextLimitTokens.toLocaleString(locale)} Token
                  </strong>
                </div>
              </div>
              <div className="progress">
                <span className={`progress-fill progress-fill--${contextUsageBucket}`} />
              </div>
              <div className="kv-list">
                  {contextRows.map((row) => (
                    <button
                      key={row.label}
                      type="button"
                      className="kv-row-btn"
                      onClick={() => {
                        setInspectedLabel(row.label);
                        onContextInspect(row.label);
                      }}
                    >
                      <span>{row.label}</span>
                      <strong>{row.value}</strong>
                    </button>
                  ))}
              </div>

              {contextDetail ? (
                <div className="context-detail" role="note">
                  <strong>{inspectedLabel}</strong>
                  <p>{contextDetail}</p>
                </div>
              ) : null}
            </div>
          </section>
        ) : null}

        {activeTab === "sources" ? (
          <section>
            <h2 className="panel-title">Verwendete Quellen</h2>
            <div className="context-detail" role="note">
              <strong>Aktive Ebene</strong>
              <p>{activeProjectLabel}</p>
            </div>
            <ul className="source-tree">
              {sourceTree.map((node) => renderSourceNode(node, 0))}
              {sourceTree.length === 0 ? <li className="empty-note">Keine Quellen aktiv</li> : null}
            </ul>
          </section>
        ) : null}

        {activeTab === "info" ? (
          <section>
            <h2 className="panel-title">Chat-Infos</h2>
            <div className="context-meter">
              <div className="kv-list">
                  {infoRows.map((row) => (
                    <div key={row.label}>
                      <span>{row.label}</span>
                      <strong>{row.value}</strong>
                    </div>
                  ))}
              </div>
            </div>
          </section>
        ) : null}

        {activeTab === "logs" ? (
          <section>
            <h2 className="panel-title">Standard-Logs</h2>
            <ul className="logs-list">
              {logRows.map((entry) => (
                <li key={entry}>{entry}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {activeTab === "users" ? (
          <section>
            <h2 className="panel-title">Nutzerstatus</h2>
            <ul className="users-list" aria-label="Nutzer online oder offline">
              {users.map((user) => {
                const isCurrentUser = user.id === currentUserId;
                const statusClassName = user.online ? "status-dot status-dot--ok" : "status-dot status-dot--neutral";
                const statusLabel = !user.isActive ? "Gesperrt" : user.online ? "Online" : "Offline";
                return (
                  <li key={user.id} className="users-list__item">
                    <div className="users-list__identity">
                      <span className={statusClassName} aria-hidden="true" />
                      <strong>
                        {user.username}
                        {isCurrentUser ? " (Du)" : ""}
                      </strong>
                      {user.isAdmin ? <span className="users-list__badge">Admin</span> : null}
                    </div>
                    <div className="users-list__meta">
                      <span>{statusLabel}</span>
                      {!user.online && user.lastSeenAt ? <span>Zuletzt aktiv: {new Date(user.lastSeenAt).toLocaleString(locale, { timeZone: timezone })}</span> : null}
                    </div>
                    {currentUserIsAdmin && onAdminUpdateUser ? (
                      <div className="users-list__actions">
                        <button
                          type="button"
                          className="ghost-btn"
                          title="Einstellungen"
                          aria-label="Einstellungen"
                          onClick={() => {
                            setEditingUserId(user.id);
                            setEditUsername(user.username);
                            setEditIsAdmin(user.isAdmin);
                            setEditIsActive(user.isActive);
                            setEditPassword("");
                            setEditError(null);
                          }}
                        >
                          ⚙
                        </button>
                        {!isCurrentUser && onAdminKickUser ? (
                          <button
                            type="button"
                            className="ghost-btn"
                            title="Rausschmeissen"
                            aria-label="Rausschmeissen"
                            disabled={!user.isActive}
                            onClick={() => {
                              void (async () => {
                                const approved = window.confirm(`Nutzer ${user.username} jetzt offline setzen und rausschmeissen?`);
                                if (!approved) {
                                  return;
                                }
                                try {
                                  await onAdminKickUser(user.id);
                                } catch (error) {
                                  const message = error instanceof Error ? error.message : "Nutzer konnte nicht rausgeschmissen werden.";
                                  setEditError(message);
                                }
                              })();
                            }}
                          >
                            ⛔
                          </button>
                        ) : null}
                        {!isCurrentUser && onAdminUnlockUser ? (
                          <button
                            type="button"
                            className="ghost-btn"
                            title="Entsperren"
                            aria-label="Entsperren"
                            disabled={user.isActive}
                            onClick={() => {
                              void (async () => {
                                const approved = window.confirm(`Nutzer ${user.username} jetzt entsperren?`);
                                if (!approved) {
                                  return;
                                }
                                try {
                                  await onAdminUnlockUser(user.id);
                                } catch (error) {
                                  const message = error instanceof Error ? error.message : "Nutzer konnte nicht entsperrt werden.";
                                  setEditError(message);
                                }
                              })();
                            }}
                          >
                            🔓
                          </button>
                        ) : null}
                        {!isCurrentUser && onAdminDeleteUser ? (
                          <button
                            type="button"
                            className="ghost-btn"
                            title="Loeschen"
                            aria-label="Loeschen"
                            onClick={() => {
                              void (async () => {
                                const approved = window.confirm(`Nutzer ${user.username} wirklich loeschen?`);
                                if (!approved) {
                                  return;
                                }
                                try {
                                  await onAdminDeleteUser(user.id);
                                } catch (error) {
                                  const message = error instanceof Error ? error.message : "Nutzer konnte nicht geloescht werden.";
                                  setEditError(message);
                                }
                              })();
                            }}
                          >
                            🗑
                          </button>
                        ) : null}
                      </div>
                    ) : null}

                    {editingUserId === user.id && currentUserIsAdmin && onAdminUpdateUser ? (
                      <form
                        className="users-list__editor"
                        onSubmit={(event) => {
                          event.preventDefault();
                          void (async () => {
                            const normalizedUsername = editUsername.trim();
                            if (normalizedUsername.length < 3) {
                              setEditError("Benutzername muss mindestens 3 Zeichen haben.");
                              return;
                            }
                            if (editPassword.trim().length > 0 && editPassword.trim().length < 4) {
                              setEditError("Neues Passwort muss mindestens 4 Zeichen haben.");
                              return;
                            }
                            setEditPending(true);
                            setEditError(null);
                            try {
                              await onAdminUpdateUser({
                                userId: user.id,
                                username: normalizedUsername,
                                isAdmin: editIsAdmin,
                                isActive: editIsActive,
                                password: editPassword.trim() || undefined,
                              });
                              setEditingUserId(null);
                              setEditPassword("");
                            } catch (error) {
                              const message = error instanceof Error ? error.message : "Einstellungen konnten nicht gespeichert werden.";
                              setEditError(message);
                            } finally {
                              setEditPending(false);
                            }
                          })();
                        }}
                      >
                        <label>
                          Name
                          <input value={editUsername} onChange={(event) => setEditUsername(event.target.value)} disabled={editPending} />
                        </label>
                        <label className="model-radio-wrap model-profile-toggle">
                          <input
                            type="checkbox"
                            checked={editIsActive}
                            onChange={(event) => setEditIsActive(event.target.checked)}
                            disabled={editPending}
                          />
                          Konto aktiv
                        </label>
                        <label className="model-radio-wrap model-profile-toggle">
                          <input
                            type="checkbox"
                            checked={editIsAdmin}
                            onChange={(event) => setEditIsAdmin(event.target.checked)}
                            disabled={editPending}
                          />
                          Adminrechte
                        </label>
                        <label>
                          Neues Passwort (optional)
                          <input
                            type="password"
                            autoComplete="new-password"
                            value={editPassword}
                            onChange={(event) => setEditPassword(event.target.value)}
                            disabled={editPending}
                          />
                        </label>
                        <div className="users-list__editor-actions">
                          <button type="submit" className="action-btn" disabled={editPending}>
                            {editPending ? "Speichert..." : "Speichern"}
                          </button>
                          <button
                            type="button"
                            className="ghost-btn"
                            disabled={editPending}
                            onClick={() => {
                              setEditingUserId(null);
                              setEditError(null);
                            }}
                          >
                            Abbrechen
                          </button>
                        </div>
                        {editError ? <span>{editError}</span> : null}
                      </form>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          </section>
        ) : null}
      </div>
    </aside>
  );
}
