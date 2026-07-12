import { useEffect, useState, type ReactNode } from "react";
import type {
  AuthUser,
  TrainingDatasetFileEntry,
  TrainingDatasetSummary,
  TrainingJobSummary,
  TrainingTrainerOption,
  TrainingPreflightResult,
  UiModelEntry,
  WorkspaceAppointment,
  WorkspaceProject,
  WorkspaceSource,
} from "../../types/api";

type ModelProfileDraft = {
  systemPrompt: string;
  temperature: string;
  samplingTopK: string;
  maxNewTokens: string;
  topK: string;
  topP: string;
  repetitionPenalty: string;
  stopSequences: string;
  seed: string;
  doSample: boolean;
  preferGpu: boolean;
};

type TrainingSettingsDraft = {
  enabled: boolean;
  defaultTrainer: string;
  baseModel: string;
  artifactsDirectory: string;
  datasetsDirectory: string;
  maxConcurrentJobs: string;
  autoStartQueue: boolean;
  autoEvaluate: boolean;
  autoRegisterModel: boolean;
};

type GeneralSettingsDraft = {
  language: "de" | "en";
  theme: "system" | "light" | "dark";
  timezone: string;
};

type ChatSettingsDraft = {
  temperature: string;
  maxNewTokens: string;
  topP: string;
  topK: string;
  repetitionPenalty: string;
  doSample: boolean;
  seed: string;
  contextLimitTokens: string;
  contextSafetyMarginTokens: string;
};

type KnowledgeSettingsDraft = {
  topK: string;
  minScoreRatio: string;
  minAbsoluteScore: string;
  minScoreGap: string;
};

type LogsSettingsDraft = {
  logLevel: "DEBUG" | "INFO" | "WARNING" | "ERROR";
};

type WorkspacePageProps = {
  view: "Suche" | "Projekte" | "Bibliothek" | "Termine" | "Plugins" | "Einstellungen" | "Chats";
  projects: WorkspaceProject[];
  appointments: WorkspaceAppointment[];
  sources: WorkspaceSource[];
  modelEntries: UiModelEntry[];
  selectedModelId: string;
  modelLoaded: boolean;
  modelActionPending: boolean;
  modelDirectoryPending: boolean;
  modelProfilePending: boolean;
  generalSettingsPending: boolean;
  chatSettingsPending: boolean;
  knowledgeSettingsPending: boolean;
  logsSettingsPending: boolean;
  trainingSettingsPending: boolean;
  trainingPreflightPending: boolean;
  modelDirectories: string[];
  modelProfile: ModelProfileDraft;
  generalSettings: GeneralSettingsDraft;
  chatSettings: ChatSettingsDraft;
  knowledgeSettings: KnowledgeSettingsDraft;
  logsSettings: LogsSettingsDraft;
  trainingSettings: TrainingSettingsDraft;
  trainingPreflightResult: TrainingPreflightResult | null;
  trainingDatasetFiles: TrainingDatasetFileEntry[];
  trainingDatasets: TrainingDatasetSummary[];
  trainingJobs: TrainingJobSummary[];
  trainerOptions: TrainingTrainerOption[];
  trainingCompatibility: Record<string, { compatible: boolean; reason: string | null }>;
  onFetchTrainingCompatibility: (trainerName: string) => Promise<Record<string, { compatible: boolean; reason: string | null }>>;
  onActivateModel: (modelId: string) => Promise<void>;
  onDeactivateModel: () => Promise<void>;
  onScanModels: () => Promise<void>;
  onSetModelRelevance: (modelId: string, relevance: "favorite" | "irrelevant" | null) => Promise<void>;
  onSaveModelDirectories: (directories: string[]) => Promise<void>;
  onSaveModelProfile: (profile: ModelProfileDraft) => Promise<void>;
  onSaveGeneralSettings: (profile: GeneralSettingsDraft) => Promise<void>;
  onSaveChatSettings: (profile: ChatSettingsDraft) => Promise<void>;
  onSaveKnowledgeSettings: (profile: KnowledgeSettingsDraft) => Promise<void>;
  onSaveLogsSettings: (profile: LogsSettingsDraft) => Promise<void>;
  onSaveTrainingSettings: (profile: TrainingSettingsDraft) => Promise<void>;
  onCreateTrainingDataset: (name: string, projectId: number | null) => Promise<void>;
  onRegisterTrainingDatasetFile: (name: string, fileName: string, validationFileName: string | undefined, projectId: number | null) => Promise<void>;
  onUploadTrainingDataset: (name: string, sourceFile: File, validationFile: File | null, projectId: number | null) => Promise<void>;
  onImportTrainingDatasetFromUrl: (name: string, sourceUrl: string, validationSourceUrl: string | undefined, projectId: number | null) => Promise<void>;
  onCreateTrainingJob: (datasetId: number, baseModelId?: string, trainerName?: string) => Promise<void>;
  onRunTrainingPreflight: (datasetId: number, baseModelId?: string, trainerName?: string) => Promise<TrainingPreflightResult>;
  onCancelTrainingJob: (jobId: number) => Promise<void>;
  onRetryTrainingJob: (jobId: number) => Promise<void>;
  currentUser: AuthUser;
  onAdminCreateUser: (username: string, password: string, isAdmin: boolean) => Promise<void>;
  onExportDiagnosticsReport: () => Promise<void>;
  selectedProjectId: number | null;
  onSelectProject: (projectId: number | null) => void;
  onCreateProject: (name: string) => Promise<void>;
  onRenameProject: (projectId: number, name: string) => Promise<void>;
  onDeleteProject: (projectId: number) => Promise<void>;
  onUploadWorkspaceSource: (file: File) => Promise<void>;
};

const plugins = [
  { name: "Dateisystem", state: "aktiv", perms: "Dateizugriff" },
  { name: "Kalender", state: "aktiv", perms: "Kalender lesen/schreiben" },
  { name: "E-Mail", state: "deaktiviert", perms: "E-Mail Versand" },
];

const settingsGroups = [
  ["Allgemein", "Sprache, Theme, Zeitzone"],
  ["Darstellung", "Schriftgroesse, Sidebars, Animationen"],
  ["Chat", "Temperatur, System-Prompt, Token-Limits"],
  ["Modelle", "Aktives Modell, Backend, VRAM-Limit"],
  ["Modellverzeichnisse", "Pfade, Scan, Auto-Neuladen"],
  ["Training", "Trainer, Queue und Laufzeitverhalten"],
  ["Wissen", "Embedding-Modell, Chunk-Groesse, Top-K"],
  ["Prompts", "System-Prompts, benutzerdefinierte Prompts"],
  ["Plugins", "Installiert, Berechtigungen"],
  ["Benutzer", "Profil, Passwort, Teams"],
  ["Datenbank", "Status, Backup"],
  ["Logs", "Log-Level, Anzeige"],
  ["System", "Version, Systeminfos"],
] as const;

function PageFrame({ title, action, children }: { title: string; action?: string; children: ReactNode }) {
  return (
    <section className="page-view" aria-label={title}>
      <header className="page-view__header">
        <h1>{title}</h1>
        {action ? <button className="action-btn action-btn--primary">{action}</button> : null}
      </header>
      <div className="page-view__content">{children}</div>
    </section>
  );
}

