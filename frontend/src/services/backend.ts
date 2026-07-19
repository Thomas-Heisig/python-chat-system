import type {
  AuthUser,
  ChatMessage,
  ConversationGenerationProfiles,
  ConversationSummary,
  HealthModelState,
  UiModelEntry,
  WorkspaceAppointment,
  WorkspaceProject,
  WorkspaceSource,
  PresenceUser,
  PluginDescriptor,
  PluginCatalogEntry,
  PluginFrontendAction,
  PluginFrontendDefinition,
  PluginFrontendPage,
  PluginFrontendPageCard,
  PluginFrontendPageSection,
  PluginFrontendSection,
  PluginSettingsDrafts,
  PluginSettingField,
  ApiCapabilities,
  TrainingDatasetSummary,
  TrainingDatasetFileEntry,
  TrainingJobSummary,
  TrainingModelCompatibilityEntry,
  TrainingPreflightResult,
  TrainingTrainerOption,
} from "../types/api";

type ModelListResponse = {
  items: Array<{
    id: number;
    name: string;
    model_path: string;
    backend: string;
    load_status: string;
    is_active: boolean;
    source_kind?: "lokal" | "remote" | "ollama_local" | "ollama_cloud";
    source_label?: string;
    ollama_installed?: boolean;
    ollama_capabilities?: string[];
    tool_calling?: boolean;
    structured_output?: boolean;
    reasoning?: boolean;
    parameter_size?: string | null;
    quantization_level?: string | null;
    context_length?: number | null;
    pull_status?: {
      state: string;
      detail?: string | null;
      progress_percent?: number | null;
      total?: number | null;
      completed?: number | null;
      updated_at?: string;
    } | null;
    model_format?: string;
    model_family?: string;
    task_type?: string;
    group?: string;
    relevance?: "active" | "favorite" | "relevant" | "unavailable" | "irrelevant";
    relevance_flag?: "favorite" | "irrelevant" | null;
    status_label?: string;
    status_color?: "green" | "blue" | "yellow" | "red" | "gray";
    reason_unavailable?: string | null;
    requires_custom_code?: boolean;
    custom_code_trusted?: boolean;
    custom_loader_id?: string | null;
    capabilities?: {
      supports_inference?: boolean;
      supports_training?: boolean;
      supports_peft_training?: boolean;
      supports_4bit?: boolean;
      supports_chat?: boolean;
      supports_embeddings?: boolean;
      supports_reranking?: boolean;
      supports_vision?: boolean;
      supports_audio?: boolean;
    };
  }>;
};

type HealthModelResponse = {
  active_model_id: number | null;
  loaded: boolean;
  backend: string | null;
};

type ProjectsResponse = { items: WorkspaceProject[] };
type AppointmentsResponse = { items: WorkspaceAppointment[] };
type SourcesResponse = { items: WorkspaceSource[] };
type ConversationsResponse = {
  items: Array<{
    id: number;
    title: string;
    updated_at: string;
    last_message: string | null;
    owner_user_id: number;
    owner_username: string;
    project_id: number | null;
  }>;
};
type ConversationGenerationProfilesResponse = {
  conversation_id: number;
  active_version_id: string | null;
  versions: Array<{
    id: string;
    name: string;
    created_at: string;
    created_by_user_id: number;
    params: {
      system_prompt: string;
      temperature: number;
      top_k: number;
      top_p: number;
      repetition_penalty: number;
      stop_sequences: string[];
      seed: number;
      do_sample: boolean;
      max_new_tokens: number;
      retrieval_top_k: number;
    };
  }>;
  history: Array<{
    id: string;
    action: string;
    version_id: string;
    created_at: string;
    user_id: number;
  }>;
};
type MessagesResponse = {
  items: Array<{
    id: number;
    conversation_id: number;
    role: "user" | "assistant";
    content: string;
    created_at: string;
    author_username: string | null;
  }>;
};
type SendMessageResponse = {
  conversation_id: number;
  user_message_id: number;
  assistant_message_id: number;
  message: string;
  model_id: number | null;
};
type PostUserOnlyMessageResponse = {
  conversation_id: number;
  message_id: number;
};
type StreamConversationEvent = {
  conversation_id: number;
};
type StreamTokenEvent = {
  token: string;
};
type StreamDoneEvent = {
  conversation_id: number;
  assistant_message_id: number | null;
  model_id: number | null;
  message: string;
  aborted: boolean;
  deduplicated?: boolean;
};
type StreamErrorEvent = {
  detail?: string;
  error?: {
    code?: string;
    message?: string;
    retry?: {
      retryable?: boolean;
      after_seconds?: number | null;
    };
    details?: Record<string, unknown>;
  };
};
type SendMessageStreamCallbacks = {
  onConversation?: (event: StreamConversationEvent) => void;
  onToken?: (event: StreamTokenEvent) => void;
  onDone?: (event: StreamDoneEvent) => void;
  onError?: (event: StreamErrorEvent) => void;
};
type ChatImagePayload = {
  name: string;
  mime_type: string;
  data_base64: string;
};
type ScanModelsResponse = {
  discovered: number;
  inserted: number;
};
type PullOllamaModelResponse = {
  started: boolean;
  state: string;
  detail?: string | null;
};
type CancelOllamaModelPullResponse = {
  cancelled: boolean;
  state: string;
  detail?: string | null;
};
type SettingResponse = {
  category: string;
  key: string;
  value: unknown;
};
type UpdateSettingResponse = {
  updated: boolean;
  effect: string;
};
type CleanupObsoleteChatSettingsResponse = {
  dry_run: boolean;
  category: string;
  keys: string[];
  matched_count: number;
  deleted?: number;
  remaining_count: number;
};
type PluginExecuteResponse = {
  plugin_id: string;
  plugin_input: Record<string, unknown>;
  plugin_settings: Record<string, unknown>;
  plugin_response: Record<string, unknown>;
};
type PluginsListResponse = {
  items?: Array<{
    id?: unknown;
    name?: unknown;
    description?: unknown;
    category?: unknown;
    status?: unknown;
    api_key_required?: unknown;
    intent_pattern?: unknown;
    settings_fields?: unknown;
    plugin_frontend?: unknown;
    input_schema?: unknown;
    output_schema?: unknown;
  }>;
};

type PluginSettingsValidationDetail = {
  code?: unknown;
  message?: unknown;
  plugin_id?: unknown;
  field_errors?: unknown;
};
type AuthResponse = {
  user: AuthUser;
  access_token: string;
  token_type: string;
};
type UserPresenceResponse = {
  items: Array<{
    id: number;
    username: string;
    is_admin: boolean;
    is_active: boolean;
    online: boolean;
    last_seen_at: string | null;
  }>;
};
type CapabilitiesResponse = {
  service: string;
  version: string;
  features: Record<string, boolean>;
};

type TrainingDatasetsResponse = {
  items: Array<{
    id: number;
    name: string;
    description: string | null;
    source_type: string;
    status: string;
    version: number;
    project_id: number | null;
    created_at: string;
    updated_at: string;
    metadata: Record<string, unknown>;
  }>;
};

type TrainingDatasetFilesResponse = {
  items: Array<{
    relative_path: string;
    size_bytes: number;
    modified_at: string;
  }>;
};

type TrainingJobsResponse = {
  items: Array<{
    id: number;
    dataset_id: number;
    base_model_id: string;
    trainer_name: string;
    status: string;
    created_at: string;
    updated_at: string;
    hyperparameters: Record<string, unknown>;
    result: Record<string, unknown> | null;
    error_message: string | null;
    progress?: number | null;
    current_step?: number | null;
    total_steps?: number | null;
    current_epoch?: number | null;
    loss?: number | null;
    learning_rate?: number | null;
    logs?: string[];
    is_simulation?: boolean | null;
    estimated_vram_mb?: number | null;
    peak_vram_mb?: number | null;
    samples_per_second?: number | null;
    steps_per_second?: number | null;
    elapsed_seconds?: number | null;
  }>;
};

type TrainingPreflightResponse = {
  ready: boolean;
  model_id: number | null;
  model_name: string | null;
  model_format: string | null;
  trainer: string;
  target_modules_mode: string;
  resolved_target_modules: string[];
  target_modules_source: string;
  cuda_available: boolean;
  supports_4bit: boolean;
  dataset_valid: boolean;
  warnings: Array<{ code: string; message: string }>;
  errors: Array<{ code: string; message: string }>;
};

type TrainingFileRole = "source" | "training" | "validation" | "test" | "manifest" | "canonical";
type TrainingRoleFiles = Partial<Record<TrainingFileRole, string>>;

type TrainingTrainersResponse = {
  items: Array<{
    id: string;
    label: string;
    available: boolean;
    reason_unavailable: string | null;
    is_simulation: boolean;
  }>;
};

type TrainingCompatibilityResponse = {
  trainer: string;
  items: Array<{
    model_id: number;
    model_name: string;
    compatible: boolean;
    reason: string | null;
  }>;
};

