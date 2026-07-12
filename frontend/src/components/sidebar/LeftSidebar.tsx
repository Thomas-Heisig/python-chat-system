import { useMemo, useState } from "react";
import type { ConversationSummary } from "../../types/api";

type LeftSidebarProps = {
  collapsed: boolean;
  activeNav: "Chats" | "Suche" | "Projekte" | "Bibliothek" | "Termine" | "Plugins" | "Einstellungen";
  selectedConversationId: number | null;
  conversations: ConversationSummary[];
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

export function LeftSidebar({
  collapsed,
  activeNav,
  selectedConversationId,
  conversations,
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
  onMoveConversation,
  onRenameConversation,
  onSetConversationVisibility,
  onDeleteConversation,
  onNewConversation,
  onLogout,
}: LeftSidebarProps) {
  const [draggedConversationId, setDraggedConversationId] = useState<number | null>(null);
  const [menuConversationId, setMenuConversationId] = useState<number | null>(null);
  const [renameDraft, setRenameDraft] = useState("");
  const [moveTargetId, setMoveTargetId] = useState<string>("root");
  const [visibilityDraft, setVisibilityDraft] = useState<"private" | "internal" | "public">("internal");
  const userInitials = useMemo(() => {
    const cleaned = currentUsername.trim();
    if (!cleaned) {
      return "U";
    }
    return cleaned.slice(0, 2).toUpperCase();
  }, [currentUsername]);

  const conversationById = useMemo(() => {
    const map = new Map<number, ConversationSummary>();
    conversations.forEach((conversation) => map.set(conversation.id, conversation));
    return map;
  }, [conversations]);

  const childrenByParent = useMemo(() => {
    const map = new Map<number | null, ConversationSummary[]>();
    const addToParent = (parentId: number | null, conversation: ConversationSummary) => {
      const bucket = map.get(parentId) ?? [];
      bucket.push(conversation);
      map.set(parentId, bucket);
    };

    conversations.forEach((conversation) => {
      const parentId = conversationTree[conversation.id] ?? null;
      if (parentId != null && !conversationById.has(parentId)) {
        addToParent(null, conversation);
        return;
      }
      addToParent(parentId, conversation);
    });

    return map;
  }, [conversationTree, conversationById, conversations]);

  const renderConversationNode = (conversation: ConversationSummary, depth: number) => {
    const children = childrenByParent.get(conversation.id) ?? [];

    return (
      <div key={conversation.id} className="chat-tree-node">
        <div
          className={`chat-row chat-row--depth-${Math.min(depth, 4)}`}
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

  const rootConversations = childrenByParent.get(null) ?? [];
  const ui = language === "en"
    ? {
        navigation: "Navigation",
        search: "Search",
        newConversation: "New conversation",
        chats: "Chats",
        conversations: "Conversations",
        noConversations: "No conversations yet",
        nextAppointments: "Next appointments",
        logout: "Logout",
      }
    : {
        navigation: "Navigation",
        search: "Suchen",
        newConversation: "Neue Konversation",
        chats: "Chats",
        conversations: "Konversationen",
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
            <h3 className="chat-group__title label">{ui.conversations}</h3>
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
            <div className="chat-list">
              {rootConversations.map((conversation) => renderConversationNode(conversation, 0))}
              {rootConversations.length === 0 ? <span className="empty-note">{ui.noConversations}</span> : null}
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
    </aside>
  );
}
