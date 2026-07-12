import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import ReactMarkdown from "react-markdown";

import type { ChatMessage, SendWorkflowState } from "../../types/api";

type OutgoingImageAttachment = {
  name: string;
  mimeType: string;
  file: File;
};

type OutgoingChatPayload = {
  message: string;
  images: OutgoingImageAttachment[];
};

type ChatWorkspaceProps = {
  chatTitle: string;
  currentUsername: string;
  assistantDisplayName: string;
  collaboratorUsername: string | null;
  hasOtherUserInConversation: boolean;
  aiParticipationEnabled: boolean;
  messages: ChatMessage[];
  modelEntries: Array<{ id: string; name: string; loaded: boolean; category: "lokal" | "remote" }>;
  sources: Array<{ id: number; file: string; position: string; relevance: string }>;
  selectedModelId: string;
  modelLoaded: boolean;
  sendState: SendWorkflowState;
  sendError: string | null;
  locale: string;
  timezone: string;
  language: "de" | "en";
  onChangeModel: (modelId: string) => void;
  onSendMessage: (payload: OutgoingChatPayload) => Promise<void>;
  onStopMessage: () => void;
  onRetryLastMessage: () => Promise<void>;
  onOpenRightPanel: () => void;
  onToggleAiParticipation: (enabled: boolean) => void;
  onOpenSource: (sourceId: number) => void;
  projects: Array<{ id: number; name: string }>;
  selectedProjectId: number | null;
  canAssignProject: boolean;
  onAssignProject: (projectId: number | null) => void;
};