export type DiagnosticsReport = {
  generated_at: string;
  backend_status: {
    service_name: string;
    environment: string;
    hostname: string;
    active_model_id: number | null;
    model_loaded: boolean;
    active_backend: string | null;
    database_status: string;
  };
  python: {
    version: string;
    executable: string;
    platform: string;
    prefix: string;
    base_prefix: string;
  };
  cuda: {
    available: boolean;
  };
  ports: {
    listening: Array<{
      host: string;
      port: number;
      pid: number | null;
    }>;
  };
  paths: {
    cwd: string;
    database_url: string;
    database_path: string | null;
    model_base_directories: string[];
  };
};

export type ContextUsageResponse = {
  context_limit_tokens: number;
  available_context_tokens: number;
  used_context_tokens: number;
  usage_ratio: number;
  breakdown: {
    system_prompt_tokens: number;
    chat_history_tokens: number;
    user_message_tokens: number;
    assistant_prefix_tokens: number;
    external_data_tokens: number;
    files_tokens: number;
    output_reserve_tokens: number;
    safety_margin_tokens: number;
  };
  history: {
    total_messages: number;
    dropped_messages: number;
  };
  external_data: {
    integrated: boolean;
    sources_count: number;
    selected_count: number;
    dropped_count: number;
    top_k: number;
    selected_sources: Array<{
      id: number;
      file: string;
      position: string;
      relevance: string;
      status: string;
    }>;
  };
};

const API_BASE_URL = String(import.meta.env.VITE_API_BASE_URL ?? "")
  .trim()
  .replace(/\/+$/, "");
const AUTH_TOKEN_STORAGE_KEY = "local-chat-auth-token";

let authToken: string | null = null;
let heartbeatInFlight: Promise<void> | null = null;

export function setAuthToken(token: string | null): void {
  authToken = token && token.trim().length > 0 ? token.trim() : null;
  try {
    if (typeof window === "undefined") {
      return;
    }
    if (authToken) {
      window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, authToken);
    } else {
      window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
    }
  } catch {
    // Ignore storage failures and keep the in-memory token authoritative.
  }
}

export function getAuthToken(): string | null {
  if (authToken) {
    return authToken;
  }

  try {
    if (typeof window === "undefined") {
      return null;
    }
    const storedToken = window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
    if (storedToken && storedToken.trim().length > 0) {
      authToken = storedToken.trim();
      return authToken;
    }
  } catch {
    return null;
  }

  return null;
}

function withApiBase(path: string): string {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }
  return API_BASE_URL ? `${API_BASE_URL}${path}` : path;
}

type ParsedApiError = {
  messageSuffix: string;
};

export class PluginSettingsValidationError extends Error {
  readonly pluginId: string;
  readonly fieldErrors: Record<string, string>;

  constructor(message: string, pluginId: string, fieldErrors: Record<string, string>) {
    super(message);
    this.name = "PluginSettingsValidationError";
    this.pluginId = pluginId;
    this.fieldErrors = fieldErrors;
  }
}

function parseApiErrorBody(body: {
  detail?: unknown;
  error?: {
    code?: unknown;
    message?: unknown;
    retry?: {
      retryable?: unknown;
      after_seconds?: unknown;
    };
    details?: unknown;
  };
}): ParsedApiError {
  let messageSuffix = "";

  const detailObject = body.detail && typeof body.detail === "object" ? (body.detail as Record<string, unknown>) : null;
  const nestedDetail =
    body.error &&
    typeof body.error === "object" &&
    body.error.details &&
    typeof body.error.details === "object" &&
    (body.error.details as Record<string, unknown>).detail &&
    typeof (body.error.details as Record<string, unknown>).detail === "object"
      ? ((body.error.details as Record<string, unknown>).detail as Record<string, unknown>)
      : null;

  if (body.error && typeof body.error === "object") {
    const errorCode = typeof body.error.code === "string" ? body.error.code : null;
    const errorMessage = typeof body.error.message === "string" ? body.error.message : null;
    const retryAfter =
      body.error.retry && typeof body.error.retry.after_seconds === "number"
        ? body.error.retry.after_seconds
        : null;

    if (nestedDetail) {
      const nestedCode = typeof nestedDetail.code === "string" ? nestedDetail.code : null;
      const nestedMessage = typeof nestedDetail.message === "string" ? nestedDetail.message : null;
      if (nestedCode && nestedMessage) {
        messageSuffix = `: [${nestedCode}] ${nestedMessage}`;
      } else if (nestedMessage) {
        messageSuffix = `: ${nestedMessage}`;
      }
    }

    if (!messageSuffix && errorCode && errorMessage) {
      messageSuffix = `: [${errorCode}] ${errorMessage}`;
    } else if (!messageSuffix && errorMessage) {
      messageSuffix = `: ${errorMessage}`;
    }

    if (retryAfter != null) {
      messageSuffix += ` (retry after ${retryAfter}s)`;
    }
  } else if (typeof body.detail === "string") {
    messageSuffix = `: ${body.detail}`;
  } else if (detailObject) {
    const detailCode = typeof detailObject.code === "string" ? detailObject.code : null;
    const detailMessage = typeof detailObject.message === "string" ? detailObject.message : null;
    if (detailCode && detailMessage) {
      messageSuffix = `: [${detailCode}] ${detailMessage}`;
    } else if (detailMessage) {
      messageSuffix = `: ${detailMessage}`;
    } else if (detailCode) {
      messageSuffix = `: ${detailCode}`;
    }
  }

  return { messageSuffix };
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = withApiBase(path);
  const headers = new Headers(init?.headers ?? { "Content-Type": "application/json" });
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = getAuthToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(url, {
    headers,
    ...init,
  });

  if (!response.ok) {
    let detail = "";
    try {
      const body = (await response.json()) as {
        detail?: unknown;
        error?: {
          code?: unknown;
          message?: unknown;
          retry?: {
            retryable?: unknown;
            after_seconds?: unknown;
          };
          details?: unknown;
        };
      };

      detail = parseApiErrorBody(body).messageSuffix;
    } catch {
      detail = "";
    }
    throw new Error(`API request failed (${response.status}) for ${url}${detail}`);
  }

  return (await response.json()) as T;
}

async function parseResponseErrorSuffix(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as {
      detail?: unknown;
      error?: {
        code?: unknown;
        message?: unknown;
        retry?: {
          retryable?: unknown;
          after_seconds?: unknown;
        };
        details?: unknown;
      };
    };
    return parseApiErrorBody(body).messageSuffix;
  } catch {
    return "";
  }
}

export async function getModels(): Promise<UiModelEntry[]> {
  const response = await requestJson<ModelListResponse>("/api/models");
  return response.items.map((item) => ({
    id: String(item.id),
    name: item.name,
    modelPath: item.model_path,
    backend: item.backend,
    loadStatus: item.load_status,
    loaded: item.load_status === "ready",
    category: item.source_kind ?? "lokal",
    sourceLabel: item.source_label ?? "Lokal",
    isActive: item.is_active,
    ollamaInstalled: Boolean(item.ollama_installed),
    ollamaCapabilities: Array.isArray(item.ollama_capabilities)
      ? item.ollama_capabilities.filter((entry): entry is string => typeof entry === "string")
      : [],
    toolCalling: Boolean(item.tool_calling),
    structuredOutput: Boolean(item.structured_output),
    reasoning: Boolean(item.reasoning),
    parameterSize: item.parameter_size ?? null,
    quantizationLevel: item.quantization_level ?? null,
    contextLength: typeof item.context_length === "number" ? item.context_length : null,
    pullStatus: item.pull_status
      ? {
          state: item.pull_status.state,
          detail: item.pull_status.detail ?? null,
          progressPercent: typeof item.pull_status.progress_percent === "number" ? item.pull_status.progress_percent : null,
          total: typeof item.pull_status.total === "number" ? item.pull_status.total : null,
          completed: typeof item.pull_status.completed === "number" ? item.pull_status.completed : null,
          updatedAt: String(item.pull_status.updated_at ?? ""),
        }
      : null,
    modelFormat: item.model_format,
    modelFamily: item.model_family,
    taskType: item.task_type,
    group: item.group,
    relevance: item.relevance,
    relevanceFlag: item.relevance_flag ?? null,
    statusLabel: item.status_label,
    statusColor: item.status_color,
    reasonUnavailable: item.reason_unavailable ?? null,
    requiresCustomCode: Boolean(item.requires_custom_code),
    customCodeTrusted: Boolean(item.custom_code_trusted),
    customLoaderId: item.custom_loader_id ?? null,
    capabilities: item.capabilities
      ? {
          supportsInference: Boolean(item.capabilities.supports_inference),
          supportsTraining: Boolean(item.capabilities.supports_training),
          supportsPeftTraining: Boolean(item.capabilities.supports_peft_training),
          supports4bit: Boolean(item.capabilities.supports_4bit),
          supportsChat: Boolean(item.capabilities.supports_chat),
          supportsEmbeddings: Boolean(item.capabilities.supports_embeddings),
          supportsReranking: Boolean(item.capabilities.supports_reranking),
          supportsVision: Boolean(item.capabilities.supports_vision),
          supportsAudio: Boolean(item.capabilities.supports_audio),
        }
      : undefined,
  }));
}

