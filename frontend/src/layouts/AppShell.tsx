import { useEffect, useMemo, useRef, useState } from "react";
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
  assignConversationProject,
  adminCreateUser,
  adminDeleteUser,
  adminKickUser,
  adminUnlockUser,
  adminUpdateUser,
  createConversation,
  createTrainingDataset,
  getTrainingDatasetFiles,
  importTrainingDatasetFromUrl,
  registerTrainingDatasetFile,
  createTrainingJob,
  cancelTrainingJob,
  runTrainingPreflight,
  createWorkspaceProject,
  deleteWorkspaceProject,
  deleteConversation,
  deactivateModel,
  getConversations,
  getTrainingDatasets,
  getTrainingCompatibility,
  getTrainingJobs,
  getTrainingTrainers,
  getHealthModel,
  getMessages,
  getModels,
  getWorkspaceAppointments,
  getCapabilities,
  getContextUsage,
  downloadDiagnosticsReport,
  getWorkspaceProjects,
  retryTrainingJob,
  renameWorkspaceProject,
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
  updateSetting,
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
  artifactsDirectory: string;
  datasetsDirectory: string;
  maxConcurrentJobs: string;
  autoStartQueue: boolean;
  autoEvaluate: boolean;
  autoRegisterModel: boolean;
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
  const [generalSettings, setGeneralSettings] = useState<GeneralSettings>(DEFAULT_GENERAL_SETTINGS);
  const [trainingSettingsPending, setTrainingSettingsPending] = useState(false);
  const [trainingSettings, setTrainingSettings] = useState<TrainingSettingsDraft>({
    enabled: false,
    defaultTrainer: "peft_lora",
    baseModel: "",
    artifactsDirectory: "./training-artifacts",
    datasetsDirectory: "./training-datasets",
    maxConcurrentJobs: "1",
    autoStartQueue: true,
    autoEvaluate: true,
    autoRegisterModel: false,
  });
  const [chatSettingsPending, setChatSettingsPending] = useState(false);
  const [chatSettings, setChatSettings] = useState<ChatSettingsDraft>({
    temperature: "0.3",
    maxNewTokens: "512",
    topP: "0.9",
    topK: "40",
    repetitionPenalty: "1.1",
    doSample: true,
    seed: "42",
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
  const [trainingPreflightPending, setTrainingPreflightPending] = useState(false);
  const [trainingPreflightResult, setTrainingPreflightResult] = useState<TrainingPreflightResult | null>(null);
  const conversationTreeSettingKey = useMemo(() => buildConversationTreeSettingKey(currentUser.id), [currentUser.id]);
  const activeStreamControllerRef = useRef<AbortController | null>(null);
  const sendStateRef = useRef<SendWorkflowState>("disabled");
  const messagePollTimerRef = useRef<number | null>(null);
  const messagePollInFlightRef = useRef(false);
  const presencePollTimerRef = useRef<number | null>(null);
  const presencePollInFlightRef = useRef(false);

  const capabilitiesQuery = useQuery({
    queryKey: QUERY_KEY_CAPABILITIES,
    queryFn: async () => getCapabilities().catch(() => null),
  });

  const modelsQuery = useQuery({
    queryKey: QUERY_KEY_MODELS,
    queryFn: getModels,
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
    queryFn: () => getTrainingDatasets(currentUser.id),
    enabled: activeNav === "Einstellungen",
  });

  const trainingDatasetFilesQuery = useQuery({
    queryKey: [...QUERY_KEY_TRAINING_DATASET_FILES, currentUser.id],
    queryFn: () => getTrainingDatasetFiles(currentUser.id),
    enabled: activeNav === "Einstellungen",
  });

  const trainingJobsQuery = useQuery({
    queryKey: [...QUERY_KEY_TRAINING_JOBS, currentUser.id],
    queryFn: () => getTrainingJobs(currentUser.id),
    enabled: activeNav === "Einstellungen",
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
  const selectedChatTitle = selectedConversation?.title ?? "Neue Konversation";
  const selectedChatProjectId = selectedConversation?.projectId ?? null;
  const selectedProject = projects.find((project) => project.id === (selectedChatProjectId ?? selectedProjectId ?? -1)) ?? null;
  const selectedProjectLabel = selectedProject?.name ?? "Kein Projekt";

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
      artifactsDirectoryValue,
      datasetsDirectoryValue,
      maxConcurrentJobsValue,
      autoStartQueueValue,
      autoEvaluateValue,
      autoRegisterModelValue,
    ] = await Promise.all([
      getSettingCached("training", "enabled", currentUser.id),
      getSettingCached("training", "default_trainer", currentUser.id),
      getSettingCached("training", "base_model", currentUser.id),
      getSettingCached("training", "artifacts_directory", currentUser.id),
      getSettingCached("training", "datasets_directory", currentUser.id),
      getSettingCached("training", "max_concurrent_jobs", currentUser.id),
      getSettingCached("training", "auto_start_queue", currentUser.id),
      getSettingCached("training", "auto_evaluate", currentUser.id),
      getSettingCached("training", "auto_register_model", currentUser.id),
    ]);

    setTrainingSettings({
      enabled: typeof enabledValue === "boolean" ? enabledValue : false,
      defaultTrainer:
        typeof defaultTrainerValue === "string" && defaultTrainerValue.trim().length > 0
          ? defaultTrainerValue.trim()
          : "peft_lora",
      baseModel: typeof baseModelValue === "string" ? baseModelValue.trim() : "",
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
      const normalizedArtifactsDirectory = profile.artifactsDirectory.trim() || "./training-artifacts";
      const normalizedDatasetsDirectory = profile.datasetsDirectory.trim() || "./training-datasets";
      const maxConcurrentJobsNumber = Number(profile.maxConcurrentJobs);

      await Promise.all([
        updateSettingWithCache("training", "enabled", profile.enabled, currentUser.id),
        updateSettingWithCache("training", "default_trainer", normalizedTrainer, currentUser.id),
        updateSettingWithCache("training", "base_model", normalizedBaseModel, currentUser.id),
        updateSettingWithCache("training", "artifacts_directory", normalizedArtifactsDirectory, currentUser.id),
        updateSettingWithCache("training", "datasets_directory", normalizedDatasetsDirectory, currentUser.id),
        updateSettingWithCache(
          "training",
          "max_concurrent_jobs",
          Number.isFinite(maxConcurrentJobsNumber) ? Math.max(1, Math.round(maxConcurrentJobsNumber)) : 1,
          currentUser.id,
        ),
        updateSettingWithCache("training", "auto_start_queue", profile.autoStartQueue, currentUser.id),
        updateSettingWithCache("training", "auto_evaluate", profile.autoEvaluate, currentUser.id),
        updateSettingWithCache("training", "auto_register_model", profile.autoRegisterModel, currentUser.id),
      ]);

      setTrainingSettings({
        ...profile,
        defaultTrainer: normalizedTrainer,
        baseModel: normalizedBaseModel,
        artifactsDirectory: normalizedArtifactsDirectory,
        datasetsDirectory: normalizedDatasetsDirectory,
        maxConcurrentJobs: String(Number.isFinite(maxConcurrentJobsNumber) ? Math.max(1, Math.round(maxConcurrentJobsNumber)) : 1),
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
      temperatureValue,
      maxTokensValue,
      topPValue,
      topKValue,
      repetitionPenaltyValue,
      doSampleValue,
      seedValue,
      contextLimitValue,
      contextSafetyMarginValue,
    ] = await Promise.all([
      getSettingCached("chat", "temperature", currentUser.id),
      getSettingCached("chat", "max_new_tokens", currentUser.id),
      getSettingCached("chat", "top_p", currentUser.id),
      getSettingCached("chat", "top_k", currentUser.id),
      getSettingCached("chat", "repetition_penalty", currentUser.id),
      getSettingCached("chat", "do_sample", currentUser.id),
      getSettingCached("chat", "seed", currentUser.id),
      getSettingCached("chat", "context_limit_tokens", currentUser.id),
      getSettingCached("chat", "context_safety_margin_tokens", currentUser.id),
    ]);

    setChatSettings({
      temperature: String(typeof temperatureValue === "number" ? temperatureValue : 0.3),
      maxNewTokens: String(typeof maxTokensValue === "number" ? maxTokensValue : 512),
      topP: String(typeof topPValue === "number" ? topPValue : 0.9),
      topK: String(typeof topKValue === "number" ? topKValue : 40),
      repetitionPenalty: String(typeof repetitionPenaltyValue === "number" ? repetitionPenaltyValue : 1.1),
      doSample: typeof doSampleValue === "boolean" ? doSampleValue : true,
      seed: String(typeof seedValue === "number" ? seedValue : 42),
      contextLimitTokens: String(typeof contextLimitValue === "number" ? contextLimitValue : 8192),
      contextSafetyMarginTokens: String(typeof contextSafetyMarginValue === "number" ? contextSafetyMarginValue : 128),
    });
  };

  const handleSaveChatSettings = async (profile: ChatSettingsDraft) => {
    setChatSettingsPending(true);
    try {
      const temperatureNumber = Number(profile.temperature);
      const maxTokensNumber = Number(profile.maxNewTokens);
      const topPNumber = Number(profile.topP);
      const topKNumber = Number(profile.topK);
      const repetitionPenaltyNumber = Number(profile.repetitionPenalty);
      const seedNumber = Number(profile.seed);
      const contextLimitNumber = Number(profile.contextLimitTokens);
      const contextSafetyMarginNumber = Number(profile.contextSafetyMarginTokens);

      await Promise.all([
        updateSettingWithCache("chat", "temperature", Number.isFinite(temperatureNumber) ? Math.min(2, Math.max(0, temperatureNumber)) : 0.3, currentUser.id),
        updateSettingWithCache("chat", "max_new_tokens", Number.isFinite(maxTokensNumber) ? Math.max(1, Math.round(maxTokensNumber)) : 512, currentUser.id),
        updateSettingWithCache("chat", "top_p", Number.isFinite(topPNumber) ? Math.min(1, Math.max(0.01, topPNumber)) : 0.9, currentUser.id),
        updateSettingWithCache("chat", "top_k", Number.isFinite(topKNumber) ? Math.max(0, Math.round(topKNumber)) : 40, currentUser.id),
        updateSettingWithCache(
          "chat",
          "repetition_penalty",
          Number.isFinite(repetitionPenaltyNumber) ? Math.min(2, Math.max(0.5, repetitionPenaltyNumber)) : 1.1,
          currentUser.id,
        ),
        updateSettingWithCache("chat", "do_sample", profile.doSample, currentUser.id),
        updateSettingWithCache("chat", "seed", Number.isFinite(seedNumber) ? Math.max(0, Math.round(seedNumber)) : 42, currentUser.id),
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
    fileName: string,
    validationFileName: string | undefined,
    projectId: number | null,
  ) => {
    try {
      await registerTrainingDatasetFile({
        userId: currentUser.id,
        name,
        fileName,
        validationFileName,
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
    sourceFile: File,
    validationFile: File | null,
    projectId: number | null,
  ) => {
    try {
      await uploadTrainingDataset({
        userId: currentUser.id,
        name,
        sourceFile,
        validationFile,
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
    sourceUrl: string,
    validationSourceUrl: string | undefined,
    projectId: number | null,
  ) => {
    try {
      await importTrainingDatasetFromUrl({
        userId: currentUser.id,
        name,
        sourceUrl,
        validationSourceUrl,
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
    } catch {
      pushToast("error", `Training-Job konnte nicht erstellt werden: ${extractErrorMessage(error)}`);
    }
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

  const handleCreateProject = async (name: string) => {
    const normalized = name.trim();
    if (!normalized) {
      pushToast("error", "Projektname darf nicht leer sein.");
      return;
    }

    try {
      const created = await createWorkspaceProject(normalized, currentUser.id);
      await reloadProjects();
      setSelectedProjectId(created.id);
      pushToast("success", `Projekt ${created.name} erstellt.`);
    } catch {
      pushToast("error", "Projekt konnte nicht erstellt werden.");
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

  const handleUploadWorkspaceSource = async (file: File) => {
    await uploadWorkspaceSource({ userId: currentUser.id, file, projectId: selectedProjectId });
    await queryClient.invalidateQueries({ queryKey: QUERY_KEY_SOURCES });
  };

  const handleAssignConversationProject = async (projectId: number | null) => {
    if (selectedConversation == null) {
      pushToast("error", "Waehle zuerst einen Chat aus.");
      return;
    }

    if (!canModifySelectedConversation) {
      pushToast("error", "Projektzuordnung ist nur fuer eigene Chats erlaubt.");
      return;
    }

    try {
      await assignConversationProject(selectedConversation.id, projectId, currentUser.id);
      await reloadConversationData(selectedConversation.id);
      setSelectedProjectId(projectId);
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
          loadLogsSettings(),
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
    if (selectedConversation?.projectId != null) {
      setSelectedProjectId(selectedConversation.projectId);
      return;
    }

    if (selectedProjectId != null && projects.some((project) => project.id === selectedProjectId)) {
      return;
    }

    setSelectedProjectId(projects[0]?.id ?? null);
  }, [projects, selectedConversation, selectedProjectId]);

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
        window.setTimeout(() => setSendState(modelLoaded ? "idle" : "disabled"), 200);
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
        window.setTimeout(() => setSendState(modelLoaded ? "idle" : "disabled"), 350);
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
    setSendState("streaming");

    const controller = new AbortController();
    activeStreamControllerRef.current = controller;

    let streamedConversationId = activeConversationId;
    let streamingCompleted = false;

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
            queryClient.setQueryData<ChatMessage[]>(optimisticMessagesKey, (current = []) =>
              current.map((item) =>
                item.id === localAssistantMessageId
                  ? {
                      ...item,
                      conversationId: streamedConversationId ?? item.conversationId,
                      content: `${item.content}${event.token}`,
                    }
                  : item,
              ),
            );
          },
          onDone: (event) => {
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
          },
          onError: (event) => {
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
        window.setTimeout(() => setSendState(modelLoaded ? "idle" : "disabled"), 450);
      } else if (controller.signal.aborted) {
        setSendState(modelLoaded ? "idle" : "disabled");
      } else {
        setSendState("error");
      }
    } catch (error) {
      if (controller.signal.aborted) {
        if (streamedConversationId != null) {
          await reloadConversationData(streamedConversationId);
        }
        setSendState(modelLoaded ? "idle" : "disabled");
      } else {
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
    window.setTimeout(() => setSendState(modelLoaded ? "idle" : "disabled"), 250);
  };

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
          conversationVisibilityMap={conversationVisibilityMap}
          conversationTree={conversationTree}
          appointments={appointments}
          currentUsername={currentUser.username}
          currentUserId={currentUser.id}
          currentUserRoleLabel={currentUser.is_admin ? "Administrator" : "Benutzer"}
          onToggleCollapse={() => setLeftCollapsed((current) => !current)}
          onSelectNav={(next) => setActiveNav(next)}
          onSelectChat={setActiveConversationId}
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
          {activeNav === "Chats" ? (
            <ChatWorkspace
              chatTitle={selectedChatTitle}
              currentUsername={currentUser.username}
              assistantDisplayName={assistantDisplayName}
              collaboratorUsername={collaboratorUsername}
              hasOtherUserInConversation={hasOtherUserInConversation}
              aiParticipationEnabled={aiParticipationEnabled}
              messages={messages}
              modelEntries={models}
              selectedModelId={selectedModelId}
              modelLoaded={modelLoaded}
              sendState={sendState}
              sendError={sendError}
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
              sources={sources}
              projects={projects.map((project) => ({ id: project.id, name: project.name }))}
              selectedProjectId={selectedChatProjectId}
              canAssignProject={canModifySelectedConversation}
              onAssignProject={(projectId) => {
                void handleAssignConversationProject(projectId);
              }}
            />
          ) : (
            <WorkspacePage
              view={activeNav}
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
              chatSettingsPending={chatSettingsPending}
              knowledgeSettingsPending={knowledgeSettingsPending}
              logsSettingsPending={logsSettingsPending}
              trainingSettingsPending={trainingSettingsPending}
              modelDirectories={modelDirectories}
              modelProfile={modelProfile}
              generalSettings={generalSettings}
              chatSettings={chatSettings}
              knowledgeSettings={knowledgeSettings}
              logsSettings={logsSettings}
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
              onDeactivateModel={handleDeactivateModel}
              onScanModels={handleScanModels}
              onSetModelRelevance={handleSetModelRelevance}
              onSaveModelDirectories={handleSaveModelDirectories}
              onSaveModelProfile={handleSaveModelProfile}
              onSaveGeneralSettings={handleSaveGeneralSettings}
              onSaveChatSettings={handleSaveChatSettings}
              onSaveKnowledgeSettings={handleSaveKnowledgeSettings}
              onSaveLogsSettings={handleSaveLogsSettings}
              onSaveTrainingSettings={handleSaveTrainingSettings}
              onCreateTrainingDataset={handleCreateTrainingDataset}
              onRegisterTrainingDatasetFile={handleRegisterTrainingDatasetFile}
              onUploadTrainingDataset={handleUploadTrainingDataset}
              onImportTrainingDatasetFromUrl={handleImportTrainingDatasetFromUrl}
              onCreateTrainingJob={handleCreateTrainingJob}
              onRunTrainingPreflight={handleRunTrainingPreflight}
              onCancelTrainingJob={handleCancelTrainingJob}
              onRetryTrainingJob={handleRetryTrainingJob}
              currentUser={currentUser}
              selectedProjectId={selectedProjectId}
              onSelectProject={setSelectedProjectId}
              onCreateProject={handleCreateProject}
              onRenameProject={handleRenameProject}
              onDeleteProject={handleDeleteProject}
              onUploadWorkspaceSource={handleUploadWorkspaceSource}
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
          )}
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