export function WorkspacePage({
  view,
  projects,
  appointments,
  sources,
  modelEntries,
  selectedModelId,
  modelLoaded,
  modelActionPending,
  modelDirectoryPending,
  modelProfilePending,
  generalSettingsPending,
  chatSettingsPending,
  knowledgeSettingsPending,
  logsSettingsPending,
  trainingSettingsPending,
  trainingPreflightPending,
  modelDirectories,
  modelProfile,
  generalSettings,
  chatSettings,
  knowledgeSettings,
  logsSettings,
  trainingSettings,
  trainingPreflightResult,
  trainingDatasetFiles,
  trainingDatasets,
  trainingJobs,
  trainerOptions,
  trainingCompatibility,
  onFetchTrainingCompatibility,
  onActivateModel,
  onDeactivateModel,
  onScanModels,
  onSetModelRelevance,
  onSaveModelDirectories,
  onSaveModelProfile,
  onSaveGeneralSettings,
  onSaveChatSettings,
  onSaveKnowledgeSettings,
  onSaveLogsSettings,
  onSaveTrainingSettings,
  onCreateTrainingDataset,
  onRegisterTrainingDatasetFile,
  onUploadTrainingDataset,
  onImportTrainingDatasetFromUrl,
  onCreateTrainingJob,
  onRunTrainingPreflight,
  onCancelTrainingJob,
  onRetryTrainingJob,
  currentUser,
  onAdminCreateUser,
  onExportDiagnosticsReport,
  selectedProjectId,
  onSelectProject,
  onCreateProject,
  onRenameProject,
  onDeleteProject,
  onUploadWorkspaceSource,
}: WorkspacePageProps) {
  const [activeSettingsGroup, setActiveSettingsGroup] = useState<(typeof settingsGroups)[number][0]>("Allgemein");
  const [directoryDraft, setDirectoryDraft] = useState<string[]>(modelDirectories);
  const [newDirectory, setNewDirectory] = useState("");
  const [profileDraft, setProfileDraft] = useState<ModelProfileDraft>(modelProfile);
  const [generalDraft, setGeneralDraft] = useState<GeneralSettingsDraft>(generalSettings);
  const [chatDraft, setChatDraft] = useState<ChatSettingsDraft>(chatSettings);
  const [knowledgeDraft, setKnowledgeDraft] = useState<KnowledgeSettingsDraft>(knowledgeSettings);
  const [logsDraft, setLogsDraft] = useState<LogsSettingsDraft>(logsSettings);
  const [trainingDraft, setTrainingDraft] = useState<TrainingSettingsDraft>(trainingSettings);
  const [newDatasetName, setNewDatasetName] = useState("");
  const [newDatasetProjectId, setNewDatasetProjectId] = useState<string>("");
  const [existingDatasetFile, setExistingDatasetFile] = useState("");
  const [existingValidationFile, setExistingValidationFile] = useState("");
  const [uploadDatasetFile, setUploadDatasetFile] = useState<File | null>(null);
  const [uploadValidationFile, setUploadValidationFile] = useState<File | null>(null);
  const [datasetSourceUrl, setDatasetSourceUrl] = useState("");
  const [datasetValidationUrl, setDatasetValidationUrl] = useState("");
  const [newJobDatasetId, setNewJobDatasetId] = useState<string>("");
  const [newJobBaseModelId, setNewJobBaseModelId] = useState(trainingSettings.baseModel);
  const [newJobTrainerId, setNewJobTrainerId] = useState(trainingSettings.defaultTrainer);
  const [compatibilityMap, setCompatibilityMap] = useState<Record<string, { compatible: boolean; reason: string | null }>>(
    trainingCompatibility,
  );
  const [selectedTrainingJobId, setSelectedTrainingJobId] = useState<number | null>(null);
  const [createUsername, setCreateUsername] = useState("");
  const [createPassword, setCreatePassword] = useState("");
  const [createIsAdmin, setCreateIsAdmin] = useState(false);
  const [createPending, setCreatePending] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [newProjectName, setNewProjectName] = useState("");
  const [projectActionPending, setProjectActionPending] = useState(false);
  const [projectRenameDraft, setProjectRenameDraft] = useState<Record<number, string>>({});
  const [sourceUploadFile, setSourceUploadFile] = useState<File | null>(null);
  const [sourceUploadPending, setSourceUploadPending] = useState(false);

  const registeredDatasetFiles = new Set(
    trainingDatasets.flatMap((dataset) => {
      const sourcePath = typeof dataset.metadata.source_path === "string" ? dataset.metadata.source_path : "";
      const validationPath = typeof dataset.metadata.validation_source_path === "string" ? dataset.metadata.validation_source_path : "";
      return [sourcePath, validationPath].filter((item) => item.length > 0);
    }),
  );

  const datasetRootSuffix = trainingDraft.datasetsDirectory.replace(/\\/g, "/").replace(/^\.\//, "");
  const visibleDatasetFiles = trainingDatasetFiles.map((file) => {
    const normalizedRelativePath = file.relativePath.replace(/\\/g, "/");
    const absoluteCandidate = `${trainingDraft.datasetsDirectory.replace(/\//g, "\\")}\\${normalizedRelativePath.replace(/\//g, "\\")}`;
    const isRegistered = registeredDatasetFiles.has(absoluteCandidate) || registeredDatasetFiles.has(normalizedRelativePath) || registeredDatasetFiles.has(`${datasetRootSuffix}/${normalizedRelativePath}`);
    return { ...file, isRegistered };
  });

  useEffect(() => {
    setDirectoryDraft(modelDirectories);
  }, [modelDirectories]);

  useEffect(() => {
    setProfileDraft(modelProfile);
  }, [modelProfile]);

  useEffect(() => {
    setGeneralDraft(generalSettings);
  }, [generalSettings]);

  useEffect(() => {
    setChatDraft(chatSettings);
  }, [chatSettings]);

  useEffect(() => {
    setKnowledgeDraft(knowledgeSettings);
  }, [knowledgeSettings]);

  useEffect(() => {
    setLogsDraft(logsSettings);
  }, [logsSettings]);

  const generalSettingsDirty =
    generalDraft.language !== generalSettings.language ||
    generalDraft.theme !== generalSettings.theme ||
    generalDraft.timezone.trim() !== generalSettings.timezone;

  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (!generalSettingsDirty) {
        return;
      }
      event.preventDefault();
      event.returnValue = "";
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [generalSettingsDirty]);

  useEffect(() => {
    setTrainingDraft(trainingSettings);
  }, [trainingSettings]);

  useEffect(() => {
    if (newJobBaseModelId.trim().length === 0) {
      setNewJobBaseModelId(trainingSettings.baseModel);
    }
  }, [newJobBaseModelId, trainingSettings.baseModel]);

  useEffect(() => {
    if (newJobTrainerId.trim().length === 0) {
      setNewJobTrainerId(trainingSettings.defaultTrainer);
    }
  }, [newJobTrainerId, trainingSettings.defaultTrainer]);

  useEffect(() => {
    setCompatibilityMap(trainingCompatibility);
  }, [trainingCompatibility]);

  const selectedTrainingJob =
    selectedTrainingJobId == null ? null : trainingJobs.find((job) => job.id === selectedTrainingJobId) ?? null;
  const selectedConfiguredBaseModel =
    trainingDraft.baseModel.trim().length > 0
      ? modelEntries.find((model) => model.name === trainingDraft.baseModel || model.id === trainingDraft.baseModel) ?? null
      : null;
  const selectedNewJobBaseModel =
    newJobBaseModelId.trim().length > 0
      ? modelEntries.find((model) => model.name === newJobBaseModelId || model.id === newJobBaseModelId) ?? null
      : null;

  const selectedTrainerOption =
    trainerOptions.find((option) => option.id === trainingDraft.defaultTrainer.trim().toLowerCase()) ?? null;
  const selectedJobTrainerOption =
    trainerOptions.find((option) => option.id === newJobTrainerId.trim().toLowerCase()) ?? null;

  const statusDotClass = (entry: UiModelEntry) => {
    if (entry.statusColor === "green") {
      return "status-dot status-dot--ok";
    }
    if (entry.statusColor === "yellow") {
      return "status-dot status-dot--warn";
    }
    if (entry.statusColor === "red") {
      return "status-dot status-dot--error";
    }
    if (entry.statusColor === "gray") {
      return "status-dot status-dot--neutral";
    }
    return "status-dot";
  };

  const groupedModelEntries = modelEntries.reduce<Record<string, UiModelEntry[]>>((acc, model) => {
    const group = model.group ?? "Hilfsmodelle";
    if (!acc[group]) {
      acc[group] = [];
    }
    acc[group].push(model);
    return acc;
  }, {});

  const compatibleForTrainer = (model: UiModelEntry, trainerId: string): { compatible: boolean; reason: string | null } => {
    const normalizedTrainer = trainerId.trim().toLowerCase();
    if (normalizedTrainer.length === 0) {
      return { compatible: true, reason: null };
    }
    const match = compatibilityMap[model.id];
    if (match) {
      return match;
    }
    if (normalizedTrainer !== "peft_lora") {
      return { compatible: true, reason: null };
    }
    return { compatible: false, reason: "Keine Kompatibilitaetsdaten fuer dieses Modell." };
  };

  const refreshCompatibility = (trainerId: string) => {
    const normalized = trainerId.trim().toLowerCase();
    if (!normalized) {
      return;
    }
    void onFetchTrainingCompatibility(normalized).then((nextMap) => {
      setCompatibilityMap(nextMap);
    });
  };

  const isJobTerminal = (status: string) => {
    const normalized = status.trim().toLowerCase();
    return normalized === "completed" || normalized === "cancelled" || normalized === "failed";
  };

  if (view === "Projekte") {
    return (
      <PageFrame title="Projekte">
        <div className="model-dir-add-row">
          <input
            className="model-dir-input"
            type="text"
            placeholder="Projektname"
            value={newProjectName}
            onChange={(event) => setNewProjectName(event.target.value)}
            disabled={projectActionPending}
          />
          <button
            type="button"
            className="action-btn action-btn--primary"
            disabled={projectActionPending || newProjectName.trim().length === 0}
            onClick={() => {
              const name = newProjectName.trim();
              if (!name) {
                return;
              }
              setProjectActionPending(true);
              void onCreateProject(name)
                .then(() => {
                  setNewProjectName("");
                })
                .finally(() => {
                  setProjectActionPending(false);
                });
            }}
          >
            Neues Projekt
          </button>
        </div>
        <div className="card-list">
          {projects.map((project) => (
            <article key={project.id} className="page-card">
              <strong>{project.name}</strong>
              <span>{project.chats} Chats</span>
              <span>{project.documents} Dokumente</span>
              <div className="model-settings-controls">
                <button
                  type="button"
                  className="ghost-btn"
                  disabled={projectActionPending}
                  onClick={() => onSelectProject(project.id)}
                >
                  {selectedProjectId === project.id ? "Ausgewaehlt" : "Auswaehlen"}
                </button>
                <input
                  className="model-dir-input"
                  type="text"
                  aria-label={`Projekt ${project.name} umbenennen`}
                  title={`Projekt ${project.name} umbenennen`}
                  value={projectRenameDraft[project.id] ?? project.name}
                  onChange={(event) => {
                    const value = event.target.value;
                    setProjectRenameDraft((current) => ({ ...current, [project.id]: value }));
                  }}
                  disabled={projectActionPending}
                />
                <button
                  type="button"
                  className="ghost-btn"
                  disabled={projectActionPending}
                  onClick={() => {
                    const nextName = (projectRenameDraft[project.id] ?? project.name).trim();
                    if (!nextName || nextName === project.name) {
                      return;
                    }
                    setProjectActionPending(true);
                    void onRenameProject(project.id, nextName).finally(() => {
                      setProjectActionPending(false);
                    });
                  }}
                >
                  Umbenennen
                </button>
                <button
                  type="button"
                  className="action-btn action-btn--danger"
                  disabled={projectActionPending}
                  onClick={() => {
                    const accepted = window.confirm(`Projekt "${project.name}" wirklich loeschen?`);
                    if (!accepted) {
                      return;
                    }
                    setProjectActionPending(true);
                    void onDeleteProject(project.id).finally(() => {
                      setProjectActionPending(false);
                    });
                  }}
                >
                  Loeschen
                </button>
              </div>
            </article>
          ))}
        </div>
      </PageFrame>
    );
  }

  if (view === "Bibliothek") {
    return (
      <PageFrame title="Bibliothek" action="Dokument importieren">
        <div className="model-dir-add-row">
          <input
            className="model-dir-input"
            type="file"
            accept=".pdf,.md,.txt,.docx"
            onChange={(event) => {
              const nextFile = event.target.files?.[0] ?? null;
              setSourceUploadFile(nextFile);
            }}
            disabled={sourceUploadPending}
          />
          <button
            type="button"
            className="action-btn action-btn--primary"
            disabled={sourceUploadPending || sourceUploadFile == null}
            onClick={() => {
              if (sourceUploadFile == null) {
                return;
              }
              setSourceUploadPending(true);
              void onUploadWorkspaceSource(sourceUploadFile)
                .then(() => {
                  setSourceUploadFile(null);
                })
                .finally(() => {
                  setSourceUploadPending(false);
                });
            }}
          >
            {sourceUploadPending ? "Upload..." : "Quelle hochladen"}
          </button>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Datei</th>
              <th>Status</th>
              <th>Quelle</th>
              <th>Projekt</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((row) => (
              <tr key={row.id}>
                <td>{row.file}</td>
                <td>Bereit</td>
                <td>{row.position}</td>
                <td>{row.relevance}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </PageFrame>
    );
  }

  if (view === "Termine") {
    return (
      <PageFrame title="Termine" action="Neuer Termin">
        <div className="card-list">
          {appointments.map((appointment) => (
            <article key={appointment.id} className="page-card">
              <strong>{appointment.date} · {appointment.title}</strong>
              <span>Status: {appointment.state}</span>
            </article>
          ))}
        </div>
      </PageFrame>
    );
  }

  if (view === "Plugins") {
    return (
      <PageFrame title="Plugins">
        <div className="card-list">
          {plugins.map((plugin) => (
            <article key={plugin.name} className="page-card">
              <strong>{plugin.name}</strong>
              <span>Status: {plugin.state}</span>
              <span>Berechtigung: {plugin.perms}</span>
            </article>
          ))}
        </div>
      </PageFrame>
    );
  }

  if (view === "Einstellungen") {
    return (
      <PageFrame title="Einstellungen">
        <div className="settings-layout">
          <nav className="settings-nav">
            {settingsGroups.map(([group]) => (
              <button
                key={group}
                className={`settings-nav-item ${group === activeSettingsGroup ? "settings-nav-item--active" : ""}`}
                type="button"
                onClick={() => setActiveSettingsGroup(group)}
              >
                {group}
              </button>
            ))}
          </nav>
          <div className="settings-content">
            {activeSettingsGroup === "Allgemein" ? (
              <article className="page-card model-settings-card">
                <div className="model-settings-card__header">
                  <strong>Allgemeine Einstellungen</strong>
                  <div className="model-settings-card__actions">
                    <button
                      type="button"
                      className="action-btn action-btn--primary"
                      disabled={generalSettingsPending}
                      onClick={() => {
                        void onSaveGeneralSettings(generalDraft);
                      }}
                    >
                      Speichern
                    </button>
                  </div>
                </div>

                {generalSettingsDirty ? <span>Ungespeicherte Aenderungen</span> : <span>Alle Aenderungen gespeichert</span>}

                <span>Persoenliche Basiswerte fuer Sprache, Theme und Zeitzone.</span>

                <div className="model-profile-grid">
                  <label className="model-profile-field">
                    <span>Sprache</span>
                    <select
                      className="model-dir-input"
                      value={generalDraft.language}
                      onChange={(event) => {
                        const nextLanguage = event.target.value === "en" ? "en" : "de";
                        setGeneralDraft((current) => ({ ...current, language: nextLanguage }));
                      }}
                      disabled={generalSettingsPending}
                    >
                      <option value="de">Deutsch</option>
                      <option value="en">English</option>
                    </select>
                  </label>

                  <label className="model-profile-field">
                    <span>Theme</span>
                    <select
                      className="model-dir-input"
                      value={generalDraft.theme}
                      onChange={(event) => {
                        const rawTheme = event.target.value;
                        const nextTheme =
                          rawTheme === "light" || rawTheme === "dark" || rawTheme === "system"
                            ? rawTheme
                            : "system";
                        setGeneralDraft((current) => ({ ...current, theme: nextTheme }));
                      }}
                      disabled={generalSettingsPending}
                    >
                      <option value="system">System</option>
                      <option value="light">Hell</option>
                      <option value="dark">Dunkel</option>
                    </select>
                  </label>

                  <label className="model-profile-field">
                    <span>Zeitzone (IANA)</span>
                    <input
                      className="model-dir-input"
                      type="text"
                      placeholder="Europe/Berlin"
                      value={generalDraft.timezone}
                      onChange={(event) => {
                        setGeneralDraft((current) => ({ ...current, timezone: event.target.value }));
                      }}
                      disabled={generalSettingsPending}
                    />
                  </label>
                </div>
              </article>
            ) : null}

            {activeSettingsGroup === "Modelle" ? (
              <article className="page-card model-settings-card">
                <div className="model-settings-card__header">
                  <strong>Modelle laden</strong>
                  <div className="model-settings-card__actions">
                    <button
                      type="button"
                      className="ghost-btn"
                      disabled={modelActionPending}
                      onClick={() => {
                        void onScanModels();
                      }}
                    >
                      Scan aktualisieren
                    </button>
                  </div>
                </div>

                <span>Aktueller Status: {modelLoaded ? "Modell geladen" : "Kein Modell geladen"}</span>

                <div className="model-settings-list">
                  {Object.entries(groupedModelEntries).map(([groupName, entries]) => (
                    <div key={groupName}>
                      <div className="model-settings-meta">
                        <strong>{groupName}</strong>
                      </div>
                      {entries.map((model) => {
                    const isSelected = model.id === selectedModelId;
                    const isActive = model.isActive;
                    return (
                      <div key={model.id} className={`model-settings-row ${isActive ? "model-settings-row--active" : ""}`}>
                        <div>
                          <strong>{model.name}</strong>
                          <div className="model-settings-meta">
                            <span className="status-line">
                              <span className={statusDotClass(model)} aria-hidden="true" />
                              {model.statusLabel ?? (model.loaded ? "Bereit" : "Nicht geladen")}
                            </span>
                            <span>{isActive ? "Aktiv" : "Inaktiv"}</span>
                            {model.taskType ? <span>Task: {model.taskType}</span> : null}
                            {model.modelFormat ? <span>Format: {model.modelFormat}</span> : null}
                            {model.reasonUnavailable ? <span>{model.reasonUnavailable}</span> : null}
                          </div>
                        </div>
                        <div className="model-settings-controls">
                          <label className="model-radio-wrap">
                            <input
                              type="radio"
                              name="settings-model"
                              checked={isSelected}
                              onChange={() => {
                                void onActivateModel(model.id);
                              }}
                              disabled={modelActionPending}
                            />
                            Auswaehlen
                          </label>
                          <button
                            type="button"
                            className={`ghost-btn ${model.relevanceFlag === "favorite" ? "ghost-btn--active" : ""}`}
                            disabled={modelActionPending}
                            onClick={() => {
                              const next = model.relevanceFlag === "favorite" ? null : "favorite";
                              void onSetModelRelevance(model.id, next);
                            }}
                          >
                            Favorit
                          </button>
                          <button
                            type="button"
                            className={`ghost-btn ${model.relevanceFlag === "irrelevant" ? "ghost-btn--active" : ""}`}
                            disabled={modelActionPending}
                            onClick={() => {
                              const next = model.relevanceFlag === "irrelevant" ? null : "irrelevant";
                              void onSetModelRelevance(model.id, next);
                            }}
                          >
                            Irrelevant
                          </button>
                          <button
                            type="button"
                            className={isActive ? "action-btn action-btn--danger" : "action-btn"}
                            disabled={modelActionPending}
                            onClick={() => {
                              if (isActive) {
                                void onDeactivateModel();
                                return;
                              }
                              void onActivateModel(model.id);
                            }}
                          >
                            {isActive ? "Entladen" : "Laden"}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                    </div>
                  ))}
                  {modelEntries.length === 0 ? <span>Keine Modelle gefunden. Bitte Scan starten.</span> : null}
                </div>
              </article>
            ) : null}

            {activeSettingsGroup === "Modellverzeichnisse" ? (
              <article className="page-card model-settings-card">
                <div className="model-settings-card__header">
                  <strong>Modellverzeichnisse</strong>
                  <div className="model-settings-card__actions">
                    <button
                      type="button"
                      className="action-btn action-btn--primary"
                      disabled={modelDirectoryPending}
                      onClick={() => {
                        void onSaveModelDirectories(directoryDraft);
                      }}
                    >
                      Speichern
                    </button>
                  </div>
                </div>

                <span>Pfade fuer Modellscan und automatische Modell-Erkennung.</span>

                <div className="model-dir-add-row">
                  <input
                    className="model-dir-input"
                    type="text"
                    placeholder="z. B. F:/KI/models"
                    value={newDirectory}
                    onChange={(event) => setNewDirectory(event.target.value)}
                    disabled={modelDirectoryPending}
                  />
                  <button
                    type="button"
                    className="action-btn"
                    disabled={modelDirectoryPending || newDirectory.trim().length === 0}
                    onClick={() => {
                      const normalized = newDirectory.trim();
                      if (directoryDraft.includes(normalized)) {
                        setNewDirectory("");
                        return;
                      }
                      setDirectoryDraft((items) => [...items, normalized]);
                      setNewDirectory("");
                    }}
                  >
                    Hinzufuegen
                  </button>
                </div>

                <div className="model-settings-list">
                  {directoryDraft.map((directory) => (
                    <div key={directory} className="model-settings-row">
                      <div>
                        <strong>{directory}</strong>
                      </div>
                      <div className="model-settings-controls">
                        <button
                          type="button"
                          className="ghost-btn"
                          disabled={modelDirectoryPending}
                          onClick={() => {
                            setDirectoryDraft((items) => items.filter((item) => item !== directory));
                          }}
                        >
                          Entfernen
                        </button>
                      </div>
                    </div>
                  ))}
                  {directoryDraft.length === 0 ? <span>Keine Modellverzeichnisse konfiguriert.</span> : null}
                </div>
              </article>
            ) : null}

            {activeSettingsGroup === "Prompts" ? (
              <article className="page-card model-settings-card">
                <div className="model-settings-card__header">
                  <strong>Individuelle Prompt- und Modell-Einstellungen</strong>
                  <div className="model-settings-card__actions">
                    <button
                      type="button"
                      className="action-btn action-btn--primary"
                      disabled={modelProfilePending || selectedModelId.length === 0}
                      onClick={() => {
                        void onSaveModelProfile(profileDraft);
                      }}
                    >
                      Speichern
                    </button>
                  </div>
                </div>

                <span>Diese Werte gelten nur fuer das aktuell ausgewaehlte Modell.</span>

                <div className="model-profile-grid">
                  <div className="model-settings-card__actions">
                    <button
                      type="button"
                      className="ghost-btn"
                      disabled={modelProfilePending || selectedModelId.length === 0}
                      onClick={() => {
                        setProfileDraft((current) => ({
                          ...current,
                          temperature: "0.0",
                          topP: "0.85",
                          repetitionPenalty: "1.1",
                        }));
                      }}
                    >
                      Modus praezise
                    </button>
                    <button
                      type="button"
                      className="ghost-btn"
                      disabled={modelProfilePending || selectedModelId.length === 0}
                      onClick={() => {
                        setProfileDraft((current) => ({
                          ...current,
                          temperature: "0.7",
                          topP: "0.95",
                          repetitionPenalty: "1.0",
                        }));
                      }}
                    >
                      Modus kreativ
                    </button>
                  </div>

                  <label className="model-profile-field">
                    <span>System-Prompt</span>
                    <textarea
                      className="model-profile-textarea"
                      value={profileDraft.systemPrompt}
                      onChange={(event) => {
                        setProfileDraft((current) => ({ ...current, systemPrompt: event.target.value }));
                      }}
                      disabled={modelProfilePending || selectedModelId.length === 0}
                      rows={5}
                    />
                  </label>

                  <label className="model-profile-field">
                    <span>Temperatur</span>
                    <input
                      className="model-dir-input"
                      type="number"
                      min="0"
                      max="2"
                      step="0.1"
                      value={profileDraft.temperature}
                      onChange={(event) => {
                        setProfileDraft((current) => ({ ...current, temperature: event.target.value }));
                      }}
                      disabled={modelProfilePending || selectedModelId.length === 0}
                    />
                  </label>

                  <label className="model-profile-field">
                    <span>Sampling Top-K</span>
                    <input
                      className="model-dir-input"
                      type="number"
                      min="0"
                      step="1"
                      value={profileDraft.samplingTopK}
                      onChange={(event) => {
                        setProfileDraft((current) => ({ ...current, samplingTopK: event.target.value }));
                      }}
                      disabled={modelProfilePending || selectedModelId.length === 0}
                    />
                  </label>

                  <label className="model-profile-field">
                    <span>Max New Tokens</span>
                    <input
                      className="model-dir-input"
                      type="number"
                      min="1"
                      step="1"
                      value={profileDraft.maxNewTokens}
                      onChange={(event) => {
                        setProfileDraft((current) => ({ ...current, maxNewTokens: event.target.value }));
                      }}
                      disabled={modelProfilePending || selectedModelId.length === 0}
                    />
                  </label>

                  <label className="model-profile-field">
                    <span>Retrieval Top-K</span>
                    <input
                      className="model-dir-input"
                      type="number"
                      min="1"
                      step="1"
                      value={profileDraft.topK}
                      onChange={(event) => {
                        setProfileDraft((current) => ({ ...current, topK: event.target.value }));
                      }}
                      disabled={modelProfilePending || selectedModelId.length === 0}
                    />
                  </label>

                  <label className="model-profile-field">
                    <span>Top-P</span>
                    <input
                      className="model-dir-input"
                      type="number"
                      min="0.01"
                      max="1"
                      step="0.01"
                      value={profileDraft.topP}
                      onChange={(event) => {
                        setProfileDraft((current) => ({ ...current, topP: event.target.value }));
                      }}
                      disabled={modelProfilePending || selectedModelId.length === 0}
                    />
                  </label>

                  <label className="model-profile-field">
                    <span>Repetition Penalty</span>
                    <input
                      className="model-dir-input"
                      type="number"
                      min="0.5"
                      max="2"
                      step="0.01"
                      value={profileDraft.repetitionPenalty}
                      onChange={(event) => {
                        setProfileDraft((current) => ({ ...current, repetitionPenalty: event.target.value }));
                      }}
                      disabled={modelProfilePending || selectedModelId.length === 0}
                    />
                  </label>

                  <label className="model-profile-field">
                    <span>Stop Sequences (kommagetrennt)</span>
                    <input
                      className="model-dir-input"
                      type="text"
                      value={profileDraft.stopSequences}
                      onChange={(event) => {
                        setProfileDraft((current) => ({ ...current, stopSequences: event.target.value }));
                      }}
                      disabled={modelProfilePending || selectedModelId.length === 0}
                    />
                  </label>

                  <label className="model-profile-field">
                    <span>Seed</span>
                    <input
                      className="model-dir-input"
                      type="number"
                      min="0"
                      step="1"
                      value={profileDraft.seed}
                      onChange={(event) => {
                        setProfileDraft((current) => ({ ...current, seed: event.target.value }));
                      }}
                      disabled={modelProfilePending || selectedModelId.length === 0}
                    />
                  </label>

                  <label className="model-radio-wrap model-profile-toggle">
                    <input
                      type="checkbox"
                      checked={profileDraft.doSample}
                      onChange={(event) => {
                        setProfileDraft((current) => ({ ...current, doSample: event.target.checked }));
                      }}
                      disabled={modelProfilePending || selectedModelId.length === 0}
                    />
                    do_sample
                  </label>

                  <label className="model-radio-wrap model-profile-toggle">
                    <input
                      type="checkbox"
                      checked={profileDraft.preferGpu}
                      onChange={(event) => {
                        setProfileDraft((current) => ({ ...current, preferGpu: event.target.checked }));
                      }}
                      disabled={modelProfilePending || selectedModelId.length === 0}
                    />
                    GPU bevorzugen
                  </label>
                </div>

                {selectedModelId.length === 0 ? <span>Bitte zuerst ein Modell auswaehlen.</span> : null}
              </article>
            ) : null}

            {activeSettingsGroup === "Chat" ? (
              <article className="page-card model-settings-card">
                <div className="model-settings-card__header">
                  <strong>Chat-Einstellungen</strong>
                  <div className="model-settings-card__actions">
                    <button
                      type="button"
                      className="action-btn action-btn--primary"
                      disabled={chatSettingsPending}
                      onClick={() => {
                        void onSaveChatSettings(chatDraft);
                      }}
                    >
                      Speichern
                    </button>
                  </div>
                </div>

                <span>Globale Standardwerte fuer Antwortstil, Sampling und Kontextbudget.</span>

                <div className="model-profile-grid">
                  <label className="model-profile-field"><span>Temperatur</span><input className="model-dir-input" type="number" min="0" max="2" step="0.1" value={chatDraft.temperature} onChange={(event) => setChatDraft((current) => ({ ...current, temperature: event.target.value }))} disabled={chatSettingsPending} /></label>
                  <label className="model-profile-field"><span>Max New Tokens</span><input className="model-dir-input" type="number" min="1" step="1" value={chatDraft.maxNewTokens} onChange={(event) => setChatDraft((current) => ({ ...current, maxNewTokens: event.target.value }))} disabled={chatSettingsPending} /></label>
                  <label className="model-profile-field"><span>Top-P</span><input className="model-dir-input" type="number" min="0.01" max="1" step="0.01" value={chatDraft.topP} onChange={(event) => setChatDraft((current) => ({ ...current, topP: event.target.value }))} disabled={chatSettingsPending} /></label>
                  <label className="model-profile-field"><span>Top-K</span><input className="model-dir-input" type="number" min="0" step="1" value={chatDraft.topK} onChange={(event) => setChatDraft((current) => ({ ...current, topK: event.target.value }))} disabled={chatSettingsPending} /></label>
                  <label className="model-profile-field"><span>Repetition Penalty</span><input className="model-dir-input" type="number" min="0.5" max="2" step="0.01" value={chatDraft.repetitionPenalty} onChange={(event) => setChatDraft((current) => ({ ...current, repetitionPenalty: event.target.value }))} disabled={chatSettingsPending} /></label>
                  <label className="model-profile-field"><span>Seed</span><input className="model-dir-input" type="number" min="0" step="1" value={chatDraft.seed} onChange={(event) => setChatDraft((current) => ({ ...current, seed: event.target.value }))} disabled={chatSettingsPending} /></label>
                  <label className="model-profile-field"><span>Context Limit Tokens</span><input className="model-dir-input" type="number" min="512" step="1" value={chatDraft.contextLimitTokens} onChange={(event) => setChatDraft((current) => ({ ...current, contextLimitTokens: event.target.value }))} disabled={chatSettingsPending} /></label>
                  <label className="model-profile-field"><span>Safety Margin Tokens</span><input className="model-dir-input" type="number" min="0" step="1" value={chatDraft.contextSafetyMarginTokens} onChange={(event) => setChatDraft((current) => ({ ...current, contextSafetyMarginTokens: event.target.value }))} disabled={chatSettingsPending} /></label>
                  <label className="model-radio-wrap model-profile-toggle">
                    <input type="checkbox" checked={chatDraft.doSample} onChange={(event) => setChatDraft((current) => ({ ...current, doSample: event.target.checked }))} disabled={chatSettingsPending} />
                    do_sample
                  </label>
                </div>
              </article>
            ) : null}

            {activeSettingsGroup === "Wissen" ? (
              <article className="page-card model-settings-card">
                <div className="model-settings-card__header">
                  <strong>Wissen / Retrieval</strong>
                  <div className="model-settings-card__actions">
                    <button
                      type="button"
                      className="action-btn action-btn--primary"
                      disabled={knowledgeSettingsPending}
                      onClick={() => {
                        void onSaveKnowledgeSettings(knowledgeDraft);
                      }}
                    >
                      Speichern
                    </button>
                  </div>
                </div>

                <span>Steuert die Quelleauswahl und Relevanzgrenzen fuer externen Kontext.</span>

                <div className="model-profile-grid">
                  <label className="model-profile-field"><span>Top-K</span><input className="model-dir-input" type="number" min="1" step="1" value={knowledgeDraft.topK} onChange={(event) => setKnowledgeDraft((current) => ({ ...current, topK: event.target.value }))} disabled={knowledgeSettingsPending} /></label>
                  <label className="model-profile-field"><span>Min Score Ratio</span><input className="model-dir-input" type="number" min="0" max="1" step="0.01" value={knowledgeDraft.minScoreRatio} onChange={(event) => setKnowledgeDraft((current) => ({ ...current, minScoreRatio: event.target.value }))} disabled={knowledgeSettingsPending} /></label>
                  <label className="model-profile-field"><span>Min Absolute Score</span><input className="model-dir-input" type="number" min="0" step="1" value={knowledgeDraft.minAbsoluteScore} onChange={(event) => setKnowledgeDraft((current) => ({ ...current, minAbsoluteScore: event.target.value }))} disabled={knowledgeSettingsPending} /></label>
                  <label className="model-profile-field"><span>Min Score Gap</span><input className="model-dir-input" type="number" min="0" step="1" value={knowledgeDraft.minScoreGap} onChange={(event) => setKnowledgeDraft((current) => ({ ...current, minScoreGap: event.target.value }))} disabled={knowledgeSettingsPending} /></label>
                </div>
              </article>
            ) : null}

            {activeSettingsGroup === "Logs" ? (
              <article className="page-card model-settings-card">
                <div className="model-settings-card__header">
                  <strong>Logs</strong>
                  <div className="model-settings-card__actions">
                    <button
                      type="button"
                      className="action-btn action-btn--primary"
                      disabled={logsSettingsPending}
                      onClick={() => {
                        void onSaveLogsSettings(logsDraft);
                      }}
                    >
                      Speichern
                    </button>
                  </div>
                </div>

                <span>Legt das globale Backend-Loglevel fest.</span>

                <div className="model-profile-grid">
                  <label className="model-profile-field">
                    <span>Log Level</span>
                    <select className="model-dir-input" value={logsDraft.logLevel} onChange={(event) => setLogsDraft({ logLevel: (event.target.value as LogsSettingsDraft["logLevel"]) })} disabled={logsSettingsPending}>
                      <option value="DEBUG">DEBUG</option>
                      <option value="INFO">INFO</option>
                      <option value="WARNING">WARNING</option>
                      <option value="ERROR">ERROR</option>
                    </select>
                  </label>
                </div>
              </article>
            ) : null}

            {activeSettingsGroup === "Training" ? (
              <article className="page-card model-settings-card">
                <div className="model-settings-card__header">
                  <strong>Training-Einstellungen</strong>
                  <div className="model-settings-card__actions">
                    <button
                      type="button"
                      className="action-btn action-btn--primary"
                      disabled={trainingSettingsPending}
                      onClick={() => {
                        void onSaveTrainingSettings(trainingDraft);
                      }}
                    >
                      Speichern
                    </button>
                  </div>
                </div>

                <span>Globale Trainingskonfiguration fuer Jobs, Queue und Artefaktablage.</span>

                <div className="model-profile-grid">
                  <label className="model-radio-wrap model-profile-toggle">
                    <input
                      type="checkbox"
                      checked={trainingDraft.enabled}
                      onChange={(event) => {
                        setTrainingDraft((current) => ({ ...current, enabled: event.target.checked }));
                      }}
                      disabled={trainingSettingsPending}
                    />
                    Training aktiviert
                  </label>

                  <label className="model-profile-field">
                    <span>Standard-Trainer</span>
                    <select
                      className="model-dir-input"
                      value={trainingDraft.defaultTrainer}
                      onChange={(event) => {
                        const nextTrainer = event.target.value;
                        setTrainingDraft((current) => ({ ...current, defaultTrainer: nextTrainer }));
                        refreshCompatibility(nextTrainer);
                      }}
                      disabled={trainingSettingsPending}
                    >
                      {trainerOptions.map((trainer) => (
                        <option key={trainer.id} value={trainer.id} disabled={!trainer.available}>
                          {trainer.label}
                          {trainer.available ? "" : " (nicht verfuegbar)"}
                        </option>
                      ))}
                    </select>
                  </label>

                  {!selectedTrainerOption?.available ? (
                    <div className="model-settings-meta" role="status" aria-live="polite">
                      <span>Der ausgewaehlte Trainer ist derzeit nicht verfuegbar.</span>
                      <span>{selectedTrainerOption?.reasonUnavailable ?? "Bitte waehle einen verfuegbaren Trainer."}</span>
                    </div>
                  ) : null}

                  <label className="model-profile-field">
                    <span>Basis-Modell (Model Manager)</span>
                    <select
                      className="model-dir-input"
                      value={trainingDraft.baseModel}
                      onChange={(event) => {
                        setTrainingDraft((current) => ({ ...current, baseModel: event.target.value }));
                      }}
                      disabled={trainingSettingsPending}
                    >
                      <option value="">Nicht festgelegt</option>
                      {modelEntries.map((model) => {
                        const compatibility = compatibleForTrainer(model, trainingDraft.defaultTrainer);
                        return (
                          <option key={model.id} value={model.name} disabled={!compatibility.compatible}>
                            {model.name}
                            {compatibility.compatible ? "" : ` (inkompatibel: ${compatibility.reason ?? "Grund unbekannt"})`}
                          </option>
                        );
                      })}
                    </select>
                  </label>

                  <div className="model-settings-meta">
                    <span>
                      Gewaehlt: {selectedConfiguredBaseModel ? selectedConfiguredBaseModel.name : trainingDraft.baseModel || "(kein Modell)"}
                    </span>
                    {selectedConfiguredBaseModel ? <span>Backend: {selectedConfiguredBaseModel.backend}</span> : null}
                    {selectedConfiguredBaseModel ? <span>Status: {selectedConfiguredBaseModel.loadStatus}</span> : null}
                    {selectedConfiguredBaseModel ? <span>Pfad: {selectedConfiguredBaseModel.modelPath}</span> : null}
                  </div>

                  <label className="model-profile-field">
                    <span>Artefakte-Verzeichnis</span>
                    <input
                      className="model-dir-input"
                      type="text"
                      value={trainingDraft.artifactsDirectory}
                      onChange={(event) => {
                        setTrainingDraft((current) => ({ ...current, artifactsDirectory: event.target.value }));
                      }}
                      disabled={trainingSettingsPending}
                    />
                  </label>

                  <label className="model-profile-field">
                    <span>Datasets-Verzeichnis</span>
                    <input
                      className="model-dir-input"
                      type="text"
                      value={trainingDraft.datasetsDirectory}
                      onChange={(event) => {
                        setTrainingDraft((current) => ({ ...current, datasetsDirectory: event.target.value }));
                      }}
                      disabled={trainingSettingsPending}
                    />
                  </label>

                  <label className="model-profile-field">
                    <span>Max. parallele Jobs</span>
                    <input
                      className="model-dir-input"
                      type="number"
                      min="1"
                      step="1"
                      value={trainingDraft.maxConcurrentJobs}
                      onChange={(event) => {
                        setTrainingDraft((current) => ({ ...current, maxConcurrentJobs: event.target.value }));
                      }}
                      disabled={trainingSettingsPending}
                    />
                  </label>

                  <label className="model-radio-wrap model-profile-toggle">
                    <input
                      type="checkbox"
                      checked={trainingDraft.autoStartQueue}
                      onChange={(event) => {
                        setTrainingDraft((current) => ({ ...current, autoStartQueue: event.target.checked }));
                      }}
                      disabled={trainingSettingsPending}
                    />
                    Queue automatisch starten
                  </label>

                  <label className="model-radio-wrap model-profile-toggle">
                    <input
                      type="checkbox"
                      checked={trainingDraft.autoEvaluate}
                      onChange={(event) => {
                        setTrainingDraft((current) => ({ ...current, autoEvaluate: event.target.checked }));
                      }}
                      disabled={trainingSettingsPending}
                    />
                    Nach Training evaluieren
                  </label>

                  <label className="model-radio-wrap model-profile-toggle">
                    <input
                      type="checkbox"
                      checked={trainingDraft.autoRegisterModel}
                      onChange={(event) => {
                        setTrainingDraft((current) => ({ ...current, autoRegisterModel: event.target.checked }));
                      }}
                      disabled={trainingSettingsPending}
                    />
                    Modell automatisch registrieren
                  </label>
                </div>

                <div className="model-settings-card__header">
                  <strong>Datasets</strong>
                </div>

                <div className="model-settings-card__header">
                  <strong>Vorhandene Dateien</strong>
                </div>

                <div className="model-dir-add-row">
                  <input
                    className="model-dir-input"
                    type="text"
                    placeholder="Neues Dataset"
                    value={newDatasetName}
                    onChange={(event) => setNewDatasetName(event.target.value)}
                    disabled={trainingSettingsPending}
                  />
                  <select
                    className="model-dir-input"
                    aria-label="Projektzuordnung fuer neues Dataset"
                    title="Projektzuordnung fuer neues Dataset"
                    value={newDatasetProjectId}
                    onChange={(event) => setNewDatasetProjectId(event.target.value)}
                    disabled={trainingSettingsPending}
                  >
                    <option value="">Ohne Projekt</option>
                    {projects.map((project) => (
                      <option key={project.id} value={String(project.id)}>
                        {project.name}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    className="action-btn"
                    disabled={trainingSettingsPending || newDatasetName.trim().length === 0}
                    onClick={() => {
                      const projectId = newDatasetProjectId.trim().length > 0 ? Number(newDatasetProjectId) : null;
                      void onCreateTrainingDataset(newDatasetName, Number.isInteger(projectId) ? projectId : null).then(() => {
                        setNewDatasetName("");
                      });
                    }}
                  >
                    Leeres Dataset anlegen
                  </button>
                </div>

                <div className="model-dir-add-row">
                  <select
                    className="model-dir-input"
                    value={existingDatasetFile}
                    onChange={(event) => setExistingDatasetFile(event.target.value)}
                    disabled={trainingSettingsPending}
                    aria-label="Trainingsdatei aus Ordner"
                  >
                    <option value="">Datei aus Trainingsordner waehlen</option>
                    {visibleDatasetFiles.map((file) => (
                      <option key={file.relativePath} value={file.relativePath}>
                        {file.relativePath}{file.isRegistered ? " (bereits registriert)" : ""}
                      </option>
                    ))}
                  </select>
                  <select
                    className="model-dir-input"
                    value={existingValidationFile}
                    onChange={(event) => setExistingValidationFile(event.target.value)}
                    disabled={trainingSettingsPending}
                    aria-label="Validierungsdatei aus Ordner"
                  >
                    <option value="">Optionale Validierungsdatei</option>
                    {visibleDatasetFiles.map((file) => (
                      <option key={`validation-${file.relativePath}`} value={file.relativePath}>
                        {file.relativePath}{file.isRegistered ? " (bereits registriert)" : ""}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    className="action-btn"
                    disabled={trainingSettingsPending || newDatasetName.trim().length === 0 || existingDatasetFile.trim().length === 0}
                    onClick={() => {
                      const projectId = newDatasetProjectId.trim().length > 0 ? Number(newDatasetProjectId) : null;
                      void onRegisterTrainingDatasetFile(
                        newDatasetName,
                        existingDatasetFile,
                        existingValidationFile.trim().length > 0 ? existingValidationFile : undefined,
                        Number.isInteger(projectId) ? projectId : null,
                      );
                    }}
                  >
                    Ordnerdatei registrieren
                  </button>
                </div>

                <div className="model-settings-list">
                  {visibleDatasetFiles.map((file) => (
                    <div key={`file-${file.relativePath}`} className="model-settings-row">
                      <div>
                        <strong>{file.relativePath}</strong>
                        <div className="model-settings-meta">
                          <span>{file.sizeBytes} Bytes</span>
                          <span>{new Date(file.modifiedAt).toLocaleString("de-DE")}</span>
                          <span>{file.isRegistered ? "registriert" : "noch nicht registriert"}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                  {visibleDatasetFiles.length === 0 ? <span>Keine unterstuetzten Datensatzdateien im Trainingsordner gefunden.</span> : null}
                </div>

                <div className="model-settings-card__header">
                  <strong>Datei hochladen</strong>
                </div>

                <div className="model-dir-add-row">
                  <input
                    className="model-dir-input"
                    type="file"
                    accept=".jsonl,.json,.csv,.md,.markdown,.txt,.yaml,.yml,.xml,.html,.htm,.pdf,.docx"
                    onChange={(event) => setUploadDatasetFile(event.target.files?.[0] ?? null)}
                    disabled={trainingSettingsPending}
                  />
                  <input
                    className="model-dir-input"
                    type="file"
                    accept=".jsonl,.json,.csv,.md,.markdown,.txt,.yaml,.yml,.xml,.html,.htm,.pdf,.docx"
                    onChange={(event) => setUploadValidationFile(event.target.files?.[0] ?? null)}
                    disabled={trainingSettingsPending}
                  />
                  <button
                    type="button"
                    className="action-btn"
                    disabled={trainingSettingsPending || newDatasetName.trim().length === 0 || uploadDatasetFile == null}
                    onClick={() => {
                      const projectId = newDatasetProjectId.trim().length > 0 ? Number(newDatasetProjectId) : null;
                      if (uploadDatasetFile == null) {
                        return;
                      }
                      void onUploadTrainingDataset(
                        newDatasetName,
                        uploadDatasetFile,
                        uploadValidationFile,
                        Number.isInteger(projectId) ? projectId : null,
                      ).then(() => {
                        setUploadDatasetFile(null);
                        setUploadValidationFile(null);
                      });
                    }}
                  >
                    Datei hochladen
                  </button>
                </div>

                <div className="model-settings-card__header">
                  <strong>URL importieren</strong>
                </div>

                <div className="model-dir-add-row">
                  <input
                    className="model-dir-input"
                    type="url"
                    placeholder="Trainingsdatei URL"
                    value={datasetSourceUrl}
                    onChange={(event) => setDatasetSourceUrl(event.target.value)}
                    disabled={trainingSettingsPending}
                  />
                  <input
                    className="model-dir-input"
                    type="url"
                    placeholder="Optionale Validierungsdatei URL"
                    value={datasetValidationUrl}
                    onChange={(event) => setDatasetValidationUrl(event.target.value)}
                    disabled={trainingSettingsPending}
                  />
                  <button
                    type="button"
                    className="action-btn"
                    disabled={trainingSettingsPending || newDatasetName.trim().length === 0 || datasetSourceUrl.trim().length === 0}
                    onClick={() => {
                      const projectId = newDatasetProjectId.trim().length > 0 ? Number(newDatasetProjectId) : null;
                      void onImportTrainingDatasetFromUrl(
                        newDatasetName,
                        datasetSourceUrl.trim(),
                        datasetValidationUrl.trim().length > 0 ? datasetValidationUrl.trim() : undefined,
                        Number.isInteger(projectId) ? projectId : null,
                      );
                    }}
                  >
                    URL importieren
                  </button>
                </div>

                <div className="model-settings-list">
                  {trainingDatasets.map((dataset) => (
                    <div key={dataset.id} className="model-settings-row">
                      <div>
                        <strong>
                          #{dataset.id} {dataset.name}
                        </strong>
                        <div className="model-settings-meta">
                          <span>Status: {dataset.status}</span>
                          <span>Version: {dataset.version}</span>
                          <span>Quelle: {dataset.sourceType}</span>
                          <span>Pfad: {String(dataset.metadata.source_path ?? "-")}</span>
                          <span>Validierung: {String(dataset.metadata.validation_source_path ?? "-")}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                  {trainingDatasets.length === 0 ? <span>Noch keine Datasets vorhanden.</span> : null}
                </div>

                <div className="model-settings-card__header">
                  <strong>Training-Jobs</strong>
                </div>

                <div className="model-dir-add-row">
                  <select
                    className="model-dir-input"
                    aria-label="Dataset fuer neuen Training-Job"
                    title="Dataset fuer neuen Training-Job"
                    value={newJobDatasetId}
                    onChange={(event) => setNewJobDatasetId(event.target.value)}
                    disabled={trainingSettingsPending}
                  >
                    <option value="">Dataset waehlen</option>
                    {trainingDatasets.map((dataset) => (
                      <option key={dataset.id} value={String(dataset.id)}>
                        #{dataset.id} {dataset.name}
                      </option>
                    ))}
                  </select>
                  <select
                    className="model-dir-input"
                    aria-label="Trainer fuer neuen Training-Job"
                    title="Trainer fuer neuen Training-Job"
                    value={newJobTrainerId}
                    onChange={(event) => {
                      const nextTrainer = event.target.value;
                      setNewJobTrainerId(nextTrainer);
                      refreshCompatibility(nextTrainer);
                    }}
                    disabled={trainingSettingsPending}
                  >
                    {trainerOptions.map((trainer) => (
                      <option key={trainer.id} value={trainer.id} disabled={!trainer.available}>
                        {trainer.label}
                        {trainer.available ? "" : " (nicht verfuegbar)"}
                      </option>
                    ))}
                  </select>
                  <select
                    className="model-dir-input"
                    aria-label="Basis-Modell fuer neuen Training-Job"
                    title="Basis-Modell fuer neuen Training-Job"
                    value={newJobBaseModelId}
                    onChange={(event) => setNewJobBaseModelId(event.target.value)}
                    disabled={trainingSettingsPending}
                  >
                    <option value="">Training-Default verwenden</option>
                    {modelEntries.map((model) => {
                      const compatibility = compatibleForTrainer(model, newJobTrainerId);
                      return (
                        <option key={model.id} value={model.name} disabled={!compatibility.compatible}>
                          {model.name}
                          {compatibility.compatible ? "" : ` (inkompatibel: ${compatibility.reason ?? "Grund unbekannt"})`}
                        </option>
                      );
                    })}
                  </select>
                  <button
                    type="button"
                    className="action-btn"
                    disabled={trainingSettingsPending || newJobDatasetId.trim().length === 0}
                    onClick={() => {
                      const datasetId = Number(newJobDatasetId);
                      if (!Number.isInteger(datasetId) || datasetId <= 0) {
                        return;
                      }
                      const explicitBaseModel = newJobBaseModelId.trim();
                      const explicitTrainer = newJobTrainerId.trim();
                      void onRunTrainingPreflight(
                        datasetId,
                        explicitBaseModel.length > 0 ? explicitBaseModel : undefined,
                        explicitTrainer.length > 0 ? explicitTrainer : undefined,
                      );
                    }}
                  >
                    {trainingPreflightPending ? "Preflight laeuft..." : "Preflight pruefen"}
                  </button>
                  <button
                    type="button"
                    className="action-btn"
                    disabled={trainingSettingsPending || trainingPreflightPending || newJobDatasetId.trim().length === 0}
                    onClick={() => {
                      const datasetId = Number(newJobDatasetId);
                      if (!Number.isInteger(datasetId) || datasetId <= 0) {
                        return;
                      }
                      const explicitBaseModel = newJobBaseModelId.trim();
                      const explicitTrainer = newJobTrainerId.trim();
                      void onCreateTrainingJob(
                        datasetId,
                        explicitBaseModel.length > 0 ? explicitBaseModel : undefined,
                        explicitTrainer.length > 0 ? explicitTrainer : undefined,
                      ).then(() => {
                        setNewJobBaseModelId(trainingDraft.baseModel);
                      });
                    }}
                  >
                    Job starten
                  </button>
                </div>

                <div className="model-settings-meta">
                  <span>
                    Trainer: {(selectedJobTrainerOption?.label ?? newJobTrainerId) || trainingDraft.defaultTrainer || "(kein Trainer)"}
                  </span>
                  <span>
                    Verwendet: {selectedNewJobBaseModel ? selectedNewJobBaseModel.name : newJobBaseModelId.trim() || trainingDraft.baseModel || "(kein Modell)"}
                  </span>
                  {selectedNewJobBaseModel ? <span>Backend: {selectedNewJobBaseModel.backend}</span> : null}
                  {selectedNewJobBaseModel ? <span>Status: {selectedNewJobBaseModel.loadStatus}</span> : null}
                </div>

                {trainingPreflightResult ? (
                  <article className="page-card">
                    <strong>Preflight-Ergebnis</strong>
                    <div className="model-settings-meta">
                      <span>Ready: {trainingPreflightResult.ready ? "ja" : "nein"}</span>
                      <span>Trainer: {trainingPreflightResult.trainer}</span>
                      <span>Modell: {trainingPreflightResult.modelName ?? "-"}</span>
                      <span>Format: {trainingPreflightResult.modelFormat ?? "-"}</span>
                      <span>CUDA: {trainingPreflightResult.cudaAvailable ? "verfuegbar" : "nicht verfuegbar"}</span>
                      <span>4-bit: {trainingPreflightResult.supports4bit ? "unterstuetzt" : "nicht unterstuetzt"}</span>
                      <span>Dataset: {trainingPreflightResult.datasetValid ? "gueltig" : "ungueltig"}</span>
                    </div>
                    <label className="model-profile-field">
                      <span>Fehler</span>
                      <textarea
                        className="model-profile-textarea"
                        value={
                          trainingPreflightResult.errors.length > 0
                            ? trainingPreflightResult.errors.map((item) => `${item.code}: ${item.message}`).join("\n")
                            : "(keine Fehler)"
                        }
                        readOnly
                        rows={4}
                      />
                    </label>
                    <label className="model-profile-field">
                      <span>Warnungen</span>
                      <textarea
                        className="model-profile-textarea"
                        value={
                          trainingPreflightResult.warnings.length > 0
                            ? trainingPreflightResult.warnings.map((item) => `${item.code}: ${item.message}`).join("\n")
                            : "(keine Warnungen)"
                        }
                        readOnly
                        rows={3}
                      />
                    </label>
                  </article>
                ) : null}

                <div className="model-settings-list">
                  {trainingJobs.map((job) => (
                    <div key={job.id} className="model-settings-row">
                      <div>
                        <strong>
                          Job #{job.id} · Dataset #{job.datasetId}
                        </strong>
                        <div className="model-settings-meta">
                          <span>Status: {job.status}</span>
                          <span>Trainer: {job.trainerName}</span>
                          <span>Base Model: {job.baseModelId}</span>
                        </div>
                      </div>
                      <div className="model-settings-controls">
                        <button
                          type="button"
                          className="ghost-btn"
                          onClick={() => setSelectedTrainingJobId(job.id)}
                        >
                          Details
                        </button>
                        <button
                          type="button"
                          className="ghost-btn"
                          disabled={isJobTerminal(job.status)}
                          onClick={() => {
                            void onCancelTrainingJob(job.id);
                          }}
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          className="action-btn"
                          onClick={() => {
                            void onRetryTrainingJob(job.id);
                          }}
                        >
                          Retry
                        </button>
                      </div>
                    </div>
                  ))}
                  {trainingJobs.length === 0 ? <span>Noch keine Jobs vorhanden.</span> : null}
                </div>

                {selectedTrainingJob ? (
                  <article className="page-card">
                    <strong>Job-Details #{selectedTrainingJob.id}</strong>
                    <span>Status: {selectedTrainingJob.status}</span>
                    <span>Dataset: #{selectedTrainingJob.datasetId}</span>
                    <span>Trainer: {selectedTrainingJob.trainerName}</span>
                    <span>Base Model: {selectedTrainingJob.baseModelId}</span>
                    <span>Aktualisiert: {new Date(selectedTrainingJob.updatedAt).toLocaleString()}</span>

                    <label className="model-profile-field">
                      <span>Hyperparameter</span>
                      <textarea
                        className="model-profile-textarea"
                        value={JSON.stringify(selectedTrainingJob.hyperparameters, null, 2)}
                        readOnly
                        rows={6}
                      />
                    </label>

                    <label className="model-profile-field">
                      <span>Resultat</span>
                      <textarea
                        className="model-profile-textarea"
                        value={selectedTrainingJob.result ? JSON.stringify(selectedTrainingJob.result, null, 2) : "(kein Resultat)"}
                        readOnly
                        rows={6}
                      />
                    </label>

                    <label className="model-profile-field">
                      <span>Fehler</span>
                      <textarea
                        className="model-profile-textarea"
                        value={selectedTrainingJob.errorMessage ?? "(kein Fehler)"}
                        readOnly
                        rows={4}
                      />
                    </label>
                  </article>
                ) : null}
              </article>
            ) : null}

            {activeSettingsGroup === "Benutzer" ? (
              <article className="page-card model-settings-card">
                <div className="model-settings-card__header">
                  <strong>Benutzerkonten</strong>
                </div>

                {!currentUser.is_admin ? (
                  <span>Nur Administratoren koennen Benutzerkonten anlegen.</span>
                ) : (
                  <form
                    className="model-profile-grid"
                    onSubmit={(event) => {
                      event.preventDefault();
                      void (async () => {
                        const username = createUsername.trim();
                        const password = createPassword.trim();
                        if (username.length < 3) {
                          setCreateError("Benutzername muss mindestens 3 Zeichen haben.");
                          return;
                        }
                        if (password.length < 4) {
                          setCreateError("Passwort muss mindestens 4 Zeichen haben.");
                          return;
                        }

                        setCreatePending(true);
                        setCreateError(null);
                        try {
                          await onAdminCreateUser(username, password, createIsAdmin);
                          setCreateUsername("");
                          setCreatePassword("");
                          setCreateIsAdmin(false);
                        } catch (error) {
                          const message = error instanceof Error ? error.message : "Benutzer konnte nicht angelegt werden.";
                          setCreateError(message);
                        } finally {
                          setCreatePending(false);
                        }
                      })();
                    }}
                  >
                    <label className="model-profile-field">
                      <span>Benutzername</span>
                      <input
                        className="model-dir-input"
                        type="text"
                        value={createUsername}
                        onChange={(event) => setCreateUsername(event.target.value)}
                        disabled={createPending}
                      />
                    </label>

                    <label className="model-profile-field">
                      <span>Passwort</span>
                      <input
                        className="model-dir-input"
                        type="password"
                        value={createPassword}
                        onChange={(event) => setCreatePassword(event.target.value)}
                        disabled={createPending}
                      />
                    </label>

                    <label className="model-radio-wrap model-profile-toggle">
                      <input
                        type="checkbox"
                        checked={createIsAdmin}
                        onChange={(event) => setCreateIsAdmin(event.target.checked)}
                        disabled={createPending}
                      />
                      Als Admin anlegen
                    </label>

                    <div>
                      <button type="submit" className="action-btn action-btn--primary" disabled={createPending}>
                        {createPending ? "Wird angelegt..." : "Benutzer anlegen"}
                      </button>
                    </div>

                    {createError ? <span>{createError}</span> : null}
                  </form>
                )}
              </article>
            ) : null}

            {activeSettingsGroup !== "Modelle" &&
            activeSettingsGroup !== "Modellverzeichnisse" &&
            activeSettingsGroup !== "Training" &&
            activeSettingsGroup !== "Chat" &&
            activeSettingsGroup !== "Wissen" &&
            activeSettingsGroup !== "Logs" &&
            activeSettingsGroup !== "Prompts" &&
            activeSettingsGroup !== "Benutzer" ? (
              <article className="page-card">
                <strong>{activeSettingsGroup}</strong>
                <span>{settingsGroups.find(([group]) => group === activeSettingsGroup)?.[1] ?? "Einstellungen"}</span>
                {activeSettingsGroup === "System" ? (
                  <div>
                    <button
                      type="button"
                      className="action-btn action-btn--primary"
                      onClick={() => {
                        void onExportDiagnosticsReport();
                      }}
                    >
                      Diagnosebericht exportieren
                    </button>
                  </div>
                ) : null}
              </article>
            ) : null}
          </div>
        </div>
      </PageFrame>
    );
  }

  return (
    <PageFrame title="Suche">
      <p>Globale Suche ueber Chats, Projekte, Bibliothek, Termine und Einstellungen.</p>
      <div className="card-list">
        <article className="page-card"><strong>Chats</strong><span>Angebot Waschbecken</span></article>
        <article className="page-card"><strong>Projekte</strong><span>Heisig Naturstein</span></article>
        <article className="page-card"><strong>Bibliothek</strong><span>Angebot_Klaener.pdf</span></article>
      </div>
    </PageFrame>
  );
}