export type SpeechModel = {
  id: number;
  name: string;
  task: "speech_to_text" | "text_to_speech" | "voice_activity_detection";
  family: string;
  backend: string;
  available: boolean;
  settings: {
    languages: string[];
    tasks: string[];
    speakers: string[];
    supports_timestamps: boolean;
    supports_language: boolean;
  };
};

export async function getSpeechModels(): Promise<SpeechModel[]> {
  const response = await requestJson<{ items: SpeechModel[] }>("/api/speech/models");
  return response.items;
}

export async function transcribeSpeech(input: {
  modelId: number; audio: Blob; language: string; task: string; timestamps: boolean;
  chunkLength: number; strideLength: number; device: string;
  vadEnabled?: boolean; vadModelId?: number; vadThreshold?: number; vadPaddingMs?: number; vadMergeGapMs?: number;
}): Promise<{ text: string; chunks: Array<Record<string, unknown>> }> {
  const form = new FormData();
  form.append("model_id", String(input.modelId));
  form.append("audio", input.audio, "recording.webm");
  form.append("language", input.language);
  form.append("task", input.task);
  form.append("return_timestamps", String(input.timestamps));
  form.append("chunk_length_s", String(input.chunkLength));
  form.append("stride_length_s", String(input.strideLength));
  form.append("device", input.device);
  if (input.vadEnabled && input.vadModelId) {
    form.append("vad_enabled", "true");
    form.append("vad_model_id", String(input.vadModelId));
    form.append("vad_threshold", String(input.vadThreshold ?? 0.5));
    form.append("vad_padding_ms", String(input.vadPaddingMs ?? 120));
    form.append("vad_merge_gap_ms", String(input.vadMergeGapMs ?? 180));
  }
  const headers = new Headers();
  const token = getAuthToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(withApiBase("/api/speech/transcribe"), { method: "POST", headers, body: form });
  if (!response.ok) {
    const detail = await parseResponseErrorSuffix(response);
    throw new Error(`Transkription fehlgeschlagen (${response.status})${detail}`);
  }
  return response.json() as Promise<{ text: string; chunks: Array<Record<string, unknown>> }>;
}

export async function synthesizeSpeech(input: {
  modelId: number; text: string; language: string; speaker: string; speed: number; device: string;
}): Promise<Blob> {
  const headers = new Headers({ "Content-Type": "application/json" });
  const token = getAuthToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(withApiBase("/api/speech/synthesize"), {
    method: "POST", headers, body: JSON.stringify({
      model_id: input.modelId, text: input.text, language: input.language,
      speaker: input.speaker, speed: input.speed, device: input.device,
    }),
  });
  if (!response.ok) {
    const detail = await parseResponseErrorSuffix(response);
    throw new Error(`Sprachausgabe fehlgeschlagen (${response.status})${detail}`);
  }
  return response.blob();
}

export async function detectSpeechActivity(input: {
  modelId: number; audio: Blob; threshold: number; device: string;
}): Promise<{ speaking: boolean; segments: Array<{ start: number; end: number }>; max_confidence: number; speech_ratio: number; sample_rate: number }> {
  const form = new FormData();
  form.append("model_id", String(input.modelId));
  form.append("audio", input.audio, "recording.webm");
  form.append("threshold", String(input.threshold));
  form.append("device", input.device);
  const headers = new Headers();
  const token = getAuthToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(withApiBase("/api/speech/detect-activity"), { method: "POST", headers, body: form });
  if (!response.ok) {
    const detail = await parseResponseErrorSuffix(response);
    throw new Error(`VAD fehlgeschlagen (${response.status})${detail}`);
  }
  return response.json() as Promise<{ speaking: boolean; segments: Array<{ start: number; end: number }>; max_confidence: number; speech_ratio: number; sample_rate: number }>;
}

export async function setModelRelevance(
  modelId: string,
  relevance: "favorite" | "irrelevant" | null,
  userId = 1,
): Promise<void> {
  await requestJson(`/api/models/${encodeURIComponent(modelId)}/relevance`, {
    method: "POST",
    body: JSON.stringify({
      relevance,
      user_id: userId,
    }),
  });
}

export async function getTrainingTrainers(): Promise<TrainingTrainerOption[]> {
  const response = await requestJson<TrainingTrainersResponse>("/api/training/trainers");
  return response.items.map((item) => ({
    id: item.id,
    label: item.label,
    available: item.available,
    reasonUnavailable: item.reason_unavailable,
    isSimulation: item.is_simulation,
  }));
}

export async function getTrainingCompatibility(trainerName: string): Promise<TrainingModelCompatibilityEntry[]> {
  const normalized = trainerName.trim();
  const response = await requestJson<TrainingCompatibilityResponse>(
    `/api/training/compatibility?trainer_name=${encodeURIComponent(normalized)}`,
  );
  return response.items.map((item) => ({
    modelId: String(item.model_id),
    modelName: item.model_name,
    compatible: item.compatible,
    reason: item.reason,
  }));
}

export async function activateModel(modelId: string): Promise<void> {
  await requestJson(`/api/models/${modelId}/activate`, { method: "POST" });
}

export async function pullOllamaModel(modelId: string): Promise<{ started: boolean; state: string; detail: string | null }> {
  const response = await requestJson<PullOllamaModelResponse>(`/api/models/${modelId}/pull`, { method: "POST" });
  return {
    started: response.started,
    state: response.state,
    detail: response.detail ?? null,
  };
}

export async function cancelOllamaModelPull(modelId: string): Promise<{ cancelled: boolean; state: string; detail: string | null }> {
  const response = await requestJson<CancelOllamaModelPullResponse>(`/api/models/${modelId}/pull/cancel`, { method: "POST" });
  return {
    cancelled: response.cancelled,
    state: response.state,
    detail: response.detail ?? null,
  };
}

export async function deactivateModel(): Promise<void> {
  await requestJson("/api/models/deactivate", { method: "POST" });
}

export async function scanModels(): Promise<ScanModelsResponse> {
  return requestJson<ScanModelsResponse>("/api/models/scan", { method: "POST" });
}

export async function login(username: string, password: string): Promise<AuthUser> {
  const response = await requestJson<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  setAuthToken(response.access_token);
  return response.user;
}

export async function register(username: string, password: string): Promise<AuthUser> {
  const response = await requestJson<AuthResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  setAuthToken(response.access_token);
  return response.user;
}

export async function adminCreateUser(
  username: string,
  password: string,
  isAdmin = false,
): Promise<AuthUser> {
  const response = await requestJson<AuthResponse & { created?: boolean }>("/api/auth/admin/users", {
    method: "POST",
    body: JSON.stringify({
      username,
      password,
      is_admin: isAdmin,
    }),
  });
  return response.user;
}

export async function adminUpdateUser(
  targetUserId: number,
  payload: {
    username: string;
    isAdmin: boolean;
    isActive: boolean;
    password?: string;
  },
): Promise<AuthUser> {
  const response = await requestJson<AuthResponse & { updated?: boolean }>(`/api/auth/admin/users/${targetUserId}`, {
    method: "PATCH",
    body: JSON.stringify({
      username: payload.username,
      is_admin: payload.isAdmin,
      is_active: payload.isActive,
      password: payload.password?.trim() ? payload.password : null,
    }),
  });
  return response.user;
}

export async function adminKickUser(targetUserId: number): Promise<AuthUser> {
  const response = await requestJson<AuthResponse & { kicked?: boolean }>(`/api/auth/admin/users/${targetUserId}/kick`, {
    method: "POST",
  });
  return response.user;
}

export async function adminUnlockUser(targetUserId: number): Promise<AuthUser> {
  const response = await requestJson<AuthResponse & { unlocked?: boolean }>(`/api/auth/admin/users/${targetUserId}/unlock`, {
    method: "POST",
  });
  return response.user;
}

export async function adminDeleteUser(targetUserId: number): Promise<void> {
  await requestJson<{ deleted?: boolean; target_user_id?: number }>(`/api/auth/admin/users/${targetUserId}`, {
    method: "DELETE",
  });
}

export async function getCurrentUser(userId: number): Promise<AuthUser> {
  const route = getAuthToken() ? "/api/auth/me" : `/api/auth/me?user_id=${userId}`;
  const response = await requestJson<AuthResponse>(route);
  setAuthToken(response.access_token);
  return response.user;
}

export async function getUsersPresence(onlineWindowMinutes = 5): Promise<PresenceUser[]> {
  const response = await requestJson<UserPresenceResponse>(
    `/api/auth/users?online_window_minutes=${onlineWindowMinutes}`,
  );
  return response.items.map((item) => ({
    id: item.id,
    username: item.username,
    isAdmin: item.is_admin,
    isActive: item.is_active,
    online: item.online,
    lastSeenAt: item.last_seen_at,
  }));
}

export async function sendPresenceHeartbeat(): Promise<void> {
  if (heartbeatInFlight) {
    return heartbeatInFlight;
  }

  heartbeatInFlight = (async () => {
    await requestJson<{ ok: boolean }>("/api/auth/heartbeat", {
      method: "POST",
    });
  })().finally(() => {
    heartbeatInFlight = null;
  });

  return heartbeatInFlight;
}

