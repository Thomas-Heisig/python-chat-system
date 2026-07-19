import { startTransition, useEffect, useMemo, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ChatWorkspace } from "../components/chat/ChatWorkspace";
import { Footer } from "../components/footer/Footer";
import { Header } from "../components/header/Header";
import { RightSidebar, type RightPanelTab } from "../components/right-sidebar/RightSidebar";
import { LeftSidebar } from "../components/sidebar/LeftSidebar";
import { ToastHost, type ToastItem } from "../components/common/ToastHost";
import { WorkspacePage } from "../components/content/WorkspacePage";
import {
  applyGeneralSettingsToDocument,
  DEFAULT_GENERAL_SETTINGS,
  type GeneralSettings,
  resolveTheme,
  storeGeneralSettings,
} from "../settings/generalSettings";
import {
  activateModel,
  archiveTrainingDataset,
  archiveTrainingJob,
  assignTrainingProject,
  assignWorkspaceSourceProject,
  assignConversationProject,
  adminCreateUser,
  adminDeleteUser,
  adminKickUser,
  adminUnlockUser,
  adminUpdateUser,
  createConversation,
  createTrainingDataset,
  startTrainingFolderBatch,
  getTrainingDatasetFiles,
  importTrainingDatasetFromUrl,
  unarchiveTrainingDataset,
  unarchiveTrainingJob,
  registerTrainingDatasetFile,
  createTrainingJob,
  cancelTrainingJob,
  cancelOllamaModelPull,
  runTrainingPreflight,
  createWorkspaceProject,
  deleteWorkspaceProject,
  deleteConversation,
  deleteTrainingDataset,
  deleteTrainingJob,
  deactivateModel,
  getConversations,
  getTrainingDatasets,
  getTrainingCompatibility,
  getTrainingJobs,
  getTrainingTrainers,
  getHealthModel,
  getMessages,
  getModels,
  getPlugins,
  pullOllamaModel,
  getWorkspaceAppointments,
  getCapabilities,
  getContextUsage,
  downloadDiagnosticsReport,
  executePlugin,
  getWorkspaceProjects,
  retryTrainingJob,
  resetWorkspaceForCleanStart,
  renameWorkspaceProject,
  updateWorkspaceProjectHierarchy,
  getWorkspaceSources,
  uploadWorkspaceSource,
  getUsersPresence,
  getDiagnosticsReport,
  setModelRelevance,
  sendPresenceHeartbeat,
  getSetting,
  postUserOnlyMessage,
  renameConversation,
  scanModels,
  sendMessageStream,
  cleanupObsoleteChatSettings,
  PluginSettingsValidationError,
  updatePluginSettings,
  updateSetting,
  uploadTrainingDatasetBundle,
  uploadTrainingDataset,
} from "../services/backend";
import type {
  AuthUser,
  ChatMessage,
  ConversationSummary,
  NavView,
  SendWorkflowState,
  TrainingDatasetFileEntry,
  TrainingDatasetSummary,
  TrainingJobSummary,
  TrainingModelCompatibilityEntry,
  TrainingPreflightResult,
  TrainingTrainerOption,
  UiModelEntry,
  PluginCatalogEntry,
  PluginSettingsDrafts,
  PluginSettingField,
} from "../types/api";

type OutgoingImageAttachment = {
  name: string;
  mimeType: string;
  file: File;
};

type EncodedImageAttachment = {
  name: string;
  mime_type: string;
  data_base64: string;
};

type OutgoingChatPayload = {
  message: string;
  images: OutgoingImageAttachment[];
};

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
  projectId: string;
  artifactsDirectory: string;
  datasetsDirectory: string;
  maxConcurrentJobs: string;
  autoStartQueue: boolean;
  autoEvaluate: boolean;
  autoRegisterModel: boolean;
  autoActivateModel: boolean;
  continualTraining: boolean;
  continualModelId: string;
  archiveOnSuccess: boolean;
  deduplicateJobs: boolean;
  trainingPreset: "safe" | "balanced" | "intensive" | "custom";
  numTrainEpochs: string;
  learningRate: string;
  batchSize: string;
  gradientAccumulationSteps: string;
  maxSequenceLength: string;
  loraR: string;
  loraAlpha: string;
  loraDropout: string;
  warmupRatio: string;
  weightDecay: string;
  targetModules: string;
  loadIn4bit: boolean;
  evalSteps: string;
  saveSteps: string;
  loggingSteps: string;
  loggingFirstStep: boolean;
  maxSteps: string;
  validationSplit: string;
  loadBestModelAtEnd: boolean;
  metricForBestModel: string;
  greaterIsBetter: boolean;
  seed: string;
};

type ChatSettingsDraft = {
  pluginOrchestrationEnabled: boolean;
  autoSpecialistEnabled: boolean;
  contextLimitTokens: string;
  contextSafetyMarginTokens: string;
};

type ChatCleanupStats = {
  matchedCount: number;
  deletedCount: number;
  remainingCount: number;
  dryRun: boolean;
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

type IntegrationSettingsDraft = {
  chatgptApiKey: string;
  deeplApiKey: string;
  anthropicApiKey: string;
  googleAiApiKey: string;
  mistralApiKey: string;
  cohereApiKey: string;
  perplexityApiKey: string;
  groqApiKey: string;
  togetherApiKey: string;
  openrouterApiKey: string;
  huggingfaceApiKey: string;
  replicateApiKey: string;
  deepseekApiKey: string;
  xaiApiKey: string;
  elevenlabsApiKey: string;
  assemblyaiApiKey: string;
  tavilyApiKey: string;
  serpapiApiKey: string;
  googleMapsApiKey: string;
  mapboxApiKey: string;
  openweatherApiKey: string;
  weatherapiApiKey: string;
  tomorrowioApiKey: string;
  newsapiApiKey: string;
  twilioApiKey: string;
  sendgridApiKey: string;
  slackBotToken: string;
  discordBotToken: string;
  githubToken: string;
  notionApiKey: string;
  airtableApiKey: string;
  stripeSecretKey: string;
  azureOpenaiApiKey: string;
  awsBedrockApiKey: string;
  deepinfraApiKey: string;
  nvidiaNimApiKey: string;
  octoaiApiKey: string;
  fireworksApiKey: string;
  githubCopilotApiKey: string;
  stabilityApiKey: string;
  runwayApiKey: string;
  pikaApiKey: string;
  heygenApiKey: string;
  falApiKey: string;
  unstructuredApiKey: string;
  llamaparseApiKey: string;
  firecrawlApiKey: string;
  pineconeApiKey: string;
  weaviateApiKey: string;
  qdrantApiKey: string;
  cloudconvertApiKey: string;
  exaApiKey: string;
  braveSearchApiKey: string;
  bingSearchApiKey: string;
  gnewsApiKey: string;
  scrapingbeeApiKey: string;
  apifyApiKey: string;
  alphaVantageApiKey: string;
  yahooFinanceApiKey: string;
  openexchangeratesApiKey: string;
  whatsappBusinessApiKey: string;
  telegramBotToken: string;
  microsoftTeamsApiKey: string;
  calendlyApiKey: string;
  virustotalApiKey: string;
  hibpApiKey: string;
  ollamaLocalEnabled: boolean;
  customProviderKeysJson: string;
};

type IntegrationTestableKey =
  | "openweatherApiKey"
  | "weatherapiApiKey"
  | "tomorrowioApiKey"
  | "exaApiKey"
  | "braveSearchApiKey"
  | "bingSearchApiKey";

type IntegrationBatchResult = {
  status: "ok" | "error" | "skipped";
  message: string;
  testedAt?: string;
  durationMs?: number;
};

type IntegrationTestResults = Partial<Record<IntegrationTestableKey, IntegrationBatchResult>>;

type PluginSettingsDraft = Record<string, unknown>;
type PluginFieldErrors = Record<string, string>;

const CONVERSATION_VISIBILITY_SETTING_KEY = "conversation_visibility_map";
const CONVERSATION_AI_PARTICIPATION_SETTING_KEY = "conversation_ai_participation_map";
const AI_INTENT_MARKERS_SETTING_KEY = "ai_intent_markers";
const CONVERSATION_AI_INTENT_MARKERS_SETTING_KEY = "conversation_ai_intent_markers_map";
const DEFAULT_AI_INTENT_MARKERS = [
  "@ki",
  "@assistant",
  "@assistent",
  "ki:",
  "ki,",
  "assistant,",
  "assistent,",
  "frage an ki",
  "symple assistant",
];

const QUERY_KEY_CAPABILITIES = ["capabilities"] as const;
const QUERY_KEY_MODELS = ["models"] as const;
const QUERY_KEY_HEALTH_MODEL = ["health-model"] as const;
const QUERY_KEY_PROJECTS = ["workspace-projects"] as const;
const QUERY_KEY_APPOINTMENTS = ["workspace-appointments"] as const;
const QUERY_KEY_SOURCES = ["workspace-sources"] as const;
const QUERY_KEY_PRESENCE = ["presence", 5] as const;
const QUERY_KEY_TRAINING_DATASETS = ["training-datasets"] as const;
const QUERY_KEY_TRAINING_DATASET_FILES = ["training-dataset-files"] as const;
const QUERY_KEY_TRAINING_JOBS = ["training-jobs"] as const;
const QUERY_KEY_TRAINING_TRAINERS = ["training-trainers"] as const;
const QUERY_KEY_TRAINING_COMPATIBILITY = ["training-compatibility"] as const;
const TRAINING_JOBS_LIVE_REFETCH_MS = 2000;

function buildSettingQueryKey(category: string, key: string, userId?: number | null, teamId?: number | null) {
  return ["setting", category, key, userId ?? null, teamId ?? null] as const;
}

function buildConversationTreeSettingKey(userId: number): string {
  return `conversation_tree_user_${userId}`;
}

function makeToast(tone: ToastItem["tone"], message: string): ToastItem {
  const randomId = Math.random().toString(36).slice(2, 10);
  return { id: `toast-${randomId}`, tone, message, sticky: tone === "error" };
}

function extractErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }
  return "Unbekannter Fehler";
}

function errorContainsStatus(error: unknown, status: number): boolean {
  const message = extractErrorMessage(error);
  return message.includes(`(${status})`);
}

function getDefaultValueForType(type: PluginSettingField["type"]): unknown {
  switch (type) {
    case "boolean":
      return false;
    case "number":
      return 0;
    default:
      return "";
  }
}

function buildPluginDrafts(
  plugins: PluginCatalogEntry[],
  savedSettingsByPlugin: Record<string, Record<string, unknown>>,
): PluginSettingsDrafts {
  const drafts: PluginSettingsDrafts = {};

  for (const plugin of plugins) {
    const values: Record<string, unknown> = {};
    const savedSettings = savedSettingsByPlugin[plugin.id] ?? plugin.settings ?? {};

    for (const field of plugin.settings_fields ?? []) {
      values[field.key] =
        savedSettings[field.key] !== undefined ? savedSettings[field.key] : field.default ?? getDefaultValueForType(field.type);
    }

    drafts[plugin.id] = values;
  }

  return drafts;
}

