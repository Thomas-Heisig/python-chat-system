import { useEffect, useMemo, useRef, useState } from "react";
import type { ConversationSummary } from "../../types/api";

type LeftSidebarProps = {
  collapsed: boolean;
  activeNav: "Chats" | "Suche" | "Projekte" | "Bibliothek" | "Termine" | "Plugins" | "Einstellungen";
  selectedConversationId: number | null;
  conversations: ConversationSummary[];
  projects: Array<{ id: number; name: string; parent_project_id?: number | null }>;
  selectedProjectId: number | null;
  conversationVisibilityMap: Record<number, "private" | "internal" | "public">;
  conversationTree: Record<number, number | null>;
  appointments: Array<{ id: number; date: string; title: string; state: string }>;
  locale: string;
  timezone: string;
  language: "de" | "en";
  currentUsername: string;
  currentUserId: number;
  currentUserRoleLabel: string;
  onToggleCollapse: () => void;
  onSelectNav: (section: "Chats" | "Suche" | "Projekte" | "Bibliothek" | "Termine" | "Plugins" | "Einstellungen") => void;
  onSelectChat: (conversationId: number) => void;
  onSelectProject: (projectId: number | null) => void;
  onAssignConversationProject: (conversationId: number, projectId: number | null) => void;
  onMoveConversation: (conversationId: number, parentConversationId: number | null) => void;
  onRenameConversation: (conversationId: number, title: string) => void;
  onSetConversationVisibility: (conversationId: number, visibility: "private" | "internal" | "public") => void;
  onDeleteConversation: (conversationId: number) => void;
  onNewConversation: () => void;
  onLogout: () => void;
};

const navSections: Array<"Projekte" | "Bibliothek" | "Termine" | "Plugins" | "Chats"> = [
  "Projekte",
  "Bibliothek",
  "Termine",
  "Plugins",
  "Chats",
];

function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const selector = [
    "button:not([disabled])",
    "a[href]",
    "input:not([disabled])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    "[tabindex]:not([tabindex='-1'])",
  ].join(",");
  return Array.from(container.querySelectorAll<HTMLElement>(selector)).filter((element) => {
    return !element.hasAttribute("disabled") && element.getAttribute("aria-hidden") !== "true";
  });
}

function handleModalFocusTrap(event: React.KeyboardEvent<HTMLElement>): void {
  if (event.key !== "Tab") {
    return;
  }
  const container = event.currentTarget;
  const focusable = getFocusableElements(container);
  if (focusable.length === 0) {
    event.preventDefault();
    return;
  }
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  const active = document.activeElement as HTMLElement | null;
  if (event.shiftKey) {
    if (active == null || active === first || !container.contains(active)) {
      event.preventDefault();
      last.focus();
    }
    return;
  }
  if (active == null || active === last || !container.contains(active)) {
    event.preventDefault();
    first.focus();
  }
}