export async function getCapabilities(): Promise<ApiCapabilities> {
  return requestJson<CapabilitiesResponse>("/api/meta/capabilities");
}

export async function getDiagnosticsReport(): Promise<DiagnosticsReport> {
  return requestJson<DiagnosticsReport>("/api/system/diagnostics");
}

export async function downloadDiagnosticsReport(): Promise<Blob> {
  const url = withApiBase("/api/system/diagnostics/export");
  const headers = new Headers();
  const token = getAuthToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(url, {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    throw new Error(`Diagnostics export failed (${response.status})`);
  }

  return response.blob();
}

export async function getContextUsage(
  userId: number,
  conversationId: number | null,
  userMessage = "",
): Promise<ContextUsageResponse> {
  const params = new URLSearchParams({ user_id: String(userId) });
  if (conversationId != null) {
    params.set("conversation_id", String(conversationId));
  }
  if (userMessage.trim().length > 0) {
    params.set("user_message", userMessage.trim());
  }
  return requestJson<ContextUsageResponse>(`/api/chat/context-usage?${params.toString()}`);
}

export async function getSetting(category: string, key: string, userId?: number, teamId?: number): Promise<unknown> {
  const params = new URLSearchParams();
  if (userId != null) {
    params.set("user_id", String(userId));
  }
  if (teamId != null) {
    params.set("team_id", String(teamId));
  }
  params.set("include_secret", "true");
  const query = `?${params.toString()}`;
  const response = await requestJson<SettingResponse>(`/api/settings/${category}/${key}${query}`);
  return response.value;
}

export async function updateSetting(
  category: string,
  key: string,
  value: unknown,
  userId?: number,
  teamId?: number,
): Promise<UpdateSettingResponse> {
  return requestJson<UpdateSettingResponse>("/api/settings", {
    method: "POST",
    body: JSON.stringify({ category, key, value, user_id: userId ?? null, team_id: teamId ?? null }),
  });
}

export async function updatePluginSettings(
  pluginId: string,
  input: { settings: Record<string, unknown>; userId?: number; teamId?: number },
): Promise<UpdateSettingResponse> {
  const url = withApiBase("/api/settings");
  const headers = new Headers({ "Content-Type": "application/json" });
  const token = getAuthToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify({
      category: "plugins",
      key: `${pluginId}_profile`,
      value: input.settings,
      user_id: input.userId ?? null,
      team_id: input.teamId ?? null,
    }),
  });

  if (!response.ok) {
    let fallbackMessage = `API request failed (${response.status}) for ${url}`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      const detail = body.detail as PluginSettingsValidationDetail | undefined;
      if (
        detail &&
        typeof detail === "object" &&
        detail.code === "invalid_plugin_settings" &&
        typeof detail.field_errors === "object" &&
        detail.field_errors != null
      ) {
        const fieldErrors = Object.fromEntries(
          Object.entries(detail.field_errors as Record<string, unknown>)
            .filter(([, value]) => typeof value === "string")
            .map(([key, value]) => [key, value as string]),
        );
        const message = typeof detail.message === "string" ? detail.message : "Plugin settings validation failed.";
        const responsePluginId = typeof detail.plugin_id === "string" ? detail.plugin_id : pluginId;
        throw new PluginSettingsValidationError(message, responsePluginId, fieldErrors);
      }

      fallbackMessage += parseApiErrorBody({ detail: body.detail }).messageSuffix;
    } catch (error) {
      if (error instanceof PluginSettingsValidationError) {
        throw error;
      }
    }
    throw new Error(fallbackMessage);
  }

  return (await response.json()) as UpdateSettingResponse;
}

export async function cleanupObsoleteChatSettings(dryRun = false): Promise<CleanupObsoleteChatSettingsResponse> {
  const params = new URLSearchParams({ dry_run: dryRun ? "true" : "false" });
  return requestJson<CleanupObsoleteChatSettingsResponse>(`/api/settings/chat/cleanup-obsolete?${params.toString()}`, {
    method: "POST",
  });
}

export async function executePlugin(input: {
  pluginId: string;
  pluginInput?: Record<string, unknown>;
  pluginSettings?: Record<string, unknown>;
  userId?: number;
}): Promise<PluginExecuteResponse> {
  return requestJson<PluginExecuteResponse>("/api/plugins/execute", {
    method: "POST",
    body: JSON.stringify({
      plugin_id: input.pluginId,
      plugin_input: input.pluginInput ?? {},
      plugin_settings: input.pluginSettings ?? {},
      user_id: input.userId ?? null,
    }),
  });
}

export async function downloadBusinessLetterArtifact(documentId: string, artifactKind: string, tenantId?: string): Promise<{ blob: Blob; fileName: string | null }> {
  const params = new URLSearchParams();
  if (tenantId && tenantId.trim().length > 0) {
    params.set("tenant_id", tenantId.trim());
  }
  const query = params.toString();
  const url = withApiBase(
    `/api/plugins/business-letter/documents/${encodeURIComponent(documentId)}/artifacts/${encodeURIComponent(artifactKind)}${query ? `?${query}` : ""}`,
  );
  const headers = new Headers();
  const token = getAuthToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(url, { headers });
  if (!response.ok) {
    const detail = await parseResponseErrorSuffix(response);
    throw new Error(`API request failed (${response.status}) for ${url}${detail}`);
  }

  const disposition = response.headers.get("Content-Disposition") ?? "";
  const fileNameMatch = disposition.match(/filename="?([^";]+)"?/i);
  return {
    blob: await response.blob(),
    fileName: fileNameMatch?.[1] ?? null,
  };
}