export function ChatWorkspace({
  chatTitle,
  currentUsername,
  assistantDisplayName,
  collaboratorUsername,
  hasOtherUserInConversation,
  aiParticipationEnabled,
  modelEntries,
  messages,
  sources,
  selectedModelId,
  modelLoaded,
  sendState,
  sendError,
  locale,
  timezone,
  language,
  onChangeModel,
  onSendMessage,
  onStopMessage,
  onRetryLastMessage,
  onOpenRightPanel,
  onToggleAiParticipation,
  onOpenSource,
  projects,
  selectedProjectId,
  canAssignProject,
  onAssignProject,
}: ChatWorkspaceProps) {
  const [draft, setDraft] = useState("");
  const [selectedImages, setSelectedImages] = useState<OutgoingImageAttachment[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const imageInputRef = useRef<HTMLInputElement | null>(null);
  const hasModelSelection = selectedModelId.trim().length > 0;
  const canSend =
    hasModelSelection &&
    (draft.trim().length > 0 || selectedImages.length > 0) &&
    sendState !== "submitting" &&
    sendState !== "stopping";
  const isBusy = sendState === "submitting" || sendState === "streaming" || sendState === "stopping";
  const isDisabledState = sendState === "disabled" || !hasModelSelection;
  const isActionDisabled =
    sendState === "submitting" || sendState === "stopping" || (sendState !== "streaming" && !canSend);

  const groupedModels = useMemo(() => {
    const local = modelEntries.filter((model) => model.category === "lokal");
    const remote = modelEntries.filter((model) => model.category === "remote");
    return { local, remote };
  }, [modelEntries]);

  const sourceFootnotes = useMemo(
    () =>
      sources.map((source, index) => ({
        id: source.id,
        label: `[${index + 1}] ${source.file}, ${source.position}`,
      })),
    [sources],
  );

  const colorVariantForName = (name: string) => {
    let hash = 0;
    for (let index = 0; index < name.length; index += 1) {
      hash = (hash * 31 + name.charCodeAt(index)) % 97;
    }
    return hash % 6;
  };

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) {
      return;
    }

    textarea.style.height = "auto";
    const nextHeight = Math.max(86, Math.min(220, textarea.scrollHeight));
    textarea.style.height = `${nextHeight}px`;
  }, [draft]);

  const submitMessage = async () => {
    if (!canSend) {
      return;
    }
    const nextMessage = draft;
    const nextImages = selectedImages;
    setDraft("");
    setSelectedImages([]);
    await onSendMessage({ message: nextMessage, images: nextImages });
  };

  const handleComposerKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canSend) {
        void submitMessage();
      }
    }
  };

  const appendAttachmentToDraft = (files: FileList | null) => {
    if (!files || files.length === 0) {
      return;
    }

    const labels = Array.from(files).map((file) => `[datei: ${file.name}]`);
    setDraft((current) => `${current}${current.length > 0 ? "\n" : ""}${labels.join(" ")}`);
  };

  const appendImageAttachments = (files: FileList | null) => {
    if (!files || files.length === 0) {
      return;
    }

    const incoming = Array.from(files).map((file) => ({
      name: file.name,
      mimeType: file.type || "image/jpeg",
      file,
    }));

    setSelectedImages((current) => {
      const existingKeys = new Set(current.map((item) => `${item.name}:${item.file.size}:${item.file.lastModified}`));
      const merged = [...current];
      for (const item of incoming) {
        const key = `${item.name}:${item.file.size}:${item.file.lastModified}`;
        if (existingKeys.has(key)) {
          continue;
        }
        existingKeys.add(key);
        merged.push(item);
      }
      return merged;
    });
  };

  const buttonLabel = (() => {
    if (language === "en") {
      if (sendState === "stopping") return "Stopping...";
      if (sendState === "submitting") return "Sending...";
      if (sendState === "streaming") return "■ Stop";
      if (sendState === "success") return "Sent";
      if (sendState === "error") return "Retry send";
      return "Send";
    }
    if (sendState === "stopping") return "Stoppt...";
    if (sendState === "submitting") return "Sendet...";
    if (sendState === "streaming") return "■ Stoppen";
    if (sendState === "success") return "Gesendet";
    if (sendState === "error") return "Erneut senden";
    return "Senden";
  })();

  const ui = language === "en"
    ? {
        modelSelect: "Select model",
        context: "Context",
        projectSelect: "Project for this chat",
        aiToggle: "AI participates",
        noModel: "No model selected. Please choose a model in the chat header.",
        inputPlaceholder: "Type a message ...",
        inputLabel: "Type message",
        clearInput: "Clear input",
        sendTitle: "Send message",
        stopTitle: "Stop generation",
        retry: "Retry",
      }
    : {
        modelSelect: "Modell waehlen",
        context: "Kontext",
        projectSelect: "Projekt fuer diesen Chat",
        aiToggle: "KI redet mit",
        noModel: "Kein Modell ausgewaehlt. Bitte waehle im Chat-Header ein Modell aus.",
        inputPlaceholder: "Nachricht eingeben ...",
        inputLabel: "Nachricht eingeben",
        clearInput: "Eingabe loeschen",
        sendTitle: "Nachricht senden",
        stopTitle: "Antwortgenerierung stoppen",
        retry: "Retry",
      };

  const content = (
    <>
      <header className="chat-header">
        <div>
          <h1 className="chat-title">{chatTitle}</h1>
          <p className="meta-line">Projektzuordnung fuer diesen Chat</p>
        </div>

        <div className="chat-meta">
          <label className="model-select-wrap">
            <span className="sr-only">Modell waehlen</span>
            <select
              className="model-select"
              value={selectedModelId}
              onChange={(event) => onChangeModel(event.target.value)}
              aria-label={ui.modelSelect}
            >
              <optgroup label="Lokal">
                {groupedModels.local.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.loaded ? "● " : "○ "}
                    {model.name}
                  </option>
                ))}
              </optgroup>
              <optgroup label="Remote">
                {groupedModels.remote.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.loaded ? "● " : "○ "}
                    {model.name}
                  </option>
                ))}
              </optgroup>
            </select>
          </label>
          <button type="button" className="ghost-btn" onClick={onOpenRightPanel} title="Kontext, Quellen und Werkzeuge anzeigen">
            {ui.context}
          </button>

          <label className="model-select-wrap">
            <span className="sr-only">Projekt waehlen</span>
            <select
              className="model-select"
              value={selectedProjectId == null ? "none" : String(selectedProjectId)}
              disabled={!canAssignProject}
              onChange={(event) => {
                const value = event.target.value;
                onAssignProject(value === "none" ? null : Number(value));
              }}
              aria-label={ui.projectSelect}
              title={canAssignProject ? "Projekt fuer diesen Chat" : "Nur fuer eigene Chats bearbeitbar"}
            >
              <option value="none">Kein Projekt</option>
              {projects.map((project) => (
                <option key={project.id} value={String(project.id)}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>

          <label className="ai-participation-toggle" title={hasOtherUserInConversation ? "KI Teilnahme im Teamchat" : "Wird aktiv, sobald eine weitere Person im Chat ist"}>
            <input
              type="checkbox"
              checked={aiParticipationEnabled}
              onChange={(event) => onToggleAiParticipation(event.target.checked)}
              disabled={!hasOtherUserInConversation}
            />
            <span>{ui.aiToggle}</span>
          </label>
        </div>
      </header>

      {hasOtherUserInConversation && collaboratorUsername ? (
        <div className="chat-collab-hint" role="status" aria-live="polite">
          Weitere Person im Chat: <strong>{collaboratorUsername}</strong>
        </div>
      ) : null}

      <div className="message-list">
        {messages.map((message) => (
          <article key={message.id} className={`message message--${message.role}`}>
            <header className="message__head">
              <strong
                className={`message__author ${
                  message.role === "user"
                    ? `message__author--variant-${colorVariantForName(message.authorUsername ?? currentUsername)}`
                    : ""
                }`}
              >
                {message.role === "user" ? message.authorUsername ?? currentUsername : assistantDisplayName}
              </strong>
              <span>{new Date(message.createdAt).toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit", timeZone: timezone })}</span>
            </header>

            <div className="message__body">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>

            {message.role === "assistant" && sourceFootnotes.length > 0 ? (
              <div className="message__sources">
                {sourceFootnotes.map((source) => (
                  <button key={source.id} type="button" className="source-link" onClick={() => onOpenSource(source.id)}>
                    {source.label}
                  </button>
                ))}
              </div>
            ) : null}
          </article>
        ))}
      </div>

      <div className="composer">
        {!hasModelSelection ? (
          <div className="composer-error" role="alert">
            {ui.noModel}
          </div>
        ) : null}

        {sendError ? (
          <div className="composer-error" role="alert">
            {sendError}
          </div>
        ) : null}

        <div className="sr-only" role="status" aria-live="polite">
          {sendState === "submitting" ? "Nachricht wird gesendet" : null}
          {sendState === "streaming" ? "Antwort wird generiert" : null}
          {sendState === "error" ? "Fehler beim Senden" : null}
          {sendState === "success" ? "Nachricht erfolgreich gesendet" : null}
        </div>

        <div className="composer__box">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="sr-only"
            aria-label="Dateien auswaehlen"
            title="Dateien auswaehlen"
            onChange={(event) => {
              appendAttachmentToDraft(event.target.files);
              event.currentTarget.value = "";
            }}
          />
          <input
            ref={imageInputRef}
            type="file"
            accept="image/*"
            multiple
            className="sr-only"
            aria-label="Bilder auswaehlen"
            title="Bilder auswaehlen"
            onChange={(event) => {
              appendImageAttachments(event.target.files);
              event.currentTarget.value = "";
            }}
          />

          <textarea
            ref={textareaRef}
            placeholder={ui.inputPlaceholder}
            aria-label={ui.inputLabel}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={handleComposerKeyDown}
            disabled={isDisabledState || isBusy}
          />

          <div className="composer__bar">
            <div className="composer__tools">
              <button
                type="button"
                className="icon-btn"
                aria-label="Datei anhängen"
                onClick={() => fileInputRef.current?.click()}
                title="Datei(en) anhaengen"
              >
                📎
              </button>
              <button
                type="button"
                className="icon-btn"
                aria-label="Bild anhängen"
                onClick={() => imageInputRef.current?.click()}
                title="Bild(er) anhaengen"
              >
                🖼
              </button>
              <button
                type="button"
                className="icon-btn"
                aria-label="Werkzeuge"
                onClick={onOpenRightPanel}
                title="Werkzeug- und Kontextpanel oeffnen"
              >
                🔧
              </button>
            </div>

            <div className="composer__send">
              <span className="status-chip">Kontext: 3.420 / 8.192</span>

              {draft.length > 0 ? (
                <button
                  type="button"
                  className="ghost-btn"
                  onClick={() => setDraft("")}
                  aria-label={ui.clearInput}
                  title={ui.clearInput}
                >
                  ✕
                </button>
              ) : null}

              <button
                type="button"
                className="action-btn action-btn--primary action-btn--send"
                onClick={sendState === "streaming" ? onStopMessage : () => void submitMessage()}
                disabled={isActionDisabled}
                title={sendState === "streaming" ? ui.stopTitle : ui.sendTitle}
              >
                {buttonLabel}
              </button>

              {sendState === "error" ? (
                <button type="button" className="ghost-btn" onClick={() => void onRetryLastMessage()} title="Letzte Nachricht erneut senden">
                  {ui.retry}
                </button>
              ) : null}
            </div>
          </div>
        </div>

        <div className="token-usage">Antwortlimit: 1.500 Token</div>
        {selectedImages.length > 0 ? (
          <div className="token-usage">Bilder angehaengt: {selectedImages.map((item) => item.name).join(", ")}</div>
        ) : null}
      </div>
    </>
  );

  if (isBusy) {
    return (
      <section className="chat-workspace" aria-label="Chatbereich" aria-busy="true">
        {content}
      </section>
    );
  }

  return (
    <section className="chat-workspace" aria-label="Chatbereich" aria-busy="false">
      {content}
    </section>
  );
}
