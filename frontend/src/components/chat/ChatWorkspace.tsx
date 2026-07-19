import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import ReactMarkdown from "react-markdown";

import type { ChatMessage, SendWorkflowState } from "../../types/api";
import { detectSpeechActivity, downloadBusinessLetterArtifact, getSpeechModels, synthesizeSpeech, transcribeSpeech, type SpeechModel } from "../../services/backend";

type BusinessLetterResultAction = {
  kind: string;
  label: string;
  file_name?: string;
  document_id?: string;
  tenant_id?: string;
};

type BusinessLetterResultMarker = {
  plugin: "business_letter";
  documentId: string;
  tenantId?: string;
  documentType?: string;
  status?: string;
  actions: BusinessLetterResultAction[];
};

type ParsedMessageContent = {
  markdown: string;
  businessLetterResult: BusinessLetterResultMarker | null;
};

const BUSINESS_LETTER_RESULT_PATTERN = /\[\[business_letter_result:(\{[\s\S]*?\})\]\]/;

function parseStructuredMessageContent(content: string): ParsedMessageContent {
  const text = String(content || "");
  const match = text.match(BUSINESS_LETTER_RESULT_PATTERN);
  if (!match) {
    return { markdown: text, businessLetterResult: null };
  }

  let parsed: BusinessLetterResultMarker | null = null;
  try {
    const candidate = JSON.parse(match[1]) as Partial<BusinessLetterResultMarker>;
    if (
      candidate &&
      candidate.plugin === "business_letter" &&
      typeof candidate.documentId === "string" &&
      Array.isArray(candidate.actions)
    ) {
      parsed = {
        plugin: "business_letter",
        documentId: candidate.documentId,
        tenantId: typeof candidate.tenantId === "string" ? candidate.tenantId : "",
        documentType: typeof candidate.documentType === "string" ? candidate.documentType : "",
        status: typeof candidate.status === "string" ? candidate.status : "",
        actions: candidate.actions
          .filter((item): item is BusinessLetterResultAction => typeof item === "object" && item != null && typeof item.kind === "string" && typeof item.label === "string")
          .map((item) => ({
            kind: item.kind,
            label: item.label,
            file_name: typeof item.file_name === "string" ? item.file_name : "",
            document_id: typeof item.document_id === "string" ? item.document_id : candidate.documentId,
            tenant_id: typeof item.tenant_id === "string" ? item.tenant_id : (typeof candidate.tenantId === "string" ? candidate.tenantId : ""),
          })),
      };
    }
  } catch {
    parsed = null;
  }

  const markdown = text.replace(BUSINESS_LETTER_RESULT_PATTERN, "").trim();
  return { markdown, businessLetterResult: parsed };
}

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
  modelEntries: Array<{
    id: string;
    name: string;
    loaded: boolean;
    category: "lokal" | "remote" | "ollama_local" | "ollama_cloud";
  }>;
  sources: Array<{ id: number; file: string; position: string; relevance: string }>;
  selectedModelId: string;
  modelLoaded: boolean;
  sendState: SendWorkflowState;
  sendError: string | null;
  liveReasoning: string;
  showReasoningBubble: boolean;
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
  liveReasoning,
  showReasoningBubble,
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
}: ChatWorkspaceProps) {
  const [draft, setDraft] = useState("");
  const [selectedImages, setSelectedImages] = useState<OutgoingImageAttachment[]>([]);
  const [speechModels, setSpeechModels] = useState<SpeechModel[]>([]);
  const [speechOpen, setSpeechOpen] = useState(false);
  const [speechBusy, setSpeechBusy] = useState(false);
  const [speechError, setSpeechError] = useState<string | null>(null);
  const [sttModelId, setSttModelId] = useState(0);
  const [ttsModelId, setTtsModelId] = useState(0);
  const [vadModelId, setVadModelId] = useState(0);
  const [vadEnabled, setVadEnabled] = useState(true);
  const [vadThreshold, setVadThreshold] = useState(0.5);
  const [speechLanguage, setSpeechLanguage] = useState("auto");
  const [speechDevice, setSpeechDevice] = useState("auto");
  const [sttTask, setSttTask] = useState("transcribe");
  const [timestamps, setTimestamps] = useState(false);
  const [chunkLength, setChunkLength] = useState(30);
  const [strideLength, setStrideLength] = useState(5);
  const [ttsSpeed, setTtsSpeed] = useState(1);
  const [ttsSpeaker, setTtsSpeaker] = useState("");
  const recorderRef = useRef<MediaRecorder | null>(null);
  const recordingChunksRef = useRef<Blob[]>([]);
  const [recording, setRecording] = useState(false);
  const [artifactDownloadKey, setArtifactDownloadKey] = useState<string | null>(null);
  const [artifactDownloadError, setArtifactDownloadError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const imageInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    void getSpeechModels().then((items) => {
      setSpeechModels(items);
      setSttModelId((current) => current || items.find((item) => item.task === "speech_to_text")?.id || 0);
      setTtsModelId((current) => current || items.find((item) => item.task === "text_to_speech")?.id || 0);
      setVadModelId((current) => current || items.find((item) => item.task === "voice_activity_detection")?.id || 0);
    }).catch(() => setSpeechModels([]));
  }, []);

  const sttModels = speechModels.filter((item) => item.task === "speech_to_text");
  const ttsModels = speechModels.filter((item) => item.task === "text_to_speech");
  const vadModels = speechModels.filter((item) => item.task === "voice_activity_detection");
  const activeStt = sttModels.find((item) => item.id === sttModelId);
  const activeTts = ttsModels.find((item) => item.id === ttsModelId);

  const toggleRecording = async () => {
    if (recording && recorderRef.current) {
      recorderRef.current.stop();
      return;
    }
    if (!sttModelId) { setSpeechOpen(true); setSpeechError("Kein STT-Modell gefunden. Bitte Modelle scannen."); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
      const recorder = new MediaRecorder(stream);
      recordingChunksRef.current = [];
      recorder.ondataavailable = (event) => { if (event.data.size) recordingChunksRef.current.push(event.data); };
      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop()); setRecording(false); setSpeechBusy(true); setSpeechError(null);
        try {
          const recordedBlob = new Blob(recordingChunksRef.current, { type: recorder.mimeType });
          if (vadEnabled && vadModelId) {
            const vadResult = await detectSpeechActivity({ modelId: vadModelId, audio: recordedBlob, threshold: vadThreshold, device: speechDevice });
            if (!vadResult.speaking) {
              setSpeechError("VAD: Keine Sprachaktivitaet erkannt. Bitte erneut aufnehmen.");
              return;
            }
          }
          const result = await transcribeSpeech({
            modelId: sttModelId,
            audio: recordedBlob,
            language: speechLanguage,
            task: sttTask,
            timestamps,
            chunkLength,
            strideLength,
            device: speechDevice,
            vadEnabled,
            vadModelId,
            vadThreshold,
          });
          setDraft((current) => `${current}${current && result.text ? " " : ""}${result.text}`);
        } catch (error) { setSpeechError(error instanceof Error ? error.message : String(error)); }
        finally { setSpeechBusy(false); }
      };
      recorder.start(250); recorderRef.current = recorder; setRecording(true);
    } catch (error) { setSpeechError(error instanceof Error ? error.message : String(error)); }
  };

  const speakText = async (text: string) => {
    if (!ttsModelId || !text.trim()) { setSpeechOpen(true); setSpeechError("Kein TTS-Modell gefunden."); return; }
    setSpeechBusy(true); setSpeechError(null);
    try {
      const blob = await synthesizeSpeech({ modelId: ttsModelId, text, language: speechLanguage, speaker: ttsSpeaker, speed: ttsSpeed, device: speechDevice });
      const url = URL.createObjectURL(blob); const audio = new Audio(url);
      audio.onended = () => URL.revokeObjectURL(url); await audio.play();
    } catch (error) { setSpeechError(error instanceof Error ? error.message : String(error)); }
    finally { setSpeechBusy(false); }
  };
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
    return {
      local: modelEntries.filter((model) => model.category === "lokal"),
      ollamaLocal: modelEntries.filter((model) => model.category === "ollama_local"),
      ollamaCloud: modelEntries.filter((model) => model.category === "ollama_cloud"),
      remote: modelEntries.filter((model) => model.category === "remote"),
    };
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

  const downloadArtifact = async (messageId: number, result: BusinessLetterResultMarker, action: BusinessLetterResultAction) => {
    const downloadKey = `${messageId}:${action.kind}`;
    setArtifactDownloadKey(downloadKey);
    setArtifactDownloadError(null);
    try {
      const { blob, fileName } = await downloadBusinessLetterArtifact(result.documentId, action.kind, action.tenant_id || result.tenantId || undefined);
      const href = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = href;
      anchor.download = fileName || action.file_name || `${result.documentId}.${action.kind}`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(href);
    } catch (error) {
      setArtifactDownloadError(error instanceof Error ? error.message : String(error));
    } finally {
      setArtifactDownloadKey((current) => (current === downloadKey ? null : current));
    }
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
        reasoningStatus: "Thinking...",
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
        reasoningStatus: "Denkt...",
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
              {groupedModels.local.length > 0 ? (
                <optgroup label="Lokal">
                  {groupedModels.local.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.loaded ? "● " : "○ "}
                      {model.name}
                    </option>
                  ))}
                </optgroup>
              ) : null}
              {groupedModels.ollamaLocal.length > 0 ? (
                <optgroup label="Ollama Local">
                  {groupedModels.ollamaLocal.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.loaded ? "● " : "○ "}
                      {model.name}
                    </option>
                  ))}
                </optgroup>
              ) : null}
              {groupedModels.ollamaCloud.length > 0 ? (
                <optgroup label="Ollama Cloud">
                  {groupedModels.ollamaCloud.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.loaded ? "● " : "○ "}
                      {model.name}
                    </option>
                  ))}
                </optgroup>
              ) : null}
              {groupedModels.remote.length > 0 ? (
                <optgroup label="Remote">
                  {groupedModels.remote.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.loaded ? "● " : "○ "}
                      {model.name}
                    </option>
                  ))}
                </optgroup>
              ) : null}
            </select>
          </label>
          <button type="button" className="ghost-btn" onClick={onOpenRightPanel} title="Kontext, Quellen und Werkzeuge anzeigen">
            {ui.context}
          </button>

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
            {(() => {
              const parsedContent = parseStructuredMessageContent(message.content);
              return (
                <>
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
              <ReactMarkdown>{parsedContent.markdown}</ReactMarkdown>
            </div>

            {message.role === "assistant" && parsedContent.businessLetterResult ? (
              <section className="message-result-card" aria-label="Dokument-Ergebnis">
                <div className="message-result-card__head">
                  <strong>{parsedContent.businessLetterResult.documentType || "Dokument"}</strong>
                  {parsedContent.businessLetterResult.status ? <span>{parsedContent.businessLetterResult.status}</span> : null}
                </div>
                <div className="message-result-card__actions">
                  {parsedContent.businessLetterResult.actions.map((action) => {
                    const actionKey = `${message.id}:${action.kind}`;
                    return (
                      <button
                        key={actionKey}
                        type="button"
                        className="message-result-card__action"
                        disabled={artifactDownloadKey === actionKey}
                        onClick={() => void downloadArtifact(message.id, parsedContent.businessLetterResult as BusinessLetterResultMarker, action)}
                        title={action.file_name || action.label}
                      >
                        {artifactDownloadKey === actionKey ? `${action.label} wird geladen` : `${action.label} herunterladen`}
                      </button>
                    );
                  })}
                </div>
                {artifactDownloadError ? <div className="message-result-card__error">{artifactDownloadError}</div> : null}
              </section>
            ) : null}

            {message.role === "assistant" && ttsModels.length > 0 ? (
              <button type="button" className="message-speak-btn" disabled={speechBusy} onClick={() => void speakText(message.content)} title="Antwort vorlesen">🔊 Vorlesen</button>
            ) : null}

            {message.role === "assistant" && sourceFootnotes.length > 0 ? (
              <div className="message__sources">
                {sourceFootnotes.map((source) => (
                  <button key={source.id} type="button" className="source-link" onClick={() => onOpenSource(source.id)}>
                    {source.label}
                  </button>
                ))}
              </div>
            ) : null}
                </>
              );
            })()}
          </article>
        ))}

        {showReasoningBubble ? (
          <article className="message message--assistant message--reasoning" aria-live="polite">
            <header className="message__head">
              <strong className="message__author">{assistantDisplayName}</strong>
              <span className="message__reasoning_hint">{ui.reasoningStatus}</span>
            </header>
            <div className="message__body message__body--reasoning">{liveReasoning}</div>
          </article>
        ) : null}
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
              <button type="button" className={`icon-btn ${recording ? "speech-recording" : ""}`} aria-label={recording ? "Aufnahme stoppen" : "Spracheingabe"} disabled={speechBusy} onClick={() => void toggleRecording()} title="Sprache aufnehmen und transkribieren">
                {recording ? "⏹" : "🎙"}
              </button>
              <button type="button" className="icon-btn" aria-label="Spracheinstellungen" onClick={() => setSpeechOpen((value) => !value)} title="STT/TTS-Einstellungen">⚙️</button>
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

        {speechOpen ? (
          <section className="speech-settings" aria-label="Spracheinstellungen">
            <div className="speech-settings__head"><strong>Sprache · STT, TTS & VAD</strong><button type="button" className="ghost-btn" onClick={() => setSpeechOpen(false)}>Schließen</button></div>
            {speechError ? <div className="composer-error" role="alert">{speechError}</div> : null}
            <div className="speech-settings__grid">
              <label>STT-Modell<select value={sttModelId} onChange={(e) => setSttModelId(Number(e.target.value))}><option value={0}>Nicht verfügbar</option>{sttModels.map((m) => <option key={m.id} value={m.id}>{m.name} · {m.family}</option>)}</select></label>
              <label>TTS-Modell<select value={ttsModelId} onChange={(e) => { setTtsModelId(Number(e.target.value)); setTtsSpeaker(""); }}><option value={0}>Nicht verfügbar</option>{ttsModels.map((m) => <option key={m.id} value={m.id}>{m.name} · {m.family}</option>)}</select></label>
              <label>VAD-Modell<select value={vadModelId} onChange={(e) => setVadModelId(Number(e.target.value))}><option value={0}>Nicht verfügbar</option>{vadModels.map((m) => <option key={m.id} value={m.id}>{m.name} · {m.family}</option>)}</select></label>
              <label>Sprache<select value={speechLanguage} onChange={(e) => setSpeechLanguage(e.target.value)}>{(activeStt?.settings.languages ?? activeTts?.settings.languages ?? ["auto"]).map((v) => <option key={v}>{v}</option>)}</select></label>
              <label>Gerät<select value={speechDevice} onChange={(e) => setSpeechDevice(e.target.value)}><option value="auto">Automatisch</option><option value="cuda">GPU</option><option value="cpu">CPU</option></select></label>
              <label>STT-Aufgabe<select value={sttTask} onChange={(e) => setSttTask(e.target.value)}>{(activeStt?.settings.tasks ?? ["transcribe"]).map((value) => <option key={value} value={value}>{value === "translate" ? "Nach Englisch übersetzen" : "Transkribieren"}</option>)}</select></label>
              <label>Chunk (Sek.)<input type="number" min="5" max="120" value={chunkLength} onChange={(e) => setChunkLength(Number(e.target.value))} /></label>
              <label>Überlappung (Sek.)<input type="number" min="0" max="30" value={strideLength} onChange={(e) => setStrideLength(Number(e.target.value))} /></label>
              <label>TTS-Tempo<input type="range" min="0.5" max="2" step="0.05" value={ttsSpeed} onChange={(e) => setTtsSpeed(Number(e.target.value))} /><span>{ttsSpeed.toFixed(2)}×</span></label>
              {activeTts?.settings.speakers.length ? <label>Stimme<select value={ttsSpeaker} onChange={(e) => setTtsSpeaker(e.target.value)}><option value="">Standard</option>{activeTts.settings.speakers.map((v) => <option key={v}>{v}</option>)}</select></label> : null}
              <label className="speech-check"><input type="checkbox" checked={vadEnabled} onChange={(e) => setVadEnabled(e.target.checked)} /> VAD vor STT nutzen</label>
              <label>VAD-Schwelle<input type="range" min="0.3" max="0.9" step="0.05" value={vadThreshold} onChange={(e) => setVadThreshold(Number(e.target.value))} /><span>{vadThreshold.toFixed(2)}</span></label>
              <label className="speech-check"><input type="checkbox" checked={timestamps} onChange={(e) => setTimestamps(e.target.checked)} /> Zeitstempel erfassen</label>
            </div>
            <small>{speechModels.length ? `${sttModels.length} STT-, ${ttsModels.length} TTS- und ${vadModels.length} VAD-Modell(e) erkannt.` : "Keine Sprachmodelle erkannt. Modellverzeichnis prüfen und Scan ausführen."}</small>
          </section>
        ) : null}

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