export async function getPlugins(): Promise<PluginCatalogEntry[]> {
  const response = await requestJson<PluginsListResponse>("/api/plugins");
  const items = Array.isArray(response.items) ? response.items : [];

  return items
    .map((item) => {
      const rawFields = Array.isArray(item.settings_fields) ? item.settings_fields : [];
      const settingsFields: PluginSettingField[] = rawFields
        .map((field) => {
          if (typeof field !== "object" || field == null) {
            return null;
          }
          const row = field as Record<string, unknown>;
          const key = typeof row.key === "string" ? row.key : "";
          const label = typeof row.label === "string" ? row.label : key;
          if (!key || !label) {
            return null;
          }

          return {
            key,
            label,
            type:
              typeof row.type === "string" &&
              ["string", "text", "boolean", "number", "select", "password"].includes(row.type)
                ? (row.type as PluginSettingField["type"])
                : "string",
            group: typeof row.group === "string" ? row.group : undefined,
            description: typeof row.description === "string" ? row.description : undefined,
            default: row.default,
            required: row.required === true,
            options: Array.isArray(row.options)
              ? row.options
                  .map((option) => {
                    if (typeof option === "string") {
                      return { label: option, value: option };
                    }
                    if (typeof option !== "object" || option == null) {
                      return null;
                    }
                    const optionRow = option as Record<string, unknown>;
                    const optionValue = optionRow.value;
                    if (!["string", "number", "boolean"].includes(typeof optionValue)) {
                      return null;
                    }
                    const optionLabel = typeof optionRow.label === "string" ? optionRow.label : String(optionValue);
                    return { label: optionLabel, value: optionValue as string | number | boolean };
                  })
                  .filter((option): option is NonNullable<typeof option> => option != null)
              : undefined,
          };
        })
        .filter((field): field is NonNullable<typeof field> => field != null);

      let pluginFrontend: PluginFrontendDefinition | undefined;
      if (typeof item.plugin_frontend === "object" && item.plugin_frontend != null) {
        const rawFrontend = item.plugin_frontend as Record<string, unknown>;
        let page: PluginFrontendPage | undefined;
        if (typeof rawFrontend.page === "object" && rawFrontend.page != null) {
          const rawPage = rawFrontend.page as Record<string, unknown>;
          const rawPageSections = Array.isArray(rawPage.sections) ? rawPage.sections : [];
          const pageSections: PluginFrontendPageSection[] = rawPageSections
            .map((section) => {
              if (typeof section !== "object" || section == null) {
                return null;
              }
              const row = section as Record<string, unknown>;
              const id = typeof row.id === "string" ? row.id : "";
              const title = typeof row.title === "string" ? row.title : "";
              if (!id || !title) {
                return null;
              }
              const rawCards = Array.isArray(row.cards) ? row.cards : [];
              const cards: PluginFrontendPageCard[] = rawCards
                .map((card) => {
                  if (typeof card !== "object" || card == null) {
                    return null;
                  }
                  const cardRow = card as Record<string, unknown>;
                  const cardId = typeof cardRow.id === "string" ? cardRow.id : "";
                  const cardTitle = typeof cardRow.title === "string" ? cardRow.title : "";
                  if (!cardId || !cardTitle) {
                    return null;
                  }
                  const bullets = Array.isArray(cardRow.bullets)
                    ? cardRow.bullets.filter((entry): entry is string => typeof entry === "string" && entry.trim().length > 0)
                    : undefined;
                  return {
                    id: cardId,
                    title: cardTitle,
                    description: typeof cardRow.description === "string" ? cardRow.description : undefined,
                    bullets,
                    ctaLabel: typeof cardRow.ctaLabel === "string" ? cardRow.ctaLabel : undefined,
                    openTab:
                      cardRow.openTab === "frontend" || cardRow.openTab === "settings" || cardRow.openTab === "manual"
                        ? cardRow.openTab
                        : undefined,
                    pluginInput:
                      typeof cardRow.pluginInput === "object" && cardRow.pluginInput != null
                        ? (cardRow.pluginInput as Record<string, unknown>)
                        : undefined,
                    pluginSettings:
                      typeof cardRow.pluginSettings === "object" && cardRow.pluginSettings != null
                        ? (cardRow.pluginSettings as Record<string, unknown>)
                        : undefined,
                  };
                })
                .filter((card): card is NonNullable<typeof card> => card != null);
              return {
                id,
                title,
                description: typeof row.description === "string" ? row.description : undefined,
                cards,
              };
            })
            .filter((section): section is NonNullable<typeof section> => section != null);

          page = {
            eyebrow: typeof rawPage.eyebrow === "string" ? rawPage.eyebrow : undefined,
            headline: typeof rawPage.headline === "string" ? rawPage.headline : undefined,
            summary: typeof rawPage.summary === "string" ? rawPage.summary : undefined,
            highlights: Array.isArray(rawPage.highlights)
              ? rawPage.highlights.filter((entry): entry is string => typeof entry === "string" && entry.trim().length > 0)
              : undefined,
            sections: pageSections,
          };
        }
        const rawSections = Array.isArray(rawFrontend.sections) ? rawFrontend.sections : [];
        const sections: PluginFrontendSection[] = rawSections
          .map((section) => {
            if (typeof section !== "object" || section == null) {
              return null;
            }
            const row = section as Record<string, unknown>;
            const id = typeof row.id === "string" ? row.id : "";
            const title = typeof row.title === "string" ? row.title : "";
            if (!id || !title) {
              return null;
            }
            const rawActions = Array.isArray(row.actions) ? row.actions : [];
            const actions: PluginFrontendAction[] = rawActions
              .map((action) => {
                if (typeof action !== "object" || action == null) {
                  return null;
                }
                const actionRow = action as Record<string, unknown>;
                const actionId = typeof actionRow.id === "string" ? actionRow.id : "";
                const label = typeof actionRow.label === "string" ? actionRow.label : "";
                if (!actionId || !label) {
                  return null;
                }
                return {
                  id: actionId,
                  label,
                  description: typeof actionRow.description === "string" ? actionRow.description : undefined,
                  openTab:
                    actionRow.openTab === "frontend" || actionRow.openTab === "settings" || actionRow.openTab === "manual"
                      ? actionRow.openTab
                      : undefined,
                  pluginInput:
                    typeof actionRow.pluginInput === "object" && actionRow.pluginInput != null
                      ? (actionRow.pluginInput as Record<string, unknown>)
                      : undefined,
                  pluginSettings:
                    typeof actionRow.pluginSettings === "object" && actionRow.pluginSettings != null
                      ? (actionRow.pluginSettings as Record<string, unknown>)
                      : undefined,
                };
              })
              .filter((action): action is NonNullable<typeof action> => action != null);
            return {
              id,
              title,
              description: typeof row.description === "string" ? row.description : undefined,
              actions,
            };
          })
          .filter((section): section is NonNullable<typeof section> => section != null);

        pluginFrontend = {
          title: typeof rawFrontend.title === "string" ? rawFrontend.title : undefined,
          description: typeof rawFrontend.description === "string" ? rawFrontend.description : undefined,
          page,
          sections,
        };
      }

      return {
        id: typeof item.id === "string" ? item.id : "",
        name: typeof item.name === "string" ? item.name : "",
        description: typeof item.description === "string" ? item.description : undefined,
        category: typeof item.category === "string" ? item.category : undefined,
        status: typeof item.status === "string" ? item.status : undefined,
        api_key_required: item.api_key_required === true,
        intent_pattern: typeof item.intent_pattern === "string" ? item.intent_pattern : undefined,
        settings_fields: settingsFields,
        pluginFrontend,
        inputSchema:
          typeof item.input_schema === "object" && item.input_schema != null
            ? (item.input_schema as Record<string, unknown>)
            : undefined,
        outputSchema:
          typeof item.output_schema === "object" && item.output_schema != null
            ? (item.output_schema as Record<string, unknown>)
            : undefined,
      };
    })
    .filter((plugin) => plugin.id.trim().length > 0);
}

export async function getHealthModel(): Promise<HealthModelState> {
  const response = await requestJson<HealthModelResponse>("/api/health/model");
  return {
    activeModelId: response.active_model_id,
    loaded: response.loaded,
    backend: response.backend,
  };
}

export async function getWorkspaceProjects(userId = 1): Promise<WorkspaceProject[]> {
  const response = await requestJson<ProjectsResponse>(`/api/workspace/projects?user_id=${userId}`);
  return response.items;
}

export async function createWorkspaceProject(
  input: {
    name: string;
    userId?: number;
    parentProjectId?: number | null;
    scopeKind?: "tenant" | "user" | "area" | "project";
    areaKey?: string | null;
    tenantKey?: string | null;
    ownerUserId?: number | null;
  },
): Promise<WorkspaceProject> {
  const {
    name,
    userId = 1,
    parentProjectId = null,
    scopeKind = "project",
    areaKey = null,
    tenantKey = null,
    ownerUserId = null,
  } = input;

  return requestJson<WorkspaceProject>("/api/workspace/projects", {
    method: "POST",
    body: JSON.stringify({
      name,
      user_id: userId,
      parent_project_id: parentProjectId,
      scope_kind: scopeKind,
      area_key: areaKey,
      tenant_key: tenantKey,
      owner_user_id: ownerUserId,
    }),
  });
}