export function AppShell({ currentUser, onLogout }: { currentUser: AuthUser; onLogout: () => void }) {
    const projectsQueryKey = [...QUERY_KEY_PROJECTS, currentUser.id] as const;
  const queryClient = useQueryClient();
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [rightHidden, setRightHidden] = useState(false);
  const [leftOverlayOpen, setLeftOverlayOpen] = useState(false);
  const [rightSheetOpen, setRightSheetOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [activeRightTab, setActiveRightTab] = useState<RightPanelTab>("context");
  const [activeNav, setActiveNav] = useState<NavView>("Chats");
  const [sendState, setSendState] = useState<SendWorkflowState>("disabled");
  const [sendError, setSendError] = useState<string | null>(null);
  const [liveReasoning, setLiveReasoning] = useState<string>("");
  const [lastSubmittedDraft, setLastSubmittedDraft] = useState<string>("");
  const [lastSubmittedImages, setLastSubmittedImages] = useState<EncodedImageAttachment[]>([]);
  const [lastSubmittedIdempotencyKey, setLastSubmittedIdempotencyKey] = useState<string | null>(null);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [conversationTree, setConversationTree] = useState<Record<number, number | null>>({});
  const [conversationVisibilityMap, setConversationVisibilityMap] = useState<Record<number, "private" | "internal" | "public">>({});
  const [conversationAiParticipationMap, setConversationAiParticipationMap] = useState<Record<number, boolean>>({});
  const [conversationAiIntentMarkersMap, setConversationAiIntentMarkersMap] = useState<Record<number, string[]>>({});
  const [aiIntentMarkersDefault, setAiIntentMarkersDefault] = useState<string[]>(DEFAULT_AI_INTENT_MARKERS);
  const [assistantDisplayName, setAssistantDisplayName] = useState("Assistent");
  const [fullscreenChat, setFullscreenChat] = useState(false);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [selectedSourceId, setSelectedSourceId] = useState<number | null>(null);
  const [performanceOpen, setPerformanceOpen] = useState(false);
  const [modelActionPending, setModelActionPending] = useState(false);
  const [modelDirectories, setModelDirectories] = useState<string[]>([]);
  const [modelDirectoryPending, setModelDirectoryPending] = useState(false);
  const [modelProfile, setModelProfile] = useState<ModelProfileDraft>({
    systemPrompt: "",
    temperature: "0.1",
    samplingTopK: "6",
    maxNewTokens: "1024",
    topK: "6",
    topP: "0.95",
    repetitionPenalty: "1.05",
    stopSequences: "<end_of_turn>, <eos>",
    seed: "42",
    doSample: true,
    preferGpu: true,
  });
  const [modelProfilePending, setModelProfilePending] = useState(false);
  const [generalSettingsPending, setGeneralSettingsPending] = useState(false);
  const [workspaceResetPending, setWorkspaceResetPending] = useState(false);
  const [generalSettings, setGeneralSettings] = useState<GeneralSettings>(DEFAULT_GENERAL_SETTINGS);
  const [trainingSettingsPending, setTrainingSettingsPending] = useState(false);
  const [trainingBatchPending, setTrainingBatchPending] = useState(false);
  const [trainingSettings, setTrainingSettings] = useState<TrainingSettingsDraft>({
    enabled: false,
    defaultTrainer: "peft_lora",
    baseModel: "",
    projectId: "",
    artifactsDirectory: "./training-artifacts",
    datasetsDirectory: "./training-datasets",
    maxConcurrentJobs: "1",
    autoStartQueue: true,
    autoEvaluate: true,
    autoRegisterModel: false,
    autoActivateModel: true,
    continualTraining: true,
    continualModelId: "",
    archiveOnSuccess: true,
    deduplicateJobs: true,
    trainingPreset: "safe",
    numTrainEpochs: "4",
    learningRate: "0.0001",
    batchSize: "1",
    gradientAccumulationSteps: "4",
    maxSequenceLength: "768",
    loraR: "16",
    loraAlpha: "32",
    loraDropout: "0.05",
    warmupRatio: "0.05",
    weightDecay: "0.01",
    targetModules: "auto",
    loadIn4bit: true,
    evalSteps: "10",
    saveSteps: "10",
    loggingSteps: "1",
    loggingFirstStep: true,
    maxSteps: "0",
    validationSplit: "0.1",
    loadBestModelAtEnd: true,
    metricForBestModel: "eval_loss",
    greaterIsBetter: false,
    seed: "42",
  });
  const [chatSettingsPending, setChatSettingsPending] = useState(false);
  const [chatCleanupPending, setChatCleanupPending] = useState(false);
  const [chatCleanupStats, setChatCleanupStats] = useState<ChatCleanupStats | null>(null);
  const [chatSettings, setChatSettings] = useState<ChatSettingsDraft>({
    pluginOrchestrationEnabled: true,
    autoSpecialistEnabled: false,
    contextLimitTokens: "8192",
    contextSafetyMarginTokens: "128",
  });
  const [knowledgeSettingsPending, setKnowledgeSettingsPending] = useState(false);
  const [knowledgeSettings, setKnowledgeSettings] = useState<KnowledgeSettingsDraft>({
    topK: "6",
    minScoreRatio: "0.5",
    minAbsoluteScore: "1000",
    minScoreGap: "400",
  });
  const [logsSettingsPending, setLogsSettingsPending] = useState(false);
  const [logsSettings, setLogsSettings] = useState<LogsSettingsDraft>({
    logLevel: "INFO",
  });
  const [integrationSettingsPending, setIntegrationSettingsPending] = useState(false);
  const [integrationSettings, setIntegrationSettings] = useState<IntegrationSettingsDraft>({
    chatgptApiKey: "",
    deeplApiKey: "",
    anthropicApiKey: "",
    googleAiApiKey: "",
    mistralApiKey: "",
    cohereApiKey: "",
    perplexityApiKey: "",
    groqApiKey: "",
    togetherApiKey: "",
    openrouterApiKey: "",
    huggingfaceApiKey: "",
    replicateApiKey: "",
    deepseekApiKey: "",
    xaiApiKey: "",
    elevenlabsApiKey: "",
    assemblyaiApiKey: "",
    tavilyApiKey: "",
    serpapiApiKey: "",
    googleMapsApiKey: "",
    mapboxApiKey: "",
    openweatherApiKey: "",
    weatherapiApiKey: "",
    tomorrowioApiKey: "",
    newsapiApiKey: "",
    twilioApiKey: "",
    sendgridApiKey: "",
    slackBotToken: "",
    discordBotToken: "",
    githubToken: "",
    notionApiKey: "",
    airtableApiKey: "",
    stripeSecretKey: "",
    azureOpenaiApiKey: "",
    awsBedrockApiKey: "",
    deepinfraApiKey: "",
    nvidiaNimApiKey: "",
    octoaiApiKey: "",
    fireworksApiKey: "",
    githubCopilotApiKey: "",
    stabilityApiKey: "",
    runwayApiKey: "",
    pikaApiKey: "",
    heygenApiKey: "",
    falApiKey: "",
    unstructuredApiKey: "",
    llamaparseApiKey: "",
    firecrawlApiKey: "",
    pineconeApiKey: "",
    weaviateApiKey: "",
    qdrantApiKey: "",
    cloudconvertApiKey: "",
    exaApiKey: "",
    braveSearchApiKey: "",
    bingSearchApiKey: "",
    gnewsApiKey: "",
    scrapingbeeApiKey: "",
    apifyApiKey: "",
    alphaVantageApiKey: "",
    yahooFinanceApiKey: "",
    openexchangeratesApiKey: "",
    whatsappBusinessApiKey: "",
    telegramBotToken: "",
    microsoftTeamsApiKey: "",
    calendlyApiKey: "",
    virustotalApiKey: "",
    hibpApiKey: "",
    ollamaLocalEnabled: false,
    customProviderKeysJson: "",
  });
  const [integrationTestResults, setIntegrationTestResults] = useState<IntegrationTestResults>({});
  const [pluginDescriptors, setPluginDescriptors] = useState<PluginCatalogEntry[]>([]);
  const [pluginSettingsDrafts, setPluginSettingsDrafts] = useState<PluginSettingsDrafts>({});
  const [pluginSettingsErrors, setPluginSettingsErrors] = useState<Record<string, PluginFieldErrors>>({});
  const [savingPluginId, setSavingPluginId] = useState<string | null>(null);
  const [trainingPreflightPending, setTrainingPreflightPending] = useState(false);
  const [trainingPreflightResult, setTrainingPreflightResult] = useState<TrainingPreflightResult | null>(null);
  const conversationTreeSettingKey = useMemo(() => buildConversationTreeSettingKey(currentUser.id), [currentUser.id]);
  const activeStreamControllerRef = useRef<AbortController | null>(null);
  const sendStateRef = useRef<SendWorkflowState>("disabled");
  const messagePollTimerRef = useRef<number | null>(null);
  const messagePollInFlightRef = useRef(false);
  const presencePollTimerRef = useRef<number | null>(null);
  const presencePollInFlightRef = useRef(false);

  const resetSendStateLater = (delayMs: number): void => {
    window.setTimeout(() => {
      startTransition(() => {
        setSendState(modelLoaded ? "idle" : "disabled");
      });
    }, delayMs);
  };

  const capabilitiesQuery = useQuery({
    queryKey: QUERY_KEY_CAPABILITIES,
    queryFn: async () => getCapabilities().catch(() => null),
  });

  const modelsQuery = useQuery({
    queryKey: QUERY_KEY_MODELS,
    queryFn: getModels,
    refetchInterval: (query) => {
      const currentModels = query.state.data as UiModelEntry[] | undefined;
      return currentModels?.some((model) => {
        const state = model.pullStatus?.state;
        return state === "queued" || state === "pulling";
      })
        ? 1000
        : false;
    },
  });

  const healthModelQuery = useQuery({
    queryKey: QUERY_KEY_HEALTH_MODEL,
    queryFn: getHealthModel,
  });

  const projectsQuery = useQuery({
    queryKey: projectsQueryKey,
    queryFn: () => getWorkspaceProjects(currentUser.id),
  });

  const appointmentsQuery = useQuery({
    queryKey: QUERY_KEY_APPOINTMENTS,
    queryFn: getWorkspaceAppointments,
  });

  const sourcesQuery = useQuery({
    queryKey: QUERY_KEY_SOURCES,
    queryFn: () => getWorkspaceSources(currentUser.id),
  });

  const conversationsQuery = useQuery({
    queryKey: ["conversations", currentUser.id],
    queryFn: () => getConversations(currentUser.id),
  });

  const messagesQuery = useQuery({
    queryKey: ["messages", currentUser.id, activeConversationId],
    queryFn: () => getMessages(activeConversationId as number, 200, currentUser.id),
    enabled: activeConversationId != null,
  });

  const presenceQuery = useQuery({
    queryKey: QUERY_KEY_PRESENCE,
    queryFn: () => getUsersPresence(5),
    enabled: Boolean(capabilitiesQuery.data?.features?.["auth.users_presence"]),
  });

  const contextUsageQuery = useQuery({
    queryKey: ["context-usage", currentUser.id, activeConversationId],
    queryFn: () => getContextUsage(currentUser.id, activeConversationId),
    enabled: activeNav === "Chats",
  });

  const trainingDatasetsQuery = useQuery({
    queryKey: [...QUERY_KEY_TRAINING_DATASETS, currentUser.id],
    queryFn: () => getTrainingDatasets(currentUser.id, true),
    enabled: activeNav === "Einstellungen",
  });

  const trainingDatasetFilesQuery = useQuery({
    queryKey: [...QUERY_KEY_TRAINING_DATASET_FILES, currentUser.id],
    queryFn: () => getTrainingDatasetFiles(currentUser.id),
    enabled: activeNav === "Einstellungen",
  });

  const trainingJobsQuery = useQuery({
    queryKey: [...QUERY_KEY_TRAINING_JOBS, currentUser.id],
    queryFn: () => getTrainingJobs(currentUser.id, true),
    enabled: activeNav === "Einstellungen",
    refetchInterval: (query) => {
      if (activeNav !== "Einstellungen") {
        return false;
      }
      const jobs = query.state.data as TrainingJobSummary[] | undefined;
      const hasActiveJob =
        jobs?.some((job) => {
          const status = job.status.trim().toLowerCase();
          return status === "queued" || status === "running" || status === "in_progress" || status === "processing";
        }) ?? false;
      return hasActiveJob ? TRAINING_JOBS_LIVE_REFETCH_MS : false;
    },
    refetchIntervalInBackground: true,
  });

  const trainingTrainersQuery = useQuery({
    queryKey: QUERY_KEY_TRAINING_TRAINERS,
    queryFn: getTrainingTrainers,
    enabled: activeNav === "Einstellungen",
  });

  const compatibilityTrainer = trainingSettings.defaultTrainer.trim().toLowerCase() || "peft_lora";
  const trainingCompatibilityQuery = useQuery({
    queryKey: [...QUERY_KEY_TRAINING_COMPATIBILITY, compatibilityTrainer],
    queryFn: () => getTrainingCompatibility(compatibilityTrainer),
    enabled: activeNav === "Einstellungen" && compatibilityTrainer.length > 0,
  });

  const capabilities = capabilitiesQuery.data ?? null;
  const models = modelsQuery.data ?? [];
  const chatSelectableModels = models.filter((model) => model.capabilities?.supportsChat ?? true);
  const modelLoaded = healthModelQuery.data?.loaded ?? false;
  const projects = projectsQuery.data ?? [];
  const appointments = appointmentsQuery.data ?? [];
  const sources = sourcesQuery.data ?? [];
  const conversations: ConversationSummary[] = conversationsQuery.data ?? [];
  const messages: ChatMessage[] = messagesQuery.data ?? [];
  const presenceUsers = presenceQuery.data ?? [];
  const contextUsage = contextUsageQuery.data ?? null;
  const trainingDatasets: TrainingDatasetSummary[] = trainingDatasetsQuery.data ?? [];
  const trainingDatasetFiles: TrainingDatasetFileEntry[] = trainingDatasetFilesQuery.data ?? [];
  const trainingJobs: TrainingJobSummary[] = trainingJobsQuery.data ?? [];
  const trainerOptions: TrainingTrainerOption[] = trainingTrainersQuery.data ?? [];
  const trainingCompatibilityEntries: TrainingModelCompatibilityEntry[] = trainingCompatibilityQuery.data ?? [];
  const trainingCompatibility: Record<string, { compatible: boolean; reason: string | null }> = Object.fromEntries(
    trainingCompatibilityEntries.map((entry) => [entry.modelId, { compatible: entry.compatible, reason: entry.reason }]),
  );

  const fetchTrainingCompatibility = async (trainerName: string) => {
    const normalized = trainerName.trim().toLowerCase();
    if (!normalized) {
      return {} as Record<string, { compatible: boolean; reason: string | null }>;
    }
    const entries = await queryClient.fetchQuery({
      queryKey: [...QUERY_KEY_TRAINING_COMPATIBILITY, normalized],
      queryFn: () => getTrainingCompatibility(normalized),
    });
    return Object.fromEntries(entries.map((entry) => [entry.modelId, { compatible: entry.compatible, reason: entry.reason }]));
  };
  const selectedConversation = conversations.find((item) => item.id === activeConversationId) ?? null;
  const canModifySelectedConversation =
    selectedConversation != null && selectedConversation.ownerUserId === currentUser.id;
  const canAssignSelectedConversationProject = selectedConversation != null;
  const selectedChatTitle = selectedConversation?.title ?? "Neue Konversation";
  const selectedChatProjectId = selectedConversation?.projectId ?? null;
  const projectById = useMemo(() => new Map(projects.map((project) => [project.id, project] as const)), [projects]);

  const handleSelectProject = (projectId: number | null) => {
    setSelectedProjectId(projectId);
  };

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

  const selectedProjectIdForLabel = selectedChatProjectId ?? selectedProjectId ?? -1;
  const selectedProject = projects.find((project) => project.id === selectedProjectIdForLabel) ?? null;
  const selectedProjectLabel = selectedProject != null ? buildProjectDisplayName(selectedProject.id) : "Kein Projekt";
  const selectedChatScope = useMemo(() => {
    const lineage: number[] = [];
    const seen = new Set<number>();
    let cursor: number | null = selectedChatProjectId;

    while (cursor != null && !seen.has(cursor)) {
      seen.add(cursor);
      const project = projectById.get(cursor);
      if (project == null) {
        break;
      }
      lineage.push(project.id);
      cursor = typeof project.parent_project_id === "number" && project.parent_project_id > 0 ? project.parent_project_id : null;
    }

    const orderedLineage = lineage.reverse();
    const scopeDepthByProjectId = new Map<number, number>();
    orderedLineage.forEach((projectId, index) => {
      scopeDepthByProjectId.set(projectId, index);
    });

    return {
      projectIds: new Set<number>(orderedLineage),
      scopeDepthByProjectId,
    };
  }, [projectById, selectedChatProjectId]);

  const chatSources = useMemo(() => {
    if (selectedChatProjectId == null) {
      return sources
        .filter((source) => source.project_id == null)
        .map((source) => ({
          ...source,
          projectLabel: "Unzugeordnet",
          scopeDepth: null,
        }));
    }

    return sources
      .filter((source) => typeof source.project_id === "number" && selectedChatScope.projectIds.has(source.project_id))
      .map((source) => ({
        ...source,
        projectLabel:
          typeof source.project_id === "number"
            ? buildProjectDisplayName(source.project_id)
            : "Unzugeordnet",
        scopeDepth:
          typeof source.project_id === "number"
            ? selectedChatScope.scopeDepthByProjectId.get(source.project_id) ?? null
            : null,
      }));
  }, [buildProjectDisplayName, selectedChatProjectId, selectedChatScope, sources]);

  const reloadModelState = async (preferredModelId?: string) => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: QUERY_KEY_MODELS }),
      queryClient.invalidateQueries({ queryKey: QUERY_KEY_HEALTH_MODEL }),
    ]);

    const [reloadedModels, healthModel] = await Promise.all([
      queryClient.fetchQuery({ queryKey: QUERY_KEY_MODELS, queryFn: getModels }),
      queryClient.fetchQuery({ queryKey: QUERY_KEY_HEALTH_MODEL, queryFn: getHealthModel }),
    ]);

    const resolvedModelId =
      preferredModelId ??
      (healthModel.activeModelId != null ? String(healthModel.activeModelId) : null) ??
      reloadedModels.find((model) => model.isActive)?.id ??
      reloadedModels[0]?.id ??
      "";

    setSelectedModelId(resolvedModelId);
    return reloadedModels;
  };

  const getSettingCached = async (category: string, key: string, userId?: number | null, teamId?: number | null) => {
    const queryKey = buildSettingQueryKey(category, key, userId, teamId);
    return queryClient.fetchQuery({
      queryKey,
      queryFn: () => getSetting(category, key, userId ?? undefined),
    });
  };

  const updateSettingWithCache = async (
    category: string,
    key: string,
    value: unknown,
    userId?: number | null,
    teamId?: number | null,
  ) => {
    const effect = await updateSetting(category, key, value, userId ?? undefined);
    queryClient.setQueryData(buildSettingQueryKey(category, key, userId, teamId), value);
    await queryClient.invalidateQueries({ queryKey: ["setting", category, key] });
    return effect;
  };

  const handleActivateModel = async (modelId: string) => {
    setModelActionPending(true);
    setSelectedModelId(modelId);

    try {
      await activateModel(modelId);
      const reloadedModels = await reloadModelState(modelId);
      const model = reloadedModels.find((entry) => entry.id === modelId);
      if (model) {
        pushToast("success", `Modell ${model.name} ist aktiv`);
      }
    } catch (error) {
      const detail = extractErrorMessage(error);
      pushToast("error", `Modellwechsel fehlgeschlagen: ${detail}`);
    } finally {
      setModelActionPending(false);
    }
  };

  const handlePullModel = async (modelId: string) => {
    setModelActionPending(true);
    try {
      const result = await pullOllamaModel(modelId);
      await queryClient.invalidateQueries({ queryKey: QUERY_KEY_MODELS });
      if (result.started) {
        pushToast("info", result.detail ?? "Ollama-Download gestartet.");
      } else {
        pushToast("info", result.detail ?? "Ollama-Modell ist bereits lokal verfuegbar.");
      }
    } catch (error) {
      pushToast("error", `Ollama-Download konnte nicht gestartet werden: ${extractErrorMessage(error)}`);
    } finally {
      setModelActionPending(false);
    }
  };

  const handleCancelPullModel = async (modelId: string) => {
    setModelActionPending(true);
    try {
      const result = await cancelOllamaModelPull(modelId);
      await queryClient.invalidateQueries({ queryKey: QUERY_KEY_MODELS });
      pushToast("info", result.detail ?? (result.cancelled ? "Ollama-Download wird abgebrochen." : "Kein aktiver Download gefunden."));
    } catch (error) {
      pushToast("error", `Ollama-Download konnte nicht abgebrochen werden: ${extractErrorMessage(error)}`);
    } finally {
      setModelActionPending(false);
    }
  };

  const handleDeactivateModel = async () => {
    setModelActionPending(true);
    try {
      await deactivateModel();
      await reloadModelState(selectedModelId);
      pushToast("info", "Modell entladen.");
    } catch {
      pushToast("error", "Modell konnte nicht entladen werden.");
    } finally {
      setModelActionPending(false);
    }
  };

  const handleScanModels = async () => {
    setModelActionPending(true);
    try {
      const result = await scanModels();
      await reloadModelState(selectedModelId);
      pushToast("info", `Scan abgeschlossen: ${result.discovered} gefunden, ${result.inserted} neu.`);
    } catch {
      pushToast("error", "Modellscan fehlgeschlagen.");
    } finally {
      setModelActionPending(false);
    }
  };

  const handleSetModelRelevance = async (modelId: string, relevance: "favorite" | "irrelevant" | null) => {
    setModelActionPending(true);
    try {
      await setModelRelevance(modelId, relevance, currentUser.id);
      await reloadModelState(selectedModelId);
      pushToast("success", "Modell-Relevanz aktualisiert.");
    } catch {
      pushToast("error", "Modell-Relevanz konnte nicht gespeichert werden.");
    } finally {
      setModelActionPending(false);
    }
  };

  const loadModelDirectories = async () => {
    const value = await getSettingCached("model", "base_directories", currentUser.id);
    if (Array.isArray(value)) {
      const normalized = value
        .filter((item): item is string | number => typeof item === "string" || typeof item === "number")
        .map((item) => String(item));
      setModelDirectories(normalized);
      return;
    }
    setModelDirectories([]);
  };

  const loadGeneralSettings = async () => {
    const [languageValue, themeValue, timezoneValue] = await Promise.all([
      getSettingCached("system", "language", currentUser.id),
      getSettingCached("system", "theme", currentUser.id),
      getSettingCached("system", "timezone", currentUser.id),
    ]);

    const language = languageValue === "en" ? "en" : "de";
    const theme =
      themeValue === "light" || themeValue === "dark" || themeValue === "system"
        ? themeValue
        : "system";
    const timezone =
      typeof timezoneValue === "string" && timezoneValue.trim().length > 0
        ? timezoneValue.trim()
        : "Europe/Berlin";

    const resolved: GeneralSettings = {
      language,
      theme,
      timezone,
    };

    setGeneralSettings(resolved);
    storeGeneralSettings(resolved);
  };

  const loadModelProfile = async (modelId: string) => {
    if (!modelId) {
      setModelProfile({
        systemPrompt: "",
        temperature: "0.1",
        samplingTopK: "6",
        maxNewTokens: "1024",
        topK: "6",
        topP: "0.95",
        repetitionPenalty: "1.05",
        stopSequences: "<end_of_turn>, <eos>",
        seed: "42",
        doSample: true,
        preferGpu: true,
      });
      return;
    }

    const [
      promptValue,
      globalPromptValue,
      temperatureValue,
      maxTokensValue,
      samplingTopKValue,
      topKValue,
      topPValue,
      repetitionPenaltyValue,
      stopSequencesValue,
      seedValue,
      doSampleValue,
      preferGpuValue,
    ] = await Promise.all([
      getSettingCached("prompt", `model_${modelId}_system_prompt`, currentUser.id),
      getSettingCached("prompt", "system_prompt", currentUser.id),
      getSettingCached("chat", `model_${modelId}_temperature`, currentUser.id),
      getSettingCached("chat", `model_${modelId}_max_new_tokens`, currentUser.id),
      getSettingCached("chat", `model_${modelId}_top_k`, currentUser.id),
      getSettingCached("knowledge", `model_${modelId}_top_k`, currentUser.id),
      getSettingCached("chat", `model_${modelId}_top_p`, currentUser.id),
      getSettingCached("chat", `model_${modelId}_repetition_penalty`, currentUser.id),
      getSettingCached("chat", `model_${modelId}_stop_sequences`, currentUser.id),
      getSettingCached("chat", `model_${modelId}_seed`, currentUser.id),
      getSettingCached("chat", `model_${modelId}_do_sample`, currentUser.id),
      getSettingCached("model", `model_${modelId}_prefer_gpu`, currentUser.id),
    ]);

    const normalizedStopSequences = Array.isArray(stopSequencesValue)
      ? stopSequencesValue
          .filter((item): item is string => typeof item === "string")
          .map((item) => item.trim())
          .filter((item) => item.length > 0)
      : ["<end_of_turn>", "<eos>"];

    setModelProfile({
      systemPrompt:
        typeof promptValue === "string" && promptValue.trim().length > 0
          ? promptValue
          : typeof globalPromptValue === "string"
            ? globalPromptValue
            : "",
      temperature: String(typeof temperatureValue === "number" ? temperatureValue : 0.1),
      samplingTopK: String(typeof samplingTopKValue === "number" ? samplingTopKValue : 6),
      maxNewTokens: String(typeof maxTokensValue === "number" ? maxTokensValue : 1024),
      topK: String(typeof topKValue === "number" ? topKValue : 6),
      topP: String(typeof topPValue === "number" ? topPValue : 0.95),
      repetitionPenalty: String(typeof repetitionPenaltyValue === "number" ? repetitionPenaltyValue : 1.05),
      stopSequences: normalizedStopSequences.join(", "),
      seed: String(typeof seedValue === "number" ? seedValue : 42),
      doSample: typeof doSampleValue === "boolean" ? doSampleValue : true,
      preferGpu: typeof preferGpuValue === "boolean" ? preferGpuValue : true,
    });
  };

  const handleSaveModelDirectories = async (directories: string[]) => {
    setModelDirectoryPending(true);
    try {
      const normalized = directories.map((item) => item.trim()).filter((item) => item.length > 0);
      await updateSettingWithCache("model", "base_directories", normalized, currentUser.id);
      setModelDirectories(normalized);
      await handleScanModels();
      pushToast("success", "Modellverzeichnisse gespeichert.");
    } catch {
      pushToast("error", "Modellverzeichnisse konnten nicht gespeichert werden.");
    } finally {
      setModelDirectoryPending(false);
    }
  };

  const handleSaveModelProfile = async (profile: ModelProfileDraft) => {
    if (!selectedModelId) {
      pushToast("error", "Bitte zuerst ein Modell auswaehlen.");
      return;
    }

    setModelProfilePending(true);
    try {
      const temperatureNumber = Number(profile.temperature);
      const maxTokensNumber = Number(profile.maxNewTokens);
      const samplingTopKNumber = Number(profile.samplingTopK);
      const topKNumber = Number(profile.topK);
      const topPNumber = Number(profile.topP);
      const repetitionPenaltyNumber = Number(profile.repetitionPenalty);
      const seedNumber = Number(profile.seed);
      const stopSequences = profile.stopSequences
        .split(",")
        .map((item) => item.trim())
        .filter((item) => item.length > 0);

      await Promise.all([
        updateSettingWithCache("prompt", `model_${selectedModelId}_system_prompt`, profile.systemPrompt.trim(), currentUser.id),
        updateSettingWithCache(
          "chat",
          `model_${selectedModelId}_temperature`,
          Number.isFinite(temperatureNumber) ? temperatureNumber : 0.1,
          currentUser.id,
        ),
        updateSettingWithCache(
          "chat",
          `model_${selectedModelId}_max_new_tokens`,
          Number.isFinite(maxTokensNumber) ? Math.max(1, Math.round(maxTokensNumber)) : 1024,
          currentUser.id,
        ),
        updateSettingWithCache(
          "chat",
          `model_${selectedModelId}_top_k`,
          Number.isFinite(samplingTopKNumber) ? Math.max(0, Math.round(samplingTopKNumber)) : 6,
          currentUser.id,
        ),
        updateSettingWithCache(
          "knowledge",
          `model_${selectedModelId}_top_k`,
          Number.isFinite(topKNumber) ? Math.max(1, Math.round(topKNumber)) : 6,
          currentUser.id,
        ),
        updateSettingWithCache(
          "chat",
          `model_${selectedModelId}_top_p`,
          Number.isFinite(topPNumber) ? Math.min(1, Math.max(0.01, topPNumber)) : 0.95,
          currentUser.id,
        ),
        updateSettingWithCache(
          "chat",
          `model_${selectedModelId}_repetition_penalty`,
          Number.isFinite(repetitionPenaltyNumber) ? Math.min(2, Math.max(0.5, repetitionPenaltyNumber)) : 1.05,
          currentUser.id,
        ),
        updateSettingWithCache(
          "chat",
          `model_${selectedModelId}_stop_sequences`,
          stopSequences.length > 0 ? stopSequences : ["<end_of_turn>", "<eos>"],
          currentUser.id,
        ),
        updateSettingWithCache(
          "chat",
          `model_${selectedModelId}_seed`,
          Number.isFinite(seedNumber) ? Math.max(0, Math.round(seedNumber)) : 42,
          currentUser.id,
        ),
        updateSettingWithCache("chat", `model_${selectedModelId}_do_sample`, profile.doSample, currentUser.id),
        updateSettingWithCache("model", `model_${selectedModelId}_prefer_gpu`, profile.preferGpu, currentUser.id),
      ]);

      setModelProfile(profile);
      pushToast("success", "Modell-spezifische Prompts und Einstellungen gespeichert.");
    } catch {
      pushToast("error", "Modell-spezifische Einstellungen konnten nicht gespeichert werden.");
    } finally {
      setModelProfilePending(false);
    }
  };

  const loadTrainingSettings = async () => {
    const [
      enabledValue,
      defaultTrainerValue,
      baseModelValue,
      projectIdValue,
      artifactsDirectoryValue,
      datasetsDirectoryValue,
      maxConcurrentJobsValue,
      autoStartQueueValue,
      autoEvaluateValue,
      autoRegisterModelValue,
      continualTrainingValue,
      autoActivateModelValue,
      continualModelIdValue,
      archiveOnSuccessValue,
      deduplicateJobsValue,
      trainingPresetValue,
      numTrainEpochsValue,
      learningRateValue,
      batchSizeValue,
      gradientAccumulationStepsValue,
      maxSequenceLengthValue,
      loraRValue,
      loraAlphaValue,
      loraDropoutValue,
      warmupRatioValue,
      weightDecayValue,
      targetModulesValue,
      loadIn4bitValue,
      evalStepsValue,
      saveStepsValue,
      loggingStepsValue,
      loggingFirstStepValue,
      maxStepsValue,
      validationSplitValue,
      loadBestModelAtEndValue,
      metricForBestModelValue,
      greaterIsBetterValue,
      seedValue,
    ] = await Promise.all([
      getSettingCached("training", "enabled", currentUser.id),
      getSettingCached("training", "default_trainer", currentUser.id),
      getSettingCached("training", "base_model", currentUser.id),
      getSettingCached("training", "project_id", currentUser.id),
      getSettingCached("training", "artifacts_directory", currentUser.id),
      getSettingCached("training", "datasets_directory", currentUser.id),
      getSettingCached("training", "max_concurrent_jobs", currentUser.id),
      getSettingCached("training", "auto_start_queue", currentUser.id),
      getSettingCached("training", "auto_evaluate", currentUser.id),
      getSettingCached("training", "auto_register_model", currentUser.id),
      getSettingCached("training", "continual_training", currentUser.id),
      getSettingCached("training", "auto_activate_model", currentUser.id),
      getSettingCached("training", "continual_model_id", currentUser.id),
      getSettingCached("training", "archive_on_success", currentUser.id),
      getSettingCached("training", "deduplicate_jobs", currentUser.id),
      getSettingCached("training", "training_preset", currentUser.id),
      getSettingCached("training", "num_train_epochs", currentUser.id),
      getSettingCached("training", "learning_rate", currentUser.id),
      getSettingCached("training", "per_device_train_batch_size", currentUser.id),
      getSettingCached("training", "gradient_accumulation_steps", currentUser.id),
      getSettingCached("training", "max_sequence_length", currentUser.id),
      getSettingCached("training", "lora_r", currentUser.id),
      getSettingCached("training", "lora_alpha", currentUser.id),
      getSettingCached("training", "lora_dropout", currentUser.id),
      getSettingCached("training", "warmup_ratio", currentUser.id),
      getSettingCached("training", "weight_decay", currentUser.id),
      getSettingCached("training", "target_modules", currentUser.id),
      getSettingCached("training", "load_in_4bit", currentUser.id),
      getSettingCached("training", "eval_steps", currentUser.id),
      getSettingCached("training", "save_steps", currentUser.id),
      getSettingCached("training", "logging_steps", currentUser.id),
      getSettingCached("training", "logging_first_step", currentUser.id),
      getSettingCached("training", "max_steps", currentUser.id),
      getSettingCached("training", "validation_split", currentUser.id),
      getSettingCached("training", "load_best_model_at_end", currentUser.id),
      getSettingCached("training", "metric_for_best_model", currentUser.id),
      getSettingCached("training", "greater_is_better", currentUser.id),
      getSettingCached("training", "seed", currentUser.id),
    ]);

    setTrainingSettings({
      enabled: typeof enabledValue === "boolean" ? enabledValue : false,
      defaultTrainer:
        typeof defaultTrainerValue === "string" && defaultTrainerValue.trim().length > 0
          ? defaultTrainerValue.trim()
          : "peft_lora",
      baseModel: typeof baseModelValue === "string" ? baseModelValue.trim() : "",
      projectId: typeof projectIdValue === "number" ? String(projectIdValue) : "",
      artifactsDirectory:
        typeof artifactsDirectoryValue === "string" && artifactsDirectoryValue.trim().length > 0
          ? artifactsDirectoryValue.trim()
          : "./training-artifacts",
      datasetsDirectory:
        typeof datasetsDirectoryValue === "string" && datasetsDirectoryValue.trim().length > 0
          ? datasetsDirectoryValue.trim()
          : "./training-datasets",
      maxConcurrentJobs: String(typeof maxConcurrentJobsValue === "number" ? maxConcurrentJobsValue : 1),
      autoStartQueue: typeof autoStartQueueValue === "boolean" ? autoStartQueueValue : true,
      autoEvaluate: typeof autoEvaluateValue === "boolean" ? autoEvaluateValue : true,
      autoRegisterModel: typeof autoRegisterModelValue === "boolean" ? autoRegisterModelValue : false,
      continualTraining: typeof continualTrainingValue === "boolean" ? continualTrainingValue : true,
      autoActivateModel: typeof autoActivateModelValue === "boolean" ? autoActivateModelValue : true,
      continualModelId: typeof continualModelIdValue === "number" ? String(continualModelIdValue) : "",
      archiveOnSuccess: typeof archiveOnSuccessValue === "boolean" ? archiveOnSuccessValue : true,
      deduplicateJobs: typeof deduplicateJobsValue === "boolean" ? deduplicateJobsValue : true,
      trainingPreset:
        trainingPresetValue === "balanced" || trainingPresetValue === "intensive" || trainingPresetValue === "custom"
          ? trainingPresetValue
          : "safe",
      numTrainEpochs: String(typeof numTrainEpochsValue === "number" ? numTrainEpochsValue : 4),
      learningRate: String(typeof learningRateValue === "number" ? learningRateValue : 0.0001),
      batchSize: String(typeof batchSizeValue === "number" ? batchSizeValue : 1),
      gradientAccumulationSteps: String(typeof gradientAccumulationStepsValue === "number" ? gradientAccumulationStepsValue : 4),
      maxSequenceLength: String(typeof maxSequenceLengthValue === "number" ? maxSequenceLengthValue : 768),
      loraR: String(typeof loraRValue === "number" ? loraRValue : 16),
      loraAlpha: String(typeof loraAlphaValue === "number" ? loraAlphaValue : 32),
      loraDropout: String(typeof loraDropoutValue === "number" ? loraDropoutValue : 0.05),
      warmupRatio: String(typeof warmupRatioValue === "number" ? warmupRatioValue : 0.05),
      weightDecay: String(typeof weightDecayValue === "number" ? weightDecayValue : 0.01),
      targetModules: Array.isArray(targetModulesValue) ? targetModulesValue.join(", ") : "auto",
      loadIn4bit: typeof loadIn4bitValue === "boolean" ? loadIn4bitValue : true,
      evalSteps: String(typeof evalStepsValue === "number" ? evalStepsValue : 10),
      saveSteps: String(typeof saveStepsValue === "number" ? saveStepsValue : 10),
      loggingSteps: String(typeof loggingStepsValue === "number" ? loggingStepsValue : 1),
      loggingFirstStep: typeof loggingFirstStepValue === "boolean" ? loggingFirstStepValue : true,
      maxSteps: String(typeof maxStepsValue === "number" ? maxStepsValue : 0),
      validationSplit: String(typeof validationSplitValue === "number" ? validationSplitValue : 0.1),
      loadBestModelAtEnd: typeof loadBestModelAtEndValue === "boolean" ? loadBestModelAtEndValue : true,
      metricForBestModel:
        typeof metricForBestModelValue === "string" && metricForBestModelValue.trim().length > 0
          ? metricForBestModelValue.trim()
          : "eval_loss",
      greaterIsBetter: typeof greaterIsBetterValue === "boolean" ? greaterIsBetterValue : false,
      seed: String(typeof seedValue === "number" ? seedValue : 42),
    });
  };

  const handleSaveTrainingSettings = async (profile: TrainingSettingsDraft) => {
    setTrainingSettingsPending(true);
    try {
      const normalizedTrainer = profile.defaultTrainer.trim().toLowerCase() || "peft_lora";
      const selectedTrainer = trainerOptions.find((item) => item.id === normalizedTrainer);
      if (selectedTrainer && !selectedTrainer.available) {
        pushToast("error", selectedTrainer.reasonUnavailable ?? "Ausgewaehlter Trainer ist nicht verfuegbar.");
        return;
      }
      const normalizedBaseModel = profile.baseModel.trim();
      const projectId = Number(profile.projectId);
      const normalizedProjectId = Number.isInteger(projectId) && projectId > 0 ? projectId : null;
      const normalizedArtifactsDirectory = profile.artifactsDirectory.trim() || "./training-artifacts";
      const normalizedDatasetsDirectory = profile.datasetsDirectory.trim() || "./training-datasets";
      const maxConcurrentJobsNumber = Number(profile.maxConcurrentJobs);
      const normalizedMaxConcurrentJobs = profile.continualTraining
        ? 1
        : (Number.isFinite(maxConcurrentJobsNumber) ? Math.max(1, Math.round(maxConcurrentJobsNumber)) : 1);
      const clampNumber = (value: string, fallback: number, minimum: number, maximum: number) => {
        const parsed = Number(value);
        return Number.isFinite(parsed) ? Math.min(maximum, Math.max(minimum, parsed)) : fallback;
      };
      const clampInteger = (value: string, fallback: number, minimum: number, maximum: number) =>
        Math.round(clampNumber(value, fallback, minimum, maximum));
      const targetModules = profile.targetModules.split(",").map((item) => item.trim()).filter(Boolean);
      const continualModelId = Number(profile.continualModelId);
      const normalizedHyperparameters = {
        numTrainEpochs: clampNumber(profile.numTrainEpochs, 4, 0.1, 20),
        learningRate: clampNumber(profile.learningRate, 0.0001, 0.0000001, 1),
        batchSize: clampInteger(profile.batchSize, 1, 1, 64),
        gradientAccumulationSteps: clampInteger(profile.gradientAccumulationSteps, 4, 1, 256),
        maxSequenceLength: clampInteger(profile.maxSequenceLength, 768, 128, 32768),
        loraR: clampInteger(profile.loraR, 16, 1, 1024),
        loraAlpha: clampInteger(profile.loraAlpha, 32, 1, 4096),
        loraDropout: clampNumber(profile.loraDropout, 0.05, 0, 0.8),
        warmupRatio: clampNumber(profile.warmupRatio, 0.05, 0, 0.5),
        weightDecay: clampNumber(profile.weightDecay, 0.01, 0, 1),
        evalSteps: clampInteger(profile.evalSteps, 10, 1, 1000000),
        saveSteps: clampInteger(profile.saveSteps, 10, 10, 1000000),
        loggingSteps: clampInteger(profile.loggingSteps, 1, 1, 1000000),
        maxSteps: clampInteger(profile.maxSteps, 0, 0, 10000000),
        validationSplit: clampNumber(profile.validationSplit, 0.1, 0.02, 0.3),
        seed: clampInteger(profile.seed, 42, 0, 2147483647),
      };
      const normalizedMetricForBestModel = profile.metricForBestModel.trim().length > 0 ? profile.metricForBestModel.trim() : "eval_loss";

      await Promise.all([
        updateSettingWithCache("training", "enabled", profile.enabled, currentUser.id),
        updateSettingWithCache("training", "default_trainer", normalizedTrainer, currentUser.id),
        updateSettingWithCache("training", "base_model", normalizedBaseModel, currentUser.id),
        updateSettingWithCache("training", "project_id", normalizedProjectId, currentUser.id),
        updateSettingWithCache("training", "artifacts_directory", normalizedArtifactsDirectory, currentUser.id),
        updateSettingWithCache("training", "datasets_directory", normalizedDatasetsDirectory, currentUser.id),
        updateSettingWithCache(
          "training",
          "max_concurrent_jobs",
          normalizedMaxConcurrentJobs,
          currentUser.id,
        ),
        updateSettingWithCache("training", "auto_start_queue", profile.autoStartQueue, currentUser.id),
        updateSettingWithCache("training", "auto_evaluate", profile.autoEvaluate, currentUser.id),
        updateSettingWithCache("training", "auto_register_model", profile.continualTraining ? true : profile.autoRegisterModel, currentUser.id),
        updateSettingWithCache("training", "continual_training", profile.continualTraining, currentUser.id),
        updateSettingWithCache("training", "auto_activate_model", profile.autoActivateModel, currentUser.id),
        updateSettingWithCache(
          "training",
          "continual_model_id",
          Number.isInteger(continualModelId) && continualModelId > 0 ? continualModelId : null,
          currentUser.id,
        ),
        updateSettingWithCache("training", "archive_on_success", profile.archiveOnSuccess, currentUser.id),
        updateSettingWithCache("training", "deduplicate_jobs", profile.deduplicateJobs, currentUser.id),
        updateSettingWithCache("training", "training_preset", profile.trainingPreset, currentUser.id),
        updateSettingWithCache("training", "num_train_epochs", normalizedHyperparameters.numTrainEpochs, currentUser.id),
        updateSettingWithCache("training", "learning_rate", normalizedHyperparameters.learningRate, currentUser.id),
        updateSettingWithCache("training", "per_device_train_batch_size", normalizedHyperparameters.batchSize, currentUser.id),
        updateSettingWithCache("training", "gradient_accumulation_steps", normalizedHyperparameters.gradientAccumulationSteps, currentUser.id),
        updateSettingWithCache("training", "max_sequence_length", normalizedHyperparameters.maxSequenceLength, currentUser.id),
        updateSettingWithCache("training", "lora_r", normalizedHyperparameters.loraR, currentUser.id),
        updateSettingWithCache("training", "lora_alpha", normalizedHyperparameters.loraAlpha, currentUser.id),
        updateSettingWithCache("training", "lora_dropout", normalizedHyperparameters.loraDropout, currentUser.id),
        updateSettingWithCache("training", "warmup_ratio", normalizedHyperparameters.warmupRatio, currentUser.id),
        updateSettingWithCache("training", "weight_decay", normalizedHyperparameters.weightDecay, currentUser.id),
        updateSettingWithCache("training", "target_modules", targetModules.length > 0 ? targetModules : ["auto"], currentUser.id),
        updateSettingWithCache("training", "load_in_4bit", profile.loadIn4bit, currentUser.id),
        updateSettingWithCache("training", "eval_steps", normalizedHyperparameters.evalSteps, currentUser.id),
        updateSettingWithCache("training", "save_steps", normalizedHyperparameters.saveSteps, currentUser.id),
        updateSettingWithCache("training", "logging_steps", normalizedHyperparameters.loggingSteps, currentUser.id),
        updateSettingWithCache("training", "logging_first_step", profile.loggingFirstStep, currentUser.id),
        updateSettingWithCache("training", "max_steps", normalizedHyperparameters.maxSteps, currentUser.id),
        updateSettingWithCache("training", "validation_split", normalizedHyperparameters.validationSplit, currentUser.id),
        updateSettingWithCache("training", "load_best_model_at_end", profile.loadBestModelAtEnd, currentUser.id),
        updateSettingWithCache("training", "metric_for_best_model", normalizedMetricForBestModel, currentUser.id),
        updateSettingWithCache("training", "greater_is_better", profile.greaterIsBetter, currentUser.id),
        updateSettingWithCache("training", "seed", normalizedHyperparameters.seed, currentUser.id),
      ]);

      setTrainingSettings({
        ...profile,
        defaultTrainer: normalizedTrainer,
        baseModel: normalizedBaseModel,
        projectId: normalizedProjectId === null ? "" : String(normalizedProjectId),
        artifactsDirectory: normalizedArtifactsDirectory,
        datasetsDirectory: normalizedDatasetsDirectory,
        maxConcurrentJobs: String(normalizedMaxConcurrentJobs),
        autoRegisterModel: profile.continualTraining ? true : profile.autoRegisterModel,
        continualModelId: Number.isInteger(continualModelId) && continualModelId > 0 ? String(continualModelId) : "",
        numTrainEpochs: String(normalizedHyperparameters.numTrainEpochs),
        learningRate: String(normalizedHyperparameters.learningRate),
        batchSize: String(normalizedHyperparameters.batchSize),
        gradientAccumulationSteps: String(normalizedHyperparameters.gradientAccumulationSteps),
        maxSequenceLength: String(normalizedHyperparameters.maxSequenceLength),
        loraR: String(normalizedHyperparameters.loraR),
        loraAlpha: String(normalizedHyperparameters.loraAlpha),
        loraDropout: String(normalizedHyperparameters.loraDropout),
        warmupRatio: String(normalizedHyperparameters.warmupRatio),
        weightDecay: String(normalizedHyperparameters.weightDecay),
        targetModules: (targetModules.length > 0 ? targetModules : ["auto"]).join(", "),
        evalSteps: String(normalizedHyperparameters.evalSteps),
        saveSteps: String(normalizedHyperparameters.saveSteps),
        loggingSteps: String(normalizedHyperparameters.loggingSteps),
        maxSteps: String(normalizedHyperparameters.maxSteps),
        validationSplit: String(normalizedHyperparameters.validationSplit),
        loadBestModelAtEnd: profile.loadBestModelAtEnd,
        metricForBestModel: normalizedMetricForBestModel,
        greaterIsBetter: profile.greaterIsBetter,
        seed: String(normalizedHyperparameters.seed),
      });
      pushToast("success", "Training-Einstellungen gespeichert.");
    } catch {
      pushToast("error", "Training-Einstellungen konnten nicht gespeichert werden.");
    } finally {
      setTrainingSettingsPending(false);
    }
  };

  const loadChatSettings = async () => {
    const [
      pluginOrchestrationEnabledValue,
      autoSpecialistEnabledValue,
      contextLimitValue,
      contextSafetyMarginValue,
    ] = await Promise.all([
      getSettingCached("chat", "plugin_orchestration_enabled", currentUser.id),
      getSettingCached("chat", "auto_specialist_enabled", currentUser.id),
      getSettingCached("chat", "context_limit_tokens", currentUser.id),
      getSettingCached("chat", "context_safety_margin_tokens", currentUser.id),
    ]);

    setChatSettings({
      pluginOrchestrationEnabled:
        typeof pluginOrchestrationEnabledValue === "boolean" ? pluginOrchestrationEnabledValue : true,
      autoSpecialistEnabled: typeof autoSpecialistEnabledValue === "boolean" ? autoSpecialistEnabledValue : false,
      contextLimitTokens: String(typeof contextLimitValue === "number" ? contextLimitValue : 8192),
      contextSafetyMarginTokens: String(typeof contextSafetyMarginValue === "number" ? contextSafetyMarginValue : 128),
    });
  };

  const handleSaveChatSettings = async (profile: ChatSettingsDraft) => {
    setChatSettingsPending(true);
    try {
      const contextLimitNumber = Number(profile.contextLimitTokens);
      const contextSafetyMarginNumber = Number(profile.contextSafetyMarginTokens);

      await Promise.all([
        updateSettingWithCache("chat", "plugin_orchestration_enabled", profile.pluginOrchestrationEnabled, currentUser.id),
        updateSettingWithCache("chat", "auto_specialist_enabled", profile.autoSpecialistEnabled, currentUser.id),
        updateSettingWithCache(
          "chat",
          "context_limit_tokens",
          Number.isFinite(contextLimitNumber) ? Math.max(512, Math.round(contextLimitNumber)) : 8192,
          currentUser.id,
        ),
        updateSettingWithCache(
          "chat",
          "context_safety_margin_tokens",
          Number.isFinite(contextSafetyMarginNumber) ? Math.max(0, Math.round(contextSafetyMarginNumber)) : 128,
          currentUser.id,
        ),
      ]);

      await loadChatSettings();
      pushToast("success", "Chat-Einstellungen gespeichert.");
    } catch (error) {
      pushToast("error", `Chat-Einstellungen konnten nicht gespeichert werden: ${extractErrorMessage(error)}`);
    } finally {
      setChatSettingsPending(false);
    }
  };

  const handleCleanupObsoleteChatSettings = async () => {
    setChatCleanupPending(true);
    try {
      const preview = await cleanupObsoleteChatSettings(true);
      const run = await cleanupObsoleteChatSettings(false);
      const stats: ChatCleanupStats = {
        matchedCount: typeof preview.matched_count === "number" ? preview.matched_count : 0,
        deletedCount: typeof run.deleted === "number" ? run.deleted : 0,
        remainingCount: typeof run.remaining_count === "number" ? run.remaining_count : 0,
        dryRun: false,
      };
      setChatCleanupStats(stats);
      pushToast(
        "success",
        `Legacy-Chat-Keys bereinigt: ${stats.deletedCount} entfernt (${stats.matchedCount} gefunden, ${stats.remainingCount} verbleibend).`,
      );
    } catch (error) {
      pushToast("error", `Legacy-Chat-Keys konnten nicht bereinigt werden: ${extractErrorMessage(error)}`);
    } finally {
      setChatCleanupPending(false);
    }
  };

  const loadKnowledgeSettings = async () => {
    const [topKValue, minScoreRatioValue, minAbsoluteScoreValue, minScoreGapValue] = await Promise.all([
      getSettingCached("knowledge", "top_k", currentUser.id),
      getSettingCached("knowledge", "min_score_ratio", currentUser.id),
      getSettingCached("knowledge", "min_absolute_score", currentUser.id),
      getSettingCached("knowledge", "min_score_gap", currentUser.id),
    ]);

    setKnowledgeSettings({
      topK: String(typeof topKValue === "number" ? topKValue : 6),
      minScoreRatio: String(typeof minScoreRatioValue === "number" ? minScoreRatioValue : 0.5),
      minAbsoluteScore: String(typeof minAbsoluteScoreValue === "number" ? minAbsoluteScoreValue : 1000),
      minScoreGap: String(typeof minScoreGapValue === "number" ? minScoreGapValue : 400),
    });
  };

  const handleSaveKnowledgeSettings = async (profile: KnowledgeSettingsDraft) => {
    setKnowledgeSettingsPending(true);
    try {
      const topKNumber = Number(profile.topK);
      const minScoreRatioNumber = Number(profile.minScoreRatio);
      const minAbsoluteScoreNumber = Number(profile.minAbsoluteScore);
      const minScoreGapNumber = Number(profile.minScoreGap);

      await Promise.all([
        updateSettingWithCache("knowledge", "top_k", Number.isFinite(topKNumber) ? Math.max(1, Math.round(topKNumber)) : 6, currentUser.id),
        updateSettingWithCache(
          "knowledge",
          "min_score_ratio",
          Number.isFinite(minScoreRatioNumber) ? Math.min(1, Math.max(0, minScoreRatioNumber)) : 0.5,
          currentUser.id,
        ),
        updateSettingWithCache(
          "knowledge",
          "min_absolute_score",
          Number.isFinite(minAbsoluteScoreNumber) ? Math.max(0, Math.round(minAbsoluteScoreNumber)) : 1000,
          currentUser.id,
        ),
        updateSettingWithCache(
          "knowledge",
          "min_score_gap",
          Number.isFinite(minScoreGapNumber) ? Math.max(0, Math.round(minScoreGapNumber)) : 400,
          currentUser.id,
        ),
      ]);

      await loadKnowledgeSettings();
      pushToast("success", "Wissens-Retrieval-Einstellungen gespeichert.");
    } catch (error) {
      pushToast("error", `Wissens-Einstellungen konnten nicht gespeichert werden: ${extractErrorMessage(error)}`);
    } finally {
      setKnowledgeSettingsPending(false);
    }
  };

  const loadLogsSettings = async () => {
    const value = await getSettingCached("system", "log_level", currentUser.id);
    const normalized = typeof value === "string" ? value.trim().toUpperCase() : "INFO";
    const logLevel: LogsSettingsDraft["logLevel"] =
      normalized === "DEBUG" || normalized === "INFO" || normalized === "WARNING" || normalized === "ERROR"
        ? normalized
        : "INFO";
    setLogsSettings({ logLevel });
  };

  const handleSaveLogsSettings = async (profile: LogsSettingsDraft) => {
    setLogsSettingsPending(true);
    try {
      await updateSettingWithCache("system", "log_level", profile.logLevel, currentUser.id);
      setLogsSettings(profile);
      pushToast("success", "Log-Einstellungen gespeichert.");
    } catch (error) {
      pushToast("error", `Log-Einstellungen konnten nicht gespeichert werden: ${extractErrorMessage(error)}`);
    } finally {
      setLogsSettingsPending(false);
    }
  };

  const loadIntegrationSettings = async () => {
    const stringKeys: Array<[keyof IntegrationSettingsDraft, string]> = [
      ["chatgptApiKey", "chatgpt_api_key"],
      ["deeplApiKey", "deepl_api_key"],
      ["anthropicApiKey", "anthropic_api_key"],
      ["googleAiApiKey", "google_ai_api_key"],
      ["mistralApiKey", "mistral_api_key"],
      ["cohereApiKey", "cohere_api_key"],
      ["perplexityApiKey", "perplexity_api_key"],
      ["groqApiKey", "groq_api_key"],
      ["togetherApiKey", "together_api_key"],
      ["openrouterApiKey", "openrouter_api_key"],
      ["huggingfaceApiKey", "huggingface_api_key"],
      ["replicateApiKey", "replicate_api_key"],
      ["deepseekApiKey", "deepseek_api_key"],
      ["xaiApiKey", "xai_api_key"],
      ["elevenlabsApiKey", "elevenlabs_api_key"],
      ["assemblyaiApiKey", "assemblyai_api_key"],
      ["tavilyApiKey", "tavily_api_key"],
      ["serpapiApiKey", "serpapi_api_key"],
      ["googleMapsApiKey", "google_maps_api_key"],
      ["mapboxApiKey", "mapbox_api_key"],
      ["openweatherApiKey", "openweather_api_key"],
      ["weatherapiApiKey", "weatherapi_api_key"],
      ["tomorrowioApiKey", "tomorrowio_api_key"],
      ["newsapiApiKey", "newsapi_api_key"],
      ["twilioApiKey", "twilio_api_key"],
      ["sendgridApiKey", "sendgrid_api_key"],
      ["slackBotToken", "slack_bot_token"],
      ["discordBotToken", "discord_bot_token"],
      ["githubToken", "github_token"],
      ["notionApiKey", "notion_api_key"],
      ["airtableApiKey", "airtable_api_key"],
      ["stripeSecretKey", "stripe_secret_key"],
      ["azureOpenaiApiKey", "azure_openai_api_key"],
      ["awsBedrockApiKey", "aws_bedrock_api_key"],
      ["deepinfraApiKey", "deepinfra_api_key"],
      ["nvidiaNimApiKey", "nvidia_nim_api_key"],
      ["octoaiApiKey", "octoai_api_key"],
      ["fireworksApiKey", "fireworks_api_key"],
      ["githubCopilotApiKey", "github_copilot_api_key"],
      ["stabilityApiKey", "stability_api_key"],
      ["runwayApiKey", "runway_api_key"],
      ["pikaApiKey", "pika_api_key"],
      ["heygenApiKey", "heygen_api_key"],
      ["falApiKey", "fal_api_key"],
      ["unstructuredApiKey", "unstructured_api_key"],
      ["llamaparseApiKey", "llamaparse_api_key"],
      ["firecrawlApiKey", "firecrawl_api_key"],
      ["pineconeApiKey", "pinecone_api_key"],
      ["weaviateApiKey", "weaviate_api_key"],
      ["qdrantApiKey", "qdrant_api_key"],
      ["cloudconvertApiKey", "cloudconvert_api_key"],
      ["exaApiKey", "exa_api_key"],
      ["braveSearchApiKey", "brave_search_api_key"],
      ["bingSearchApiKey", "bing_search_api_key"],
      ["gnewsApiKey", "gnews_api_key"],
      ["scrapingbeeApiKey", "scrapingbee_api_key"],
      ["apifyApiKey", "apify_api_key"],
      ["alphaVantageApiKey", "alpha_vantage_api_key"],
      ["yahooFinanceApiKey", "yahoo_finance_api_key"],
      ["openexchangeratesApiKey", "openexchangerates_api_key"],
      ["whatsappBusinessApiKey", "whatsapp_business_api_key"],
      ["telegramBotToken", "telegram_bot_token"],
      ["microsoftTeamsApiKey", "microsoft_teams_api_key"],
      ["calendlyApiKey", "calendly_api_key"],
      ["virustotalApiKey", "virustotal_api_key"],
      ["hibpApiKey", "hibp_api_key"],
      ["customProviderKeysJson", "custom_provider_keys_json"],
    ];

    const [testResultsValue, ollamaLocalEnabledValue, ...stringValues] = await Promise.all([
      getSettingCached("integrations", "integration_test_results", currentUser.id),
      getSettingCached("integrations", "ollama_local_enabled", currentUser.id),
      ...stringKeys.map(([, settingKey]) => getSettingCached("integrations", settingKey, currentUser.id)),
    ]);

    const draft: IntegrationSettingsDraft = {
      chatgptApiKey: "",
      deeplApiKey: "",
      anthropicApiKey: "",
      googleAiApiKey: "",
      mistralApiKey: "",
      cohereApiKey: "",
      perplexityApiKey: "",
      groqApiKey: "",
      togetherApiKey: "",
      openrouterApiKey: "",
      huggingfaceApiKey: "",
      replicateApiKey: "",
      deepseekApiKey: "",
      xaiApiKey: "",
      elevenlabsApiKey: "",
      assemblyaiApiKey: "",
      tavilyApiKey: "",
      serpapiApiKey: "",
      googleMapsApiKey: "",
      mapboxApiKey: "",
      openweatherApiKey: "",
      weatherapiApiKey: "",
      tomorrowioApiKey: "",
      newsapiApiKey: "",
      twilioApiKey: "",
      sendgridApiKey: "",
      slackBotToken: "",
      discordBotToken: "",
      githubToken: "",
      notionApiKey: "",
      airtableApiKey: "",
      stripeSecretKey: "",
      azureOpenaiApiKey: "",
      awsBedrockApiKey: "",
      deepinfraApiKey: "",
      nvidiaNimApiKey: "",
      octoaiApiKey: "",
      fireworksApiKey: "",
      githubCopilotApiKey: "",
      stabilityApiKey: "",
      runwayApiKey: "",
      pikaApiKey: "",
      heygenApiKey: "",
      falApiKey: "",
      unstructuredApiKey: "",
      llamaparseApiKey: "",
      firecrawlApiKey: "",
      pineconeApiKey: "",
      weaviateApiKey: "",
      qdrantApiKey: "",
      cloudconvertApiKey: "",
      exaApiKey: "",
      braveSearchApiKey: "",
      bingSearchApiKey: "",
      gnewsApiKey: "",
      scrapingbeeApiKey: "",
      apifyApiKey: "",
      alphaVantageApiKey: "",
      yahooFinanceApiKey: "",
      openexchangeratesApiKey: "",
      whatsappBusinessApiKey: "",
      telegramBotToken: "",
      microsoftTeamsApiKey: "",
      calendlyApiKey: "",
      virustotalApiKey: "",
      hibpApiKey: "",
      ollamaLocalEnabled: ollamaLocalEnabledValue === true,
      customProviderKeysJson: "",
    };

    stringKeys.forEach(([fieldKey], index) => {
      const value = stringValues[index];
      (draft as Record<string, unknown>)[fieldKey] = typeof value === "string" ? value : "";
    });

    setIntegrationSettings(draft);

    const normalized: IntegrationTestResults = {};
    if (typeof testResultsValue === "object" && testResultsValue !== null) {
      const validKeys = new Set<IntegrationTestableKey>([
        "openweatherApiKey",
        "weatherapiApiKey",
        "tomorrowioApiKey",
        "exaApiKey",
        "braveSearchApiKey",
        "bingSearchApiKey",
      ]);

      for (const [rawKey, rawValue] of Object.entries(testResultsValue as Record<string, unknown>)) {
        if (!validKeys.has(rawKey as IntegrationTestableKey)) {
          continue;
        }
        if (typeof rawValue !== "object" || rawValue === null) {
          continue;
        }

        const candidate = rawValue as Record<string, unknown>;
        const status = candidate.status;
        const message = candidate.message;
        const testedAt = candidate.testedAt;
        const durationMs = candidate.durationMs;

        if (status !== "ok" && status !== "error" && status !== "skipped") {
          continue;
        }
        if (typeof message !== "string") {
          continue;
        }

        normalized[rawKey as IntegrationTestableKey] = {
          status,
          message,
          testedAt: typeof testedAt === "string" ? testedAt : undefined,
          durationMs: typeof durationMs === "number" && Number.isFinite(durationMs) ? durationMs : undefined,
        };
      }
    }

    setIntegrationTestResults(normalized);
  };

  const handleSaveIntegrationSettings = async (profile: IntegrationSettingsDraft) => {
    setIntegrationSettingsPending(true);
    try {
      const stringEntries: Array<[string, string]> = [
        ["chatgpt_api_key", profile.chatgptApiKey],
        ["deepl_api_key", profile.deeplApiKey],
        ["anthropic_api_key", profile.anthropicApiKey],
        ["google_ai_api_key", profile.googleAiApiKey],
        ["mistral_api_key", profile.mistralApiKey],
        ["cohere_api_key", profile.cohereApiKey],
        ["perplexity_api_key", profile.perplexityApiKey],
        ["groq_api_key", profile.groqApiKey],
        ["together_api_key", profile.togetherApiKey],
        ["openrouter_api_key", profile.openrouterApiKey],
        ["huggingface_api_key", profile.huggingfaceApiKey],
        ["replicate_api_key", profile.replicateApiKey],
        ["deepseek_api_key", profile.deepseekApiKey],
        ["xai_api_key", profile.xaiApiKey],
        ["elevenlabs_api_key", profile.elevenlabsApiKey],
        ["assemblyai_api_key", profile.assemblyaiApiKey],
        ["tavily_api_key", profile.tavilyApiKey],
        ["serpapi_api_key", profile.serpapiApiKey],
        ["google_maps_api_key", profile.googleMapsApiKey],
        ["mapbox_api_key", profile.mapboxApiKey],
        ["openweather_api_key", profile.openweatherApiKey],
        ["weatherapi_api_key", profile.weatherapiApiKey],
        ["tomorrowio_api_key", profile.tomorrowioApiKey],
        ["newsapi_api_key", profile.newsapiApiKey],
        ["twilio_api_key", profile.twilioApiKey],
        ["sendgrid_api_key", profile.sendgridApiKey],
        ["slack_bot_token", profile.slackBotToken],
        ["discord_bot_token", profile.discordBotToken],
        ["github_token", profile.githubToken],
        ["notion_api_key", profile.notionApiKey],
        ["airtable_api_key", profile.airtableApiKey],
        ["stripe_secret_key", profile.stripeSecretKey],
        ["azure_openai_api_key", profile.azureOpenaiApiKey],
        ["aws_bedrock_api_key", profile.awsBedrockApiKey],
        ["deepinfra_api_key", profile.deepinfraApiKey],
        ["nvidia_nim_api_key", profile.nvidiaNimApiKey],
        ["octoai_api_key", profile.octoaiApiKey],
        ["fireworks_api_key", profile.fireworksApiKey],
        ["github_copilot_api_key", profile.githubCopilotApiKey],
        ["stability_api_key", profile.stabilityApiKey],
        ["runway_api_key", profile.runwayApiKey],
        ["pika_api_key", profile.pikaApiKey],
        ["heygen_api_key", profile.heygenApiKey],
        ["fal_api_key", profile.falApiKey],
        ["unstructured_api_key", profile.unstructuredApiKey],
        ["llamaparse_api_key", profile.llamaparseApiKey],
        ["firecrawl_api_key", profile.firecrawlApiKey],
        ["pinecone_api_key", profile.pineconeApiKey],
        ["weaviate_api_key", profile.weaviateApiKey],
        ["qdrant_api_key", profile.qdrantApiKey],
        ["cloudconvert_api_key", profile.cloudconvertApiKey],
        ["exa_api_key", profile.exaApiKey],
        ["brave_search_api_key", profile.braveSearchApiKey],
        ["bing_search_api_key", profile.bingSearchApiKey],
        ["gnews_api_key", profile.gnewsApiKey],
        ["scrapingbee_api_key", profile.scrapingbeeApiKey],
        ["apify_api_key", profile.apifyApiKey],
        ["alpha_vantage_api_key", profile.alphaVantageApiKey],
        ["yahoo_finance_api_key", profile.yahooFinanceApiKey],
        ["openexchangerates_api_key", profile.openexchangeratesApiKey],
        ["whatsapp_business_api_key", profile.whatsappBusinessApiKey],
        ["telegram_bot_token", profile.telegramBotToken],
        ["microsoft_teams_api_key", profile.microsoftTeamsApiKey],
        ["calendly_api_key", profile.calendlyApiKey],
        ["virustotal_api_key", profile.virustotalApiKey],
        ["hibp_api_key", profile.hibpApiKey],
        ["custom_provider_keys_json", profile.customProviderKeysJson],
      ];
      await Promise.all([
        ...stringEntries.map(([key, value]) => updateSettingWithCache("integrations", key, value.trim(), currentUser.id)),
        updateSettingWithCache("integrations", "ollama_local_enabled", profile.ollamaLocalEnabled, currentUser.id),
      ]);
      await loadIntegrationSettings();
      pushToast("success", "API-Schluessel gespeichert.");
    } catch (error) {
      pushToast("error", `API-Schluessel konnten nicht gespeichert werden: ${extractErrorMessage(error)}`);
    } finally {
      setIntegrationSettingsPending(false);
    }
  };

  const handleSaveIntegrationTestResults = async (results: IntegrationTestResults) => {
    setIntegrationTestResults(results);
    try {
      await updateSettingWithCache("integrations", "integration_test_results", results, currentUser.id);
    } catch (error) {
      pushToast("error", `Test-Ergebnisse konnten nicht gespeichert werden: ${extractErrorMessage(error)}`);
    }
  };

  const loadPluginSettings = async () => {
    const descriptors = await getPlugins();
    setPluginDescriptors(descriptors);

    const profiles = await Promise.all(
      descriptors.map(async (plugin) => {
        const value = await getSettingCached("plugins", `${plugin.id}_profile`, currentUser.id);
        const profile =
          typeof value === "object" && value !== null ? (value as Record<string, unknown>) : ({} as Record<string, unknown>);
        return [plugin.id, profile] as const;
      }),
    );

    const savedByPlugin = Object.fromEntries(profiles);
    setPluginSettingsDrafts(buildPluginDrafts(descriptors, savedByPlugin));
    setPluginSettingsErrors({});
  };

  const handlePluginSettingChange = (pluginId: string, fieldKey: string, value: unknown) => {
    setPluginSettingsDrafts((current) => ({
      ...current,
      [pluginId]: {
        ...(current[pluginId] ?? {}),
        [fieldKey]: value,
      },
    }));

    setPluginSettingsErrors((current) => {
      const pluginErrors = current[pluginId];
      if (!pluginErrors || pluginErrors[fieldKey] == null) {
        return current;
      }
      const nextPluginErrors = { ...pluginErrors };
      delete nextPluginErrors[fieldKey];
      return {
        ...current,
        [pluginId]: nextPluginErrors,
      };
    });
  };

  const handleSavePluginSettings = async (pluginId: string) => {
    const descriptor = pluginDescriptors.find((plugin) => plugin.id === pluginId);
    if (!descriptor) {
      pushToast("error", "Plugin-Metadaten nicht verfuegbar.");
      return;
    }

    const profile = pluginSettingsDrafts[pluginId] ?? {};
    setSavingPluginId(pluginId);
    setPluginSettingsErrors((current) => ({ ...current, [pluginId]: {} }));

    try {
      await updatePluginSettings(pluginId, {
        settings: profile,
        userId: currentUser.id,
      });
      await loadPluginSettings();
      pushToast("success", `Plugin-Einstellungen gespeichert: ${descriptor.name || pluginId}.`);
    } catch (error) {
      if (error instanceof PluginSettingsValidationError) {
        setPluginSettingsErrors((current) => ({
          ...current,
          [pluginId]: error.fieldErrors,
        }));
        pushToast("error", `Plugin-Einstellungen ungueltig: ${error.message}`);
        return;
      }
      pushToast("error", `Plugin-Einstellungen konnten nicht gespeichert werden: ${extractErrorMessage(error)}`);
    } finally {
      setSavingPluginId(null);
    }
  };

  const handleExecutePlugin = async (input: {
    pluginId: string;
    pluginInput?: Record<string, unknown>;
    pluginSettings?: Record<string, unknown>;
    userId?: number;
  }) => {
    return executePlugin({
      pluginId: input.pluginId,
      pluginInput: input.pluginInput ?? {},
      pluginSettings: input.pluginSettings ?? {},
      userId: input.userId ?? currentUser.id,
    });
  };

  const handleSaveGeneralSettings = async (profile: GeneralSettings) => {
    setGeneralSettingsPending(true);
    try {
      const normalizedLanguage: "de" | "en" = profile.language === "en" ? "en" : "de";
      const normalizedTheme: "system" | "light" | "dark" =
        profile.theme === "light" || profile.theme === "dark" ? profile.theme : "system";
      const normalizedTimezone = profile.timezone.trim() || "Europe/Berlin";

      await Promise.all([
        updateSettingWithCache("system", "language", normalizedLanguage, currentUser.id),
        updateSettingWithCache("system", "theme", normalizedTheme, currentUser.id),
        updateSettingWithCache("system", "timezone", normalizedTimezone, currentUser.id),
      ]);

      const nextSettings: GeneralSettings = {
        language: normalizedLanguage,
        theme: normalizedTheme,
        timezone: normalizedTimezone,
      };
      setGeneralSettings(nextSettings);
      storeGeneralSettings(nextSettings);
      pushToast("success", "Allgemeine Einstellungen gespeichert.");
    } catch (error) {
      pushToast("error", `Allgemeine Einstellungen konnten nicht gespeichert werden: ${extractErrorMessage(error)}`);
    } finally {
      setGeneralSettingsPending(false);
    }
  };

  const reloadTrainingData = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: [...QUERY_KEY_TRAINING_DATASETS, currentUser.id] }),
      queryClient.invalidateQueries({ queryKey: [...QUERY_KEY_TRAINING_DATASET_FILES, currentUser.id] }),
      queryClient.invalidateQueries({ queryKey: [...QUERY_KEY_TRAINING_JOBS, currentUser.id] }),
    ]);
  };

  const handleCreateTrainingDataset = async (name: string, projectId: number | null) => {
    const normalized = name.trim();
    if (!normalized) {
      pushToast("error", "Dataset-Name darf nicht leer sein.");
      return;
    }

    try {
      await createTrainingDataset({
        userId: currentUser.id,
        name: normalized,
        projectId,
      });
      await reloadTrainingData();
      pushToast("success", "Dataset erstellt.");
    } catch {
      pushToast("error", "Dataset konnte nicht erstellt werden.");
    }
  };

  const handleRegisterTrainingDatasetFile = async (
    name: string,
    files: Partial<Record<"source" | "training" | "validation" | "test" | "manifest", string>>,
    projectId: number | null,
  ) => {
    try {
      await registerTrainingDatasetFile({
        userId: currentUser.id,
        name,
        files,
        projectId,
        metadata: {
          language: "de",
          task_type: "domain_qa",
          format: "messages",
        },
      });
      await reloadTrainingData();
      pushToast("success", "Dataset aus Ordner registriert.");
    } catch (error) {
      pushToast("error", `Dataset-Datei konnte nicht registriert werden: ${extractErrorMessage(error)}`);
    }
  };

  const handleUploadTrainingDataset = async (
    name: string,
    files: Partial<Record<"source" | "training" | "validation" | "test" | "manifest", File | null>>,
    projectId: number | null,
  ) => {
    try {
      await uploadTrainingDataset({
        userId: currentUser.id,
        name,
        files,
        projectId,
        metadata: {
          language: "de",
          task_type: "domain_qa",
          format: "messages",
        },
      });
      await reloadTrainingData();
      pushToast("success", "Trainingsdatei hochgeladen und registriert.");
    } catch (error) {
      pushToast("error", `Upload fehlgeschlagen: ${extractErrorMessage(error)}`);
    }
  };

  const handleImportTrainingDatasetFromUrl = async (
    name: string,
    files: Partial<Record<"source" | "validation" | "test", string>>,
    projectId: number | null,
  ) => {
    try {
      await importTrainingDatasetFromUrl({
        userId: currentUser.id,
        name,
        files,
        projectId,
        metadata: {
          language: "de",
          task_type: "domain_qa",
          format: "messages",
        },
      });
      await reloadTrainingData();
      pushToast("success", "Dataset von URL importiert.");
    } catch (error) {
      pushToast("error", `URL-Import fehlgeschlagen: ${extractErrorMessage(error)}`);
    }
  };

  const handleUploadTrainingDatasetBundle = async (name: string, bundleFile: File, projectId: number | null) => {
    try {
      await uploadTrainingDatasetBundle({
        userId: currentUser.id,
        name,
        bundleFile,
        projectId,
        metadata: {
          language: "de",
          task_type: "domain_qa",
          format: "messages",
        },
      });
      await reloadTrainingData();
      pushToast("success", "ZIP-Bundle importiert und als Dataset registriert.");
    } catch (error) {
      pushToast("error", `ZIP-Import fehlgeschlagen: ${extractErrorMessage(error)}`);
    }
  };

  const handleCreateTrainingJob = async (datasetId: number, baseModelId?: string, trainerName?: string) => {
    const normalizedBaseModelId = typeof baseModelId === "string" ? baseModelId.trim() : "";
    const normalizedTrainerName = typeof trainerName === "string" ? trainerName.trim().toLowerCase() : "";

    try {
      const preflight = await runTrainingPreflight({
        userId: currentUser.id,
        datasetId,
        baseModelId: normalizedBaseModelId.length > 0 ? normalizedBaseModelId : undefined,
        trainerName: normalizedTrainerName.length > 0 ? normalizedTrainerName : undefined,
      });
      setTrainingPreflightResult(preflight);
      if (!preflight.ready) {
        pushToast("error", "Preflight fehlgeschlagen. Jobstart wurde blockiert.");
        return;
      }

      await createTrainingJob({
        userId: currentUser.id,
        datasetId,
        baseModelId: normalizedBaseModelId.length > 0 ? normalizedBaseModelId : undefined,
        trainerName: normalizedTrainerName.length > 0 ? normalizedTrainerName : undefined,
      });
      await reloadTrainingData();
      pushToast("success", "Training-Job eingereiht.");
    } catch (error) {
      pushToast("error", `Training-Job konnte nicht erstellt werden: ${extractErrorMessage(error)}`);
    }
  };

  const handleBatchCreateTrainingJobs = async (newCycle = false) => {
    setTrainingBatchPending(true);
    try {
      const result = await startTrainingFolderBatch({
        userId: currentUser.id,
        newCycle,
      });
      await reloadTrainingData();
      if (result.counts.queued > 0) {
        pushToast(
          "success",
          `${result.counts.queued} Ordner ${newCycle ? "für einen neuen Trainingszyklus" : "als einzelne, sequenzielle Jobs"} eingereiht; ${result.counts.skipped} übersprungen.`,
        );
      } else if (result.counts.errors === 0) {
        pushToast("success", `Keine neuen Jobs erforderlich: ${result.counts.skipped} Ordner bereits verarbeitet oder eingeplant.`);
      }
      if (result.counts.errors > 0) {
        pushToast(
          "error",
          `${result.counts.errors} Ordner fehlerhaft: ${result.errors.slice(0, 3).map((item) => `${item.folder}: ${item.reason}`).join(" | ")}`,
        );
      }
    } catch (error) {
      pushToast("error", `Sammelstart fehlgeschlagen: ${extractErrorMessage(error)}`);
    } finally {
      setTrainingBatchPending(false);
    }
  };

  const handleAssignTrainingProject = async (projectId: number | null) => {
    const result = await assignTrainingProject({ userId: currentUser.id, projectId, includeArchived: true });
    await reloadTrainingData();
    pushToast("success", `${result.updated} Trainingsdatensätze dem Projekt zugeordnet.`);
  };

  const handleRunTrainingPreflight = async (datasetId: number, baseModelId?: string, trainerName?: string) => {
    const normalizedBaseModelId = typeof baseModelId === "string" ? baseModelId.trim() : "";
    const normalizedTrainerName = typeof trainerName === "string" ? trainerName.trim().toLowerCase() : "";
    setTrainingPreflightPending(true);
    try {
      const preflight = await runTrainingPreflight({
        userId: currentUser.id,
        datasetId,
        baseModelId: normalizedBaseModelId.length > 0 ? normalizedBaseModelId : undefined,
        trainerName: normalizedTrainerName.length > 0 ? normalizedTrainerName : undefined,
      });
      setTrainingPreflightResult(preflight);
      if (preflight.ready) {
        pushToast("success", "Preflight erfolgreich. Training kann gestartet werden.");
      } else {
        pushToast("error", "Preflight meldet harte Fehler. Jobstart ist gesperrt.");
      }
      return preflight;
    } catch {
      pushToast("error", "Preflight konnte nicht ausgefuehrt werden.");
      throw new Error("training_preflight_failed");
    } finally {
      setTrainingPreflightPending(false);
    }
  };

  const handleCancelTrainingJob = async (jobId: number) => {
    try {
      await cancelTrainingJob(jobId, currentUser.id);
      await reloadTrainingData();
      pushToast("success", `Job #${jobId} wurde abgebrochen.`);
    } catch {
      pushToast("error", `Job #${jobId} konnte nicht abgebrochen werden.`);
    }
  };

  const handleRetryTrainingJob = async (jobId: number) => {
    try {
      const retried = await retryTrainingJob(jobId, currentUser.id);
      await reloadTrainingData();
      pushToast("success", `Retry erstellt (neuer Job #${retried.id}).`);
    } catch {
      pushToast("error", `Retry fuer Job #${jobId} fehlgeschlagen.`);
    }
  };

  const handleArchiveTrainingDataset = async (datasetId: number) => {
    try {
      await archiveTrainingDataset(datasetId, currentUser.id);
      await reloadTrainingData();
      pushToast("success", `Dataset #${datasetId} archiviert.`);
    } catch (error) {
      pushToast("error", `Dataset #${datasetId} konnte nicht archiviert werden: ${extractErrorMessage(error)}`);
    }
  };

  const handleDeleteTrainingDataset = async (datasetId: number) => {
    try {
      await deleteTrainingDataset(datasetId, currentUser.id);
      await reloadTrainingData();
      pushToast("success", `Dataset #${datasetId} geloescht.`);
    } catch (error) {
      pushToast("error", `Dataset #${datasetId} konnte nicht geloescht werden: ${extractErrorMessage(error)}`);
    }
  };

  const handleUnarchiveTrainingDataset = async (datasetId: number) => {
    try {
      await unarchiveTrainingDataset(datasetId, currentUser.id);
      await reloadTrainingData();
      pushToast("success", `Dataset #${datasetId} wiederhergestellt.`);
    } catch (error) {
      pushToast("error", `Dataset #${datasetId} konnte nicht wiederhergestellt werden: ${extractErrorMessage(error)}`);
    }
  };

  const handleArchiveTrainingJob = async (jobId: number) => {
    try {
      await archiveTrainingJob(jobId, currentUser.id);
      await reloadTrainingData();
      pushToast("success", `Job #${jobId} archiviert.`);
    } catch (error) {
      pushToast("error", `Job #${jobId} konnte nicht archiviert werden: ${extractErrorMessage(error)}`);
    }
  };

  const handleDeleteTrainingJob = async (jobId: number) => {
    try {
      await deleteTrainingJob(jobId, currentUser.id);
      await reloadTrainingData();
      pushToast("success", `Job #${jobId} geloescht.`);
    } catch (error) {
      pushToast("error", `Job #${jobId} konnte nicht geloescht werden: ${extractErrorMessage(error)}`);
    }
  };

  const handleUnarchiveTrainingJob = async (jobId: number) => {
    try {
      await unarchiveTrainingJob(jobId, currentUser.id);
      await reloadTrainingData();
      pushToast("success", `Job #${jobId} wiederhergestellt.`);
    } catch (error) {
      pushToast("error", `Job #${jobId} konnte nicht wiederhergestellt werden: ${extractErrorMessage(error)}`);
    }
  };

  const loadConversationTree = async () => {
    const raw = await getSettingCached("chat", conversationTreeSettingKey, currentUser.id);
    if (typeof raw !== "object" || raw === null || Array.isArray(raw)) {
      setConversationTree({});
      return;
    }

    const mappedEntries = Object.entries(raw)
      .map(([key, value]) => {
        const conversationId = Number(key);
        const parentId = value == null ? null : Number(value);
        if (!Number.isInteger(conversationId)) {
          return null;
        }
        if (parentId != null && !Number.isInteger(parentId)) {
          return [conversationId, null] as const;
        }
        return [conversationId, parentId] as const;
      })
      .filter((item): item is readonly [number, number | null] => item != null);

    setConversationTree(Object.fromEntries(mappedEntries));
  };

  const loadConversationVisibilityMap = async () => {
    const raw = await getSettingCached("chat", CONVERSATION_VISIBILITY_SETTING_KEY);
    if (typeof raw !== "object" || raw === null || Array.isArray(raw)) {
      setConversationVisibilityMap({});
      return;
    }

    const next: Record<number, "private" | "internal" | "public"> = {};
    Object.entries(raw).forEach(([conversationIdRaw, visibilityRaw]) => {
      const conversationId = Number(conversationIdRaw);
      if (!Number.isInteger(conversationId)) {
        return;
      }
      if (visibilityRaw === "private" || visibilityRaw === "internal" || visibilityRaw === "public") {
        next[conversationId] = visibilityRaw;
      }
    });
    setConversationVisibilityMap(next);
  };

  const loadConversationAiParticipationMap = async () => {
    const raw = await getSettingCached("chat", CONVERSATION_AI_PARTICIPATION_SETTING_KEY);
    if (typeof raw !== "object" || raw === null || Array.isArray(raw)) {
      setConversationAiParticipationMap({});
      return;
    }

    const next: Record<number, boolean> = {};
    Object.entries(raw).forEach(([conversationIdRaw, enabledRaw]) => {
      const conversationId = Number(conversationIdRaw);
      if (!Number.isInteger(conversationId) || typeof enabledRaw !== "boolean") {
        return;
      }
      next[conversationId] = enabledRaw;
    });
    setConversationAiParticipationMap(next);
  };

  const loadAssistantDisplayName = async () => {
    const configured = await getSettingCached("prompt", "assistant_display_name", currentUser.id);
    const normalized = typeof configured === "string" ? configured.trim() : "";
    setAssistantDisplayName(normalized.length > 0 ? normalized : "Assistent");
  };

  const loadAiIntentMarkersSettings = async () => {
    const [defaultMarkersRaw, perConversationRaw] = await Promise.all([
      getSettingCached("chat", AI_INTENT_MARKERS_SETTING_KEY, currentUser.id),
      getSettingCached("chat", CONVERSATION_AI_INTENT_MARKERS_SETTING_KEY),
    ]);

    if (Array.isArray(defaultMarkersRaw)) {
      const parsedDefault = defaultMarkersRaw
        .filter((item): item is string => typeof item === "string")
        .map((item) => item.trim().toLowerCase())
        .filter((item) => item.length > 0);
      setAiIntentMarkersDefault(parsedDefault.length > 0 ? parsedDefault : DEFAULT_AI_INTENT_MARKERS);
    } else {
      setAiIntentMarkersDefault(DEFAULT_AI_INTENT_MARKERS);
    }

    if (typeof perConversationRaw !== "object" || perConversationRaw === null || Array.isArray(perConversationRaw)) {
      setConversationAiIntentMarkersMap({});
      return;
    }

    const nextMap: Record<number, string[]> = {};
    Object.entries(perConversationRaw).forEach(([conversationIdRaw, markersRaw]) => {
      const conversationId = Number(conversationIdRaw);
      if (!Number.isInteger(conversationId) || !Array.isArray(markersRaw)) {
        return;
      }

      const parsed = markersRaw
        .filter((item): item is string => typeof item === "string")
        .map((item) => item.trim().toLowerCase())
        .filter((item) => item.length > 0);

      if (parsed.length > 0) {
        nextMap[conversationId] = parsed;
      }
    });
    setConversationAiIntentMarkersMap(nextMap);
  };

  const isExplicitAiIntent = (input: string, markers: string[]) => {
    const normalized = input.trim().toLowerCase();
    if (!normalized) {
      return false;
    }
    return markers.some((marker) => normalized.includes(marker));
  };
  const handleSetAiParticipation = async (conversationId: number, enabled: boolean) => {
    const nextMap: Record<number, boolean> = {
      ...conversationAiParticipationMap,
      [conversationId]: enabled,
    };

    try {
      await updateSettingWithCache("chat", CONVERSATION_AI_PARTICIPATION_SETTING_KEY, nextMap);
      setConversationAiParticipationMap(nextMap);
      pushToast("success", enabled ? "KI nimmt wieder aktiv teil." : "KI bleibt still, bis sie direkt gefragt wird.");
    } catch {
      pushToast("error", "KI-Teilnahme konnte nicht gespeichert werden.");
    }
  };


  const persistConversationTree = async (nextTree: Record<number, number | null>) => {
    setConversationTree(nextTree);
    await updateSettingWithCache("chat", conversationTreeSettingKey, nextTree, currentUser.id);
  };

  const handleMoveConversation = async (conversationId: number, parentConversationId: number | null) => {
    if (conversationId === parentConversationId) {
      return;
    }

    let cursor = parentConversationId;
    while (cursor != null) {
      if (cursor === conversationId) {
        pushToast("error", "Ein Chat kann nicht in sich selbst verschoben werden.");
        return;
      }
      cursor = conversationTree[cursor] ?? null;
    }

    const nextTree: Record<number, number | null> = {
      ...conversationTree,
      [conversationId]: parentConversationId,
    };

    try {
      await persistConversationTree(nextTree);
      pushToast("success", "Chat wurde verschoben.");
    } catch {
      pushToast("error", "Chat konnte nicht verschoben werden.");
    }
  };

  const handleDeleteConversation = async (conversationId: number) => {
    const targetConversation = conversations.find((item) => item.id === conversationId) ?? null;
    if (targetConversation != null && targetConversation.ownerUserId !== currentUser.id) {
      pushToast("error", "Nur der Besitzer kann diesen Chat loeschen.");
      return;
    }

    try {
      await deleteConversation(conversationId, currentUser.id);

      const nextTree: Record<number, number | null> = {};
      Object.entries(conversationTree).forEach(([idRaw, parentIdRaw]) => {
        const id = Number(idRaw);
        const parentId = parentIdRaw == null ? null : Number(parentIdRaw);

        if (id === conversationId) {
          return;
        }

        nextTree[id] = parentId === conversationId ? null : parentId;
      });

      await persistConversationTree(nextTree);

      const nextActiveId = activeConversationId === conversationId ? null : activeConversationId;
      await reloadConversationData(nextActiveId);

      pushToast("success", "Chat geloescht.");
    } catch (error) {
      if (errorContainsStatus(error, 404)) {
        const nextTree: Record<number, number | null> = {};
        Object.entries(conversationTree).forEach(([idRaw, parentIdRaw]) => {
          const id = Number(idRaw);
          const parentId = parentIdRaw == null ? null : Number(parentIdRaw);
          if (id === conversationId) {
            return;
          }
          nextTree[id] = parentId === conversationId ? null : parentId;
        });
        await persistConversationTree(nextTree);
        await reloadConversationData(activeConversationId === conversationId ? null : activeConversationId);
        pushToast("info", "Chat war bereits entfernt und wurde aus der Ansicht bereinigt.");
        return;
      }
      pushToast("error", `Chat konnte nicht geloescht werden: ${extractErrorMessage(error)}`);
    }
  };

  const handleRenameConversation = async (conversationId: number, title: string) => {
    const normalized = title.trim();
    if (!normalized) {
      pushToast("error", "Titel darf nicht leer sein.");
      return;
    }

    try {
      await renameConversation(conversationId, normalized, currentUser.id);
      await reloadConversationData(activeConversationId);
      pushToast("success", "Chat umbenannt.");
    } catch {
      pushToast("error", "Chat konnte nicht umbenannt werden.");
    }
  };

  const handleSetConversationVisibility = async (
    conversationId: number,
    visibility: "private" | "internal" | "public",
  ) => {
    const nextMap: Record<number, "private" | "internal" | "public"> = {
      ...conversationVisibilityMap,
      [conversationId]: visibility,
    };

    try {
      await updateSettingWithCache("chat", CONVERSATION_VISIBILITY_SETTING_KEY, nextMap);
      setConversationVisibilityMap(nextMap);
      await reloadConversationData(activeConversationId);
      pushToast("success", `Chat ist jetzt ${visibility === "private" ? "Privat" : visibility === "internal" ? "Intern" : "Oeffentlich"}.`);
    } catch {
      pushToast("error", "Sichtbarkeit konnte nicht gespeichert werden.");
    }
  };

  const reloadProjects = async () => {
    await queryClient.invalidateQueries({ queryKey: projectsQueryKey });
    await queryClient.fetchQuery({ queryKey: projectsQueryKey, queryFn: () => getWorkspaceProjects(currentUser.id) });
  };

  const createConversationSafely = async () => {
    const preferredProjectId =
      selectedProjectId != null && projects.some((project) => project.id === selectedProjectId)
        ? selectedProjectId
        : null;

    try {
      return await createConversation(currentUser.id, undefined, preferredProjectId);
    } catch (error) {
      if (preferredProjectId != null && errorContainsStatus(error, 404)) {
        setSelectedProjectId(null);
        await reloadProjects();
        return createConversation(currentUser.id, undefined, null);
      }
      throw error;
    }
  };

  const handleCreateProject = async (
    name: string,
    options?: {
      parentProjectId?: number | null;
      scopeKind?: "tenant" | "user" | "area" | "project";
      areaKey?: string | null;
      tenantKey?: string | null;
      ownerUserId?: number | null;
    },
  ) => {
    const normalized = name.trim();
    if (!normalized) {
      pushToast("error", "Projektname darf nicht leer sein.");
      return;
    }

    try {
      const created = await createWorkspaceProject({
        name: normalized,
        userId: currentUser.id,
        parentProjectId: options?.parentProjectId ?? null,
        scopeKind: options?.scopeKind ?? "project",
        areaKey: options?.areaKey ?? null,
        tenantKey: options?.tenantKey ?? null,
        ownerUserId: options?.ownerUserId ?? currentUser.id,
      });
      await reloadProjects();
      setSelectedProjectId(created.id);
      pushToast("success", `Projekt ${created.name} erstellt.`);
      return created.id;
    } catch {
      pushToast("error", "Projekt konnte nicht erstellt werden.");
      return undefined;
    }
  };

  const handleRenameProject = async (projectId: number, name: string) => {
    const normalized = name.trim();
    if (!normalized) {
      pushToast("error", "Projektname darf nicht leer sein.");
      return;
    }

    try {
      await renameWorkspaceProject(projectId, normalized, currentUser.id);
      await reloadProjects();
      pushToast("success", "Projekt umbenannt.");
    } catch {
      pushToast("error", "Projekt konnte nicht umbenannt werden.");
    }
  };

  const handleDeleteProject = async (projectId: number) => {
    try {
      await deleteWorkspaceProject(projectId, currentUser.id);
      await Promise.all([reloadProjects(), reloadConversationData(activeConversationId)]);
      if (selectedProjectId === projectId) {
        setSelectedProjectId(null);
      }
      pushToast("success", "Projekt geloescht.");
    } catch {
      pushToast("error", "Projekt konnte nicht geloescht werden.");
    }
  };

  const handleUpdateProjectHierarchy = async (input: {
    projectId: number;
    parentProjectId: number | null;
    scopeKind: "tenant" | "user" | "area" | "project";
    areaKey: string | null;
    tenantKey: string | null;
    ownerUserId: number | null;
  }) => {
    try {
      await updateWorkspaceProjectHierarchy({
        projectId: input.projectId,
        userId: currentUser.id,
        parentProjectId: input.parentProjectId,
        scopeKind: input.scopeKind,
        areaKey: input.areaKey,
        tenantKey: input.tenantKey,
        ownerUserId: input.ownerUserId,
      });
      await reloadProjects();
      pushToast("success", "Projekt-Hierarchie gespeichert.");
    } catch {
      pushToast("error", "Projekt-Hierarchie konnte nicht gespeichert werden.");
    }
  };

  const handleCleanStartReset = async () => {
    const shouldProceed = window.confirm(
      "Alle Chats und Projekte werden dauerhaft geloescht. Dies kann nicht rueckgaengig gemacht werden. Fortfahren?",
    );
    if (!shouldProceed) {
      return;
    }

    setWorkspaceResetPending(true);
    try {
      await resetWorkspaceForCleanStart(currentUser.id);

      localStorage.removeItem(buildConversationTreeSettingKey(currentUser.id));
      setConversationTree({});
      setConversationVisibilityMap({});
      setConversationAiParticipationMap({});
      setConversationAiIntentMarkersMap({});
      setSelectedProjectId(null);
      setSelectedSourceId(null);

      await Promise.all([reloadProjects(), reloadConversationData(null)]);

      pushToast("success", "Neustart ausgefuehrt: Alle Chats und Projekte wurden geloescht.");
    } catch (error) {
      pushToast("error", `Neustart fehlgeschlagen: ${extractErrorMessage(error)}`);
    } finally {
      setWorkspaceResetPending(false);
    }
  };

  const handleUploadWorkspaceSource = async (file: File) => {
    await uploadWorkspaceSource({ userId: currentUser.id, file, projectId: selectedProjectId });
    await queryClient.invalidateQueries({ queryKey: QUERY_KEY_SOURCES });
  };

  const handleAssignSourceToProject = async (sourceId: number, projectId: number | null) => {
    try {
      await assignWorkspaceSourceProject({
        sourceId,
        userId: currentUser.id,
        projectId,
      });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEY_SOURCES });
      pushToast("success", "Quelle wurde der Ebene zugeordnet.");
    } catch {
      pushToast("error", "Quellen-Zuordnung konnte nicht gespeichert werden.");
    }
  };

  const handleAssignConversationProject = async (projectId: number | null) => {
    if (selectedConversation == null) {
      pushToast("error", "Waehle zuerst einen Chat aus.");
      return;
    }

    try {
      await assignConversationProject(selectedConversation.id, projectId, currentUser.id);
      await reloadConversationData(selectedConversation.id);
      pushToast("success", projectId == null ? "Projektzuordnung entfernt." : "Chat wurde Projekt zugeordnet.");
    } catch (error) {
      if (errorContainsStatus(error, 404)) {
        await reloadConversationData(activeConversationId);
        pushToast("error", "Projektzuordnung nicht moeglich: Chat existiert nicht mehr oder ist nicht sichtbar.");
        return;
      }
      pushToast("error", `Projektzuordnung konnte nicht gespeichert werden: ${extractErrorMessage(error)}`);
    }
  };

  const reloadConversationData = async (conversationId: number | null) => {
    const conversationsKey = ["conversations", currentUser.id] as const;
    const loadedConversations = await queryClient.fetchQuery({
      queryKey: conversationsKey,
      queryFn: () => getConversations(currentUser.id),
    });

    queryClient.setQueryData(conversationsKey, loadedConversations);

    const resolvedConversationId = conversationId ?? loadedConversations[0]?.id ?? null;
    setActiveConversationId(resolvedConversationId);

    if (resolvedConversationId != null) {
      const messagesKey = ["messages", currentUser.id, resolvedConversationId] as const;
      const loadedMessages = await queryClient.fetchQuery({
        queryKey: messagesKey,
        queryFn: () => getMessages(resolvedConversationId, 200, currentUser.id),
      });
      queryClient.setQueryData(messagesKey, loadedMessages);
    } else {
      queryClient.removeQueries({ queryKey: ["messages", currentUser.id] });
    }
  };

  useEffect(() => {
    void (async () => {
      try {
        await loadModelDirectories();
        await Promise.all([
          loadGeneralSettings(),
          loadChatSettings(),
          loadKnowledgeSettings(),
          loadIntegrationSettings(),
          loadLogsSettings(),
          loadPluginSettings(),
          loadConversationTree(),
          loadConversationVisibilityMap(),
          loadConversationAiParticipationMap(),
          loadAiIntentMarkersSettings(),
          loadAssistantDisplayName(),
          loadTrainingSettings(),
        ]);
      } catch {
        pushToast("error", "Backend-Daten konnten nicht geladen werden.");
      }
    })();
  }, []);

  useEffect(() => {
    if (selectedModelId) {
      return;
    }

    const activeModelId = healthModelQuery.data?.activeModelId != null ? String(healthModelQuery.data.activeModelId) : null;
    const fallbackModelId = models.find((model) => model.isActive)?.id ?? models[0]?.id ?? "";
    const resolvedModelId = activeModelId ?? fallbackModelId;
    if (resolvedModelId) {
      setSelectedModelId(resolvedModelId);
    }
  }, [selectedModelId, healthModelQuery.data, models]);

  useEffect(() => {
    applyGeneralSettingsToDocument(generalSettings);
  }, [generalSettings]);
  useEffect(() => {
    if (generalSettings.theme !== "system") {
      return;
    }
    if (typeof window.matchMedia !== "function") {
      return;
    }

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const applySystemTheme = () => {
      const root = document.documentElement;
      root.setAttribute("data-ui-theme", resolveTheme("system"));
    };

    applySystemTheme();
    mediaQuery.addEventListener("change", applySystemTheme);
    return () => mediaQuery.removeEventListener("change", applySystemTheme);
  }, [generalSettings.theme]);

  useEffect(() => {
    if (activeConversationId != null) {
      return;
    }
    const firstConversationId = conversations[0]?.id ?? null;
    if (firstConversationId != null) {
      setActiveConversationId(firstConversationId);
    }
  }, [activeConversationId, conversations]);

  useEffect(() => {
    if (!capabilities?.features?.["auth.heartbeat"]) {
      return;
    }
    void sendPresenceHeartbeat().catch(() => undefined);
  }, [capabilities?.features]);

  useEffect(() => {
    void loadModelProfile(selectedModelId);
  }, [selectedModelId]);

  useEffect(() => {
    if (!modelLoaded) {
      setSendState("disabled");
      return;
    }
    if (sendState === "disabled") {
      setSendState("idle");
    }
  }, [modelLoaded, sendState]);

  useEffect(() => {
    const applyResponsive = () => {
      const width = window.innerWidth;
      setIsMobile(width < 1024);
      setRightHidden(width < 1200);
      setLeftCollapsed(width < 900);
      if (width < 1024) {
        setRightCollapsed(true);
      }
    };

    applyResponsive();
    window.addEventListener("resize", applyResponsive);
    return () => window.removeEventListener("resize", applyResponsive);
  }, []);

  useEffect(() => {
    if (toasts.length === 0) {
      return;
    }

    const timers: number[] = [];
    toasts.forEach((toast) => {
      if (!toast.sticky) {
        timers.push(
          window.setTimeout(() => {
            setToasts((items) => items.filter((item) => item.id !== toast.id));
          }, 5000),
        );
      }
    });

    return () => {
      timers.forEach((timer) => window.clearTimeout(timer));
    };
  }, [toasts]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      const ctrlOrMeta = event.ctrlKey || event.metaKey;

      if (ctrlOrMeta && event.shiftKey && key === "l") {
        event.preventDefault();
        setLeftCollapsed((current) => !current);
        return;
      }

      if (ctrlOrMeta && event.shiftKey && key === "r") {
        event.preventDefault();
        setRightCollapsed((current) => !current);
        return;
      }

      if (ctrlOrMeta && key === "n") {
        event.preventDefault();
        void (async () => {
          try {
            const created = await createConversationSafely();
            setActiveNav("Chats");
            await reloadConversationData(created.id);
            setToasts((items) => [...items, makeToast("success", "Neue leere Konversation erstellt")]);
          } catch {
            pushToast("error", "Neue Konversation konnte nicht erstellt werden.");
          }
        })();
        return;
      }

      if (ctrlOrMeta && key === ",") {
        event.preventDefault();
        setActiveNav("Einstellungen");
        return;
      }

      if (ctrlOrMeta && key === "k") {
        event.preventDefault();
        setActiveNav("Suche");
        return;
      }

      if (ctrlOrMeta && event.shiftKey && key === "e") {
        event.preventDefault();
        setToasts((items) => [...items, makeToast("success", "Chat als Markdown exportiert")]);
        return;
      }

      if (ctrlOrMeta && event.shiftKey && key === "f") {
        event.preventDefault();
        setFullscreenChat((current) => !current);
        return;
      }

      if (ctrlOrMeta && event.shiftKey && key === "p") {
        event.preventDefault();
        setPerformanceOpen((current) => !current);
        return;
      }

      if (event.altKey && key === "arrowup") {
        event.preventDefault();
        if (conversations.length > 0) {
          const currentIndex = conversations.findIndex((item) => item.id === activeConversationId);
          const nextIndex = currentIndex <= 0 ? conversations.length - 1 : currentIndex - 1;
          setActiveConversationId(conversations[nextIndex].id);
        }
        setActiveNav("Chats");
        return;
      }

      if (event.altKey && key === "arrowdown") {
        event.preventDefault();
        if (conversations.length > 0) {
          const currentIndex = conversations.findIndex((item) => item.id === activeConversationId);
          const nextIndex = currentIndex === -1 || currentIndex + 1 >= conversations.length ? 0 : currentIndex + 1;
          setActiveConversationId(conversations[nextIndex].id);
        }
        setActiveNav("Chats");
        return;
      }

      if (key === "escape" && sendState === "streaming") {
        if (activeStreamControllerRef.current) {
          activeStreamControllerRef.current.abort();
        }
        setSendState("stopping");
        resetSendStateLater(200);
        return;
      }

      if (key === "escape") {
        setLeftOverlayOpen(false);
        setRightSheetOpen(false);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [sendState, conversations, activeConversationId, modelLoaded, currentUser.id, selectedProjectId]);

  useEffect(() => {
    sendStateRef.current = sendState;
  }, [sendState]);

  useEffect(() => {
    if (activeConversationId == null) {
      return;
    }

    if (messagePollTimerRef.current != null) {
      window.clearInterval(messagePollTimerRef.current);
      messagePollTimerRef.current = null;
    }

    let isCancelled = false;

    const refreshMessages = async () => {
      if (typeof document !== "undefined" && document.visibilityState !== "visible") {
        return;
      }

      if (messagePollInFlightRef.current) {
        return;
      }

      const sendStateCurrent = sendStateRef.current;
      const isSendBusy =
        sendStateCurrent === "submitting" || sendStateCurrent === "streaming" || sendStateCurrent === "stopping";
      if (isSendBusy) {
        return;
      }

      messagePollInFlightRef.current = true;
      try {
        const latestMessages = await getMessages(activeConversationId, 200, currentUser.id);
        if (isCancelled) {
          return;
        }

        const messagesKey = ["messages", currentUser.id, activeConversationId] as const;
        queryClient.setQueryData<ChatMessage[]>(messagesKey, (current = []) => {
          if (current.length === latestMessages.length) {
            const currentLast = current[current.length - 1];
            const latestLast = latestMessages[latestMessages.length - 1];
            if (
              currentLast?.id === latestLast?.id &&
              currentLast?.content === latestLast?.content &&
              currentLast?.createdAt === latestLast?.createdAt
            ) {
              return current;
            }
          }

          return latestMessages;
        });
      } catch {
        // Live refresh should remain silent; initial load already reports hard failures.
      } finally {
        messagePollInFlightRef.current = false;
      }
    };

    messagePollTimerRef.current = window.setInterval(() => {
      void refreshMessages();
    }, 3000);

    return () => {
      isCancelled = true;
      messagePollInFlightRef.current = false;
      if (messagePollTimerRef.current != null) {
        window.clearInterval(messagePollTimerRef.current);
        messagePollTimerRef.current = null;
      }
    };
  }, [activeConversationId, currentUser.id, queryClient]);

  useEffect(() => {
    const hasPresenceCapability = Boolean(capabilities?.features?.["auth.users_presence"]);
    if (!hasPresenceCapability) {
      if (presencePollTimerRef.current != null) {
        window.clearInterval(presencePollTimerRef.current);
        presencePollTimerRef.current = null;
      }
      return;
    }

    if (presencePollTimerRef.current != null) {
      window.clearInterval(presencePollTimerRef.current);
      presencePollTimerRef.current = null;
    }

    const refreshPresence = async () => {
      if (typeof document !== "undefined" && document.visibilityState !== "visible") {
        return;
      }

      if (presencePollInFlightRef.current) {
        return;
      }

      presencePollInFlightRef.current = true;

      try {
        if (capabilities?.features?.["auth.heartbeat"]) {
          await sendPresenceHeartbeat();
        }
        const users = await getUsersPresence(5);
        queryClient.setQueryData(QUERY_KEY_PRESENCE, users);
      } catch {
        // Presence refresh is optional and should not impact chat flows.
      } finally {
        presencePollInFlightRef.current = false;
      }
    };

    // Initial presence is already loaded during backend bootstrap.
    presencePollTimerRef.current = window.setInterval(() => {
      void refreshPresence();
    }, 20000);

    return () => {
      presencePollInFlightRef.current = false;
      if (presencePollTimerRef.current != null) {
        window.clearInterval(presencePollTimerRef.current);
        presencePollTimerRef.current = null;
      }
    };
  }, [capabilities, queryClient]);

  const mainLayoutClassName = useMemo(() => {
    const classNames: string[] = [
      "main-layout",
      leftCollapsed ? "main-layout--left-collapsed" : "main-layout--left-expanded",
    ];

    if (fullscreenChat) {
      classNames.push("main-layout--chat-focus");
    }

    if (rightHidden) {
      classNames.push("main-layout--right-hidden");
    } else if (rightCollapsed) {
      classNames.push("main-layout--right-collapsed");
    } else {
      classNames.push("main-layout--right-open");
    }

    return classNames.join(" ");
  }, [fullscreenChat, leftCollapsed, rightCollapsed, rightHidden]);

  const hasOtherUserInConversation = selectedConversation != null && selectedConversation.ownerUserId !== currentUser.id;
  const collaboratorUsername = hasOtherUserInConversation ? selectedConversation?.ownerUsername ?? null : null;
  const aiParticipationEnabled =
    selectedConversation == null ? true : (conversationAiParticipationMap[selectedConversation.id] ?? !hasOtherUserInConversation);
  const aiIntentMarkers =
    selectedConversation == null
      ? aiIntentMarkersDefault
      : (conversationAiIntentMarkersMap[selectedConversation.id] ?? aiIntentMarkersDefault);

  const dismissToast = (id: string) => {
    setToasts((items) => items.filter((item) => item.id !== id));
  };

  const pushToast = (tone: ToastItem["tone"], message: string) => {
    setToasts((items) => [...items, makeToast(tone, message)]);
  };

  const createIdempotencyKey = () => {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
      return crypto.randomUUID();
    }
    return `idem-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  };

  const encodeImageAttachments = async (images: OutgoingImageAttachment[]): Promise<EncodedImageAttachment[]> => {
    const encoded = await Promise.all(
      images.map(
        (item) =>
          new Promise<EncodedImageAttachment>((resolve, reject) => {
            const reader = new FileReader();
            reader.onerror = () => reject(new Error(`Datei konnte nicht gelesen werden: ${item.name}`));
            reader.onload = () => {
              const result = typeof reader.result === "string" ? reader.result : "";
              const separator = result.indexOf(",");
              const dataBase64 = separator >= 0 ? result.slice(separator + 1) : result;
              if (!dataBase64) {
                reject(new Error(`Datei konnte nicht codiert werden: ${item.name}`));
                return;
              }
              resolve({
                name: item.name,
                mime_type: item.mimeType || "image/jpeg",
                data_base64: dataBase64,
              });
            };
            reader.readAsDataURL(item.file);
          }),
      ),
    );
    return encoded;
  };

  const refreshPresenceUsers = async () => {
    const refreshedUsers = await getUsersPresence(5).catch(() => []);
    queryClient.setQueryData(QUERY_KEY_PRESENCE, refreshedUsers);
  };

  const handleSendMessage = async (
    payload: OutgoingChatPayload,
    forcedIdempotencyKey?: string,
    forcedImages?: EncodedImageAttachment[],
  ) => {
    const message = payload.message;
    if (!modelLoaded) {
      setSendState("disabled");
      setSendError("Kein Modell geladen. Bitte ein geladenes Modell waehlen.");
      return;
    }

    setSendError(null);

    if (hasOtherUserInConversation && !aiParticipationEnabled && !isExplicitAiIntent(message, aiIntentMarkers)) {
      setSendState("submitting");
      try {
        const result = await postUserOnlyMessage({
          userId: currentUser.id,
          conversationId: activeConversationId ?? undefined,
          message,
        });
        await reloadConversationData(result.conversation_id);
        pushToast("info", `Nachricht gesendet. KI bleibt zurueckhaltend (Trigger: '${aiIntentMarkers[0] ?? "@ki"}').`);
        setSendState("success");
        resetSendStateLater(350);
      } catch {
        setSendState("error");
        setSendError("Nachricht konnte nicht gesendet werden. Bitte erneut versuchen.");
      }
      return;
    }

    if (activeStreamControllerRef.current) {
      return;
    }

    const idempotencyKey = forcedIdempotencyKey ?? createIdempotencyKey();
    const encodedImages = forcedImages ?? (await encodeImageAttachments(payload.images));

    const localUserMessageId = -Date.now();
    const localAssistantMessageId = localUserMessageId - 1;
    const nowIso = new Date().toISOString();
    const optimisticMessagesKey = ["messages", currentUser.id, activeConversationId] as const;

    queryClient.setQueryData<ChatMessage[]>(optimisticMessagesKey, (current = []) => [
      ...current,
      {
        id: localUserMessageId,
        conversationId: activeConversationId ?? 0,
        role: "user",
        content: message,
        createdAt: nowIso,
        authorUsername: currentUser.username,
      },
      {
        id: localAssistantMessageId,
        conversationId: activeConversationId ?? 0,
        role: "assistant",
        content: "",
        createdAt: nowIso,
        authorUsername: null,
      },
    ]);

    setLastSubmittedDraft(message);
    setLastSubmittedImages(encodedImages);
    setLastSubmittedIdempotencyKey(idempotencyKey);
    setLiveReasoning("");
    setSendState("streaming");

    const controller = new AbortController();
    activeStreamControllerRef.current = controller;

    let streamedConversationId = activeConversationId;
    let streamingCompleted = false;
    let streamBuffer = "";
    let insideReasoningBlock = false;

    const reasoningStartTag = "<think>";
    const reasoningEndTag = "</think>";

    const longestSuffixMatchingTagPrefix = (value: string, tag: string): number => {
      const maxLength = Math.min(value.length, tag.length - 1);
      for (let length = maxLength; length > 0; length -= 1) {
        if (tag.startsWith(value.slice(-length))) {
          return length;
        }
      }
      return 0;
    };

    const appendAssistantToken = (token: string) => {
      if (!token) {
        return;
      }
      queryClient.setQueryData<ChatMessage[]>(optimisticMessagesKey, (current = []) =>
        current.map((item) =>
          item.id === localAssistantMessageId
            ? {
                ...item,
                conversationId: streamedConversationId ?? item.conversationId,
                content: `${item.content}${token}`,
              }
            : item,
        ),
      );
    };

    const appendReasoningToken = (token: string) => {
      if (!token) {
        return;
      }
      setLiveReasoning((current) => `${current}${token}`);
    };

    const consumeStreamChunk = (chunk: string) => {
      if (!chunk) {
        return;
      }
      streamBuffer += chunk;

      while (streamBuffer.length > 0) {
        const marker = insideReasoningBlock ? reasoningEndTag : reasoningStartTag;
        const markerIndex = streamBuffer.indexOf(marker);

        if (markerIndex === -1) {
          const holdLength = longestSuffixMatchingTagPrefix(streamBuffer, marker);
          const emitLength = streamBuffer.length - holdLength;
          if (emitLength <= 0) {
            return;
          }
          const textPart = streamBuffer.slice(0, emitLength);
          streamBuffer = streamBuffer.slice(emitLength);
          if (insideReasoningBlock) {
            appendReasoningToken(textPart);
          } else {
            appendAssistantToken(textPart);
          }
          return;
        }

        if (markerIndex > 0) {
          const textPart = streamBuffer.slice(0, markerIndex);
          if (insideReasoningBlock) {
            appendReasoningToken(textPart);
          } else {
            appendAssistantToken(textPart);
          }
        }

        streamBuffer = streamBuffer.slice(markerIndex + marker.length);
        insideReasoningBlock = !insideReasoningBlock;
      }
    };

    const flushStreamBuffer = () => {
      if (!streamBuffer) {
        return;
      }
      if (insideReasoningBlock) {
        appendReasoningToken(streamBuffer);
      } else {
        appendAssistantToken(streamBuffer);
      }
      streamBuffer = "";
    };

    try {
      await sendMessageStream(
        {
        userId: currentUser.id,
        conversationId: activeConversationId ?? undefined,
        message,
        idempotencyKey,
        modelId: selectedModelId ? Number(selectedModelId) : undefined,
        images: encodedImages,
      },
        {
          onConversation: (event) => {
            if (Number.isInteger(event.conversation_id)) {
              streamedConversationId = event.conversation_id;
              setActiveConversationId(event.conversation_id);
            }
          },
          onToken: (event) => {
            if (typeof event.token !== "string") {
              return;
            }
            consumeStreamChunk(event.token);
          },
          onDone: (event) => {
            flushStreamBuffer();
            streamingCompleted = true;
            if (Number.isInteger(event.conversation_id)) {
              streamedConversationId = event.conversation_id;
            }
            if (event.aborted) {
              pushToast("info", "Antwort wurde serverseitig abgebrochen.");
            }
            if (event.deduplicated) {
              pushToast("info", "Vorherige identische Anfrage erkannt, bestehende Antwort wiederverwendet.");
            }
            setLiveReasoning("");
          },
          onError: (event) => {
            flushStreamBuffer();
            setLiveReasoning("");
            const errorCode =
              event.error && typeof event.error.code === "string" ? event.error.code : null;
            const errorMessage =
              event.error && typeof event.error.message === "string"
                ? event.error.message
                : typeof event.detail === "string"
                  ? event.detail
                  : "Unbekannter Streaming-Fehler";
            setSendError(
              errorCode
                ? `Streaming-Fehler [${errorCode}]: ${errorMessage}`
                : `Streaming-Fehler: ${errorMessage}`,
            );
          },
        },
        controller.signal,
      );

      if (streamedConversationId != null) {
        await reloadConversationData(streamedConversationId);
      }

      if (!controller.signal.aborted && streamingCompleted) {
        setSendState("success");
        resetSendStateLater(450);
      } else if (controller.signal.aborted) {
        setLiveReasoning("");
        setSendState(modelLoaded ? "idle" : "disabled");
      } else {
        setLiveReasoning("");
        setSendState("error");
      }
    } catch (error) {
      if (controller.signal.aborted) {
        if (streamedConversationId != null) {
          await reloadConversationData(streamedConversationId);
        }
        setLiveReasoning("");
        setSendState(modelLoaded ? "idle" : "disabled");
      } else {
        setLiveReasoning("");
        setSendState("error");
        setSendError("Nachricht konnte nicht gesendet werden. Bitte erneut versuchen.");
        void error;
      }
    } finally {
      if (activeStreamControllerRef.current === controller) {
        activeStreamControllerRef.current = null;
      }
    }
  };

  const handleRetry = async () => {
    if (!lastSubmittedDraft.trim()) {
      return;
    }
    await handleSendMessage(
      {
        message: lastSubmittedDraft,
        images: [],
      },
      lastSubmittedIdempotencyKey ?? createIdempotencyKey(),
      lastSubmittedImages,
    );
  };

  const handleStop = () => {
    if (activeStreamControllerRef.current) {
      activeStreamControllerRef.current.abort();
    }
    setSendState("stopping");
    resetSendStateLater(250);
  };

  const locale = generalSettings.language === "de" ? "de-DE" : "en-US";
  const isSettingsOrPluginsOverlay = activeNav === "Einstellungen" || activeNav === "Plugins";
  const showChatSurface = activeNav === "Chats" || isSettingsOrPluginsOverlay;

  const renderWorkspacePage = (view: NavView) => (
    <WorkspacePage
      view={view}
      projects={projects}
      appointments={appointments}
      sources={sources}
      modelEntries={models}
      selectedModelId={selectedModelId}
      modelLoaded={modelLoaded}
      modelActionPending={modelActionPending}
      modelDirectoryPending={modelDirectoryPending}
      modelProfilePending={modelProfilePending}
      generalSettingsPending={generalSettingsPending}
      cleanStartPending={workspaceResetPending}
      chatSettingsPending={chatSettingsPending}
      chatCleanupPending={chatCleanupPending}
      knowledgeSettingsPending={knowledgeSettingsPending}
      integrationSettingsPending={integrationSettingsPending}
      logsSettingsPending={logsSettingsPending}
      trainingSettingsPending={trainingSettingsPending}
      trainingBatchPending={trainingBatchPending}
      modelDirectories={modelDirectories}
      modelProfile={modelProfile}
      generalSettings={generalSettings}
      chatSettings={chatSettings}
      chatCleanupStats={chatCleanupStats}
      knowledgeSettings={knowledgeSettings}
      integrationSettings={integrationSettings}
      integrationTestResults={integrationTestResults}
      logsSettings={logsSettings}
      pluginDescriptors={pluginDescriptors}
      pluginSettingsDrafts={pluginSettingsDrafts}
      pluginSettingsErrors={pluginSettingsErrors}
      savingPluginId={savingPluginId}
      trainingSettings={trainingSettings}
      trainingPreflightPending={trainingPreflightPending}
      trainingPreflightResult={trainingPreflightResult}
      trainingDatasetFiles={trainingDatasetFiles}
      trainingDatasets={trainingDatasets}
      trainingJobs={trainingJobs}
      trainerOptions={trainerOptions}
      trainingCompatibility={trainingCompatibility}
      onFetchTrainingCompatibility={fetchTrainingCompatibility}
      onActivateModel={handleActivateModel}
      onPullModel={handlePullModel}
      onCancelPullModel={handleCancelPullModel}
      onDeactivateModel={handleDeactivateModel}
      onScanModels={handleScanModels}
      onSetModelRelevance={handleSetModelRelevance}
      onSaveModelDirectories={handleSaveModelDirectories}
      onSaveModelProfile={handleSaveModelProfile}
      onSaveGeneralSettings={handleSaveGeneralSettings}
      onCleanStartReset={handleCleanStartReset}
      onSaveChatSettings={handleSaveChatSettings}
      onCleanupObsoleteChatSettings={handleCleanupObsoleteChatSettings}
      onSaveKnowledgeSettings={handleSaveKnowledgeSettings}
      onSaveIntegrationSettings={handleSaveIntegrationSettings}
      onSaveIntegrationTestResults={handleSaveIntegrationTestResults}
      onSaveLogsSettings={handleSaveLogsSettings}
      onPluginSettingChange={handlePluginSettingChange}
      onSavePluginSettings={handleSavePluginSettings}
      onExecutePlugin={handleExecutePlugin}
      onSaveTrainingSettings={handleSaveTrainingSettings}
      onBatchCreateTrainingJobs={handleBatchCreateTrainingJobs}
      onAssignTrainingProject={handleAssignTrainingProject}
      onCreateTrainingDataset={handleCreateTrainingDataset}
      onRegisterTrainingDatasetFile={handleRegisterTrainingDatasetFile}
      onUploadTrainingDataset={handleUploadTrainingDataset}
      onImportTrainingDatasetFromUrl={handleImportTrainingDatasetFromUrl}
      onUploadTrainingDatasetBundle={handleUploadTrainingDatasetBundle}
      onCreateTrainingJob={handleCreateTrainingJob}
      onRunTrainingPreflight={handleRunTrainingPreflight}
      onCancelTrainingJob={handleCancelTrainingJob}
      onRetryTrainingJob={handleRetryTrainingJob}
      onArchiveTrainingDataset={handleArchiveTrainingDataset}
      onDeleteTrainingDataset={handleDeleteTrainingDataset}
      onUnarchiveTrainingDataset={handleUnarchiveTrainingDataset}
      onArchiveTrainingJob={handleArchiveTrainingJob}
      onDeleteTrainingJob={handleDeleteTrainingJob}
      onUnarchiveTrainingJob={handleUnarchiveTrainingJob}
      currentUser={currentUser}
      selectedProjectId={selectedProjectId}
      onSelectProject={handleSelectProject}
      onCreateProject={handleCreateProject}
      onRenameProject={handleRenameProject}
      onDeleteProject={handleDeleteProject}
      onUpdateProjectHierarchy={handleUpdateProjectHierarchy}
      onUploadWorkspaceSource={handleUploadWorkspaceSource}
      onAssignSourceToProject={handleAssignSourceToProject}
      onAdminCreateUser={async (username, password, isAdmin) => {
        const created = await adminCreateUser(username, password, isAdmin);
        pushToast(
          "success",
          `Benutzer ${created.username} wurde angelegt${created.is_admin ? " (Admin)" : ""}.`,
        );
      }}
      onExportDiagnosticsReport={async () => {
        try {
          await getDiagnosticsReport();
          const blob = await downloadDiagnosticsReport();
          const url = window.URL.createObjectURL(blob);
          const anchor = document.createElement("a");
          const now = new Date().toISOString().replace(/[:.]/g, "-");
          anchor.href = url;
          anchor.download = `diagnostics-${now}.json`;
          document.body.appendChild(anchor);
          anchor.click();
          document.body.removeChild(anchor);
          window.URL.revokeObjectURL(url);
          pushToast("success", "Diagnosebericht wurde exportiert.");
        } catch {
          pushToast("error", "Diagnosebericht konnte nicht exportiert werden.");
        }
      }}
    />
  );

  return (
    <div className="app-shell">
      <ToastHost items={toasts} onClose={dismissToast} />

      <Header
        onOpenLeftMenu={() => setLeftOverlayOpen((current) => !current)}
        modelLoaded={modelLoaded}
        onOpenSettings={() => {
          setActiveNav((current) => (current === "Einstellungen" ? "Chats" : "Einstellungen"));
        }}
        selectedProjectName={selectedProjectLabel}
        onOpenProjects={() => setActiveNav("Projekte")}
        locale={locale}
        timezone={generalSettings.timezone}
        language={generalSettings.language}
      />

      {!selectedModelId ? (
        <div className="system-warning" role="alert">
          Kein Modell ausgewaehlt. Bitte im Chat-Header ein Modell waehlen.
        </div>
      ) : null}

      <div className={mainLayoutClassName}>
        <LeftSidebar
          collapsed={leftCollapsed}
          activeNav={activeNav}
          selectedConversationId={activeConversationId}
          conversations={conversations}
          projects={projects}
          selectedProjectId={selectedProjectId}
          conversationVisibilityMap={conversationVisibilityMap}
          conversationTree={conversationTree}
          appointments={appointments}
          locale={locale}
          timezone={generalSettings.timezone}
          language={generalSettings.language}
          currentUsername={currentUser.username}
          currentUserId={currentUser.id}
          currentUserRoleLabel={currentUser.is_admin ? "Administrator" : "Benutzer"}
          onToggleCollapse={() => setLeftCollapsed((current) => !current)}
          onSelectNav={(next) => setActiveNav(next)}
          onSelectChat={setActiveConversationId}
          onSelectProject={handleSelectProject}
          onAssignConversationProject={(conversationId, projectId) => {
            const targetConversation = conversations.find((conversation) => conversation.id === conversationId) ?? null;
            if (targetConversation == null) {
              return;
            }
            void (async () => {
              try {
                await assignConversationProject(conversationId, projectId, currentUser.id);
                await reloadConversationData(activeConversationId);
                pushToast("success", projectId == null ? "Projektzuordnung entfernt." : "Chat wurde Projekt zugeordnet.");
              } catch (error) {
                pushToast("error", `Projektzuordnung konnte nicht gespeichert werden: ${extractErrorMessage(error)}`);
              }
            })();
          }}
          onMoveConversation={(conversationId, parentConversationId) => {
            void handleMoveConversation(conversationId, parentConversationId);
          }}
          onRenameConversation={(conversationId, title) => {
            void handleRenameConversation(conversationId, title);
          }}
          onSetConversationVisibility={(conversationId, visibility) => {
            void handleSetConversationVisibility(conversationId, visibility);
          }}
          onDeleteConversation={(conversationId) => {
            void handleDeleteConversation(conversationId);
          }}
          onNewConversation={() => {
            void (async () => {
              try {
                const created = await createConversationSafely();
                setActiveNav("Chats");
                await reloadConversationData(created.id);
                pushToast("success", "Neue leere Konversation erstellt");
              } catch {
                pushToast("error", "Neue Konversation konnte nicht erstellt werden.");
              }
            })();
          }}
          onLogout={onLogout}
        />

        <main className="workspace-main">
          {showChatSurface ? (
            <ChatWorkspace
              chatTitle={selectedChatTitle}
              currentUsername={currentUser.username}
              assistantDisplayName={assistantDisplayName}
              collaboratorUsername={collaboratorUsername}
              hasOtherUserInConversation={hasOtherUserInConversation}
              aiParticipationEnabled={aiParticipationEnabled}
              messages={messages}
              modelEntries={chatSelectableModels}
              selectedModelId={selectedModelId}
              modelLoaded={modelLoaded}
              sendState={sendState}
              sendError={sendError}
              liveReasoning={liveReasoning}
              showReasoningBubble={sendState === "streaming" && liveReasoning.trim().length > 0}
              locale={locale}
              timezone={generalSettings.timezone}
              language={generalSettings.language}
              onChangeModel={handleActivateModel}
              onSendMessage={handleSendMessage}
              onStopMessage={handleStop}
              onRetryLastMessage={handleRetry}
              onOpenRightPanel={() => {
                if (isMobile) {
                  setRightSheetOpen(true);
                } else {
                  setRightHidden(false);
                  setRightCollapsed(false);
                }
              }}
              onToggleAiParticipation={(enabled) => {
                if (selectedConversation == null) {
                  return;
                }
                void handleSetAiParticipation(selectedConversation.id, enabled);
              }}
              onOpenSource={(sourceId) => {
                setSelectedSourceId(sourceId);
                setActiveRightTab("sources");
                if (isMobile) {
                  setRightSheetOpen(true);
                } else {
                  setRightHidden(false);
                  setRightCollapsed(false);
                }
              }}
              sources={chatSources}
              activeProjectLabel={selectedProjectLabel}
            />
          ) : null}

          {!showChatSurface ? renderWorkspacePage(activeNav) : null}

          {isSettingsOrPluginsOverlay ? (
            <div
              className="workspace-overlay"
              role="dialog"
              aria-modal="true"
              aria-label={activeNav === "Einstellungen" ? "Einstellungen" : "Plugins"}
              onClick={() => setActiveNav("Chats")}
            >
              <div
                className="workspace-overlay__content"
                onClick={(event) => {
                  event.stopPropagation();
                }}
              >
                <div className="workspace-overlay__header">
                  <strong>{activeNav}</strong>
                  <button
                    type="button"
                    className="ghost-btn"
                    onClick={() => setActiveNav("Chats")}
                  >
                    Schliessen
                  </button>
                </div>
                {renderWorkspacePage(activeNav)}
              </div>
            </div>
          ) : null}
        </main>

        {!rightHidden ? (
          <RightSidebar
            collapsed={rightCollapsed}
            activeTab={activeRightTab}
            selectedSourceId={selectedSourceId}
            sources={sources}
            users={presenceUsers}
            currentUserId={currentUser.id}
            currentUserIsAdmin={currentUser.is_admin}
            locale={locale}
            timezone={generalSettings.timezone}
            contextUsage={contextUsage}
            onToggleCollapse={() => setRightCollapsed((current) => !current)}
            onChangeTab={setActiveRightTab}
            onContextInspect={(label) => pushToast("info", `${label} als Detailansicht geoeffnet`)}
            onAdminUpdateUser={
              currentUser.is_admin
                ? async ({ userId, username, isAdmin, isActive, password }) => {
                    await adminUpdateUser(userId, {
                      username,
                      isAdmin,
                      isActive,
                      password,
                    });
                    await refreshPresenceUsers();
                    pushToast("success", `Nutzer ${username} wurde aktualisiert.`);
                  }
                : undefined
            }
            onAdminKickUser={
              currentUser.is_admin
                ? async (userId) => {
                    const updated = await adminKickUser(userId);
                    await refreshPresenceUsers();
                    pushToast("success", `Nutzer ${updated.username} wurde rausgeschmissen (offline).`);
                  }
                : undefined
            }
            onAdminUnlockUser={
              currentUser.is_admin
                ? async (userId) => {
                    const updated = await adminUnlockUser(userId);
                    await refreshPresenceUsers();
                    pushToast("success", `Nutzer ${updated.username} wurde entsperrt.`);
                  }
                : undefined
            }
            onAdminDeleteUser={
              currentUser.is_admin
                ? async (userId) => {
                    await adminDeleteUser(userId);
                    await refreshPresenceUsers();
                    pushToast("success", "Nutzer wurde geloescht.");
                  }
                : undefined
            }
          />
        ) : null}
      </div>

      {isMobile && leftOverlayOpen ? (
        <div className="overlay overlay--left" role="dialog" aria-label="Navigation">
          <LeftSidebar
            collapsed={false}
            activeNav={activeNav}
            selectedConversationId={activeConversationId}
            conversations={conversations}
            conversationVisibilityMap={conversationVisibilityMap}
            conversationTree={conversationTree}
            appointments={appointments}
            locale={locale}
            timezone={generalSettings.timezone}
            language={generalSettings.language}
            currentUsername={currentUser.username}
            currentUserId={currentUser.id}
            currentUserRoleLabel={currentUser.is_admin ? "Administrator" : "Benutzer"}
            onToggleCollapse={() => setLeftOverlayOpen(false)}
            onSelectNav={(next) => {
              setActiveNav(next);
              setLeftOverlayOpen(false);
            }}
            onSelectChat={(conversationId) => {
              setActiveConversationId(conversationId);
              setActiveNav("Chats");
              setLeftOverlayOpen(false);
            }}
            onMoveConversation={(conversationId, parentConversationId) => {
              void handleMoveConversation(conversationId, parentConversationId);
            }}
            onRenameConversation={(conversationId, title) => {
              void handleRenameConversation(conversationId, title);
            }}
            onSetConversationVisibility={(conversationId, visibility) => {
              void handleSetConversationVisibility(conversationId, visibility);
            }}
            onDeleteConversation={(conversationId) => {
              void handleDeleteConversation(conversationId);
            }}
            onNewConversation={() => {
              void (async () => {
                try {
                  const created = await createConversationSafely();
                  setActiveConversationId(created.id);
                  setActiveNav("Chats");
                  setLeftOverlayOpen(false);
                  await reloadConversationData(created.id);
                  pushToast("success", "Neue Konversation gestartet");
                } catch {
                  pushToast("error", "Neue Konversation konnte nicht erstellt werden.");
                }
              })();
            }}
            onLogout={onLogout}
          />
        </div>
      ) : null}

      {isMobile && rightSheetOpen ? (
        <div className="overlay overlay--bottom" role="dialog" aria-label="Kontext und Infos">
          <RightSidebar
            collapsed={false}
            activeTab={activeRightTab}
            selectedSourceId={selectedSourceId}
            sources={sources}
            users={presenceUsers}
            currentUserId={currentUser.id}
            currentUserIsAdmin={currentUser.is_admin}
            locale={locale}
            timezone={generalSettings.timezone}
            contextUsage={contextUsage}
            onToggleCollapse={() => setRightSheetOpen(false)}
            onChangeTab={setActiveRightTab}
            onContextInspect={(label) => pushToast("info", `${label} als Detailansicht geoeffnet`)}
            onAdminUpdateUser={
              currentUser.is_admin
                ? async ({ userId, username, isAdmin, isActive, password }) => {
                    await adminUpdateUser(userId, {
                      username,
                      isAdmin,
                      isActive,
                      password,
                    });
                    await refreshPresenceUsers();
                    pushToast("success", `Nutzer ${username} wurde aktualisiert.`);
                  }
                : undefined
            }
            onAdminKickUser={
              currentUser.is_admin
                ? async (userId) => {
                    const updated = await adminKickUser(userId);
                    await refreshPresenceUsers();
                    pushToast("success", `Nutzer ${updated.username} wurde rausgeschmissen (offline).`);
                  }
                : undefined
            }
            onAdminUnlockUser={
              currentUser.is_admin
                ? async (userId) => {
                    const updated = await adminUnlockUser(userId);
                    await refreshPresenceUsers();
                    pushToast("success", `Nutzer ${updated.username} wurde entsperrt.`);
                  }
                : undefined
            }
            onAdminDeleteUser={
              currentUser.is_admin
                ? async (userId) => {
                    await adminDeleteUser(userId);
                    await refreshPresenceUsers();
                    pushToast("success", "Nutzer wurde geloescht.");
                  }
                : undefined
            }
          />
        </div>
      ) : null}

      {performanceOpen ? (
        <aside className="performance-overlay" role="status" aria-label="Performance Overlay">
          <strong>Performance</strong>
          <span>TTFT: 420 ms</span>
          <span>TPS: 28,4</span>
          <span>VRAM: 8,2 GB</span>
          <span>Queue: 0</span>
          <span>Token: 628</span>
        </aside>
      ) : null}

      <Footer
        modelLoaded={modelLoaded}
        plugins={["Dateisystem", "Kalender"]}
        onOpenPlugin={(plugin) => {
          setActiveNav("Plugins");
          pushToast("info", `${plugin} Konfiguration geoeffnet`);
        }}
      />
    </div>
  );
}
