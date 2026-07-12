export type NavView = "Chats" | "Suche" | "Projekte" | "Bibliothek" | "Termine" | "Plugins" | "Einstellungen";

export type AuthUser = {
  id: number;
  username: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
};

export type PresenceUser = {
  id: number;
  username: string;
  isAdmin: boolean;
  isActive: boolean;
  online: boolean;
  lastSeenAt: string | null;
};

export type UiModelEntry = {
  id: string;
  name: string;
  modelPath: string;
  backend: string;
  loadStatus: string;
  loaded: boolean;
  category: "lokal" | "remote";
  isActive: boolean;
  modelFormat?: string;
  modelFamily?: string;
  taskType?: string;
  group?: string;
  relevance?: "active" | "favorite" | "relevant" | "unavailable" | "irrelevant";
  relevanceFlag?: "favorite" | "irrelevant" | null;
  statusLabel?: string;
  statusColor?: "green" | "blue" | "yellow" | "red" | "gray";
  reasonUnavailable?: string | null;
  requiresCustomCode?: boolean;
  customCodeTrusted?: boolean;
  customLoaderId?: string | null;
  capabilities?: {
    supportsInference: boolean;
    supportsTraining: boolean;
    supportsPeftTraining: boolean;
    supports4bit: boolean;
    supportsChat: boolean;
    supportsEmbeddings: boolean;
    supportsReranking: boolean;
    supportsVision: boolean;
    supportsAudio: boolean;
  };
};

export type TrainingTrainerOption = {
  id: string;
  label: string;
  available: boolean;
  reasonUnavailable: string | null;
  isSimulation: boolean;
};

export type TrainingModelCompatibilityEntry = {
  modelId: string;
  modelName: string;
  compatible: boolean;
  reason: string | null;
};

export type WorkspaceProject = {
  id: number;
  name: string;
  chats: number;
  documents: number;
};

export type WorkspaceAppointment = {
  id: number;
  date: string;
  title: string;
  state: string;
};

export type WorkspaceSource = {
  id: number;
  file: string;
  position: string;
  relevance: string;
  status?: string;
  source?: string;
};

export type ConversationSummary = {
  id: number;
  title: string;
  updatedAt: string;
  lastMessage: string | null;
  ownerUserId: number;
  ownerUsername: string;
  projectId: number | null;
};

export type ConversationGenerationParams = {
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

export type ConversationGenerationProfileVersion = {
  id: string;
  name: string;
  created_at: string;
  created_by_user_id: number;
  params: ConversationGenerationParams;
};

export type ConversationGenerationProfileHistoryEvent = {
  id: string;
  action: string;
  version_id: string;
  created_at: string;
  user_id: number;
};

export type ConversationGenerationProfiles = {
  conversation_id: number;
  active_version_id: string | null;
  versions: ConversationGenerationProfileVersion[];
  history: ConversationGenerationProfileHistoryEvent[];
};

export type ChatMessage = {
  id: number;
  conversationId: number;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  authorUsername: string | null;
};

export type SendWorkflowState =
  | "idle"
  | "disabled"
  | "submitting"
  | "success"
  | "streaming"
  | "error"
  | "stopping";

export type HealthModelState = {
  activeModelId: number | null;
  loaded: boolean;
  backend: string | null;
};

export type ApiCapabilities = {
  service: string;
  version: string;
  features: Record<string, boolean>;
};

export type TrainingDatasetSummary = {
  id: number;
  name: string;
  description: string | null;
  sourceType: string;
  status: string;
  version: number;
  projectId: number | null;
  createdAt: string;
  updatedAt: string;
  metadata: Record<string, unknown>;
};

export type TrainingDatasetFileEntry = {
  relativePath: string;
  sizeBytes: number;
  modifiedAt: string;
};

export type TrainingJobSummary = {
  id: number;
  datasetId: number;
  baseModelId: string;
  trainerName: string;
  status: string;
  createdAt: string;
  updatedAt: string;
  hyperparameters: Record<string, unknown>;
  result: Record<string, unknown> | null;
  errorMessage: string | null;
  progress?: number | null;
  currentStep?: number | null;
  totalSteps?: number | null;
  currentEpoch?: number | null;
  loss?: number | null;
  learningRate?: number | null;
  logs?: string[];
  isSimulation?: boolean | null;
  estimatedVramMb?: number | null;
  peakVramMb?: number | null;
  samplesPerSecond?: number | null;
  stepsPerSecond?: number | null;
  elapsedSeconds?: number | null;
};

export type TrainingPreflightIssue = {
  code: string;
  message: string;
};

export type TrainingPreflightResult = {
  ready: boolean;
  modelId: number | null;
  modelName: string | null;
  modelFormat: string | null;
  trainer: string;
  cudaAvailable: boolean;
  supports4bit: boolean;
  datasetValid: boolean;
  warnings: TrainingPreflightIssue[];
  errors: TrainingPreflightIssue[];
};