export async function renameWorkspaceProject(projectId: number, name: string, userId = 1): Promise<void> {
  await requestJson(`/api/workspace/projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify({ name, user_id: userId }),
  });
}

export async function deleteWorkspaceProject(projectId: number, userId = 1): Promise<void> {
  await requestJson(`/api/workspace/projects/${projectId}?user_id=${userId}`, {
    method: "DELETE",
  });
}

export async function updateWorkspaceProjectHierarchy(
  input: {
    projectId: number;
    userId?: number;
    parentProjectId?: number | null;
    scopeKind?: "tenant" | "user" | "area" | "project";
    areaKey?: string | null;
    tenantKey?: string | null;
    ownerUserId?: number | null;
  },
): Promise<void> {
  const {
    projectId,
    userId = 1,
    parentProjectId = null,
    scopeKind = "project",
    areaKey = null,
    tenantKey = null,
    ownerUserId = null,
  } = input;

  await requestJson(`/api/workspace/projects/${projectId}/hierarchy`, {
    method: "PATCH",
    body: JSON.stringify({
      user_id: userId,
      parent_project_id: parentProjectId,
      scope_kind: scopeKind,
      area_key: areaKey,
      tenant_key: tenantKey,
      owner_user_id: ownerUserId,
    }),
  });
}

export async function resetWorkspaceForCleanStart(userId = 1): Promise<void> {
  await requestJson(`/api/workspace/reset-clean-start?user_id=${userId}`, {
    method: "POST",
  });
}

export async function getWorkspaceAppointments(): Promise<WorkspaceAppointment[]> {
  const response = await requestJson<AppointmentsResponse>("/api/workspace/appointments");
  return response.items;
}

export async function getWorkspaceSources(userId = 1): Promise<WorkspaceSource[]> {
  const response = await requestJson<SourcesResponse>(`/api/workspace/sources?user_id=${userId}`);
  return response.items;
}

export async function uploadWorkspaceSource(input: { userId: number; file: File; projectId?: number | null }): Promise<void> {
  const form = new FormData();
  form.append("user_id", String(input.userId));
  if (typeof input.projectId === "number") {
    form.append("project_id", String(input.projectId));
  }
  form.append("source_file", input.file);

  const url = withApiBase("/api/workspace/sources/upload");
  const headers = new Headers();
  const token = getAuthToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(url, {
    method: "POST",
    headers,
    body: form,
  });

  if (!response.ok) {
    let detail = "";
    try {
      const body = (await response.json()) as { detail?: unknown };
      detail = body.detail ? `: ${String(body.detail)}` : "";
    } catch {
      detail = "";
    }
    throw new Error(`Source upload failed (${response.status})${detail}`);
  }
}

export async function assignWorkspaceSourceProject(input: {
  sourceId: number;
  userId?: number;
  projectId?: number | null;
}): Promise<void> {
  const userId = input.userId ?? 1;
  const projectPart =
    typeof input.projectId === "number" ? `project_id=${input.projectId}` : "project_id=";
  await requestJson(`/api/workspace/sources/${input.sourceId}/project?user_id=${userId}&${projectPart}`, {
    method: "PATCH",
  });
}

export async function getConversations(userId = 1): Promise<ConversationSummary[]> {
  const response = await requestJson<ConversationsResponse>(`/api/conversations?user_id=${userId}`);
  return response.items.map((item) => ({
    id: item.id,
    title: item.title,
    updatedAt: item.updated_at,
    lastMessage: item.last_message,
    ownerUserId: item.owner_user_id,
    ownerUsername: item.owner_username,
    projectId: item.project_id,
  }));
}

export async function createConversation(userId = 1, title?: string, projectId?: number | null): Promise<ConversationSummary> {
  const response = await requestJson<{
    id: number;
    title: string;
    updated_at: string;
    owner_user_id: number;
    owner_username: string;
    project_id: number | null;
  }>("/api/conversations", {
    method: "POST",
    body: JSON.stringify({ user_id: userId, title, project_id: projectId ?? null }),
  });
  return {
    id: response.id,
    title: response.title,
    updatedAt: response.updated_at,
    lastMessage: null,
    ownerUserId: response.owner_user_id,
    ownerUsername: response.owner_username,
    projectId: response.project_id,
  };
}

export async function assignConversationProject(
  conversationId: number,
  projectId: number | null,
  userId = 1,
): Promise<void> {
  await requestJson(`/api/conversations/${conversationId}/project`, {
    method: "PATCH",
    body: JSON.stringify({ user_id: userId, project_id: projectId }),
  });
}

export async function deleteConversation(conversationId: number, userId = 1): Promise<void> {
  try {
    await requestJson(`/api/conversations/${conversationId}?user_id=${userId}`, {
      method: "DELETE",
    });
    return;
  } catch {
    await requestJson(`/api/conversations/${conversationId}/delete?user_id=${userId}`, {
      method: "POST",
    });
  }
}

export async function renameConversation(conversationId: number, title: string, userId = 1): Promise<void> {
  await requestJson(`/api/conversations/${conversationId}`, {
    method: "PATCH",
    body: JSON.stringify({ user_id: userId, title }),
  });
}

export async function getConversationGenerationProfiles(
  conversationId: number,
  userId = 1,
): Promise<ConversationGenerationProfiles> {
  return requestJson<ConversationGenerationProfilesResponse>(
    `/api/conversations/${conversationId}/generation-profiles?user_id=${userId}`,
  );
}

export async function createConversationGenerationProfile(
  conversationId: number,
  payload: {
    userId?: number;
    name?: string;
    params: {
      system_prompt: string;
      temperature: number;
      top_k: number;
      top_p: number;
      repetition_penalty: number;
      stop_sequences: string[];
      seed: number;
      do_sample: boolean;
      max_new_tokens: number;
      retrieval_top_k: number;
    };
    activate?: boolean;
  },
): Promise<ConversationGenerationProfiles> {
  return requestJson<ConversationGenerationProfilesResponse>(
    `/api/conversations/${conversationId}/generation-profiles`,
    {
      method: "POST",
      body: JSON.stringify({
        user_id: payload.userId ?? 1,
        name: payload.name,
        params: payload.params,
        activate: payload.activate ?? true,
      }),
    },
  );
}

export async function activateConversationGenerationProfile(
  conversationId: number,
  versionId: string,
  userId = 1,
): Promise<ConversationGenerationProfiles> {
  return requestJson<ConversationGenerationProfilesResponse>(
    `/api/conversations/${conversationId}/generation-profiles/${encodeURIComponent(versionId)}/activate`,
    {
      method: "POST",
      body: JSON.stringify({ user_id: userId }),
    },
  );
}

export async function getMessages(conversationId: number, limit = 200, userId = 1): Promise<ChatMessage[]> {
  const response = await requestJson<MessagesResponse>(
    `/api/messages?conversation_id=${conversationId}&limit=${limit}&user_id=${userId}`,
  );
  return response.items.map((item) => ({
    id: item.id,
    conversationId: item.conversation_id,
    role: item.role,
    content: item.content,
    createdAt: item.created_at,
    authorUsername: item.author_username,
  }));
}

export async function sendMessage(payload: {
  userId?: number;
  conversationId?: number;
  message: string;
  idempotencyKey?: string;
  modelId?: number;
}): Promise<SendMessageResponse> {
  return requestJson<SendMessageResponse>("/api/messages", {
    method: "POST",
    body: JSON.stringify({
      user_id: payload.userId ?? 1,
      conversation_id: payload.conversationId,
      message: payload.message,
      idempotency_key: payload.idempotencyKey,
      model_id: payload.modelId,
    }),
  });
}

export async function postUserOnlyMessage(payload: {
  userId?: number;
  conversationId?: number;
  message: string;
}): Promise<PostUserOnlyMessageResponse> {
  return requestJson<PostUserOnlyMessageResponse>("/api/messages/user-only", {
    method: "POST",
    body: JSON.stringify({
      user_id: payload.userId ?? 1,
      conversation_id: payload.conversationId,
      message: payload.message,
    }),
  });
}

export async function sendMessageStream(
  payload: {
    userId?: number;
    conversationId?: number;
    message: string;
    idempotencyKey?: string;
    modelId?: number;
    images?: ChatImagePayload[];
  },
  callbacks: SendMessageStreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const streamUrl = withApiBase("/api/chat/generate");
  const response = await fetch(streamUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: payload.userId ?? 1,
      conversation_id: payload.conversationId,
      message: payload.message,
      idempotency_key: payload.idempotencyKey,
      model_id: payload.modelId,
      images: payload.images ?? [],
      stream: true,
    }),
    signal,
  });

  if (!response.ok) {
    let detail = "";
    try {
      const body = (await response.json()) as {
        detail?: unknown;
        error?: {
          code?: unknown;
          message?: unknown;
          retry?: {
            retryable?: unknown;
            after_seconds?: unknown;
          };
          details?: unknown;
        };
      };
      detail = parseApiErrorBody(body).messageSuffix;
    } catch {
      detail = "";
    }
    throw new Error(`API request failed (${response.status}) for ${streamUrl}${detail}`);
  }

  if (!response.body) {
    throw new Error("Streaming response body is not available.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const dispatchEvent = (rawEvent: string) => {
    const lines = rawEvent.split("\n");
    let eventName = "message";
    const dataLines: string[] = [];

    for (const line of lines) {
      if (line.startsWith("event:")) {
        eventName = line.slice(6).trim();
        continue;
      }
      if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trim());
      }
    }

    if (dataLines.length === 0) {
      return;
    }

    let payloadObject: unknown = {};
    try {
      payloadObject = JSON.parse(dataLines.join("\n"));
    } catch {
      payloadObject = {};
    }

    if (eventName === "conversation") {
      callbacks.onConversation?.(payloadObject as StreamConversationEvent);
      return;
    }
    if (eventName === "token") {
      callbacks.onToken?.(payloadObject as StreamTokenEvent);
      return;
    }
    if (eventName === "done") {
      callbacks.onDone?.(payloadObject as StreamDoneEvent);
      return;
    }
    if (eventName === "error") {
      callbacks.onError?.(payloadObject as StreamErrorEvent);
    }
  };

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    let separatorIndex = buffer.indexOf("\n\n");
    while (separatorIndex !== -1) {
      const rawEvent = buffer.slice(0, separatorIndex).trim();
      buffer = buffer.slice(separatorIndex + 2);
      if (rawEvent.length > 0) {
        dispatchEvent(rawEvent);
      }
      separatorIndex = buffer.indexOf("\n\n");
    }
  }

  const tail = buffer.trim();
  if (tail.length > 0) {
    dispatchEvent(tail);
  }
}

export async function getTrainingDatasets(userId = 1, includeArchived = false): Promise<TrainingDatasetSummary[]> {
  const response = await requestJson<TrainingDatasetsResponse>(`/api/training/datasets?user_id=${userId}&include_archived=${includeArchived}`);
  return response.items.map((item) => ({
    id: item.id,
    name: item.name,
    description: item.description,
    sourceType: item.source_type,
    status: item.status,
    version: item.version,
    projectId: item.project_id,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
    metadata: item.metadata,
  }));
}

export async function getTrainingDatasetFiles(userId = 1): Promise<TrainingDatasetFileEntry[]> {
  const response = await requestJson<TrainingDatasetFilesResponse>(`/api/training/datasets/files?user_id=${userId}`);
  return response.items.map((item) => ({
    relativePath: item.relative_path,
    sizeBytes: item.size_bytes,
    modifiedAt: item.modified_at,
  }));
}

export async function createTrainingDataset(
  payload: {
    userId?: number;
    name: string;
    description?: string | null;
    projectId?: number | null;
    sourceType?: string;
    status?: string;
    version?: number;
    metadata?: Record<string, unknown>;
  },
): Promise<TrainingDatasetSummary> {
  const response = await requestJson<TrainingDatasetsResponse["items"][number]>("/api/training/datasets", {
    method: "POST",
    body: JSON.stringify({
      user_id: payload.userId ?? 1,
      name: payload.name,
      description: payload.description ?? null,
      project_id: payload.projectId ?? null,
      source_type: payload.sourceType ?? "manual",
      status: payload.status ?? "ready",
      version: payload.version ?? 1,
      metadata: payload.metadata ?? {},
    }),
  });
  return {
    id: response.id,
    name: response.name,
    description: response.description,
    sourceType: response.source_type,
    status: response.status,
    version: response.version,
    projectId: response.project_id,
    createdAt: response.created_at,
    updatedAt: response.updated_at,
    metadata: response.metadata,
  };
}

export type FolderBatchResult = {
  root: string;
  sequential: boolean;
  new_cycle: boolean;
  cycle_id: string | null;
  project_id: number | null;
  queued: Array<{ folder: string; dataset_id: number; job_id: number }>;
  skipped: Array<{ folder: string; dataset_id?: number; job_id?: number; reason: string }>;
  errors: Array<{ folder: string; reason: string; message?: string }>;
  counts: { discovered: number; queued: number; skipped: number; errors: number };
};

export async function startTrainingFolderBatch(payload: {
  userId?: number; baseModelId?: string; trainerName?: string; projectId?: number | null; newCycle?: boolean;
}): Promise<FolderBatchResult> {
  return requestJson<FolderBatchResult>("/api/training/jobs/batch-from-folder", {
    method: "POST",
    body: JSON.stringify({
      user_id: payload.userId ?? 1,
      base_model_id: payload.baseModelId?.trim() || null,
      trainer_name: payload.trainerName?.trim() || null,
      project_id: payload.projectId ?? null,
      new_cycle: payload.newCycle ?? false,
      hyperparameters: {},
    }),
  });
}

export async function assignTrainingProject(payload: {
  userId?: number;
  projectId: number | null;
  datasetIds?: number[];
  includeArchived?: boolean;
}): Promise<{ updated: number; project_id: number | null }> {
  return requestJson<{ updated: number; project_id: number | null }>("/api/training/datasets/assign-project", {
    method: "PATCH",
    body: JSON.stringify({
      user_id: payload.userId ?? 1,
      project_id: payload.projectId,
      dataset_ids: payload.datasetIds ?? [],
      include_archived: payload.includeArchived ?? true,
    }),
  });
}

export async function registerTrainingDatasetFile(payload: {
  userId?: number;
  name: string;
  files: TrainingRoleFiles;
  description?: string | null;
  projectId?: number | null;
  metadata?: Record<string, unknown>;
}): Promise<TrainingDatasetSummary> {
  const items = Object.entries(payload.files)
    .filter((entry): entry is [TrainingFileRole, string] => typeof entry[1] === "string" && entry[1].trim().length > 0)
    .map(([role, fileName]) => ({ role, file_name: fileName.trim() }));

  const sourceLegacy = payload.files.source ?? payload.files.training ?? "";
  const validationLegacy = payload.files.validation ?? null;
  const testLegacy = payload.files.test ?? null;

  const response = await requestJson<TrainingDatasetsResponse["items"][number]>("/api/training/datasets/register-file", {
    method: "POST",
    body: JSON.stringify({
      user_id: payload.userId ?? 1,
      name: payload.name,
      file_name: sourceLegacy,
      validation_file_name: validationLegacy,
      test_file_name: testLegacy,
      files: items,
      description: payload.description ?? null,
      project_id: payload.projectId ?? null,
      metadata: payload.metadata ?? {},
    }),
  });
  return {
    id: response.id,
    name: response.name,
    description: response.description,
    sourceType: response.source_type,
    status: response.status,
    version: response.version,
    projectId: response.project_id,
    createdAt: response.created_at,
    updatedAt: response.updated_at,
    metadata: response.metadata,
  };
}

export async function uploadTrainingDataset(payload: {
  userId?: number;
  name: string;
  files: Partial<Record<Exclude<TrainingFileRole, "canonical">, File | null>>;
  description?: string | null;
  projectId?: number | null;
  metadata?: Record<string, unknown>;
}): Promise<TrainingDatasetSummary> {
  const form = new FormData();
  form.set("user_id", String(payload.userId ?? 1));
  form.set("name", payload.name);
  form.set("description", payload.description ?? "");
  form.set("project_id", payload.projectId == null ? "" : String(payload.projectId));
  form.set("metadata_json", JSON.stringify(payload.metadata ?? {}));
  const fileEntries: Array<[Exclude<TrainingFileRole, "canonical">, string]> = [
    ["source", "source_file"],
    ["training", "training_file"],
    ["validation", "validation_file"],
    ["test", "test_file"],
    ["manifest", "manifest_file"],
  ];
  for (const [role, fieldName] of fileEntries) {
    const file = payload.files[role];
    if (file != null) {
      form.set(fieldName, file);
    }
  }

  const url = withApiBase("/api/training/datasets/upload");
  const headers = new Headers();
  const token = getAuthToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(url, { method: "POST", body: form, headers });
  if (!response.ok) {
    throw new Error(`API request failed (${response.status}) for ${url}`);
  }
  const body = (await response.json()) as TrainingDatasetsResponse["items"][number];
  return {
    id: body.id,
    name: body.name,
    description: body.description,
    sourceType: body.source_type,
    status: body.status,
    version: body.version,
    projectId: body.project_id,
    createdAt: body.created_at,
    updatedAt: body.updated_at,
    metadata: body.metadata,
  };
}

export async function importTrainingDatasetFromUrl(payload: {
  userId?: number;
  name: string;
  files: Partial<Record<"source" | "validation" | "test", string>>;
  description?: string | null;
  projectId?: number | null;
  metadata?: Record<string, unknown>;
}): Promise<TrainingDatasetSummary> {
  const response = await requestJson<TrainingDatasetsResponse["items"][number]>("/api/training/datasets/import-url", {
    method: "POST",
    body: JSON.stringify({
      user_id: payload.userId ?? 1,
      name: payload.name,
      source_url: payload.files.source,
      validation_source_url: payload.files.validation ?? null,
      test_source_url: payload.files.test ?? null,
      description: payload.description ?? null,
      project_id: payload.projectId ?? null,
      metadata: payload.metadata ?? {},
    }),
  });
  return {
    id: response.id,
    name: response.name,
    description: response.description,
    sourceType: response.source_type,
    status: response.status,
    version: response.version,
    projectId: response.project_id,
    createdAt: response.created_at,
    updatedAt: response.updated_at,
    metadata: response.metadata,
  };
}

export async function archiveTrainingDataset(datasetId: number, userId = 1): Promise<TrainingDatasetSummary> {
  const response = await requestJson<TrainingDatasetsResponse["items"][number]>(`/api/training/datasets/${datasetId}/archive?user_id=${userId}`, {
    method: "POST",
  });
  return {
    id: response.id,
    name: response.name,
    description: response.description,
    sourceType: response.source_type,
    status: response.status,
    version: response.version,
    projectId: response.project_id,
    createdAt: response.created_at,
    updatedAt: response.updated_at,
    metadata: response.metadata,
  };
}

export async function unarchiveTrainingDataset(datasetId: number, userId = 1): Promise<TrainingDatasetSummary> {
  const response = await requestJson<TrainingDatasetsResponse["items"][number]>(`/api/training/datasets/${datasetId}/unarchive?user_id=${userId}`, {
    method: "POST",
  });
  return {
    id: response.id,
    name: response.name,
    description: response.description,
    sourceType: response.source_type,
    status: response.status,
    version: response.version,
    projectId: response.project_id,
    createdAt: response.created_at,
    updatedAt: response.updated_at,
    metadata: response.metadata,
  };
}

export async function deleteTrainingDataset(datasetId: number, userId = 1): Promise<void> {
  await requestJson<{ deleted: boolean }>(`/api/training/datasets/${datasetId}?user_id=${userId}`, {
    method: "DELETE",
  });
}

export async function uploadTrainingDatasetBundle(payload: {
  userId?: number;
  name: string;
  bundleFile: File;
  description?: string | null;
  projectId?: number | null;
  metadata?: Record<string, unknown>;
}): Promise<TrainingDatasetSummary> {
  const form = new FormData();
  form.set("user_id", String(payload.userId ?? 1));
  form.set("name", payload.name);
  form.set("description", payload.description ?? "");
  form.set("project_id", payload.projectId == null ? "" : String(payload.projectId));
  form.set("metadata_json", JSON.stringify(payload.metadata ?? {}));
  form.set("bundle_file", payload.bundleFile);

  const url = withApiBase("/api/training/datasets/upload-bundle");
  const headers = new Headers();
  const token = getAuthToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(url, { method: "POST", body: form, headers });
  if (!response.ok) {
    throw new Error(`API request failed (${response.status}) for ${url}`);
  }
  const body = (await response.json()) as TrainingDatasetsResponse["items"][number];
  return {
    id: body.id,
    name: body.name,
    description: body.description,
    sourceType: body.source_type,
    status: body.status,
    version: body.version,
    projectId: body.project_id,
    createdAt: body.created_at,
    updatedAt: body.updated_at,
    metadata: body.metadata,
  };
}

export async function getTrainingJobs(userId = 1, includeArchived = false): Promise<TrainingJobSummary[]> {
  const response = await requestJson<TrainingJobsResponse>(`/api/training/jobs?user_id=${userId}&include_archived=${includeArchived}`);
  return response.items.map((item) => ({
    id: item.id,
    datasetId: item.dataset_id,
    baseModelId: item.base_model_id,
    trainerName: item.trainer_name,
    status: item.status,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
    hyperparameters: item.hyperparameters,
    result: item.result,
    errorMessage: item.error_message,
    progress: item.progress ?? null,
    currentStep: item.current_step ?? null,
    totalSteps: item.total_steps ?? null,
    currentEpoch: item.current_epoch ?? null,
    loss: item.loss ?? null,
    learningRate: item.learning_rate ?? null,
    logs: item.logs ?? [],
    isSimulation: item.is_simulation ?? null,
    estimatedVramMb: item.estimated_vram_mb ?? null,
    peakVramMb: item.peak_vram_mb ?? null,
    samplesPerSecond: item.samples_per_second ?? null,
    stepsPerSecond: item.steps_per_second ?? null,
    elapsedSeconds: item.elapsed_seconds ?? null,
  }));
}

export async function createTrainingJob(
  payload: {
    userId?: number;
    datasetId: number;
    baseModelId?: string;
    trainerName?: string;
    hyperparameters?: Record<string, unknown>;
  },
): Promise<TrainingJobSummary> {
  const normalizedBaseModelId = typeof payload.baseModelId === "string" ? payload.baseModelId.trim() : "";
  const response = await requestJson<TrainingJobsResponse["items"][number]>("/api/training/jobs", {
    method: "POST",
    body: JSON.stringify({
      user_id: payload.userId ?? 1,
      dataset_id: payload.datasetId,
      base_model_id: normalizedBaseModelId.length > 0 ? normalizedBaseModelId : undefined,
      trainer_name: payload.trainerName,
      hyperparameters: payload.hyperparameters ?? {},
    }),
  });
  return {
    id: response.id,
    datasetId: response.dataset_id,
    baseModelId: response.base_model_id,
    trainerName: response.trainer_name,
    status: response.status,
    createdAt: response.created_at,
    updatedAt: response.updated_at,
    hyperparameters: response.hyperparameters,
    result: response.result,
    errorMessage: response.error_message,
    progress: response.progress ?? null,
    currentStep: response.current_step ?? null,
    totalSteps: response.total_steps ?? null,
    currentEpoch: response.current_epoch ?? null,
    loss: response.loss ?? null,
    learningRate: response.learning_rate ?? null,
    logs: response.logs ?? [],
    isSimulation: response.is_simulation ?? null,
    estimatedVramMb: response.estimated_vram_mb ?? null,
    peakVramMb: response.peak_vram_mb ?? null,
    samplesPerSecond: response.samples_per_second ?? null,
    stepsPerSecond: response.steps_per_second ?? null,
    elapsedSeconds: response.elapsed_seconds ?? null,
  };
}

export async function runTrainingPreflight(
  payload: {
    userId?: number;
    datasetId: number;
    baseModelId?: string;
    trainerName?: string;
    hyperparameters?: Record<string, unknown>;
  },
): Promise<TrainingPreflightResult> {
  const normalizedBaseModelId = typeof payload.baseModelId === "string" ? payload.baseModelId.trim() : "";
  const response = await requestJson<TrainingPreflightResponse>("/api/training/preflight", {
    method: "POST",
    body: JSON.stringify({
      user_id: payload.userId ?? 1,
      dataset_id: payload.datasetId,
      base_model_id: normalizedBaseModelId.length > 0 ? normalizedBaseModelId : undefined,
      trainer_name: payload.trainerName,
      hyperparameters: payload.hyperparameters ?? {},
    }),
  });

  return {
    ready: response.ready,
    modelId: response.model_id,
    modelName: response.model_name,
    modelFormat: response.model_format,
    trainer: response.trainer,
    targetModulesMode: response.target_modules_mode,
    resolvedTargetModules: response.resolved_target_modules,
    targetModulesSource: response.target_modules_source,
    cudaAvailable: response.cuda_available,
    supports4bit: response.supports_4bit,
    datasetValid: response.dataset_valid,
    warnings: response.warnings,
    errors: response.errors,
  };
}

export async function cancelTrainingJob(jobId: number, userId = 1): Promise<TrainingJobSummary> {
  const response = await requestJson<TrainingJobsResponse["items"][number]>(
    `/api/training/jobs/${jobId}/cancel?user_id=${userId}`,
    {
      method: "POST",
    },
  );
  return {
    id: response.id,
    datasetId: response.dataset_id,
    baseModelId: response.base_model_id,
    trainerName: response.trainer_name,
    status: response.status,
    createdAt: response.created_at,
    updatedAt: response.updated_at,
    hyperparameters: response.hyperparameters,
    result: response.result,
    errorMessage: response.error_message,
    progress: response.progress ?? null,
    currentStep: response.current_step ?? null,
    totalSteps: response.total_steps ?? null,
    currentEpoch: response.current_epoch ?? null,
    loss: response.loss ?? null,
    learningRate: response.learning_rate ?? null,
    logs: response.logs ?? [],
    isSimulation: response.is_simulation ?? null,
    estimatedVramMb: response.estimated_vram_mb ?? null,
    peakVramMb: response.peak_vram_mb ?? null,
    samplesPerSecond: response.samples_per_second ?? null,
    stepsPerSecond: response.steps_per_second ?? null,
    elapsedSeconds: response.elapsed_seconds ?? null,
  };
}

export async function retryTrainingJob(jobId: number, userId = 1): Promise<TrainingJobSummary> {
  const response = await requestJson<TrainingJobsResponse["items"][number]>(
    `/api/training/jobs/${jobId}/retry?user_id=${userId}`,
    {
      method: "POST",
    },
  );
  return {
    id: response.id,
    datasetId: response.dataset_id,
    baseModelId: response.base_model_id,
    trainerName: response.trainer_name,
    status: response.status,
    createdAt: response.created_at,
    updatedAt: response.updated_at,
    hyperparameters: response.hyperparameters,
    result: response.result,
    errorMessage: response.error_message,
    progress: response.progress ?? null,
    currentStep: response.current_step ?? null,
    totalSteps: response.total_steps ?? null,
    currentEpoch: response.current_epoch ?? null,
    loss: response.loss ?? null,
    learningRate: response.learning_rate ?? null,
    logs: response.logs ?? [],
    isSimulation: response.is_simulation ?? null,
    estimatedVramMb: response.estimated_vram_mb ?? null,
    peakVramMb: response.peak_vram_mb ?? null,
    samplesPerSecond: response.samples_per_second ?? null,
    stepsPerSecond: response.steps_per_second ?? null,
    elapsedSeconds: response.elapsed_seconds ?? null,
  };
}

export async function archiveTrainingJob(jobId: number, userId = 1): Promise<TrainingJobSummary> {
  const response = await requestJson<TrainingJobsResponse["items"][number]>(`/api/training/jobs/${jobId}/archive?user_id=${userId}`, {
    method: "POST",
  });
  return {
    id: response.id,
    datasetId: response.dataset_id,
    baseModelId: response.base_model_id,
    trainerName: response.trainer_name,
    status: response.status,
    createdAt: response.created_at,
    updatedAt: response.updated_at,
    hyperparameters: response.hyperparameters,
    result: response.result,
    errorMessage: response.error_message,
    progress: response.progress ?? null,
    currentStep: response.current_step ?? null,
    totalSteps: response.total_steps ?? null,
    currentEpoch: response.current_epoch ?? null,
    loss: response.loss ?? null,
    learningRate: response.learning_rate ?? null,
    logs: response.logs ?? [],
    isSimulation: response.is_simulation ?? null,
    estimatedVramMb: response.estimated_vram_mb ?? null,
    peakVramMb: response.peak_vram_mb ?? null,
    samplesPerSecond: response.samples_per_second ?? null,
    stepsPerSecond: response.steps_per_second ?? null,
    elapsedSeconds: response.elapsed_seconds ?? null,
  };
}

export async function unarchiveTrainingJob(jobId: number, userId = 1): Promise<TrainingJobSummary> {
  const response = await requestJson<TrainingJobsResponse["items"][number]>(`/api/training/jobs/${jobId}/unarchive?user_id=${userId}`, {
    method: "POST",
  });
  return {
    id: response.id,
    datasetId: response.dataset_id,
    baseModelId: response.base_model_id,
    trainerName: response.trainer_name,
    status: response.status,
    createdAt: response.created_at,
    updatedAt: response.updated_at,
    hyperparameters: response.hyperparameters,
    result: response.result,
    errorMessage: response.error_message,
    progress: response.progress ?? null,
    currentStep: response.current_step ?? null,
    totalSteps: response.total_steps ?? null,
    currentEpoch: response.current_epoch ?? null,
    loss: response.loss ?? null,
    learningRate: response.learning_rate ?? null,
    logs: response.logs ?? [],
    isSimulation: response.is_simulation ?? null,
    estimatedVramMb: response.estimated_vram_mb ?? null,
    peakVramMb: response.peak_vram_mb ?? null,
    samplesPerSecond: response.samples_per_second ?? null,
    stepsPerSecond: response.steps_per_second ?? null,
    elapsedSeconds: response.elapsed_seconds ?? null,
  };
}

export async function deleteTrainingJob(jobId: number, userId = 1): Promise<void> {
  await requestJson<{ deleted: boolean }>(`/api/training/jobs/${jobId}?user_id=${userId}`, {
    method: "DELETE",
  });
}