export function LeftSidebar({
  collapsed,
  activeNav,
  selectedConversationId,
  conversations,
  projects,
  selectedProjectId,
  conversationVisibilityMap,
  conversationTree,
  appointments,
  locale,
  timezone,
  language,
  currentUsername,
  currentUserId,
  currentUserRoleLabel,
  onToggleCollapse,
  onSelectNav,
  onSelectChat,
  onSelectProject,
  onAssignConversationProject,
  onMoveConversation,
  onRenameConversation,
  onSetConversationVisibility,
  onDeleteConversation,
  onNewConversation,
  onLogout,
}: LeftSidebarProps) {
  const lastDetailOpenerRef = useRef<HTMLElement | null>(null);
  const [draggedConversationId, setDraggedConversationId] = useState<number | null>(null);
  const [menuConversationId, setMenuConversationId] = useState<number | null>(null);
  const [detailConversationId, setDetailConversationId] = useState<number | null>(null);
  const [renameDraft, setRenameDraft] = useState("");
  const [projectDraft, setProjectDraft] = useState<string>("none");
  const [moveTargetId, setMoveTargetId] = useState<string>("root");
  const [visibilityDraft, setVisibilityDraft] = useState<"private" | "internal" | "public">("internal");

  const openConversationDetails = (conversationId: number) => {
    if (document.activeElement instanceof HTMLElement) {
      lastDetailOpenerRef.current = document.activeElement;
    }
    setDetailConversationId(conversationId);
  };
  const userInitials = useMemo(() => {
    const cleaned = currentUsername.trim();
    if (!cleaned) {
      return "U";
    }
    return cleaned.slice(0, 2).toUpperCase();
  }, [currentUsername]);

  const projectById = useMemo(() => {
    return new Map(projects.map((project) => [project.id, project] as const));
  }, [projects]);

  const buildProjectDisplayName = (projectId: number): string => {
    const lineage: string[] = [];
    const seen = new Set<number>();
    let cursor: number | null = projectId;

    while (cursor != null && !seen.has(cursor)) {
      seen.add(cursor);
      const project = projectById.get(cursor);
      if (project == null) {
        break;
      }
      lineage.push(project.name);
      cursor = typeof project.parent_project_id === "number" && project.parent_project_id > 0 ? project.parent_project_id : null;
    }

    if (lineage.length === 0) {
      return String(projectId);
    }

    return lineage.reverse().join(" / ");
  };

  const projectsByParent = useMemo(() => {
    const map = new Map<number | null, Array<(typeof projects)[number]>>();

    projects.forEach((project) => {
      const parentId = typeof project.parent_project_id === "number" && project.parent_project_id > 0 ? project.parent_project_id : null;
      const bucket = map.get(parentId) ?? [];
      bucket.push(project);
      map.set(parentId, bucket);
    });

    for (const bucket of map.values()) {
      bucket.sort((left, right) => buildProjectDisplayName(left.id).localeCompare(buildProjectDisplayName(right.id), "de"));
    }

    return map;
  }, [buildProjectDisplayName, projects]);

  const selectedProjectLineage = useMemo(() => {
    const lineage = new Set<number>();
    const seen = new Set<number>();
    let cursor: number | null = selectedProjectId;

    if (cursor == null) {
      return lineage;
    }

    while (cursor != null && !seen.has(cursor)) {
      seen.add(cursor);
      const project = projectById.get(cursor);
      if (project == null) {
        break;
      }
      lineage.add(project.id);
      cursor = typeof project.parent_project_id === "number" && project.parent_project_id > 0 ? project.parent_project_id : null;
    }

    return lineage;
  }, [projectById, selectedProjectId]);

  const selectedProjectScopeIds = useMemo(() => {
    if (selectedProjectId == null) {
      return null;
    }

    const scopeIds = new Set<number>();
    const visit = (projectId: number) => {
      if (scopeIds.has(projectId)) {
        return;
      }
      scopeIds.add(projectId);
      (projectsByParent.get(projectId) ?? []).forEach((childProject) => visit(childProject.id));
    };

    visit(selectedProjectId);
    return scopeIds;
  }, [projectsByParent, selectedProjectId]);

  const visibleConversations = useMemo(() => {
    if (selectedProjectScopeIds == null) {
      return conversations;
    }

    return conversations.filter((conversation) => conversation.projectId != null && selectedProjectScopeIds.has(conversation.projectId));
  }, [conversations, selectedProjectScopeIds]);

  const visibleConversationById = useMemo(() => {
    const map = new Map<number, ConversationSummary>();
    visibleConversations.forEach((conversation) => map.set(conversation.id, conversation));
    return map;
  }, [visibleConversations]);

  const visibleChildrenByParent = useMemo(() => {
    const map = new Map<number | null, ConversationSummary[]>();
    const addToParent = (parentId: number | null, conversation: ConversationSummary) => {
      const bucket = map.get(parentId) ?? [];
      bucket.push(conversation);
      map.set(parentId, bucket);
    };

    visibleConversations.forEach((conversation) => {
      const parentId = conversationTree[conversation.id] ?? null;
      if (parentId != null && !visibleConversationById.has(parentId)) {
        addToParent(null, conversation);
        return;
      }
      addToParent(parentId, conversation);
    });

    return map;
  }, [conversationTree, visibleConversations, visibleConversationById]);

  const visibleConversationRoots = visibleChildrenByParent.get(null) ?? [];
  const detailConversation = detailConversationId != null
    ? conversations.find((conversation) => conversation.id === detailConversationId) ?? null
    : null;

  useEffect(() => {
    if (detailConversationId == null) {
      return;
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setDetailConversationId(null);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [detailConversationId]);

  useEffect(() => {
    if (detailConversationId != null) {
      return;
    }
    const opener = lastDetailOpenerRef.current;
    if (opener) {
      opener.focus();
      lastDetailOpenerRef.current = null;
    }
  }, [detailConversationId]);

  const renderConversationNode = (conversation: ConversationSummary, depth: number) => {
    const children = visibleChildrenByParent.get(conversation.id) ?? [];

    return (
      <div key={conversation.id} className="chat-tree-node">
        <div
          className="chat-row"
          style={{ "--tree-depth": depth } as CSSProperties}
          onDragOver={(event) => {
            event.preventDefault();
          }}
          onDrop={(event) => {
            event.preventDefault();
            const draggedIdRaw = event.dataTransfer.getData("text/plain");
            const draggedId = Number(draggedIdRaw);
            if (!Number.isInteger(draggedId) || draggedId === conversation.id) {
              return;
            }
            onMoveConversation(draggedId, conversation.id);
            setDraggedConversationId(null);
          }}
        >
          <button
            type="button"
            className={`chat-item ${selectedConversationId === conversation.id ? "chat-item--active" : ""}`}
            title={conversation.title}
            draggable
            onDragStart={(event) => {
              event.dataTransfer.setData("text/plain", String(conversation.id));
              event.dataTransfer.effectAllowed = "move";
              setDraggedConversationId(conversation.id);
            }}
            onDragEnd={() => {
              setDraggedConversationId(null);
            }}
            onClick={() => onSelectChat(conversation.id)}
            onDoubleClick={() => {
              const currentParent = conversationTree[conversation.id];
              const currentVisibility = conversationVisibilityMap[conversation.id] ?? "internal";
              setRenameDraft(conversation.title);
              setProjectDraft(conversation.projectId == null ? "none" : String(conversation.projectId));
              setMoveTargetId(currentParent == null ? "root" : String(currentParent));
              setVisibilityDraft(currentVisibility);
              openConversationDetails(conversation.id);
            }}
          >
            {conversation.title}
          </button>
          <button
            type="button"
            className="chat-delete-btn"
            onClick={() => {
              const currentParent = conversationTree[conversation.id];
              const currentVisibility = conversationVisibilityMap[conversation.id] ?? "internal";
              setRenameDraft(conversation.title);
              setProjectDraft(conversation.projectId == null ? "none" : String(conversation.projectId));
              setMoveTargetId(currentParent == null ? "root" : String(currentParent));
              setVisibilityDraft(currentVisibility);
              setMenuConversationId((current) => (current === conversation.id ? null : conversation.id));
            }}
            aria-label={`Chat ${conversation.title} Aktionen`}
            title="Aktionen"
          >
            ⋮
          </button>
        </div>

        {menuConversationId === conversation.id ? (
          <div className="chat-context-menu" role="region" aria-label={`Aktionen fuer ${conversation.title}`}>
            <label className="chat-context-menu__field">
              <span>Umbenennen</span>
              <input
                type="text"
                value={renameDraft}
                onChange={(event) => setRenameDraft(event.target.value)}
              />
            </label>
            <button
              type="button"
              className="ghost-btn"
              onClick={() => {
                onRenameConversation(conversation.id, renameDraft);
                setMenuConversationId(null);
              }}
            >
              Namen speichern
            </button>

            <button
              type="button"
              className="ghost-btn"
              onClick={() => {
                openConversationDetails(conversation.id);
                setMenuConversationId(null);
              }}
            >
              Gross oeffnen
            </button>

            <label className="chat-context-menu__field">
              <span>Sichtbarkeit</span>
              <select
                value={visibilityDraft}
                onChange={(event) => setVisibilityDraft(event.target.value as "private" | "internal" | "public")}
              >
                <option value="private">Privat</option>
                <option value="internal">Intern</option>
                <option value="public">Oeffentlich</option>
              </select>
            </label>
            <button
              type="button"
              className="ghost-btn"
              onClick={() => {
                onSetConversationVisibility(conversation.id, visibilityDraft);
                setMenuConversationId(null);
              }}
            >
              Sichtbarkeit speichern
            </button>

            <label className="chat-context-menu__field">
              <span>Projektzuordnung</span>
              <select aria-label="Projektzuordnung" value={projectDraft} onChange={(event) => setProjectDraft(event.target.value)}>
                <option value="none">Kein Projekt</option>
                {projects.map((project) => (
                  <option key={project.id} value={String(project.id)}>
                    {buildProjectDisplayName(project.id)}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="ghost-btn"
              onClick={() => {
                onAssignConversationProject(conversation.id, projectDraft === "none" ? null : Number(projectDraft));
                setMenuConversationId(null);
              }}
            >
              Projekt speichern
            </button>

            <label className="chat-context-menu__field">
              <span>In Unterchat verschieben</span>
              <select
                value={moveTargetId}
                onChange={(event) => setMoveTargetId(event.target.value)}
              >
                <option value="root">Hauptebene</option>
                {conversations
                  .filter((entry) => entry.id !== conversation.id)
                  .map((entry) => (
                    <option key={entry.id} value={String(entry.id)}>
                      {entry.title}
                    </option>
                  ))}
              </select>
            </label>
            <button
              type="button"
              className="ghost-btn"
              onClick={() => {
                const nextParent = moveTargetId === "root" ? null : Number(moveTargetId);
                onMoveConversation(conversation.id, Number.isInteger(nextParent as number) ? nextParent : null);
                setMenuConversationId(null);
              }}
            >
              Verschieben
            </button>

            <button
              type="button"
              className="action-btn action-btn--danger"
              disabled={conversation.ownerUserId !== currentUserId}
              onClick={() => {
                if (conversation.ownerUserId !== currentUserId) {
                  return;
                }
                const accepted = window.confirm(`Chat \"${conversation.title}\" wirklich loeschen?`);
                if (!accepted) {
                  return;
                }
                onDeleteConversation(conversation.id);
                setMenuConversationId(null);
              }}
              title={conversation.ownerUserId === currentUserId ? "Chat loeschen" : "Nur der Besitzer kann loeschen"}
            >
              Loeschen
            </button>
          </div>
        ) : null}

        {children.length > 0 ? <div className="chat-tree-children">{children.map((child) => renderConversationNode(child, depth + 1))}</div> : null}
      </div>
    );
  };

  const renderProjectNode = (project: (typeof projects)[number], depth: number) => {
    const childProjects = projectsByParent.get(project.id) ?? [];
    const isSelected = selectedProjectId === project.id;
    const isAncestor = selectedProjectLineage.has(project.id) && !isSelected;

    return (
      <div key={project.id} className="project-tree-node">
        <div className="project-tree-row" style={{ "--tree-depth": depth } as CSSProperties}>
          {childProjects.length > 0 ? (
            <button
              type="button"
              className="project-tree-toggle"
              onClick={() => onSelectProject(project.id)}
              aria-label={`Projektordner ${buildProjectDisplayName(project.id)} auswaehlen`}
            >
              ▸
            </button>
          ) : (
            <span className="project-tree-toggle project-tree-toggle--spacer" aria-hidden="true" />
          )}
          <button
            type="button"
            className={`project-tree-label ${isSelected ? "project-tree-label--selected" : ""} ${isAncestor ? "project-tree-label--ancestor" : ""}`}
            onClick={() => onSelectProject(project.id)}
            aria-label={`Projektordner ${buildProjectDisplayName(project.id)}`}
            aria-pressed={isSelected}
            title={buildProjectDisplayName(project.id)}
          >
            {project.name}
          </button>
        </div>

        <div className="project-tree-children">
          {childProjects.map((childProject) => renderProjectNode(childProject, depth + 1))}
        </div>
      </div>
    );
  };

  const rootProjects = projectsByParent.get(null) ?? [];
  const projectHeaderLabel = selectedProjectId != null ? buildProjectDisplayName(selectedProjectId) : "Alle Chats";
  const ui = language === "en"
    ? {
        navigation: "Navigation",
        search: "Search",
        newConversation: "New conversation",
        chats: "Chats",
        projects: "Projects",
        allChats: "All chats",
        currentProject: "Current project",
        noConversations: "No conversations yet",
        nextAppointments: "Next appointments",
        logout: "Logout",
      }
    : {
        navigation: "Navigation",
        search: "Suchen",
        newConversation: "Neue Konversation",
        chats: "Chats",
        projects: "Projekte",
        allChats: "Alle Chats",
        currentProject: "Aktuelles Projekt",
        noConversations: "Noch keine Konversationen",
        nextAppointments: "Naechste Termine",
        logout: "Abmelden",
      };

  const formatAppointmentDate = (dateRaw: string) => {
    const parsed = new Date(dateRaw);
    if (Number.isNaN(parsed.getTime())) {
      return dateRaw;
    }
    return parsed.toLocaleDateString(locale, {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      timeZone: timezone,
    });
  };

  return (
    <aside className={`left-sidebar ${collapsed ? "left-sidebar--collapsed" : ""}`}>
      <div className="left-sidebar__header">
        <div className="logo-row" title="Kernschmiede">
          <img src="/kernschmiede-logo.svg" alt="Kernschmiede" className="sidebar-logo" />
          <span className="label">Kernschmiede</span>
        </div>

        <button type="button" className="icon-btn" onClick={onToggleCollapse} aria-label="Sidebar ein-/ausklappen">
          {collapsed ? "▶" : "◀"}
        </button>
      </div>

      <div className="left-sidebar__search">
        <button
          type="button"
          className="action-btn"
          title="Strg + K"
          onClick={() => onSelectNav("Suche")}
          aria-label={ui.search}
        >
          <span aria-hidden="true">🔍</span>
          <span className="label">{ui.search}</span>
        </button>
      </div>

      <div className="left-sidebar__new">
        <button
          type="button"
          className="action-btn action-btn--primary"
          onClick={onNewConversation}
          title="Strg + N"
          aria-label={ui.newConversation}
        >
          <span aria-hidden="true">＋</span>
          <span className="label">{ui.newConversation}</span>
        </button>
      </div>

      <section className="left-sidebar__section">
        <h2 className="left-sidebar__group-title label">{ui.navigation}</h2>
        <div className="nav-list">
          {navSections.map((section) => (
            <button
              key={section}
              type="button"
              className={`nav-item ${activeNav === section ? "nav-item--active" : ""}`}
              onClick={() => onSelectNav(section)}
              title={section}
            >
              {section}
            </button>
          ))}
        </div>
      </section>

      <section className="chat-scroll">
        <h2 className="left-sidebar__group-title label">{ui.chats}</h2>
        <div className="chat-group-list">
          <section className="chat-group">
            <div className="sidebar-section-header">
              <h3 className="chat-group__title label">{ui.projects}</h3>
              <button type="button" className="sidebar-text-button" onClick={() => onSelectProject(null)} aria-pressed={selectedProjectId == null}>
                {ui.allChats}
              </button>
            </div>

            <div className="project-tree">
              {rootProjects.map((project) => renderProjectNode(project, 0))}
            </div>
          </section>

          <section className="chat-group">
            <div className="sidebar-section-header">
              <h3 className="chat-group__title label">{ui.currentProject}</h3>
              <span className="sidebar-count">{projectHeaderLabel}</span>
            </div>

            {draggedConversationId != null ? (
              <button
                type="button"
                className="chat-root-dropzone"
                onDragOver={(event) => {
                  event.preventDefault();
                }}
                onDrop={(event) => {
                  event.preventDefault();
                  const draggedIdRaw = event.dataTransfer.getData("text/plain");
                  const draggedId = Number(draggedIdRaw);
                  if (!Number.isInteger(draggedId)) {
                    return;
                  }
                  onMoveConversation(draggedId, null);
                  setDraggedConversationId(null);
                }}
              >
                Auf Hauptebene ablegen
              </button>
            ) : null}

            <div className="chat-tree">
              {visibleConversationRoots.map((conversation) => renderConversationNode(conversation, 0))}
              {visibleConversationRoots.length === 0 ? <span className="empty-note">{ui.noConversations}</span> : null}
            </div>
          </section>
        </div>

        <h2 className="left-sidebar__group-title label">{ui.nextAppointments}</h2>
        <div className="chat-list">
          {appointments.slice(0, 5).map((entry) => (
            <button
              key={entry.id}
              type="button"
              className="chat-item"
              onClick={() => onSelectNav("Termine")}
              title={`${formatAppointmentDate(entry.date)} ${entry.title}`}
            >
              {formatAppointmentDate(entry.date)} {entry.title}
            </button>
          ))}
        </div>
      </section>

      <div className="left-sidebar__user">
        <div className="user-card" title="Benutzer">
          <span className="avatar">{userInitials}</span>
          <div className="label">
            <div>{currentUsername}</div>
            <small>{currentUserRoleLabel}</small>
          </div>
          <button type="button" className="ghost-btn user-logout-btn" onClick={onLogout}>
            {ui.logout}
          </button>
        </div>
      </div>

      {detailConversation ? (
        <div className="plugin-popup-overlay" role="dialog" aria-modal="true" aria-label="Modal: Chat-Details" onClick={() => setDetailConversationId(null)}>
          <div
            className="plugin-popup"
            onClick={(event) => event.stopPropagation()}
            onKeyDown={(event) => {
              if (event.key === "Escape") {
                event.preventDefault();
                setDetailConversationId(null);
                return;
              }
              handleModalFocusTrap(event);
            }}
            tabIndex={-1}
          >
            <div className="plugin-popup__header">
              <div>
                <strong>{detailConversation.title}</strong>
                <span>Chat · ID {detailConversation.id}</span>
              </div>
              <div className="model-settings-card__actions">
                <button
                  type="button"
                  className="ghost-btn"
                  autoFocus
                  onClick={() => {
                    onSelectChat(detailConversation.id);
                    setDetailConversationId(null);
                  }}
                >
                  Oeffnen
                </button>
                <button type="button" className="ghost-btn" onClick={() => setDetailConversationId(null)}>
                  Schliessen
                </button>
              </div>
            </div>
            <div className="plugin-popup__body">
              <article className="page-card model-settings-card">
                <div className="model-settings-meta">
                  <span>Sichtbarkeit: {conversationVisibilityMap[detailConversation.id] ?? "internal"}</span>
                  <span>Projekt: {detailConversation.projectId == null ? "Kein Projekt" : buildProjectDisplayName(detailConversation.projectId)}</span>
                  <span>Besitzer: {detailConversation.ownerUserId ?? "-"}</span>
                </div>

                <div className="model-profile-grid">
                  <label className="model-profile-field">
                    <span>Umbenennen</span>
                    <input type="text" value={renameDraft} onChange={(event) => setRenameDraft(event.target.value)} />
                  </label>
                  <label className="model-profile-field">
                    <span>Sichtbarkeit</span>
                    <select value={visibilityDraft} onChange={(event) => setVisibilityDraft(event.target.value as "private" | "internal" | "public") }>
                      <option value="private">Privat</option>
                      <option value="internal">Intern</option>
                      <option value="public">Oeffentlich</option>
                    </select>
                  </label>
                  <label className="model-profile-field">
                    <span>Projektzuordnung</span>
                    <select value={projectDraft} onChange={(event) => setProjectDraft(event.target.value)}>
                      <option value="none">Kein Projekt</option>
                      {projects.map((project) => (
                        <option key={project.id} value={String(project.id)}>
                          {buildProjectDisplayName(project.id)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="model-profile-field">
                    <span>In Unterchat verschieben</span>
                    <select value={moveTargetId} onChange={(event) => setMoveTargetId(event.target.value)}>
                      <option value="root">Hauptebene</option>
                      {conversations.filter((entry) => entry.id !== detailConversation.id).map((entry) => (
                        <option key={entry.id} value={String(entry.id)}>{entry.title}</option>
                      ))}
                    </select>
                  </label>
                </div>

                <div className="model-settings-card__actions">
                  <button type="button" className="ghost-btn" onClick={() => onRenameConversation(detailConversation.id, renameDraft)}>
                    Namen speichern
                  </button>
                  <button type="button" className="ghost-btn" onClick={() => onSetConversationVisibility(detailConversation.id, visibilityDraft)}>
                    Sichtbarkeit speichern
                  </button>
                  <button type="button" className="ghost-btn" onClick={() => onAssignConversationProject(detailConversation.id, projectDraft === "none" ? null : Number(projectDraft))}>
                    Projekt speichern
                  </button>
                  <button
                    type="button"
                    className="ghost-btn"
                    onClick={() => {
                      const nextParent = moveTargetId === "root" ? null : Number(moveTargetId);
                      onMoveConversation(detailConversation.id, Number.isInteger(nextParent as number) ? nextParent : null);
                    }}
                  >
                    Verschieben
                  </button>
                  <button
                    type="button"
                    className="action-btn action-btn--danger"
                    disabled={detailConversation.ownerUserId !== currentUserId}
                    onClick={() => {
                      if (detailConversation.ownerUserId !== currentUserId) {
                        return;
                      }
                      const accepted = window.confirm(`Chat \"${detailConversation.title}\" wirklich loeschen?`);
                      if (!accepted) {
                        return;
                      }
                      onDeleteConversation(detailConversation.id);
                      setDetailConversationId(null);
                    }}
                  >
                    Loeschen
                  </button>
                </div>
              </article>
            </div>
          </div>
        </div>
      ) : null}
    </aside>
  );
}
