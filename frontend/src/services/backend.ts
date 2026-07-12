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
type SettingResponse = {
  category: string;
  key: string;
  value: unknown;
};
type UpdateSettingResponse = {
  updated: boolean;
  effect: string;
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
  cuda_available: boolean;
  supports_4bit: boolean;
  dataset_valid: boolean;
  warnings: Array<{ code: string; message: string }>;
  errors: Array<{ code: string; message: string }>;
};

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

let authToken: string | null = null;
let heartbeatInFlight: Promise<void> | null = null;

export function setAuthToken(token: string | null): void {
  authToken = token && token.trim().length > 0 ? token.trim() : null;
}

export function getAuthToken(): string | null {
  return authToken;
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

  if (body.error && typeof body.error === "object") {
    const errorCode = typeof body.error.code === "string" ? body.error.code : null;
    const errorMessage = typeof body.error.message === "string" ? body.error.message : null;
    const retryAfter =
      body.error.retry && typeof body.error.retry.after_seconds === "number"
        ? body.error.retry.after_seconds
        : null;

    if (errorCode && errorMessage) {
      messageSuffix = `: [${errorCode}] ${errorMessage}`;
    } else if (errorMessage) {
      messageSuffix = `: ${errorMessage}`;
    }

    if (retryAfter != null) {
      messageSuffix += ` (retry after ${retryAfter}s)`;
    }
  } else if (typeof body.detail === "string") {
    messageSuffix = `: ${body.detail}`;
  }

  return { messageSuffix };
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = withApiBase(path);
  const headers = new Headers(init?.headers ?? { "Content-Type": "application/json" });
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
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

export async function getModels(): Promise<UiModelEntry[]> {
  const response = await requestJson<ModelListResponse>("/api/models");
  return response.items.map((item) => ({
    id: String(item.id),
    name: item.name,
    modelPath: item.model_path,
    backend: item.backend,
    loadStatus: item.load_status,
    loaded: item.load_status === "ready",
    category: "lokal",
    isActive: item.is_active,
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
  const route = authToken ? "/api/auth/me" : `/api/auth/me?user_id=${userId}`;
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
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
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

export async function getSetting(category: string, key: string, userId?: number): Promise<unknown> {
  const userQuery = userId != null ? `?user_id=${userId}` : "";
  const response = await requestJson<SettingResponse>(`/api/settings/${category}/${key}${userQuery}`);
  return response.value;
}

export async function updateSetting(category: string, key: string, value: unknown, userId?: number): Promise<UpdateSettingResponse> {
  return requestJson<UpdateSettingResponse>("/api/settings", {
    method: "POST",
    body: JSON.stringify({ category, key, value, user_id: userId ?? null }),
  });
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

export async function createWorkspaceProject(name: string, userId = 1): Promise<WorkspaceProject> {
  return requestJson<WorkspaceProject>("/api/workspace/projects", {
    method: "POST",
    body: JSON.stringify({ name, user_id: userId }),
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
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
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

export async function getTrainingDatasets(userId = 1): Promise<TrainingDatasetSummary[]> {
  const response = await requestJson<TrainingDatasetsResponse>(`/api/training/datasets?user_id=${userId}`);
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

export async function registerTrainingDatasetFile(payload: {
  userId?: number;
  name: string;
  fileName: string;
  validationFileName?: string;
  description?: string | null;
  projectId?: number | null;
  metadata?: Record<string, unknown>;
}): Promise<TrainingDatasetSummary> {
  const response = await requestJson<TrainingDatasetsResponse["items"][number]>("/api/training/datasets/register-file", {
    method: "POST",
    body: JSON.stringify({
      user_id: payload.userId ?? 1,
      name: payload.name,
      file_name: payload.fileName,
      validation_file_name: payload.validationFileName ?? null,
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
  sourceFile: File;
  validationFile?: File | null;
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
  form.set("source_file", payload.sourceFile);
  if (payload.validationFile) {
    form.set("validation_file", payload.validationFile);
  }

  const url = withApiBase("/api/training/datasets/upload");
  const headers = new Headers();
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
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
  sourceUrl: string;
  validationSourceUrl?: string;
  description?: string | null;
  projectId?: number | null;
  metadata?: Record<string, unknown>;
}): Promise<TrainingDatasetSummary> {
  const response = await requestJson<TrainingDatasetsResponse["items"][number]>("/api/training/datasets/import-url", {
    method: "POST",
    body: JSON.stringify({
      user_id: payload.userId ?? 1,
      name: payload.name,
      source_url: payload.sourceUrl,
      validation_source_url: payload.validationSourceUrl ?? null,
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

export async function getTrainingJobs(userId = 1): Promise<TrainingJobSummary[]> {
  const response = await requestJson<TrainingJobsResponse>(`/api/training/jobs?user_id=${userId}`);
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
