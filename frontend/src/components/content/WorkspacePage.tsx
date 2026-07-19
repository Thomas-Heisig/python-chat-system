import { useEffect, useState, type ReactNode } from "react";
import { getAuthToken } from "../../services/backend";
import { BusinessLetterManualPage } from "../../../../plugins/business_letter/frontend/BusinessLetterManualPage";
import { CalculatorManualPage } from "../../../../plugins/calculator/frontend/CalculatorManualPage";
import type {
  AuthUser,
  PluginCatalogEntry,
  PluginFrontendAction,
  PluginSettingField,
  PluginSettingsDrafts,
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

type PluginFieldErrors = Record<string, string>;
type PluginExecuteResponse = {
  plugin_id: string;
  plugin_input: Record<string, unknown>;
  plugin_settings: Record<string, unknown>;
  plugin_response: Record<string, unknown>;
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

type GeneralSettingsDraft = {
  language: "de" | "en";
  theme: "system" | "light" | "dark";
  timezone: string;
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
  cleanStartPending: boolean;
  chatSettingsPending: boolean;
  chatCleanupPending: boolean;
  knowledgeSettingsPending: boolean;
  integrationSettingsPending: boolean;
  logsSettingsPending: boolean;
  trainingSettingsPending: boolean;
  trainingBatchPending: boolean;
  trainingPreflightPending: boolean;
  modelDirectories: string[];
  modelProfile: ModelProfileDraft;
  generalSettings: GeneralSettingsDraft;
  chatSettings: ChatSettingsDraft;
  chatCleanupStats: ChatCleanupStats | null;
  knowledgeSettings: KnowledgeSettingsDraft;
  integrationSettings: IntegrationSettingsDraft;
  integrationTestResults: Partial<Record<(typeof testableIntegrationKeyOrder)[number], IntegrationBatchResult>>;
  logsSettings: LogsSettingsDraft;
  pluginDescriptors: PluginCatalogEntry[];
  pluginSettingsDrafts: PluginSettingsDrafts;
  pluginSettingsErrors: Record<string, PluginFieldErrors>;
  savingPluginId: string | null;
  trainingSettings: TrainingSettingsDraft;
  trainingPreflightResult: TrainingPreflightResult | null;
  trainingDatasetFiles: TrainingDatasetFileEntry[];
  trainingDatasets: TrainingDatasetSummary[];
  trainingJobs: TrainingJobSummary[];
  trainerOptions: TrainingTrainerOption[];
  trainingCompatibility: Record<string, { compatible: boolean; reason: string | null }>;
  onFetchTrainingCompatibility: (trainerName: string) => Promise<Record<string, { compatible: boolean; reason: string | null }>>;
  onActivateModel: (modelId: string) => Promise<void>;
  onPullModel: (modelId: string) => Promise<void>;
  onCancelPullModel: (modelId: string) => Promise<void>;
  onDeactivateModel: () => Promise<void>;
  onScanModels: () => Promise<void>;
  onSetModelRelevance: (modelId: string, relevance: "favorite" | "irrelevant" | null) => Promise<void>;
  onSaveModelDirectories: (directories: string[]) => Promise<void>;
  onSaveModelProfile: (profile: ModelProfileDraft) => Promise<void>;
  onSaveGeneralSettings: (profile: GeneralSettingsDraft) => Promise<void>;
  onCleanStartReset: () => Promise<void>;
  onSaveChatSettings: (profile: ChatSettingsDraft) => Promise<void>;
  onCleanupObsoleteChatSettings: () => Promise<void>;
  onSaveKnowledgeSettings: (profile: KnowledgeSettingsDraft) => Promise<void>;
  onSaveIntegrationSettings: (profile: IntegrationSettingsDraft) => Promise<void>;
  onSaveIntegrationTestResults: (
    results: Partial<Record<(typeof testableIntegrationKeyOrder)[number], IntegrationBatchResult>>,
  ) => Promise<void>;
  onSaveLogsSettings: (profile: LogsSettingsDraft) => Promise<void>;
  onPluginSettingChange: (pluginId: string, fieldKey: string, value: unknown) => void;
  onSavePluginSettings: (pluginId: string) => Promise<void>;
  onExecutePlugin?: (input: {
    pluginId: string;
    pluginInput?: Record<string, unknown>;
    pluginSettings?: Record<string, unknown>;
    userId?: number;
  }) => Promise<PluginExecuteResponse>;
  onSaveTrainingSettings: (profile: TrainingSettingsDraft) => Promise<void>;
  onBatchCreateTrainingJobs: (newCycle?: boolean) => Promise<void>;
  onAssignTrainingProject: (projectId: number | null) => Promise<void>;
  onCreateTrainingDataset: (name: string, projectId: number | null) => Promise<void>;
  onRegisterTrainingDatasetFile: (
    name: string,
    files: Partial<Record<"source" | "training" | "validation" | "test" | "manifest", string>>,
    projectId: number | null,
  ) => Promise<void>;
  onUploadTrainingDataset: (
    name: string,
    files: Partial<Record<"source" | "training" | "validation" | "test" | "manifest", File | null>>,
    projectId: number | null,
  ) => Promise<void>;
  onImportTrainingDatasetFromUrl: (
    name: string,
    files: Partial<Record<"source" | "validation" | "test", string>>,
    projectId: number | null,
  ) => Promise<void>;
  onUploadTrainingDatasetBundle: (name: string, bundleFile: File, projectId: number | null) => Promise<void>;
  onCreateTrainingJob: (datasetId: number, baseModelId?: string, trainerName?: string) => Promise<void>;
  onRunTrainingPreflight: (datasetId: number, baseModelId?: string, trainerName?: string) => Promise<TrainingPreflightResult>;
  onCancelTrainingJob: (jobId: number) => Promise<void>;
  onRetryTrainingJob: (jobId: number) => Promise<void>;
  onArchiveTrainingDataset: (datasetId: number) => Promise<void>;
  onDeleteTrainingDataset: (datasetId: number) => Promise<void>;
  onUnarchiveTrainingDataset: (datasetId: number) => Promise<void>;
  onArchiveTrainingJob: (jobId: number) => Promise<void>;
  onDeleteTrainingJob: (jobId: number) => Promise<void>;
  onUnarchiveTrainingJob: (jobId: number) => Promise<void>;
  currentUser: AuthUser;
  onAdminCreateUser: (username: string, password: string, isAdmin: boolean) => Promise<void>;
  onExportDiagnosticsReport: () => Promise<void>;
  selectedProjectId: number | null;
  onSelectProject: (projectId: number | null) => void;
  onCreateProject: (
    name: string,
    options?: {
      parentProjectId?: number | null;
      scopeKind?: "tenant" | "user" | "area" | "project";
      areaKey?: string | null;
      tenantKey?: string | null;
      ownerUserId?: number | null;
    },
  ) => Promise<number | void>;
  onRenameProject: (projectId: number, name: string) => Promise<void>;
  onDeleteProject: (projectId: number) => Promise<void>;
  onUpdateProjectHierarchy: (input: {
    projectId: number;
    parentProjectId: number | null;
    scopeKind: "tenant" | "user" | "area" | "project";
    areaKey: string | null;
    tenantKey: string | null;
    ownerUserId: number | null;
  }) => Promise<void>;
  onUploadWorkspaceSource: (file: File) => Promise<void>;
  onAssignSourceToProject: (sourceId: number, projectId: number | null) => Promise<void>;
};

const defaultBusinessLetterSoloInput: Record<string, unknown> = {
  letter_type: "angebot",
  subject: "Angebot fuer Fensterbank",
  communication_channel: "email",
  customer_company: "Kunde GmbH",
  customer_first_name: "Anna",
  customer_last_name: "Beispiel",
  customer_salutation: "Frau",
  customer_street: "Hauptweg 12",
  customer_zip: "10115",
  customer_city: "Berlin",
  customer_country: "Deutschland",
  recipient_email: "kunde@example.de",
  document_number: "DOC-PLUGIN-SOLO-1001",
  buyer_reference: "BR-PLUGIN-1001",
  issue_date: "2026-07-18",
  positions: [
    {
      name: "Fensterbank",
      quantity: "1",
      unit_code: "C62",
      price_net: "149.00",
      vat_category: "S",
      vat_rate: "19",
    },
  ],
};

const defaultCalculatorSoloInput: Record<string, unknown> = {
  action: "evaluate",
  expression: "(1250 * 0.19) + sqrt(81)",
  angle_mode: "rad",
  precision: 6,
};

function buildDefaultPluginSoloInput(pluginId: string): Record<string, unknown> {
  if (pluginId === "business_letter") {
    return defaultBusinessLetterSoloInput;
  }
  if (pluginId === "calculator") {
    return defaultCalculatorSoloInput;
  }
  return {};
}

const pluginLogoAssetModules = import.meta.glob("../../assets/plugin-logos/*.{svg,png,jpg,jpeg,webp}", {
  eager: true,
  import: "default",
}) as Record<string, string>;

function normalizePluginLogoKey(value: string): string {
  return value.trim().toLowerCase().replace(/[-_\s]+/g, "");
}

const pluginLogoByNormalizedId: Record<string, string> = Object.entries(pluginLogoAssetModules).reduce((acc, [path, url]) => {
  const fileName = path.split("/").pop() || "";
  const stem = fileName.replace(/\.[^.]+$/, "");
  if (!stem) {
    return acc;
  }
  acc[normalizePluginLogoKey(stem)] = url;
  return acc;
}, {} as Record<string, string>);

function resolvePluginWidgetLogo(pluginId: string): string | null {
  return pluginLogoByNormalizedId[normalizePluginLogoKey(pluginId)] || null;
}

function buildModelUiPrefsStorageKey(userId: number): string {
  return `model-ui-prefs-user-${userId}`;
}

function buildPluginUiPrefsStorageKey(userId: number): string {
  return `plugin-ui-prefs-user-${userId}`;
}

function buildWorkspaceDisplayPrefsStorageKey(userId: number): string {
  return `workspace-display-prefs-user-${userId}`;
}

function isKeyboardInputTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) {
    return false;
  }
  const tagName = target.tagName.toLowerCase();
  return tagName === "input" || tagName === "textarea" || tagName === "select" || target.isContentEditable;
}

const settingsGroups = [
  ["Allgemein", "Sprache, Theme, Zeitzone"],
  ["Darstellung", "Schriftgroesse, Sidebars, Animationen"],
  ["Chat", "Temperatur, System-Prompt, Token-Limits"],
  ["Integrationen", "API-Schluessel fuer externe Dienste"],
  ["Modelle", "Modelle, Verzeichnisse, Prompt-Profile"],
  ["Training", "Trainer, Queue und Laufzeitverhalten"],
  ["Wissen", "Embedding-Modell, Chunk-Groesse, Top-K"],
  ["Plugins", "Installiert, Berechtigungen"],
  ["Benutzer", "Profil, Passwort, Teams"],
  ["Datenbank", "Status, Backup"],
  ["Logs", "Log-Level, Anzeige"],
  ["System", "Version, Systeminfos"],
] as const;

const settingsGroupDescriptions: Record<(typeof settingsGroups)[number][0], string> = settingsGroups.reduce(
  (acc, [group, description]) => {
    acc[group] = description;
    return acc;
  },
  {} as Record<(typeof settingsGroups)[number][0], string>,
);

type SymbolProfile = "technisch" | "minimal" | "business";

const settingsGroupIconsTech: Record<(typeof settingsGroups)[number][0], string> = {
  Allgemein: "⚙",
  Darstellung: "🖼",
  Chat: "💬",
  Integrationen: "🔗",
  Modelle: "🧠",
  Training: "🏋",
  Wissen: "📚",
  Plugins: "🧩",
  Benutzer: "👤",
  Datenbank: "🗄",
  Logs: "📋",
  System: "🖥",
};

const settingsGroupIconsMinimal: Record<(typeof settingsGroups)[number][0], string> = {
  Allgemein: "•",
  Darstellung: "•",
  Chat: "•",
  Integrationen: "•",
  Modelle: "•",
  Training: "•",
  Wissen: "•",
  Plugins: "•",
  Benutzer: "•",
  Datenbank: "•",
  Logs: "•",
  System: "•",
};

const settingsGroupIconsBusiness: Record<(typeof settingsGroups)[number][0], string> = {
  Allgemein: "🏢",
  Darstellung: "🗂",
  Chat: "📞",
  Integrationen: "🤝",
  Modelle: "📈",
  Training: "🎯",
  Wissen: "📚",
  Plugins: "🧩",
  Benutzer: "👥",
  Datenbank: "🗄",
  Logs: "📝",
  System: "🏭",
};

function resolveSettingsGroupIcon(group: (typeof settingsGroups)[number][0], profile: SymbolProfile): string {
  if (profile === "minimal") {
    return settingsGroupIconsMinimal[group];
  }
  if (profile === "business") {
    return settingsGroupIconsBusiness[group];
  }
  return settingsGroupIconsTech[group];
}

function resolvePluginCategoryIcon(category: string, profile: SymbolProfile): string {
  if (profile === "minimal") {
    return "•";
  }
  if (profile === "business") {
    const normalizedBusiness = category.toLowerCase();
    if (normalizedBusiness.includes("kommunikation") || normalizedBusiness.includes("mail") || normalizedBusiness.includes("chat")) {
      return "💼";
    }
    if (normalizedBusiness.includes("daten") || normalizedBusiness.includes("db") || normalizedBusiness.includes("sql")) {
      return "📊";
    }
    if (normalizedBusiness.includes("suche") || normalizedBusiness.includes("search") || normalizedBusiness.includes("web")) {
      return "🌐";
    }
    return "🏷";
  }
  const normalized = category.toLowerCase();
  if (normalized.includes("kommunikation") || normalized.includes("mail") || normalized.includes("chat")) {
    return "✉";
  }
  if (normalized.includes("suche") || normalized.includes("search") || normalized.includes("web")) {
    return "🔎";
  }
  if (normalized.includes("daten") || normalized.includes("db") || normalized.includes("sql")) {
    return "🗃";
  }
  if (normalized.includes("system") || normalized.includes("core") || normalized.includes("ops")) {
    return "🛠";
  }
  if (normalized.includes("ki") || normalized.includes("ai") || normalized.includes("modell")) {
    return "🤖";
  }
  return "🧩";
}

function resolvePluginGroupIcon(groupName: string, profile: SymbolProfile): string {
  if (profile === "minimal") {
    return "•";
  }
  if (profile === "business") {
    const normalizedBusiness = groupName.toLowerCase();
    if (normalizedBusiness.includes("auth") || normalizedBusiness.includes("api") || normalizedBusiness.includes("token") || normalizedBusiness.includes("secret")) {
      return "🔒";
    }
    if (normalizedBusiness.includes("layout") || normalizedBusiness.includes("design") || normalizedBusiness.includes("template")) {
      return "🧱";
    }
    if (normalizedBusiness.includes("mail") || normalizedBusiness.includes("versand") || normalizedBusiness.includes("kommunikation")) {
      return "📬";
    }
    if (normalizedBusiness.includes("system") || normalizedBusiness.includes("runtime")) {
      return "🏢";
    }
    return "📁";
  }
  const normalized = groupName.toLowerCase();
  if (normalized.includes("auth") || normalized.includes("api") || normalized.includes("token") || normalized.includes("secret")) {
    return "🔐";
  }
  if (normalized.includes("layout") || normalized.includes("design") || normalized.includes("template")) {
    return "🎨";
  }
  if (normalized.includes("mail") || normalized.includes("versand") || normalized.includes("kommunikation")) {
    return "📨";
  }
  if (normalized.includes("nummer") || normalized.includes("mapping") || normalized.includes("regel")) {
    return "🧾";
  }
  if (normalized.includes("system") || normalized.includes("runtime")) {
    return "⚙";
  }
  return "🧩";
}

function describePluginFieldType(field: PluginSettingField): string {
  if (field.type === "boolean") {
    return "Schalter";
  }
  if (field.type === "select") {
    const optionCount = Array.isArray(field.options) ? field.options.length : 0;
    return optionCount > 0 ? `${optionCount} Auswahloptionen` : "Auswahlliste";
  }
  if (field.type === "password") {
    return "Geheimer Wert";
  }
  if (field.type === "number") {
    return "Numerischer Wert";
  }
  if (field.type === "text") {
    return "Mehrzeiliger Text";
  }
  return "Textwert";
}

function buildPluginGroupExpectation(groupName: string, fields: PluginSettingField[]): string {
  if (fields.length === 0) {
    return `${groupName}: keine Felder hinterlegt.`;
  }
  const requiredCount = fields.filter((field) => field.required).length;
  const leadField = fields[0];
  const leadDescription = leadField.description?.trim() || describePluginFieldType(leadField);
  const requiredText = requiredCount > 0 ? `, ${requiredCount} Pflichtfelder` : "";
  return `${fields.length} Felder${requiredText}. Startet mit: ${leadDescription}.`;
}

function buildPluginCategoryExpectation(plugins: PluginCatalogEntry[]): string {
  const totalFields = plugins.reduce((sum, plugin) => sum + (plugin.settings_fields ?? []).length, 0);
  const totalGroups = plugins.reduce((sum, plugin) => {
    const groups = new Set((plugin.settings_fields ?? []).map((field) => field.group?.trim() || "Allgemein"));
    return sum + groups.size;
  }, 0);
  return `${plugins.length} Plugins mit insgesamt ${totalGroups} Gruppen und ${totalFields} Feldern.`;
}

function humanizePluginAction(action: string): string {
  const normalized = action.replace(/[_-]+/g, " ").trim();
  if (!normalized) {
    return "Aktion";
  }
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function extractPluginActions(plugin: PluginCatalogEntry | null): PluginFrontendAction[] {
  if (!plugin?.inputSchema) {
    return [];
  }

  const rawProperties = plugin.inputSchema.properties;
  if (typeof rawProperties !== "object" || rawProperties == null) {
    return [];
  }

  const properties = rawProperties as Record<string, unknown>;
  const rawActionProperty = properties.action;
  if (typeof rawActionProperty !== "object" || rawActionProperty == null) {
    return [];
  }

  const actionProperty = rawActionProperty as Record<string, unknown>;
  const rawEnum = Array.isArray(actionProperty.enum) ? actionProperty.enum : [];
  return rawEnum
    .filter((value): value is string => typeof value === "string" && value.trim().length > 0)
    .map((value) => ({
      id: `generic:${value}`,
      label: humanizePluginAction(value),
      description: `Oeffnet die Plugin-Funktion ${value} im Runner.`,
      openTab: "manual" as const,
      pluginInput: { action: value },
    }));
}

const modelSettingsTabs = [
  ["overview", "Uebersicht"],
  ["directories", "Verzeichnisse"],
  ["prompts", "Prompt-Profil"],
] as const;

type IntegrationFieldDef = {
  key: keyof IntegrationSettingsDraft;
  label: string;
  kind?: "password" | "checkbox" | "json";
  hint?: string;
};

type IntegrationTabId = "llm" | "media" | "document" | "search" | "data" | "comm" | "security" | "future";

type IntegrationGroupDef = {
  id: string;
  title: string;
  fields: ReadonlyArray<IntegrationFieldDef>;
};

const integrationProviderSignupUrls: Partial<Record<keyof IntegrationSettingsDraft, string>> = {
  chatgptApiKey: "https://platform.openai.com/api-keys",
  deeplApiKey: "https://www.deepl.com/pro-api",
  anthropicApiKey: "https://console.anthropic.com/settings/keys",
  googleAiApiKey: "https://aistudio.google.com/apikey",
  mistralApiKey: "https://console.mistral.ai/api-keys/",
  cohereApiKey: "https://dashboard.cohere.com/api-keys",
  perplexityApiKey: "https://www.perplexity.ai/settings/api",
  groqApiKey: "https://console.groq.com/keys",
  togetherApiKey: "https://api.together.xyz/settings/api-keys",
  openrouterApiKey: "https://openrouter.ai/keys",
  huggingfaceApiKey: "https://huggingface.co/settings/tokens",
  replicateApiKey: "https://replicate.com/account/api-tokens",
  deepseekApiKey: "https://platform.deepseek.com/api_keys",
  xaiApiKey: "https://console.x.ai/",
  elevenlabsApiKey: "https://elevenlabs.io/app/settings/api-keys",
  assemblyaiApiKey: "https://www.assemblyai.com/dashboard/api-keys",
  tavilyApiKey: "https://app.tavily.com/home",
  serpapiApiKey: "https://serpapi.com/dashboard",
  googleMapsApiKey: "https://console.cloud.google.com/apis/credentials",
  mapboxApiKey: "https://account.mapbox.com/access-tokens/",
  openweatherApiKey: "https://home.openweathermap.org/api_keys",
  weatherapiApiKey: "https://www.weatherapi.com/my/",
  tomorrowioApiKey: "https://app.tomorrow.io/development/keys",
  newsapiApiKey: "https://newsapi.org/account",
  twilioApiKey: "https://www.twilio.com/console/project/api-keys",
  sendgridApiKey: "https://app.sendgrid.com/settings/api_keys",
  slackBotToken: "https://api.slack.com/apps",
  discordBotToken: "https://discord.com/developers/applications",
  githubToken: "https://github.com/settings/tokens",
  notionApiKey: "https://www.notion.so/profile/integrations",
  airtableApiKey: "https://airtable.com/create/tokens",
  stripeSecretKey: "https://dashboard.stripe.com/apikeys",
  azureOpenaiApiKey: "https://portal.azure.com/",
  awsBedrockApiKey: "https://console.aws.amazon.com/",
  deepinfraApiKey: "https://deepinfra.com/dash/api_keys",
  nvidiaNimApiKey: "https://build.nvidia.com/",
  octoaiApiKey: "https://octo.ai/dashboard/api-keys",
  fireworksApiKey: "https://app.fireworks.ai/settings/users/api-keys",
  githubCopilotApiKey: "https://github.com/settings/copilot",
  stabilityApiKey: "https://platform.stability.ai/account/keys",
  runwayApiKey: "https://app.runwayml.com/account/api-keys",
  pikaApiKey: "https://pika.art/",
  heygenApiKey: "https://app.heygen.com/settings?tab=api",
  falApiKey: "https://fal.ai/dashboard/keys",
  unstructuredApiKey: "https://app.unstructured.io/api-keys",
  llamaparseApiKey: "https://cloud.llamaindex.ai/api-key",
  firecrawlApiKey: "https://firecrawl.dev/app/api-keys",
  pineconeApiKey: "https://app.pinecone.io/",
  weaviateApiKey: "https://console.weaviate.cloud/",
  qdrantApiKey: "https://cloud.qdrant.io/",
  cloudconvertApiKey: "https://cloudconvert.com/dashboard/api/v2/keys",
  exaApiKey: "https://dashboard.exa.ai/api-keys",
  braveSearchApiKey: "https://api-dashboard.search.brave.com/app/keys",
  bingSearchApiKey: "https://portal.azure.com/",
  gnewsApiKey: "https://gnews.io/dashboard",
  scrapingbeeApiKey: "https://app.scrapingbee.com/account/api",
  apifyApiKey: "https://console.apify.com/account/integrations",
  alphaVantageApiKey: "https://www.alphavantage.co/support/#api-key",
  yahooFinanceApiKey: "https://www.yahooinc.com/",
  openexchangeratesApiKey: "https://openexchangerates.org/signup",
  whatsappBusinessApiKey: "https://developers.facebook.com/apps/",
  telegramBotToken: "https://core.telegram.org/bots#6-botfather",
  microsoftTeamsApiKey: "https://portal.azure.com/",
  calendlyApiKey: "https://calendly.com/integrations/api_webhooks",
  virustotalApiKey: "https://www.virustotal.com/gui/my-apikey",
  hibpApiKey: "https://haveibeenpwned.com/API/Key",
};

const integrationTabs: ReadonlyArray<{ id: IntegrationTabId; label: string }> = [
  { id: "llm", label: "LLM" },
  { id: "media", label: "Media" },
  { id: "document", label: "Dokumente" },
  { id: "search", label: "Suche/Web" },
  { id: "data", label: "Daten" },
  { id: "comm", label: "Kommunikation" },
  { id: "security", label: "Sicherheit" },
  { id: "future", label: "Zukunft" },
];

const testableIntegrationKeys = new Set<string>([
  "openweatherApiKey",
  "weatherapiApiKey",
  "tomorrowioApiKey",
  "exaApiKey",
  "braveSearchApiKey",
  "bingSearchApiKey",
]);

const testableIntegrationKeyOrder = [
  "openweatherApiKey",
  "weatherapiApiKey",
  "tomorrowioApiKey",
  "exaApiKey",
  "braveSearchApiKey",
  "bingSearchApiKey",
] as const;

const integrationTestableKeyLabels: Record<(typeof testableIntegrationKeyOrder)[number], string> = {
  openweatherApiKey: "OpenWeather",
  weatherapiApiKey: "WeatherAPI",
  tomorrowioApiKey: "Tomorrow.io",
  exaApiKey: "Exa",
  braveSearchApiKey: "Brave Search",
  bingSearchApiKey: "Bing Search",
};

type IntegrationKeyTestState = {
  status: "idle" | "testing" | "success" | "error";
  message: string;
};

type IntegrationKeyTestResult = {
  success: boolean;
  provider: string;
  error: string | null;
  providerErrors: string[];
  skipped: boolean;
};

type IntegrationBatchResult = {
  status: "ok" | "error" | "skipped";
  message: string;
  testedAt?: string;
  durationMs?: number;
};

function formatDurationMs(durationMs?: number): string {
  if (typeof durationMs !== "number" || !Number.isFinite(durationMs) || durationMs < 0) {
    return "-";
  }
  if (durationMs < 1000) {
    return `${Math.round(durationMs)} ms`;
  }
  return `${(durationMs / 1000).toFixed(1)} s`;
}

const integrationGroupsByTab: Record<IntegrationTabId, ReadonlyArray<IntegrationGroupDef>> = {
  llm: [
    {
      id: "primary",
      title: "Primäre LLM-Anbieter",
      fields: [
        { key: "chatgptApiKey", label: "ChatGPT / OpenAI API Key" },
        { key: "anthropicApiKey", label: "Anthropic API Key" },
        { key: "googleAiApiKey", label: "Google AI (Gemini) API Key" },
        { key: "mistralApiKey", label: "Mistral API Key" },
        { key: "cohereApiKey", label: "Cohere API Key" },
        { key: "deepseekApiKey", label: "DeepSeek API Key" },
        { key: "xaiApiKey", label: "xAI API Key" },
      ],
    },
    {
      id: "platforms",
      title: "Inference- und Routing-Plattformen",
      fields: [
        { key: "openrouterApiKey", label: "OpenRouter API Key" },
        { key: "togetherApiKey", label: "Together AI API Key" },
        { key: "groqApiKey", label: "Groq API Key" },
        { key: "perplexityApiKey", label: "Perplexity API Key" },
        { key: "huggingfaceApiKey", label: "Hugging Face API Key" },
        { key: "replicateApiKey", label: "Replicate API Key" },
        { key: "deepinfraApiKey", label: "DeepInfra API Key" },
        { key: "nvidiaNimApiKey", label: "NVIDIA NIM API Key" },
        { key: "octoaiApiKey", label: "OctoAI API Key" },
        { key: "fireworksApiKey", label: "Fireworks AI API Key" },
      ],
    },
    {
      id: "enterprise",
      title: "Enterprise und Spezial",
      fields: [
        { key: "azureOpenaiApiKey", label: "Azure OpenAI API Key" },
        { key: "awsBedrockApiKey", label: "AWS Bedrock API Key" },
        { key: "githubCopilotApiKey", label: "GitHub Copilot API Key" },
        { key: "deeplApiKey", label: "DeepL API Key" },
      ],
    },
  ],
  media: [
    {
      id: "audio",
      title: "Audio und Sprache",
      fields: [
        { key: "elevenlabsApiKey", label: "ElevenLabs API Key" },
        { key: "assemblyaiApiKey", label: "AssemblyAI API Key" },
      ],
    },
    {
      id: "vision",
      title: "Vision und Video",
      fields: [
        { key: "stabilityApiKey", label: "Stability AI API Key" },
        { key: "runwayApiKey", label: "Runway API Key" },
        { key: "pikaApiKey", label: "Pika API Key" },
        { key: "heygenApiKey", label: "HeyGen API Key" },
        { key: "falApiKey", label: "Fal.ai API Key" },
      ],
    },
  ],
  document: [
    {
      id: "rag",
      title: "Dokumente, RAG und Parsing",
      fields: [
        { key: "unstructuredApiKey", label: "Unstructured API Key" },
        { key: "llamaparseApiKey", label: "LlamaParse API Key" },
        { key: "firecrawlApiKey", label: "Firecrawl API Key" },
        { key: "pineconeApiKey", label: "Pinecone API Key" },
        { key: "weaviateApiKey", label: "Weaviate API Key" },
        { key: "qdrantApiKey", label: "Qdrant API Key" },
        { key: "cloudconvertApiKey", label: "CloudConvert API Key" },
      ],
    },
  ],
  search: [
    {
      id: "search-web",
      title: "Web und Suche",
      fields: [
        { key: "tavilyApiKey", label: "Tavily API Key" },
        { key: "serpapiApiKey", label: "SerpAPI Key" },
        { key: "exaApiKey", label: "Exa API Key" },
        { key: "braveSearchApiKey", label: "Brave Search API Key" },
        { key: "bingSearchApiKey", label: "Bing Search API Key" },
        { key: "newsapiApiKey", label: "NewsAPI Key" },
        { key: "gnewsApiKey", label: "GNews API Key" },
        { key: "scrapingbeeApiKey", label: "ScrapingBee API Key" },
        { key: "apifyApiKey", label: "Apify API Key" },
      ],
    },
    {
      id: "weather-maps",
      title: "Wetter und Karten",
      fields: [
        { key: "openweatherApiKey", label: "OpenWeather API Key" },
        { key: "weatherapiApiKey", label: "WeatherAPI Key" },
        { key: "tomorrowioApiKey", label: "Tomorrow.io API Key" },
        { key: "googleMapsApiKey", label: "Google Maps API Key" },
        { key: "mapboxApiKey", label: "Mapbox API Key" },
      ],
    },
  ],
  data: [
    {
      id: "finance-currency",
      title: "Finanz- und Marktdaten",
      fields: [
        { key: "alphaVantageApiKey", label: "Alpha Vantage API Key" },
        { key: "yahooFinanceApiKey", label: "Yahoo Finance API Key" },
        { key: "openexchangeratesApiKey", label: "OpenExchangeRates API Key" },
      ],
    },
  ],
  comm: [
    {
      id: "messaging",
      title: "Messaging und Versand",
      fields: [
        { key: "twilioApiKey", label: "Twilio API Key" },
        { key: "sendgridApiKey", label: "SendGrid API Key" },
        { key: "whatsappBusinessApiKey", label: "WhatsApp Business API Key" },
        { key: "telegramBotToken", label: "Telegram Bot Token" },
        { key: "slackBotToken", label: "Slack Bot Token" },
        { key: "discordBotToken", label: "Discord Bot Token" },
        { key: "microsoftTeamsApiKey", label: "Microsoft Teams API Key" },
        { key: "calendlyApiKey", label: "Calendly API Key" },
      ],
    },
    {
      id: "platforms",
      title: "Plattformen und Produktivität",
      fields: [
        { key: "githubToken", label: "GitHub Token" },
        { key: "notionApiKey", label: "Notion API Key" },
        { key: "airtableApiKey", label: "Airtable API Key" },
        { key: "stripeSecretKey", label: "Stripe Secret Key" },
      ],
    },
  ],
  security: [
    {
      id: "security",
      title: "Sicherheitsdienste",
      fields: [
        { key: "virustotalApiKey", label: "VirusTotal API Key" },
        { key: "hibpApiKey", label: "Have I Been Pwned API Key" },
      ],
    },
  ],
  future: [
    {
      id: "ollama",
      title: "Lokale Laufzeit",
      fields: [
        {
          key: "ollamaLocalEnabled",
          label: "Ollama lokal aktivieren (kein API-Key erforderlich)",
          kind: "checkbox",
          hint: "Steuert, ob lokale Ollama-Integrationen systemweit erlaubt sind.",
        },
      ],
    },
    {
      id: "custom",
      title: "Custom Provider Keys (JSON)",
      fields: [
        {
          key: "customProviderKeysJson",
          label: "Beliebige zusätzliche Provider-Keys als JSON-Objekt",
          kind: "json",
          hint: "Beispiel: {\n  \"my_provider_api_key\": \"...\"\n}",
        },
      ],
    },
  ],
};

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
  cleanStartPending,
  chatSettingsPending,
  chatCleanupPending,
  knowledgeSettingsPending,
  integrationSettingsPending,
  logsSettingsPending,
  trainingSettingsPending,
  trainingBatchPending,
  trainingPreflightPending,
  modelDirectories,
  modelProfile,
  generalSettings,
  chatSettings,
  chatCleanupStats,
  knowledgeSettings,
  integrationSettings,
  integrationTestResults,
  logsSettings,
  pluginDescriptors,
  pluginSettingsDrafts,
  pluginSettingsErrors,
  savingPluginId,
  trainingSettings,
  trainingPreflightResult,
  trainingDatasetFiles,
  trainingDatasets,
  trainingJobs,
  trainerOptions,
  trainingCompatibility,
  onFetchTrainingCompatibility,
  onActivateModel,
  onPullModel,
  onCancelPullModel,
  onDeactivateModel,
  onScanModels,
  onSetModelRelevance,
  onSaveModelDirectories,
  onSaveModelProfile,
  onSaveGeneralSettings,
  onCleanStartReset,
  onSaveChatSettings,
  onCleanupObsoleteChatSettings,
  onSaveKnowledgeSettings,
  onSaveIntegrationSettings,
  onSaveIntegrationTestResults,
  onSaveLogsSettings,
  onPluginSettingChange,
  onSavePluginSettings,
  onExecutePlugin,
  onSaveTrainingSettings,
  onBatchCreateTrainingJobs,
  onAssignTrainingProject,
  onCreateTrainingDataset,
  onRegisterTrainingDatasetFile,
  onUploadTrainingDataset,
  onImportTrainingDatasetFromUrl,
  onUploadTrainingDatasetBundle,
  onCreateTrainingJob,
  onRunTrainingPreflight,
  onCancelTrainingJob,
  onRetryTrainingJob,
  onArchiveTrainingDataset,
  onDeleteTrainingDataset,
  onUnarchiveTrainingDataset,
  onArchiveTrainingJob,
  onDeleteTrainingJob,
  onUnarchiveTrainingJob,
  currentUser,
  onAdminCreateUser,
  onExportDiagnosticsReport,
  selectedProjectId,
  onSelectProject,
  onCreateProject,
  onRenameProject,
  onDeleteProject,
  onUpdateProjectHierarchy,
  onUploadWorkspaceSource,
  onAssignSourceToProject,
}: WorkspacePageProps) {
  const [activeSettingsGroup, setActiveSettingsGroup] = useState<(typeof settingsGroups)[number][0]>("Allgemein");
  const [settingsModalGroup, setSettingsModalGroup] = useState<(typeof settingsGroups)[number][0] | null>(null);
  const [activeModelSettingsTab, setActiveModelSettingsTab] = useState<(typeof modelSettingsTabs)[number][0]>("overview");
  const [directoryDraft, setDirectoryDraft] = useState<string[]>(modelDirectories);
  const [newDirectory, setNewDirectory] = useState("");
  const [profileDraft, setProfileDraft] = useState<ModelProfileDraft>(modelProfile);
  const [generalDraft, setGeneralDraft] = useState<GeneralSettingsDraft>(generalSettings);
  const [chatDraft, setChatDraft] = useState<ChatSettingsDraft>(chatSettings);
  const [knowledgeDraft, setKnowledgeDraft] = useState<KnowledgeSettingsDraft>(knowledgeSettings);
  const [integrationDraft, setIntegrationDraft] = useState<IntegrationSettingsDraft>(integrationSettings);
  const [activeIntegrationTab, setActiveIntegrationTab] = useState<IntegrationTabId>("llm");
  const [collapsedIntegrationGroups, setCollapsedIntegrationGroups] = useState<Record<string, boolean>>({});
  const [integrationKeyTests, setIntegrationKeyTests] = useState<Record<string, IntegrationKeyTestState>>({});
  const [integrationBatchTesting, setIntegrationBatchTesting] = useState(false);
  const [integrationDisplayMode, setIntegrationDisplayMode] = useState<"inline" | "popup">("inline");
  const [symbolProfile, setSymbolProfile] = useState<SymbolProfile>("technisch");
  const [workspaceDisplayPrefsLoaded, setWorkspaceDisplayPrefsLoaded] = useState(false);
  const [integrationGroupPopup, setIntegrationGroupPopup] = useState<{
    tabId: IntegrationTabId;
    groupId: string;
  } | null>(null);
  const [integrationBatchResults, setIntegrationBatchResults] = useState<
    Partial<Record<(typeof testableIntegrationKeyOrder)[number], IntegrationBatchResult>>
  >(integrationTestResults);
  const [logsDraft, setLogsDraft] = useState<LogsSettingsDraft>(logsSettings);
  const [trainingDraft, setTrainingDraft] = useState<TrainingSettingsDraft>(trainingSettings);
  const [newTrainingProjectName, setNewTrainingProjectName] = useState("");
  const [newDatasetName, setNewDatasetName] = useState("");
  const [newDatasetProjectId, setNewDatasetProjectId] = useState<string>("");
  const [existingDatasetSourceFile, setExistingDatasetSourceFile] = useState("");
  const [existingTrainingFile, setExistingTrainingFile] = useState("");
  const [existingValidationFile, setExistingValidationFile] = useState("");
  const [existingTestFile, setExistingTestFile] = useState("");
  const [existingManifestFile, setExistingManifestFile] = useState("");
  const [uploadDatasetSourceFile, setUploadDatasetSourceFile] = useState<File | null>(null);
  const [uploadTrainingFile, setUploadTrainingFile] = useState<File | null>(null);
  const [uploadValidationFile, setUploadValidationFile] = useState<File | null>(null);
  const [uploadTestFile, setUploadTestFile] = useState<File | null>(null);
  const [uploadManifestFile, setUploadManifestFile] = useState<File | null>(null);
  const [uploadBundleFile, setUploadBundleFile] = useState<File | null>(null);
  const [datasetSourceUrl, setDatasetSourceUrl] = useState("");
  const [datasetValidationUrl, setDatasetValidationUrl] = useState("");
  const [datasetTestUrl, setDatasetTestUrl] = useState("");
  const [trainingWorkspaceTab, setTrainingWorkspaceTab] = useState<"overview" | "import" | "datasets" | "jobs">("overview");
  const [showTrainingAdvanced, setShowTrainingAdvanced] = useState(false);
  const [showRawTrainingFiles, setShowRawTrainingFiles] = useState(false);
  const [datasetViewMode, setDatasetViewMode] = useState<"active" | "archived">("active");
  const [jobViewMode, setJobViewMode] = useState<"active" | "archived">("active");
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
  const [newProjectParentId, setNewProjectParentId] = useState<string>("");
  const [newProjectScopeKind, setNewProjectScopeKind] = useState<"tenant" | "user" | "area" | "project">("project");
  const [newProjectAreaKey, setNewProjectAreaKey] = useState("");
  const [newProjectTenantKey, setNewProjectTenantKey] = useState("");
  const [projectActionPending, setProjectActionPending] = useState(false);
  const [projectDetailPopupId, setProjectDetailPopupId] = useState<number | null>(null);
  const [projectRenameDraft, setProjectRenameDraft] = useState<Record<number, string>>({});
  const [projectParentDraft, setProjectParentDraft] = useState<Record<number, string>>({});
  const [projectScopeDraft, setProjectScopeDraft] = useState<Record<number, "tenant" | "user" | "area" | "project">>({});
  const [projectAreaDraft, setProjectAreaDraft] = useState<Record<number, string>>({});
  const [projectTenantDraft, setProjectTenantDraft] = useState<Record<number, string>>({});
  const [projectOwnerDraft, setProjectOwnerDraft] = useState<Record<number, string>>({});
  const [sourceUploadFile, setSourceUploadFile] = useState<File | null>(null);
  const [sourceUploadPending, setSourceUploadPending] = useState(false);
  const [sourceDetailPopupId, setSourceDetailPopupId] = useState<number | null>(null);
  const [sourceProjectDraft, setSourceProjectDraft] = useState<Record<number, string>>({});
  const [appointmentDetailPopupId, setAppointmentDetailPopupId] = useState<number | null>(null);
  const [modelSearch, setModelSearch] = useState("");
  const [modelFamilyFilter, setModelFamilyFilter] = useState("all");
  const [filterTools, setFilterTools] = useState(false);
  const [filterThinking, setFilterThinking] = useState(false);
  const [filterVision, setFilterVision] = useState(false);
  const [filterAudio, setFilterAudio] = useState(false);
  const [filterSpeech, setFilterSpeech] = useState(false);
  const [filterOcr, setFilterOcr] = useState(false);
  const [collapsedModelGroups, setCollapsedModelGroups] = useState<Record<string, boolean>>({});
  const [modelUiPrefsLoaded, setModelUiPrefsLoaded] = useState(false);

  const getPluginFieldValue = (
    pluginId: string,
    key: string,
    fieldType: PluginSettingField["type"],
    fallback: unknown,
  ): string | number | boolean => {
    const value = pluginSettingsDrafts[pluginId]?.[key] ?? fallback;
    if (fieldType === "boolean") {
      return value === true;
    }
    if (fieldType === "number") {
      if (typeof value === "number" && Number.isFinite(value)) {
        return value;
      }
      const parsed = Number(value ?? "");
      return Number.isFinite(parsed) ? parsed : 0;
    }
    return typeof value === "string" ? value : String(value ?? "");
  };

  const isPluginFieldVisible = (
    pluginId: string,
    field: PluginSettingField,
    fields: PluginSettingField[],
  ): boolean => {
    const rule = field.visibleWhen;
    if (!rule) {
      return true;
    }

    const dependency = fields.find((entry) => entry.key === rule.field);
    if (!dependency) {
      return true;
    }

    const dependencyFallback =
      dependency.default ?? (dependency.type === "boolean" ? false : dependency.type === "number" ? 0 : "");
    const dependencyValue = getPluginFieldValue(pluginId, dependency.key, dependency.type, dependencyFallback);

    if (typeof rule.truthy === "boolean") {
      const normalizedTruthy = dependencyValue === true || (typeof dependencyValue === "string" && dependencyValue.trim().length > 0);
      return rule.truthy ? normalizedTruthy : !normalizedTruthy;
    }

    if (Object.prototype.hasOwnProperty.call(rule, "equals")) {
      return dependencyValue === rule.equals;
    }

    if (Array.isArray(rule.in) && rule.in.length > 0) {
      return rule.in.some((candidate) => candidate === dependencyValue);
    }

    return true;
  };

  const getPluginFieldDependencyHint = (
    field: PluginSettingField,
    fields: PluginSettingField[],
  ): string | null => {
    const rule = field.visibleWhen;
    if (!rule) {
      return null;
    }

    const dependency = fields.find((entry) => entry.key === rule.field);
    const dependencyLabel = dependency?.label ?? rule.field;

    if (typeof rule.truthy === "boolean") {
      return rule.truthy
        ? `abhaengig von ${dependencyLabel} (aktiv oder befuellt)`
        : `abhaengig von ${dependencyLabel} (inaktiv oder leer)`;
    }

    if (Object.prototype.hasOwnProperty.call(rule, "equals")) {
      return `abhaengig von ${dependencyLabel} = ${String(rule.equals)}`;
    }

    if (Array.isArray(rule.in) && rule.in.length > 0) {
      return `abhaengig von ${dependencyLabel} in [${rule.in.map((entry) => String(entry)).join(", ")}]`;
    }

    return `abhaengig von ${dependencyLabel}`;
  };

  const buildBusinessLetterNumberingPreview = (pluginId: string, fields: PluginSettingField[]) => {
    const relevantKeys = new Set(fields.map((field) => field.key));
    const now = new Date();
    const year = now.getFullYear();
    const month = `${now.getMonth() + 1}`.padStart(2, "0");
    const day = `${now.getDate()}`.padStart(2, "0");
    const scopes = [
      { key: "document", label: "Allgemein" },
      { key: "angebot", label: "Angebot" },
      { key: "auftragsbestaetigung", label: "Auftragsbestaetigung" },
      { key: "lieferschein", label: "Lieferschein" },
      { key: "rechnung", label: "Rechnung" },
      { key: "abschlagsrechnung", label: "Abschlagsrechnung" },
      { key: "schlussrechnung", label: "Schlussrechnung" },
      { key: "gutschrift", label: "Gutschrift" },
      { key: "stornorechnung", label: "Stornorechnung" },
      { key: "mahnung", label: "Mahnung" },
    ];

    const readValue = (scope: string, suffix: string, fallback: string | number | boolean) => {
      const key = scope === "document" ? `document_number_${suffix}` : `${scope}_document_number_${suffix}`;
      if (!relevantKeys.has(key)) {
        return fallback;
      }
      const field = fields.find((entry) => entry.key === key);
      const fieldFallback = field?.default ?? fallback;
      return getPluginFieldValue(pluginId, key, field?.type ?? "string", fieldFallback);
    };

    return scopes.map((scope) => {
      const prefix = String(readValue(scope.key, "prefix", scope.key === "document" ? "DOC" : scope.label.slice(0, 3).toUpperCase())).trim() || "DOC";
      const pattern = String(readValue(scope.key, "pattern", "{prefix}-{year}-{sequence_text}")).trim() || "{prefix}-{year}-{sequence_text}";
      const width = Number(readValue(scope.key, "width", 5)) || 5;
      const startValue = Number(readValue(scope.key, "start_value", 1)) || 1;
      const nextValue = Math.max(1, startValue);
      const sequenceText = `${nextValue}`.padStart(Math.max(1, width), "0");
      let preview = `${prefix}-${year}-${sequenceText}`;
      try {
        preview = pattern
          .split("{prefix}").join(prefix)
          .split("{year}").join(`${year}`)
          .split("{month}").join(month)
          .split("{day}").join(day)
          .split("{sequence}").join(`${nextValue}`)
          .split("{sequence_text}").join(sequenceText);
      } catch {
        preview = `${prefix}-${year}-${sequenceText}`;
      }
      return {
        scope: scope.label,
        preview,
        startValue: nextValue,
      };
    });
  };

  const configurablePluginDescriptors = pluginDescriptors.filter((plugin) => (plugin.settings_fields ?? []).length > 0);
  const pluginCategoryGroups = Array.from(
    configurablePluginDescriptors.reduce<Map<string, PluginCatalogEntry[]>>((groups, plugin) => {
      const category = plugin.category?.trim() || "Weitere Plugins";
      const bucket = groups.get(category);
      if (bucket != null) {
        bucket.push(plugin);
      } else {
        groups.set(category, [plugin]);
      }
      return groups;
    }, new Map<string, PluginCatalogEntry[]>()),
  )
    .map(([category, plugins]) => ({
      category,
      plugins: [...plugins].sort((left, right) => {
        const leftName = left.name || left.id;
        const rightName = right.name || right.id;
        return leftName.localeCompare(rightName, "de");
      }),
    }))
    .sort((left, right) => left.category.localeCompare(right.category, "de"));

  const [pluginCategoryOpenStates, setPluginCategoryOpenStates] = useState<Record<string, boolean>>({});
  const [pluginSettingsOpenStates, setPluginSettingsOpenStates] = useState<Record<string, boolean>>({});
  const [pluginFieldGroupOpenStates, setPluginFieldGroupOpenStates] = useState<Record<string, boolean>>({});
  const [pluginUiPrefsLoaded, setPluginUiPrefsLoaded] = useState(false);
  const [pluginSoloSelectedId, setPluginSoloSelectedId] = useState<string>("business_letter");
  const [pluginSoloInputJson, setPluginSoloInputJson] = useState<string>(() =>
    JSON.stringify(defaultBusinessLetterSoloInput, null, 2),
  );
  const [pluginSoloSettingsJson, setPluginSoloSettingsJson] = useState<string>("{}");
  const [pluginSoloResultJson, setPluginSoloResultJson] = useState<string>("");
  const [pluginSoloResultData, setPluginSoloResultData] = useState<PluginExecuteResponse | null>(null);
  const [pluginSoloError, setPluginSoloError] = useState<string | null>(null);
  const [pluginSoloPending, setPluginSoloPending] = useState(false);
  const [pluginPopupOpen, setPluginPopupOpen] = useState(false);
  const [pluginPopupTab, setPluginPopupTab] = useState<"frontend" | "settings" | "manual">("settings");
  const [settingsPluginCategoryPopup, setSettingsPluginCategoryPopup] = useState<string | null>(null);
  const [settingsPluginGroupPopup, setSettingsPluginGroupPopup] = useState<{
    pluginId: string;
    groupName: string;
  } | null>(null);

  const registeredDatasetFiles = new Set(
    trainingDatasets.flatMap((dataset) => {
      const values: string[] = [];
      const files = dataset.metadata.files;
      if (typeof files === "object" && files !== null) {
        for (const path of Object.values(files as Record<string, unknown>)) {
          if (typeof path === "string" && path.length > 0) {
            values.push(path);
          }
        }
      }
      const sourcePath = typeof dataset.metadata.source_path === "string" ? dataset.metadata.source_path : "";
      const validationPath = typeof dataset.metadata.validation_source_path === "string" ? dataset.metadata.validation_source_path : "";
      const testPath = typeof dataset.metadata.test_source_path === "string" ? dataset.metadata.test_source_path : "";
      return values.concat([sourcePath, validationPath, testPath]).filter((item) => item.length > 0);
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
    setPluginUiPrefsLoaded(false);
    setPluginCategoryOpenStates({});
    setPluginSettingsOpenStates({});
    setPluginFieldGroupOpenStates({});

    const storageKey = buildPluginUiPrefsStorageKey(currentUser.id);
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (!raw) {
        setPluginUiPrefsLoaded(true);
        return;
      }

      const parsed = JSON.parse(raw) as Record<string, unknown>;
      if (parsed.pluginCategoryOpenStates && typeof parsed.pluginCategoryOpenStates === "object") {
        const nextCategoryStates: Record<string, boolean> = {};
        for (const [key, value] of Object.entries(parsed.pluginCategoryOpenStates as Record<string, unknown>)) {
          if (typeof value === "boolean") {
            nextCategoryStates[key] = value;
          }
        }
        setPluginCategoryOpenStates(nextCategoryStates);
      }
      if (parsed.pluginSettingsOpenStates && typeof parsed.pluginSettingsOpenStates === "object") {
        const nextPluginStates: Record<string, boolean> = {};
        for (const [key, value] of Object.entries(parsed.pluginSettingsOpenStates as Record<string, unknown>)) {
          if (typeof value === "boolean") {
            nextPluginStates[key] = value;
          }
        }
        setPluginSettingsOpenStates(nextPluginStates);
      }
      if (parsed.pluginFieldGroupOpenStates && typeof parsed.pluginFieldGroupOpenStates === "object") {
        const nextGroupStates: Record<string, boolean> = {};
        for (const [key, value] of Object.entries(parsed.pluginFieldGroupOpenStates as Record<string, unknown>)) {
          if (typeof value === "boolean") {
            nextGroupStates[key] = value;
          }
        }
        setPluginFieldGroupOpenStates(nextGroupStates);
      }
    } catch {
      window.localStorage.removeItem(storageKey);
    } finally {
      setPluginUiPrefsLoaded(true);
    }
  }, [currentUser.id]);

  useEffect(() => {
    if (!pluginUiPrefsLoaded) {
      return;
    }

    const storageKey = buildPluginUiPrefsStorageKey(currentUser.id);
    const payload = {
      pluginCategoryOpenStates,
      pluginSettingsOpenStates,
      pluginFieldGroupOpenStates,
    };
    window.localStorage.setItem(storageKey, JSON.stringify(payload));
  }, [currentUser.id, pluginCategoryOpenStates, pluginFieldGroupOpenStates, pluginSettingsOpenStates, pluginUiPrefsLoaded]);

  useEffect(() => {
    setIntegrationDraft(integrationSettings);
    setIntegrationKeyTests({});
  }, [integrationSettings]);

  useEffect(() => {
    setWorkspaceDisplayPrefsLoaded(false);
    const storageKey = buildWorkspaceDisplayPrefsStorageKey(currentUser.id);
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (!raw) {
        setWorkspaceDisplayPrefsLoaded(true);
        return;
      }
      const parsed = JSON.parse(raw) as Record<string, unknown>;
      const parsedSymbolProfile = parsed.symbolProfile;
      if (parsedSymbolProfile === "technisch" || parsedSymbolProfile === "minimal" || parsedSymbolProfile === "business") {
        setSymbolProfile(parsedSymbolProfile);
      }
      const parsedIntegrationDisplayMode = parsed.integrationDisplayMode;
      if (parsedIntegrationDisplayMode === "inline" || parsedIntegrationDisplayMode === "popup") {
        setIntegrationDisplayMode(parsedIntegrationDisplayMode);
      }
    } catch {
      window.localStorage.removeItem(storageKey);
    } finally {
      setWorkspaceDisplayPrefsLoaded(true);
    }
  }, [currentUser.id]);

  useEffect(() => {
    if (!workspaceDisplayPrefsLoaded) {
      return;
    }
    const storageKey = buildWorkspaceDisplayPrefsStorageKey(currentUser.id);
    window.localStorage.setItem(
      storageKey,
      JSON.stringify({
        symbolProfile,
        integrationDisplayMode,
      }),
    );
  }, [currentUser.id, symbolProfile, integrationDisplayMode, workspaceDisplayPrefsLoaded]);

  useEffect(() => {
    setIntegrationBatchResults(integrationTestResults);
  }, [integrationTestResults]);

  useEffect(() => {
    if (pluginDescriptors.length === 0) {
      return;
    }
    if (pluginDescriptors.some((plugin) => plugin.id === pluginSoloSelectedId)) {
      return;
    }
    const preferred = pluginDescriptors.find((plugin) => plugin.id === "business_letter")?.id ?? pluginDescriptors[0]?.id ?? "";
    if (preferred) {
      setPluginSoloSelectedId(preferred);
      setPluginSoloInputJson(JSON.stringify(buildDefaultPluginSoloInput(preferred), null, 2));
    }
  }, [pluginDescriptors, pluginSoloSelectedId]);

  const handleRunPluginSolo = async () => {
    if (!onExecutePlugin) {
      setPluginSoloError("Plugin-Ausfuehrung ist in diesem Kontext nicht verfuegbar.");
      return;
    }
    const pluginId = pluginSoloSelectedId.trim();
    if (!pluginId) {
      setPluginSoloError("Bitte ein Plugin auswaehlen.");
      return;
    }

    let parsedInput: Record<string, unknown>;
    let parsedSettings: Record<string, unknown>;
    try {
      const payload = pluginSoloInputJson.trim() ? JSON.parse(pluginSoloInputJson) : {};
      if (typeof payload !== "object" || payload == null || Array.isArray(payload)) {
        throw new Error("Plugin-Input muss ein JSON-Objekt sein.");
      }
      parsedInput = payload as Record<string, unknown>;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Ungueltiges Input-JSON.";
      setPluginSoloError(`Input-JSON ungueltig: ${message}`);
      return;
    }

    try {
      const payload = pluginSoloSettingsJson.trim() ? JSON.parse(pluginSoloSettingsJson) : {};
      if (typeof payload !== "object" || payload == null || Array.isArray(payload)) {
        throw new Error("Plugin-Settings muessen ein JSON-Objekt sein.");
      }
      parsedSettings = payload as Record<string, unknown>;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Ungueltiges Settings-JSON.";
      setPluginSoloError(`Settings-JSON ungueltig: ${message}`);
      return;
    }

    setPluginSoloPending(true);
    setPluginSoloError(null);
    try {
      const response = await onExecutePlugin({
        pluginId,
        pluginInput: parsedInput,
        pluginSettings: parsedSettings,
        userId: currentUser.id,
      });
      setPluginSoloResultData(response);
      setPluginSoloResultJson(JSON.stringify(response, null, 2));
    } catch (error) {
      setPluginSoloError(error instanceof Error ? error.message : "Plugin-Ausfuehrung fehlgeschlagen.");
      setPluginSoloResultData(null);
      setPluginSoloResultJson("");
    } finally {
      setPluginSoloPending(false);
    }
  };

  const openPluginPopupForTab = (pluginId: string, tab: "frontend" | "settings" | "manual") => {
    setPluginSoloSelectedId(pluginId);
    setPluginSoloInputJson(JSON.stringify(buildDefaultPluginSoloInput(pluginId), null, 2));
    setPluginSoloResultJson("");
    setPluginSoloResultData(null);
    setPluginSoloError(null);
    setPluginPopupTab(tab);
    setPluginPopupOpen(true);
  };

  const applyPluginFrontendAction = (pluginId: string, action: PluginFrontendAction) => {
    setPluginSoloSelectedId(pluginId);
    if (action.pluginInput) {
      setPluginSoloInputJson(JSON.stringify(action.pluginInput, null, 2));
    }
    if (action.pluginSettings) {
      setPluginSoloSettingsJson(JSON.stringify(action.pluginSettings, null, 2));
    }
    setPluginSoloResultJson("");
    setPluginSoloResultData(null);
    setPluginSoloError(null);
    setPluginPopupTab(action.openTab ?? "manual");
  };

  const selectedPluginDescriptor = pluginDescriptors.find((plugin) => plugin.id === pluginSoloSelectedId) ?? null;
  const selectedPluginFrontend = selectedPluginDescriptor?.pluginFrontend;
  const selectedPluginActions = extractPluginActions(selectedPluginDescriptor);
  const selectedPluginFields = selectedPluginDescriptor?.settings_fields ?? [];
  const selectedPluginGroupedFields = selectedPluginFields.reduce<Record<string, PluginSettingField[]>>((acc, field) => {
    const groupName = field.group?.trim() || "Allgemein";
    if (!acc[groupName]) {
      acc[groupName] = [];
    }
    acc[groupName].push(field);
    return acc;
  }, {});
  const settingsPopupPluginDescriptor = settingsPluginGroupPopup
    ? pluginDescriptors.find((plugin) => plugin.id === settingsPluginGroupPopup.pluginId) ?? null
    : null;
  const settingsPopupPluginFields = settingsPopupPluginDescriptor?.settings_fields ?? [];
  const settingsPopupPluginGroupNames = settingsPopupPluginDescriptor
    ? Array.from(new Set(settingsPopupPluginFields.map((field) => field.group?.trim() || "Allgemein")))
    : [];
  const settingsPopupGroupFields = settingsPluginGroupPopup && settingsPopupPluginDescriptor
    ? settingsPopupPluginFields.filter(
        (field) => (field.group?.trim() || "Allgemein") === settingsPluginGroupPopup.groupName,
      )
    : [];
  const settingsPopupCategoryGroup = settingsPluginCategoryPopup
    ? pluginCategoryGroups.find((group) => group.category === settingsPluginCategoryPopup) ?? null
    : null;
  const activeSettingsGroupDescription = settingsGroups.find(([group]) => group === activeSettingsGroup)?.[1] ?? "";
  const isSettingsModalOpen = settingsModalGroup != null;
  const settingsGroupNames = settingsGroups.map(([group]) => group);
  const activeSettingsGroupIndex = settingsGroupNames.indexOf(activeSettingsGroup);
  const settingsPopupPluginIndex = settingsPopupPluginDescriptor
    ? configurablePluginDescriptors.findIndex((plugin) => plugin.id === settingsPopupPluginDescriptor.id)
    : -1;
  const settingsPopupGroupIndex = settingsPluginGroupPopup
    ? settingsPopupPluginGroupNames.indexOf(settingsPluginGroupPopup.groupName)
    : -1;

  const openSettingsGroup = (group: (typeof settingsGroups)[number][0]) => {
    setActiveSettingsGroup(group);
    setSettingsModalGroup(group);
  };

  const moveSettingsGroup = (direction: -1 | 1) => {
    if (activeSettingsGroupIndex < 0) {
      return;
    }
    const nextIndex = (activeSettingsGroupIndex + direction + settingsGroupNames.length) % settingsGroupNames.length;
    openSettingsGroup(settingsGroupNames[nextIndex]);
  };

  const openSettingsPluginSubgroup = (pluginId: string, groupName: string) => {
    setPluginSoloSelectedId(pluginId);
    setSettingsPluginGroupPopup({ pluginId, groupName });
  };

  const moveSettingsPopupPlugin = (direction: -1 | 1) => {
    if (settingsPopupPluginIndex < 0 || configurablePluginDescriptors.length === 0) {
      return;
    }
    const nextIndex = (settingsPopupPluginIndex + direction + configurablePluginDescriptors.length) % configurablePluginDescriptors.length;
    const nextPlugin = configurablePluginDescriptors[nextIndex];
    const nextGroupName = nextPlugin.settings_fields?.[0]?.group?.trim() || "Allgemein";
    openSettingsPluginSubgroup(nextPlugin.id, nextGroupName);
  };

  const moveSettingsPopupGroup = (direction: -1 | 1) => {
    if (settingsPopupGroupIndex < 0 || settingsPopupPluginGroupNames.length === 0 || !settingsPopupPluginDescriptor) {
      return;
    }
    const nextIndex = (settingsPopupGroupIndex + direction + settingsPopupPluginGroupNames.length) % settingsPopupPluginGroupNames.length;
    openSettingsPluginSubgroup(settingsPopupPluginDescriptor.id, settingsPopupPluginGroupNames[nextIndex]);
  };

  const integrationPopupGroup = integrationGroupPopup
    ? (integrationGroupsByTab[integrationGroupPopup.tabId] ?? []).find((group) => group.id === integrationGroupPopup.groupId) ?? null
    : null;

  const renderIntegrationGroupFields = (group: IntegrationGroupDef) => (
    <div className="model-profile-grid integration-profile-grid">
      {group.fields.map((field) => {
        const fieldKey = String(field.key);
        const isTestableKey = testableIntegrationKeys.has(fieldKey);
        const keyTestState = integrationKeyTests[fieldKey] ?? { status: "idle", message: "" };
        const kind = field.kind ?? "password";
        if (kind === "checkbox") {
          return (
            <label key={String(field.key)} className="model-profile-field model-profile-field--toggle">
              <span>{field.label}</span>
              <input
                type="checkbox"
                checked={Boolean(integrationDraft[field.key])}
                onChange={(event) => {
                  setIntegrationDraft((current) => ({
                    ...current,
                    [field.key]: event.target.checked,
                  }));
                }}
                disabled={integrationSettingsPending}
              />
              {field.hint ? <small className="integration-field-hint">{field.hint}</small> : null}
            </label>
          );
        }

        if (kind === "json") {
          return (
            <label key={String(field.key)} className="model-profile-field integration-json-field">
              <span>{field.label}</span>
              <textarea
                className="model-profile-textarea"
                value={String(integrationDraft[field.key] ?? "")}
                onChange={(event) => {
                  setIntegrationDraft((current) => ({
                    ...current,
                    [field.key]: event.target.value,
                  }));
                }}
                disabled={integrationSettingsPending}
              />
              {field.hint ? <small className="integration-field-hint">{field.hint}</small> : null}
            </label>
          );
        }

        return (
          <label
            key={fieldKey}
            className={`model-profile-field ${keyTestState.status === "error" ? "integration-field--error" : ""}`}
          >
            <span>{field.label}</span>
            <div className="integration-input-row">
              <input
                className="model-dir-input"
                type="password"
                autoComplete="off"
                spellCheck={false}
                value={String(integrationDraft[field.key] ?? "")}
                onChange={(event) => {
                  setIntegrationDraft((current) => ({
                    ...current,
                    [field.key]: event.target.value,
                  }));
                }}
                disabled={integrationSettingsPending}
              />
              {integrationProviderSignupUrls[field.key] ? (
                <a
                  className="integration-target-btn"
                  href={integrationProviderSignupUrls[field.key]}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={`Anmeldeseite fuer ${field.label} oeffnen`}
                  title={`Anmeldeseite fuer ${field.label} oeffnen`}
                >
                  ↗
                </a>
              ) : null}
              {isTestableKey ? (
                <button
                  type="button"
                  className="integration-test-btn"
                  disabled={integrationSettingsPending || keyTestState.status === "testing"}
                  onClick={() => {
                    void (async () => {
                      const startedAt = performance.now();
                      const result = await applySingleIntegrationKeyTest(fieldKey, integrationDraft);
                      if (!testableIntegrationKeyOrder.includes(fieldKey as (typeof testableIntegrationKeyOrder)[number])) {
                        return;
                      }
                      const durationMs = performance.now() - startedAt;
                      const testedAt = new Date().toISOString();
                      const next: IntegrationBatchResult = result.skipped
                        ? {
                          status: "skipped",
                          message: "Key fehlt",
                          testedAt,
                          durationMs,
                        }
                        : result.success
                          ? {
                            status: "ok",
                            message: `OK (${result.provider})`,
                            testedAt,
                            durationMs,
                          }
                          : {
                            status: "error",
                            message: result.error ?? "Provider-Test fehlgeschlagen.",
                            testedAt,
                            durationMs,
                          };

                      commitIntegrationBatchResults({
                        ...integrationBatchResults,
                        [fieldKey]: next,
                      });
                    })();
                  }}
                >
                  {keyTestState.status === "testing" ? "Teste..." : "Key testen"}
                </button>
              ) : null}
              {isTestableKey && keyTestState.status !== "idle" ? (
                <span
                  className={`integration-test-indicator integration-test-indicator--${keyTestState.status}`}
                  aria-label={keyTestState.status === "error" ? "Key-Test fehlgeschlagen" : "Key-Test erfolgreich"}
                  title={keyTestState.message}
                >
                  {keyTestState.status === "error" ? "!" : keyTestState.status === "success" ? "OK" : "..."}
                </span>
              ) : null}
            </div>
            {field.hint ? <small className="integration-field-hint">{field.hint}</small> : null}
            {isTestableKey && keyTestState.message.length > 0 ? (
              <small
                className={`integration-field-hint ${keyTestState.status === "error" ? "integration-field-hint--error" : ""}`}
              >
                {keyTestState.message}
              </small>
            ) : null}
          </label>
        );
      })}
    </div>
  );

  useEffect(() => {
    if (
      !pluginPopupOpen &&
      !isSettingsModalOpen &&
      settingsPluginCategoryPopup == null &&
      settingsPluginGroupPopup == null &&
      projectDetailPopupId == null &&
      sourceDetailPopupId == null &&
      appointmentDetailPopupId == null
    ) {
      return;
    }

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") {
        return;
      }
      if (settingsPluginGroupPopup != null) {
        setSettingsPluginGroupPopup(null);
        return;
      }
      if (settingsPluginCategoryPopup != null) {
        setSettingsPluginCategoryPopup(null);
        return;
      }
      if (pluginPopupOpen) {
        setPluginPopupOpen(false);
        return;
      }
      if (projectDetailPopupId != null) {
        setProjectDetailPopupId(null);
        return;
      }
      if (sourceDetailPopupId != null) {
        setSourceDetailPopupId(null);
        return;
      }
      if (appointmentDetailPopupId != null) {
        setAppointmentDetailPopupId(null);
        return;
      }
      if (isSettingsModalOpen) {
        setSettingsModalGroup(null);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [
    appointmentDetailPopupId,
    isSettingsModalOpen,
    pluginPopupOpen,
    projectDetailPopupId,
    settingsPluginCategoryPopup,
    settingsPluginGroupPopup,
    sourceDetailPopupId,
  ]);
  const selectedProjectDetail = projectDetailPopupId != null
    ? projects.find((project) => project.id === projectDetailPopupId) ?? null
    : null;
  const selectedSourceDetail = sourceDetailPopupId != null
    ? sources.find((source) => source.id === sourceDetailPopupId) ?? null
    : null;
  const selectedAppointmentDetail = appointmentDetailPopupId != null
    ? appointments.find((appointment) => appointment.id === appointmentDetailPopupId) ?? null
    : null;

  const buildSelectedPluginSettingsOverride = () => {
    if (!selectedPluginDescriptor) {
      return {} as Record<string, unknown>;
    }
    const fields = selectedPluginDescriptor.settings_fields ?? [];
    const payload: Record<string, unknown> = {};
    for (const field of fields) {
      const fallback =
        field.default ?? (field.type === "boolean" ? false : field.type === "number" ? 0 : "");
      payload[field.key] = getPluginFieldValue(selectedPluginDescriptor.id, field.key, field.type, fallback);
    }
    return payload;
  };

  const pluginSoloBusinessLetterSummary = (() => {
    if (!pluginSoloResultData || pluginSoloResultData.plugin_id !== "business_letter") {
      return null;
    }
    const response = pluginSoloResultData.plugin_response;
    const responseMap = typeof response === "object" && response != null ? (response as Record<string, unknown>) : {};
    const template = typeof responseMap.template === "object" && responseMap.template != null
      ? (responseMap.template as Record<string, unknown>)
      : {};
    const layout = typeof template.layout === "object" && template.layout != null
      ? (template.layout as Record<string, unknown>)
      : {};
    const artifacts = Array.isArray(responseMap.artifacts) ? responseMap.artifacts as Array<Record<string, unknown>> : [];
    const pdfArtifact = artifacts.find((item) => String(item.kind || "") === "pdf") ?? null;
    const delivery = typeof responseMap.delivery === "object" && responseMap.delivery != null
      ? (responseMap.delivery as Record<string, unknown>)
      : {};
    return {
      documentNumber: String((responseMap.reference as Record<string, unknown> | undefined)?.document_number || "-") || "-",
      status: String(responseMap.status || "-") || "-",
      pdfFileName: String(pdfArtifact?.file_name || "-") || "-",
      layoutTemplate: String(layout.layout_template || "-") || "-",
      logoPresent: layout.logo_present === true ? "ja" : "nein",
      logoPosition: String(layout.logo_position || "-") || "-",
      deliveryBlocked: delivery.blocked === true ? "ja" : "nein",
    };
  })();

  const pluginSoloCalculatorSummary = (() => {
    if (!pluginSoloResultData || pluginSoloResultData.plugin_id !== "calculator") {
      return null;
    }
    const response = pluginSoloResultData.plugin_response;
    const responseMap = typeof response === "object" && response != null ? (response as Record<string, unknown>) : {};
    const expression = typeof responseMap.expression === "string" ? responseMap.expression : "-";
    const result = responseMap.result;
    const angleMode = typeof responseMap.angle_mode === "string" ? responseMap.angle_mode : "rad";
    const precision = typeof responseMap.precision === "number" ? responseMap.precision : "-";
    const action = typeof responseMap.action === "string" ? responseMap.action : "evaluate";
    return {
      expression,
      result:
        typeof result === "number" && Number.isFinite(result)
          ? new Intl.NumberFormat("de-DE", { maximumFractionDigits: 12 }).format(result)
          : "-",
      angleMode,
      precision: String(precision),
      action,
    };
  })();

  const commitIntegrationBatchResults = (
    next: Partial<Record<(typeof testableIntegrationKeyOrder)[number], IntegrationBatchResult>>,
  ) => {
    setIntegrationBatchResults(next);
    void onSaveIntegrationTestResults(next);
  };

  const applySingleIntegrationKeyTest = async (
    key: string,
    profile: IntegrationSettingsDraft,
  ): Promise<IntegrationKeyTestResult> => {
    const value = String((profile as Record<string, unknown>)[key] ?? "").trim();
    if (!value) {
      setIntegrationKeyTests((current) => ({
        ...current,
        [key]: {
          status: "idle",
          message: "",
        },
      }));
      return {
        success: false,
        provider: "none",
        error: null,
        providerErrors: [],
        skipped: true,
      };
    }

    setIntegrationKeyTests((current) => ({
      ...current,
      [key]: {
        status: "testing",
        message: "Provider-Test laeuft...",
      },
    }));

    try {
      const result = await runIntegrationKeyTest(key, profile);
      if (result.skipped) {
        setIntegrationKeyTests((current) => ({
          ...current,
          [key]: {
            status: "idle",
            message: "",
          },
        }));
        return result;
      }

      const providerErrors = result.providerErrors.length > 0
        ? ` (${result.providerErrors.join(" | ")})`
        : "";
      setIntegrationKeyTests((current) => ({
        ...current,
        [key]: result.success
          ? {
              status: "success",
              message: `OK: ${result.provider}${providerErrors}`,
            }
          : {
              status: "error",
              message: `${result.error ?? "Provider-Test fehlgeschlagen."}${providerErrors}`,
            },
      }));
      return result;
    } catch (error) {
      const message = error instanceof Error && error.message.trim().length > 0
        ? error.message
        : "Provider-Test fehlgeschlagen.";
      setIntegrationKeyTests((current) => ({
        ...current,
        [key]: {
          status: "error",
          message,
        },
      }));
      return {
        success: false,
        provider: "none",
        error: message,
        providerErrors: [],
        skipped: false,
      };
    }
  };

  const runAllIntegrationKeyTests = async () => {
    setIntegrationBatchTesting(true);
    const nextResults: Partial<Record<(typeof testableIntegrationKeyOrder)[number], IntegrationBatchResult>> = {};

    try {
      for (const key of testableIntegrationKeyOrder) {
        const startedAt = performance.now();
        const result = await applySingleIntegrationKeyTest(key, integrationDraft);
        const durationMs = performance.now() - startedAt;
        const testedAt = new Date().toISOString();

        if (result.skipped) {
          nextResults[key] = {
            status: "skipped",
            message: "Key fehlt",
            testedAt,
            durationMs,
          };
          continue;
        }

        if (result.success) {
          nextResults[key] = {
            status: "ok",
            message: `OK (${result.provider})`,
            testedAt,
            durationMs,
          };
          continue;
        }

        nextResults[key] = {
          status: "error",
          message: result.error ?? "Provider-Test fehlgeschlagen.",
          testedAt,
          durationMs,
        };
      }

      commitIntegrationBatchResults(nextResults);
    } finally {
      setIntegrationBatchTesting(false);
    }
  };

  useEffect(() => {
    const nextParentDraft: Record<number, string> = {};
    const nextScopeDraft: Record<number, "tenant" | "user" | "area" | "project"> = {};
    const nextAreaDraft: Record<number, string> = {};
    const nextTenantDraft: Record<number, string> = {};
    const nextOwnerDraft: Record<number, string> = {};

    projects.forEach((project) => {
      nextParentDraft[project.id] = typeof project.parent_project_id === "number" ? String(project.parent_project_id) : "";
      const scope = project.scope_kind;
      nextScopeDraft[project.id] = scope === "tenant" || scope === "user" || scope === "area" || scope === "project" ? scope : "project";
      nextAreaDraft[project.id] = project.area_key ?? "";
      nextTenantDraft[project.id] = project.tenant_key ?? "";
      nextOwnerDraft[project.id] = typeof project.owner_user_id === "number" ? String(project.owner_user_id) : "";
    });

    setProjectParentDraft(nextParentDraft);
    setProjectScopeDraft(nextScopeDraft);
    setProjectAreaDraft(nextAreaDraft);
    setProjectTenantDraft(nextTenantDraft);
    setProjectOwnerDraft(nextOwnerDraft);
  }, [projects]);

  useEffect(() => {
    const nextSourceProjectDraft: Record<number, string> = {};
    sources.forEach((row) => {
      nextSourceProjectDraft[row.id] = typeof row.project_id === "number" ? String(row.project_id) : "";
    });
    setSourceProjectDraft(nextSourceProjectDraft);
  }, [sources]);

  const runIntegrationKeyTest = async (
    key: string,
    profile: IntegrationSettingsDraft,
  ): Promise<IntegrationKeyTestResult> => {
    const value = String((profile as Record<string, unknown>)[key] ?? "").trim();
    if (!value) {
      return {
        success: false,
        provider: "none",
        error: null,
        providerErrors: [],
        skipped: true,
      };
    }

    const weatherProviderByKey: Record<string, "openweather" | "weatherapi" | "tomorrowio"> = {
      openweatherApiKey: "openweather",
      weatherapiApiKey: "weatherapi",
      tomorrowioApiKey: "tomorrowio",
    };
    const searchProviderByKey: Record<string, "exa" | "brave" | "bing"> = {
      exaApiKey: "exa",
      braveSearchApiKey: "brave",
      bingSearchApiKey: "bing",
    };

    const token = getAuthToken();
    const headers = new Headers({ "Content-Type": "application/json" });
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    const weatherProvider = weatherProviderByKey[key];
    if (weatherProvider) {
      const response = await fetch("/api/plugins/execute", {
        method: "POST",
        headers,
        body: JSON.stringify({
          plugin_id: "weather",
          plugin_input: {
            city: "Berlin",
            country: "DE",
            provider: weatherProvider,
            forecast: false,
            lang: "de",
          },
          plugin_settings: {
            integrations: {
              openweather_api_key: key === "openweatherApiKey" ? value : "",
              weatherapi_api_key: key === "weatherapiApiKey" ? value : "",
              tomorrowio_api_key: key === "tomorrowioApiKey" ? value : "",
            },
          },
          user_id: currentUser.id,
        }),
      });

      if (!response.ok) {
        throw new Error(`Provider-Test fehlgeschlagen (${response.status}).`);
      }

      const payload = (await response.json()) as {
        plugin_response?: Record<string, unknown>;
      };
      const pluginResponse = payload.plugin_response ?? {};
      const providerErrors = Array.isArray(pluginResponse.provider_errors)
        ? pluginResponse.provider_errors.filter((item): item is string => typeof item === "string")
        : [];
      const success = pluginResponse.success === true;

      return {
        success,
        provider: typeof pluginResponse.provider === "string" ? pluginResponse.provider : weatherProvider,
        error: success
          ? null
          : typeof pluginResponse.error === "string"
            ? pluginResponse.error
            : providerErrors[0] ?? "Provider-Test fehlgeschlagen.",
        providerErrors,
        skipped: false,
      };
    }

    const searchProvider = searchProviderByKey[key];
    if (searchProvider) {
      const response = await fetch("/api/plugins/execute", {
        method: "POST",
        headers,
        body: JSON.stringify({
          plugin_id: "websearch",
          plugin_input: {
            query: "Wetter Berlin heute",
            count: 3,
            provider: searchProvider,
          },
          plugin_settings: {
            integrations: {
              exa_api_key: key === "exaApiKey" ? value : "",
              brave_search_api_key: key === "braveSearchApiKey" ? value : "",
              bing_search_api_key: key === "bingSearchApiKey" ? value : "",
            },
          },
          user_id: currentUser.id,
        }),
      });

      if (!response.ok) {
        throw new Error(`Provider-Test fehlgeschlagen (${response.status}).`);
      }

      const payload = (await response.json()) as {
        plugin_response?: Record<string, unknown>;
      };
      const pluginResponse = payload.plugin_response ?? {};
      const provider = typeof pluginResponse.provider === "string" ? pluginResponse.provider : "none";
      const results = Array.isArray(pluginResponse.results) ? pluginResponse.results : [];
      const providerErrors = Array.isArray(pluginResponse.provider_errors)
        ? pluginResponse.provider_errors.filter((item): item is string => typeof item === "string")
        : [];
      const success = provider !== "none" && results.length > 0;

      return {
        success,
        provider,
        error: success ? null : providerErrors[0] ?? "Provider lieferte keine Ergebnisse.",
        providerErrors,
        skipped: false,
      };
    }

    return {
      success: false,
      provider: "none",
      error: null,
      providerErrors: [],
      skipped: true,
    };
  };

  useEffect(() => {
    setCollapsedIntegrationGroups((current) => {
      const next = { ...current };
      for (const tab of integrationTabs) {
        const groups = integrationGroupsByTab[tab.id] ?? [];
        groups.forEach((group, index) => {
          const key = `${tab.id}:${group.id}`;
          if (!(key in next)) {
            next[key] = index > 0;
          }
        });
      }
      return next;
    });
  }, []);

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
  const selectedContinualModel = trainingDraft.continualModelId
    ? modelEntries.find((model) => model.id === trainingDraft.continualModelId) ?? null
    : null;
  const activeTrainingJobsCount = trainingJobs.filter((job) =>
    ["queued", "preparing", "running", "evaluating", "saving", "cancelling"].includes(job.status.toLowerCase()),
  ).length;
  const readyDatasetCount = trainingDatasets.filter((dataset) => dataset.status !== "archived").length;

  const selectedTrainerOption =
    trainerOptions.find((option) => option.id === trainingDraft.defaultTrainer.trim().toLowerCase()) ?? null;
  const selectedJobTrainerOption =
    trainerOptions.find((option) => option.id === newJobTrainerId.trim().toLowerCase()) ?? null;

  const applyTrainingPreset = (preset: TrainingSettingsDraft["trainingPreset"]) => {
    const profiles = {
      safe: {
        numTrainEpochs: "4", learningRate: "0.0001", batchSize: "1", gradientAccumulationSteps: "4",
        maxSequenceLength: "768", loraR: "16", loraAlpha: "32", loraDropout: "0.05",
        warmupRatio: "0.05", weightDecay: "0.01", evalSteps: "10",
        saveSteps: "10", loggingSteps: "1", maxSteps: "0", validationSplit: "0.1", loadIn4bit: true,
        loadBestModelAtEnd: true, metricForBestModel: "eval_loss", greaterIsBetter: false,
      },
      balanced: {
        numTrainEpochs: "4", learningRate: "0.0001", batchSize: "1", gradientAccumulationSteps: "4",
        maxSequenceLength: "768", loraR: "32", loraAlpha: "64", loraDropout: "0.05",
        warmupRatio: "0.05", weightDecay: "0.01", evalSteps: "10",
        saveSteps: "10", loggingSteps: "2", maxSteps: "0", validationSplit: "0.1", loadIn4bit: true,
        loadBestModelAtEnd: true, metricForBestModel: "eval_loss", greaterIsBetter: false,
      },
      intensive: {
        numTrainEpochs: "5", learningRate: "0.00008", batchSize: "1", gradientAccumulationSteps: "4",
        maxSequenceLength: "1024", loraR: "32", loraAlpha: "64", loraDropout: "0.05",
        warmupRatio: "0.05", weightDecay: "0.01", evalSteps: "10",
        saveSteps: "10", loggingSteps: "2", maxSteps: "0", validationSplit: "0.1", loadIn4bit: true,
        loadBestModelAtEnd: true, metricForBestModel: "eval_loss", greaterIsBetter: false,
      },
    } as const;
    setTrainingDraft((current) => ({
      ...current,
      trainingPreset: preset,
      ...(preset === "custom" ? {} : profiles[preset]),
    }));
  };

  const updateAdvancedTraining = (patch: Partial<TrainingSettingsDraft>) => {
    setTrainingDraft((current) => ({ ...current, ...patch, trainingPreset: "custom" }));
  };

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

  const ollamaCapabilityBadges = (entry: UiModelEntry) => {
    const badges: string[] = [];
    if (entry.toolCalling) {
      badges.push("Tools");
    }
    if (entry.reasoning) {
      badges.push("Thinking");
    }
    if (entry.capabilities?.supportsVision) {
      badges.push("Vision");
    }
    if (entry.structuredOutput) {
      badges.push("JSON");
    }
    return badges;
  };

  const isSpeechModel = (entry: UiModelEntry) => {
    return ["speech_to_text", "text_to_speech", "audio_text_generation", "voice_activity_detection"].includes(
      entry.taskType ?? "",
    );
  };

  const isAudioModel = (entry: UiModelEntry) => {
    return Boolean(entry.capabilities?.supportsAudio) || isSpeechModel(entry) || entry.taskType === "audio_generation";
  };

  const isOcrModel = (entry: UiModelEntry) => entry.taskType === "ocr";

  const shouldCollapseModelGroupByDefault = (groupName: string) => {
    return !["Text / Chat", "GGUF - Text / Chat", "Multimodal"].includes(groupName);
  };

  const availableModelFamilies = Array.from(
    new Set(
      modelEntries
        .map((model) => model.modelFamily?.trim().toLowerCase() ?? "")
        .filter((value) => value.length > 0),
    ),
  ).sort((left, right) => left.localeCompare(right));

  const filteredModelEntries = modelEntries.filter((model) => {
    const normalizedSearch = modelSearch.trim().toLowerCase();
    if (normalizedSearch.length > 0) {
      const haystack = [model.name, model.modelFamily ?? "", model.sourceLabel, model.taskType ?? "", model.parameterSize ?? ""]
        .join(" ")
        .toLowerCase();
      if (!haystack.includes(normalizedSearch)) {
        return false;
      }
    }

    if (modelFamilyFilter !== "all" && (model.modelFamily?.trim().toLowerCase() ?? "") !== modelFamilyFilter) {
      return false;
    }
    if (filterTools && !model.toolCalling) {
      return false;
    }
    if (filterThinking && !model.reasoning) {
      return false;
    }
    if (filterVision && !model.capabilities?.supportsVision) {
      return false;
    }
    if (filterAudio && !isAudioModel(model)) {
      return false;
    }
    if (filterSpeech && !isSpeechModel(model)) {
      return false;
    }
    if (filterOcr && !isOcrModel(model)) {
      return false;
    }
    return true;
  });

  const groupedModelEntries = filteredModelEntries.reduce<Record<string, UiModelEntry[]>>((acc, model) => {
    const group = model.group ?? "Hilfsmodelle";
    if (!acc[group]) {
      acc[group] = [];
    }
    acc[group].push(model);
    return acc;
  }, {});

  useEffect(() => {
    const allGroups = Array.from(new Set(modelEntries.map((model) => model.group ?? "Hilfsmodelle")));
    setCollapsedModelGroups((current) => {
      const next = { ...current };
      for (const groupName of allGroups) {
        if (!(groupName in next)) {
          next[groupName] = shouldCollapseModelGroupByDefault(groupName);
        }
      }
      return next;
    });
  }, [modelEntries]);

  useEffect(() => {
    const storageKey = buildModelUiPrefsStorageKey(currentUser.id);
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (!raw) {
        setModelUiPrefsLoaded(true);
        return;
      }
      const parsed = JSON.parse(raw) as Record<string, unknown>;
      if (typeof parsed.modelSearch === "string") {
        setModelSearch(parsed.modelSearch);
      }
      if (typeof parsed.modelFamilyFilter === "string") {
        setModelFamilyFilter(parsed.modelFamilyFilter);
      }
      if (typeof parsed.filterTools === "boolean") {
        setFilterTools(parsed.filterTools);
      }
      if (typeof parsed.filterThinking === "boolean") {
        setFilterThinking(parsed.filterThinking);
      }
      if (typeof parsed.filterVision === "boolean") {
        setFilterVision(parsed.filterVision);
      }
      if (typeof parsed.filterAudio === "boolean") {
        setFilterAudio(parsed.filterAudio);
      }
      if (typeof parsed.filterSpeech === "boolean") {
        setFilterSpeech(parsed.filterSpeech);
      }
      if (typeof parsed.filterOcr === "boolean") {
        setFilterOcr(parsed.filterOcr);
      }
      if (typeof parsed.activeModelSettingsTab === "string") {
        const nextTab = parsed.activeModelSettingsTab;
        if (nextTab === "overview" || nextTab === "directories" || nextTab === "prompts") {
          setActiveModelSettingsTab(nextTab);
        }
      }
      if (parsed.collapsedModelGroups && typeof parsed.collapsedModelGroups === "object") {
        const nextGroups: Record<string, boolean> = {};
        for (const [key, value] of Object.entries(parsed.collapsedModelGroups as Record<string, unknown>)) {
          if (typeof value === "boolean") {
            nextGroups[key] = value;
          }
        }
        setCollapsedModelGroups((current) => ({ ...current, ...nextGroups }));
      }
    } catch {
      window.localStorage.removeItem(storageKey);
    } finally {
      setModelUiPrefsLoaded(true);
    }
  }, [currentUser.id]);

  useEffect(() => {
    if (!modelUiPrefsLoaded) {
      return;
    }
    const storageKey = buildModelUiPrefsStorageKey(currentUser.id);
    const payload = {
      modelSearch,
      modelFamilyFilter,
      filterTools,
      filterThinking,
      filterVision,
      filterAudio,
      filterSpeech,
      filterOcr,
      activeModelSettingsTab,
      collapsedModelGroups,
    };
    window.localStorage.setItem(storageKey, JSON.stringify(payload));
  }, [
    activeModelSettingsTab,
    collapsedModelGroups,
    currentUser.id,
    filterAudio,
    filterOcr,
    filterSpeech,
    filterThinking,
    filterTools,
    filterVision,
    modelFamilyFilter,
    modelSearch,
    modelUiPrefsLoaded,
  ]);

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

  const isJobRunning = (status: string) => {
    const normalized = status.trim().toLowerCase();
    return normalized === "running" || normalized === "in_progress" || normalized === "processing";
  };

  const normalizeJobProgressPercent = (job: TrainingJobSummary) => {
    const progress = typeof job.progress === "number" && Number.isFinite(job.progress) ? job.progress : null;
    if (progress != null) {
      const normalized = progress <= 1 ? progress * 100 : progress;
      return Math.max(0, Math.min(100, normalized));
    }
    if (
      typeof job.currentStep === "number" &&
      Number.isFinite(job.currentStep) &&
      typeof job.totalSteps === "number" &&
      Number.isFinite(job.totalSteps) &&
      job.totalSteps > 0
    ) {
      return Math.max(0, Math.min(100, (job.currentStep / job.totalSteps) * 100));
    }
    return null;
  };

  const jobProgressLabel = (job: TrainingJobSummary) => {
    const percent = normalizeJobProgressPercent(job);
    const percentLabel = percent == null ? "-" : `${Math.round(percent)}%`;
    if (
      typeof job.currentStep === "number" &&
      Number.isFinite(job.currentStep) &&
      typeof job.totalSteps === "number" &&
      Number.isFinite(job.totalSteps) &&
      job.totalSteps > 0
    ) {
      return `${percentLabel} (${job.currentStep}/${job.totalSteps})`;
    }
    return percentLabel;
  };

  const jobFilesSummary = (job: TrainingJobSummary) => {
    const datasetInfo = job.result?.dataset;
    const filesFromResult =
      typeof datasetInfo === "object" && datasetInfo != null && typeof (datasetInfo as Record<string, unknown>).files === "object"
        ? ((datasetInfo as Record<string, unknown>).files as Record<string, unknown>)
        : null;

    const filesFromDatasetMetadata =
      trainingDatasets.find((dataset) => dataset.id === job.datasetId)?.metadata?.files as Record<string, unknown> | undefined;

    const effectiveFiles = filesFromResult ?? filesFromDatasetMetadata;
    if (effectiveFiles == null) {
      return "-";
    }

    const entries = Object.entries(effectiveFiles)
      .filter((entry): entry is [string, string] => typeof entry[1] === "string" && entry[1].length > 0)
      .map(([role, filePath]) => `${role}=${filePath}`);
    return entries.length > 0 ? entries.join(" | ") : "-";
  };

  const visibleDatasets = trainingDatasets.filter((dataset) =>
    datasetViewMode === "archived" ? dataset.status === "archived" : dataset.status !== "archived",
  );

  const visibleJobs = trainingJobs.filter((job) =>
    jobViewMode === "archived" ? job.status === "archived" : job.status !== "archived",
  );

  const sanitizeDatasetName = (raw: string) => {
    const cleaned = raw
      .trim()
      .replace(/\.[A-Za-z0-9]+$/u, "")
      .replace(/[_\s]+/gu, "-")
      .replace(/[^A-Za-z0-9-]+/gu, "-")
      .replace(/-+/gu, "-")
      .replace(/^-|-$/gu, "");
    return cleaned.length > 0 ? cleaned : "";
  };

  const deriveDatasetNameFromUrl = (url: string) => {
    try {
      const parsed = new URL(url);
      const parts = parsed.pathname.split("/").filter(Boolean);
      const fileName = parts.length > 0 ? parts[parts.length - 1] : "";
      return sanitizeDatasetName(fileName);
    } catch {
      return "";
    }
  };

  const resolveDatasetName = (candidates: Array<string | undefined>) => {
    const explicit = sanitizeDatasetName(newDatasetName);
    if (explicit.length > 0) {
      return explicit;
    }
    for (const candidate of candidates) {
      const normalized = sanitizeDatasetName(candidate ?? "");
      if (normalized.length > 0) {
        return normalized;
      }
    }
    return `dataset-${Date.now()}`;
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
          <select
            className="model-dir-input"
            value={newProjectParentId}
            onChange={(event) => setNewProjectParentId(event.target.value)}
            disabled={projectActionPending}
            aria-label="Uebergeordnetes Projekt"
            title="Uebergeordnetes Projekt"
          >
            <option value="">Keine Ebene darueber</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>{project.name}</option>
            ))}
          </select>
          <select
            className="model-dir-input"
            value={newProjectScopeKind}
            onChange={(event) => setNewProjectScopeKind(event.target.value as "tenant" | "user" | "area" | "project")}
            disabled={projectActionPending}
            aria-label="Scope"
            title="Scope"
          >
            <option value="tenant">Mandant</option>
            <option value="user">Benutzer</option>
            <option value="area">Bereich</option>
            <option value="project">Projekt</option>
          </select>
          <input
            className="model-dir-input"
            type="text"
            placeholder="Bereich (z.B. Fussball)"
            value={newProjectAreaKey}
            onChange={(event) => setNewProjectAreaKey(event.target.value)}
            disabled={projectActionPending}
          />
          <input
            className="model-dir-input"
            type="text"
            placeholder="Mandant (z.B. heisig)"
            value={newProjectTenantKey}
            onChange={(event) => setNewProjectTenantKey(event.target.value)}
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
              void onCreateProject(name, {
                parentProjectId: newProjectParentId.trim() ? Number(newProjectParentId) : null,
                scopeKind: newProjectScopeKind,
                areaKey: newProjectAreaKey.trim() || null,
                tenantKey: newProjectTenantKey.trim() || null,
              })
                .then(() => {
                  setNewProjectName("");
                  setNewProjectParentId("");
                  setNewProjectScopeKind("project");
                  setNewProjectAreaKey("");
                  setNewProjectTenantKey("");
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
              <span>Typ: {project.scope_kind ?? "project"} | Ebene: {project.depth ?? 0}</span>
              <span>Mandant: {project.tenant_key ?? "-"} | Bereich: {project.area_key ?? "-"}</span>
              <span>{project.chats} Chats</span>
              <span>{project.documents} Dokumente</span>
              <div className="model-settings-controls">
                <button
                  type="button"
                  className="ghost-btn"
                  disabled={projectActionPending}
                  onClick={() => setProjectDetailPopupId(project.id)}
                >
                  Details
                </button>
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
                <select
                  className="model-dir-input"
                  value={projectParentDraft[project.id] ?? ""}
                  onChange={(event) => {
                    const value = event.target.value;
                    setProjectParentDraft((current) => ({ ...current, [project.id]: value }));
                  }}
                  disabled={projectActionPending}
                  aria-label={`Parent fuer Projekt ${project.name}`}
                  title={`Parent fuer Projekt ${project.name}`}
                >
                  <option value="">Keine Ebene darueber</option>
                  {projects
                    .filter((candidate) => candidate.id !== project.id)
                    .map((candidate) => (
                      <option key={candidate.id} value={candidate.id}>{candidate.name}</option>
                    ))}
                </select>
                <select
                  className="model-dir-input"
                  value={projectScopeDraft[project.id] ?? "project"}
                  onChange={(event) => {
                    const value = event.target.value as "tenant" | "user" | "area" | "project";
                    setProjectScopeDraft((current) => ({ ...current, [project.id]: value }));
                  }}
                  disabled={projectActionPending}
                  aria-label={`Typ fuer Projekt ${project.name}`}
                  title={`Typ fuer Projekt ${project.name}`}
                >
                  <option value="tenant">Mandant</option>
                  <option value="user">Benutzer</option>
                  <option value="area">Bereich</option>
                  <option value="project">Projekt</option>
                </select>
                <input
                  className="model-dir-input"
                  type="text"
                  value={projectTenantDraft[project.id] ?? ""}
                  placeholder="Mandant"
                  onChange={(event) => {
                    const value = event.target.value;
                    setProjectTenantDraft((current) => ({ ...current, [project.id]: value }));
                  }}
                  disabled={projectActionPending}
                />
                <input
                  className="model-dir-input"
                  type="text"
                  value={projectAreaDraft[project.id] ?? ""}
                  placeholder="Bereich"
                  onChange={(event) => {
                    const value = event.target.value;
                    setProjectAreaDraft((current) => ({ ...current, [project.id]: value }));
                  }}
                  disabled={projectActionPending}
                />
                <input
                  className="model-dir-input"
                  type="number"
                  min={1}
                  value={projectOwnerDraft[project.id] ?? ""}
                  placeholder="Besitzer User-ID"
                  onChange={(event) => {
                    const value = event.target.value;
                    setProjectOwnerDraft((current) => ({ ...current, [project.id]: value }));
                  }}
                  disabled={projectActionPending}
                />
                <button
                  type="button"
                  className="ghost-btn"
                  disabled={projectActionPending}
                  onClick={() => {
                    setProjectActionPending(true);
                    const rawParent = (projectParentDraft[project.id] ?? "").trim();
                    const rawOwner = (projectOwnerDraft[project.id] ?? "").trim();
                    void onUpdateProjectHierarchy({
                      projectId: project.id,
                      parentProjectId: rawParent ? Number(rawParent) : null,
                      scopeKind: projectScopeDraft[project.id] ?? "project",
                      areaKey: (projectAreaDraft[project.id] ?? "").trim() || null,
                      tenantKey: (projectTenantDraft[project.id] ?? "").trim() || null,
                      ownerUserId: rawOwner ? Number(rawOwner) : null,
                    }).finally(() => {
                      setProjectActionPending(false);
                    });
                  }}
                >
                  Hierarchie speichern
                </button>
              </div>
            </article>
          ))}
        </div>

        {selectedProjectDetail ? (
          <div className="plugin-popup-overlay" role="dialog" aria-modal="true" aria-label="Projekt-Details" onClick={() => setProjectDetailPopupId(null)}>
            <div className="plugin-popup" onClick={(event) => event.stopPropagation()}>
              <div className="plugin-popup__header">
                <div>
                  <strong>{selectedProjectDetail.name}</strong>
                  <span>Projekt · {selectedProjectDetail.scope_kind ?? "project"} · Ebene {selectedProjectDetail.depth ?? 0}</span>
                </div>
                <div className="model-settings-card__actions">
                  <button type="button" className="ghost-btn" onClick={() => setProjectDetailPopupId(null)}>Schliessen</button>
                </div>
              </div>
              <div className="plugin-popup__body">
                <article className="page-card model-settings-card">
                  <div className="model-settings-meta">
                    <span>Mandant: {selectedProjectDetail.tenant_key ?? "-"}</span>
                    <span>Bereich: {selectedProjectDetail.area_key ?? "-"}</span>
                    <span>{selectedProjectDetail.chats} Chats</span>
                    <span>{selectedProjectDetail.documents} Dokumente</span>
                  </div>
                  <div className="model-profile-grid">
                    <label className="model-profile-field">
                      <span>Name</span>
                      <input
                        className="model-dir-input"
                        type="text"
                        value={projectRenameDraft[selectedProjectDetail.id] ?? selectedProjectDetail.name}
                        onChange={(event) => {
                          const value = event.target.value;
                          setProjectRenameDraft((current) => ({ ...current, [selectedProjectDetail.id]: value }));
                        }}
                        disabled={projectActionPending}
                      />
                    </label>
                    <label className="model-profile-field">
                      <span>Parent</span>
                      <select
                        className="model-dir-input"
                        value={projectParentDraft[selectedProjectDetail.id] ?? ""}
                        onChange={(event) => {
                          const value = event.target.value;
                          setProjectParentDraft((current) => ({ ...current, [selectedProjectDetail.id]: value }));
                        }}
                        disabled={projectActionPending}
                      >
                        <option value="">Keine Ebene darueber</option>
                        {projects.filter((candidate) => candidate.id !== selectedProjectDetail.id).map((candidate) => (
                          <option key={candidate.id} value={candidate.id}>{candidate.name}</option>
                        ))}
                      </select>
                    </label>
                    <label className="model-profile-field">
                      <span>Typ</span>
                      <select
                        className="model-dir-input"
                        value={projectScopeDraft[selectedProjectDetail.id] ?? "project"}
                        onChange={(event) => {
                          const value = event.target.value as "tenant" | "user" | "area" | "project";
                          setProjectScopeDraft((current) => ({ ...current, [selectedProjectDetail.id]: value }));
                        }}
                        disabled={projectActionPending}
                      >
                        <option value="tenant">Mandant</option>
                        <option value="user">Benutzer</option>
                        <option value="area">Bereich</option>
                        <option value="project">Projekt</option>
                      </select>
                    </label>
                    <label className="model-profile-field">
                      <span>Mandant</span>
                      <input
                        className="model-dir-input"
                        type="text"
                        value={projectTenantDraft[selectedProjectDetail.id] ?? ""}
                        onChange={(event) => {
                          const value = event.target.value;
                          setProjectTenantDraft((current) => ({ ...current, [selectedProjectDetail.id]: value }));
                        }}
                        disabled={projectActionPending}
                      />
                    </label>
                    <label className="model-profile-field">
                      <span>Bereich</span>
                      <input
                        className="model-dir-input"
                        type="text"
                        value={projectAreaDraft[selectedProjectDetail.id] ?? ""}
                        onChange={(event) => {
                          const value = event.target.value;
                          setProjectAreaDraft((current) => ({ ...current, [selectedProjectDetail.id]: value }));
                        }}
                        disabled={projectActionPending}
                      />
                    </label>
                    <label className="model-profile-field">
                      <span>Besitzer User-ID</span>
                      <input
                        className="model-dir-input"
                        type="number"
                        min={1}
                        value={projectOwnerDraft[selectedProjectDetail.id] ?? ""}
                        onChange={(event) => {
                          const value = event.target.value;
                          setProjectOwnerDraft((current) => ({ ...current, [selectedProjectDetail.id]: value }));
                        }}
                        disabled={projectActionPending}
                      />
                    </label>
                  </div>
                  <div className="model-settings-card__actions">
                    <button
                      type="button"
                      className="ghost-btn"
                      disabled={projectActionPending}
                      onClick={() => onSelectProject(selectedProjectDetail.id)}
                    >
                      {selectedProjectId === selectedProjectDetail.id ? "Ausgewaehlt" : "Auswaehlen"}
                    </button>
                    <button
                      type="button"
                      className="ghost-btn"
                      disabled={projectActionPending}
                      onClick={() => {
                        const nextName = (projectRenameDraft[selectedProjectDetail.id] ?? selectedProjectDetail.name).trim();
                        if (!nextName || nextName === selectedProjectDetail.name) {
                          return;
                        }
                        setProjectActionPending(true);
                        void onRenameProject(selectedProjectDetail.id, nextName).finally(() => setProjectActionPending(false));
                      }}
                    >
                      Umbenennen
                    </button>
                    <button
                      type="button"
                      className="ghost-btn"
                      disabled={projectActionPending}
                      onClick={() => {
                        setProjectActionPending(true);
                        const rawParent = (projectParentDraft[selectedProjectDetail.id] ?? "").trim();
                        const rawOwner = (projectOwnerDraft[selectedProjectDetail.id] ?? "").trim();
                        void onUpdateProjectHierarchy({
                          projectId: selectedProjectDetail.id,
                          parentProjectId: rawParent ? Number(rawParent) : null,
                          scopeKind: projectScopeDraft[selectedProjectDetail.id] ?? "project",
                          areaKey: (projectAreaDraft[selectedProjectDetail.id] ?? "").trim() || null,
                          tenantKey: (projectTenantDraft[selectedProjectDetail.id] ?? "").trim() || null,
                          ownerUserId: rawOwner ? Number(rawOwner) : null,
                        }).finally(() => setProjectActionPending(false));
                      }}
                    >
                      Hierarchie speichern
                    </button>
                    <button
                      type="button"
                      className="action-btn action-btn--danger"
                      disabled={projectActionPending}
                      onClick={() => {
                        const accepted = window.confirm(`Projekt "${selectedProjectDetail.name}" wirklich loeschen?`);
                        if (!accepted) {
                          return;
                        }
                        setProjectActionPending(true);
                        void onDeleteProject(selectedProjectDetail.id).finally(() => {
                          setProjectActionPending(false);
                          setProjectDetailPopupId(null);
                        });
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
              <th>Zuordnung</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((row) => (
              <tr key={row.id}>
                <td>{row.file}</td>
                <td>Bereit</td>
                <td>{row.position}</td>
                <td>{row.project_name ?? "Nicht zugeordnet"}</td>
                <td>
                  <div className="model-settings-controls">
                    <select
                      className="model-dir-input"
                      value={sourceProjectDraft[row.id] ?? ""}
                      onChange={(event) => {
                        const value = event.target.value;
                        setSourceProjectDraft((current) => ({ ...current, [row.id]: value }));
                      }}
                      disabled={sourceUploadPending}
                    >
                      <option value="">Keine Ebene</option>
                      {projects.map((project) => (
                        <option key={project.id} value={project.id}>{project.name}</option>
                      ))}
                    </select>
                    <button
                      type="button"
                      className="ghost-btn"
                      disabled={sourceUploadPending}
                      onClick={() => {
                        const rawValue = (sourceProjectDraft[row.id] ?? "").trim();
                        setSourceUploadPending(true);
                        void onAssignSourceToProject(row.id, rawValue ? Number(rawValue) : null).finally(() => {
                          setSourceUploadPending(false);
                        });
                      }}
                    >
                      Speichern
                    </button>
                  </div>
                </td>
                <td>
                  <button type="button" className="ghost-btn" disabled={sourceUploadPending} onClick={() => setSourceDetailPopupId(row.id)}>
                    Oeffnen
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {selectedSourceDetail ? (
          <div className="plugin-popup-overlay" role="dialog" aria-modal="true" aria-label="Bibliotheksdetail" onClick={() => setSourceDetailPopupId(null)}>
            <div className="plugin-popup" onClick={(event) => event.stopPropagation()}>
              <div className="plugin-popup__header">
                <div>
                  <strong>{selectedSourceDetail.file}</strong>
                  <span>Bibliothekseintrag</span>
                </div>
                <div className="model-settings-card__actions">
                  <button type="button" className="ghost-btn" onClick={() => setSourceDetailPopupId(null)}>Schliessen</button>
                </div>
              </div>
              <div className="plugin-popup__body">
                <article className="page-card model-settings-card">
                  <div className="model-settings-meta">
                    <span>Status: Bereit</span>
                    <span>Quelle: {selectedSourceDetail.position}</span>
                    <span>Projekt: {selectedSourceDetail.project_name ?? "Nicht zugeordnet"}</span>
                  </div>
                  <label className="model-profile-field">
                    <span>Projektzuordnung</span>
                    <select
                      className="model-dir-input"
                      value={sourceProjectDraft[selectedSourceDetail.id] ?? ""}
                      onChange={(event) => {
                        const value = event.target.value;
                        setSourceProjectDraft((current) => ({ ...current, [selectedSourceDetail.id]: value }));
                      }}
                      disabled={sourceUploadPending}
                    >
                      <option value="">Keine Ebene</option>
                      {projects.map((project) => (
                        <option key={project.id} value={project.id}>{project.name}</option>
                      ))}
                    </select>
                  </label>
                  <div className="model-settings-card__actions">
                    <button
                      type="button"
                      className="action-btn action-btn--primary"
                      disabled={sourceUploadPending}
                      onClick={() => {
                        const rawValue = (sourceProjectDraft[selectedSourceDetail.id] ?? "").trim();
                        setSourceUploadPending(true);
                        void onAssignSourceToProject(selectedSourceDetail.id, rawValue ? Number(rawValue) : null).finally(() => {
                          setSourceUploadPending(false);
                        });
                      }}
                    >
                      Speichern
                    </button>
                  </div>
                </article>
              </div>
            </div>
          </div>
        ) : null}
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
              <div className="model-settings-card__actions">
                <button type="button" className="ghost-btn" onClick={() => setAppointmentDetailPopupId(appointment.id)}>
                  Termin oeffnen
                </button>
              </div>
            </article>
          ))}
        </div>

        {selectedAppointmentDetail ? (
          <div className="plugin-popup-overlay" role="dialog" aria-modal="true" aria-label="Termin-Details" onClick={() => setAppointmentDetailPopupId(null)}>
            <div className="plugin-popup" onClick={(event) => event.stopPropagation()}>
              <div className="plugin-popup__header">
                <div>
                  <strong>{selectedAppointmentDetail.title}</strong>
                  <span>{selectedAppointmentDetail.date}</span>
                </div>
                <div className="model-settings-card__actions">
                  <button type="button" className="ghost-btn" onClick={() => setAppointmentDetailPopupId(null)}>Schliessen</button>
                </div>
              </div>
              <div className="plugin-popup__body">
                <article className="page-card model-settings-card">
                  <div className="model-settings-meta">
                    <span>Status: {selectedAppointmentDetail.state}</span>
                    <span>ID: {selectedAppointmentDetail.id}</span>
                  </div>
                </article>
              </div>
            </div>
          </div>
        ) : null}
      </PageFrame>
    );
  }

  if (view === "Plugins") {
    const listedPlugins = pluginDescriptors.length > 0
      ? pluginDescriptors
      : [
          {
            id: "filesystem",
            name: "Dateisystem",
            description: "Lokaler Dateizugriff",
            category: "System",
            status: "aktiv",
            api_key_required: false,
            settings_fields: [],
          } as PluginCatalogEntry,
          {
            id: "calendar",
            name: "Kalender",
            description: "Termine lesen und schreiben",
            category: "Organisation",
            status: "aktiv",
            api_key_required: false,
            settings_fields: [],
          } as PluginCatalogEntry,
          {
            id: "email",
            name: "E-Mail",
            description: "Ausgehender Versand",
            category: "Kommunikation",
            status: "deaktiviert",
            api_key_required: true,
            settings_fields: [],
          } as PluginCatalogEntry,
        ];

    return (
      <PageFrame title="Plugins">
        <div className="workspace-stack">
          <div className="plugin-widgets-grid" role="list" aria-label="Plugin-Widgets">
            {listedPlugins.map((plugin) => {
              const pluginName = plugin.name || plugin.id;
              const isActive = plugin.id === pluginSoloSelectedId;
              const logo = resolvePluginWidgetLogo(plugin.id);
              return (
                <article
                  key={plugin.id}
                  role="listitem"
                  className={`page-card plugin-widget-card ${isActive ? "plugin-widget-card--active" : ""}`}
                >
                  <div className="plugin-widget-card__head">
                    <div className="plugin-widget-card__logo" aria-hidden="true">
                      {logo ? (
                        <img src={logo} alt="" className="plugin-widget-card__logo-image" />
                      ) : (
                        <span>{pluginName.slice(0, 1).toUpperCase()}</span>
                      )}
                    </div>
                    <div className="plugin-widget-card__title">
                      <strong>{pluginName}</strong>
                      <span>{plugin.category || "Allgemein"}</span>
                    </div>
                  </div>
                  <span>{plugin.description || `Widget fuer ${plugin.id}`}</span>
                  <span>Status: {plugin.status || "unknown"}</span>
                  <span>Berechtigung: {plugin.api_key_required ? "API-Key erforderlich" : "Keine Pflicht-Integration"}</span>
                  <div className="model-settings-card__actions plugin-widget-card__actions">
                    <button
                      type="button"
                      className="ghost-btn"
                      aria-label={`Plugin-Frontend fuer ${pluginName} oeffnen`}
                      title={`Plugin-Frontend fuer ${pluginName} oeffnen`}
                      onClick={() => {
                        openPluginPopupForTab(plugin.id, "frontend");
                      }}
                    >
                      Frontend
                    </button>
                    <button
                      type="button"
                      className="ghost-btn"
                      aria-label={`Plugin-Settings fuer ${pluginName} oeffnen`}
                      title={`Plugin-Settings fuer ${pluginName} oeffnen`}
                      onClick={() => {
                        openPluginPopupForTab(plugin.id, "settings");
                      }}
                    >
                      ⚙
                    </button>
                    <button
                      type="button"
                      className="action-btn"
                      onClick={() => {
                        openPluginPopupForTab(plugin.id, "manual");
                      }}
                    >
                      Plugin oeffnen
                    </button>
                  </div>
                </article>
              );
            })}
          </div>

          {pluginPopupOpen ? (
            <div
              className="plugin-popup-overlay"
              role="dialog"
              aria-modal="true"
              aria-label="Plugin-Fenster"
              onClick={() => setPluginPopupOpen(false)}
            >
              <div
                  className="plugin-popup plugin-popup--deep"
                onClick={(event) => {
                  event.stopPropagation();
                }}
              >
                <div className="plugin-popup__header">
                  <div>
                    <strong>{selectedPluginDescriptor?.name || pluginSoloSelectedId}</strong>
                    <span>{selectedPluginDescriptor?.description || "Plugin-Fenster"}</span>
                  </div>
                  <div className="model-settings-card__actions">
                    <button
                      type="button"
                      className={`ghost-btn ${pluginPopupTab === "frontend" ? "ghost-btn--active" : ""}`}
                      onClick={() => setPluginPopupTab("frontend")}
                    >
                      Frontend
                    </button>
                    <button
                      type="button"
                      className={`ghost-btn ${pluginPopupTab === "settings" ? "ghost-btn--active" : ""}`}
                      onClick={() => setPluginPopupTab("settings")}
                    >
                      Settings
                    </button>
                    <button
                      type="button"
                      className={`ghost-btn ${pluginPopupTab === "manual" ? "ghost-btn--active" : ""}`}
                      onClick={() => setPluginPopupTab("manual")}
                    >
                      Plugin oeffnen
                    </button>
                    <button type="button" className="ghost-btn" onClick={() => setPluginPopupOpen(false)}>Schliessen</button>
                  </div>
                </div>

                {pluginPopupTab === "frontend" ? (
                  <div className="plugin-popup__body">
                    {selectedPluginDescriptor?.id === "business_letter" ? (
                      <BusinessLetterManualPage
                        currentUserId={currentUser.id}
                        executePlugin={async (payload) => {
                          if (!onExecutePlugin) {
                            throw new Error("Plugin-Ausfuehrung ist in diesem Kontext nicht verfuegbar.");
                          }
                          return onExecutePlugin(payload);
                        }}
                        onClose={() => setPluginPopupOpen(false)}
                      />
                    ) : null}

                    {selectedPluginDescriptor?.id === "calculator" ? (
                      <CalculatorManualPage
                        currentUserId={currentUser.id}
                        executePlugin={async (payload) => {
                          if (!onExecutePlugin) {
                            throw new Error("Plugin-Ausfuehrung ist in diesem Kontext nicht verfuegbar.");
                          }
                          return onExecutePlugin(payload);
                        }}
                      />
                    ) : null}

                    {selectedPluginDescriptor?.id !== "business_letter" && selectedPluginDescriptor?.id !== "calculator" ? (
                    <div className="workspace-stack plugin-frontend-shell">
                      <article className="page-card model-settings-card plugin-frontend-hero-card">
                        <div className="plugin-frontend-hero">
                          <div className="plugin-frontend-hero__copy">
                            {selectedPluginFrontend?.page?.eyebrow ? <span className="plugin-frontend-hero__eyebrow">{selectedPluginFrontend.page.eyebrow}</span> : null}
                            <strong>{selectedPluginFrontend?.page?.headline || selectedPluginFrontend?.title || `${selectedPluginDescriptor?.name || pluginSoloSelectedId} Frontend`}</strong>
                            <span>
                              {selectedPluginFrontend?.page?.summary || selectedPluginFrontend?.description || "Zentrale Frontpage fuer Funktionen, Presets, Settings und direkte Ausfuehrung dieses Plugins."}
                            </span>
                          </div>
                          <div className="model-settings-meta settings-plugin-card__meta plugin-frontend-hero__meta">
                            <span>{selectedPluginActions.length} Funktionen</span>
                            <span>{selectedPluginFields.length} Felder</span>
                            <span>{Object.keys(selectedPluginGroupedFields).length} Gruppen</span>
                            <span>{selectedPluginFrontend?.sections?.length ?? 0} Fachbereiche</span>
                          </div>
                        </div>
                        {selectedPluginFrontend?.page?.highlights && selectedPluginFrontend.page.highlights.length > 0 ? (
                          <div className="model-settings-meta settings-plugin-card__meta plugin-frontend-hero__highlights">
                            {selectedPluginFrontend.page.highlights.map((highlight) => (
                              <span key={`plugin-frontend-highlight:${selectedPluginDescriptor?.id}:${highlight}`}>{highlight}</span>
                            ))}
                          </div>
                        ) : null}
                        <div className="settings-plugin-grid plugin-frontend-action-grid plugin-frontend-action-grid--quickstart">
                          <article className="page-card plugin-widget-card plugin-frontend-action-card plugin-frontend-action-card--quickstart">
                            <strong>Manuelle Oberflaeche</strong>
                            <span>Direkter Einstieg in den Runner fuer freie Eingaben und Ausfuehrung.</span>
                            <div className="model-settings-card__actions plugin-widget-card__actions">
                              <button type="button" className="action-btn action-btn--primary" onClick={() => setPluginPopupTab("manual")}>
                                Runner oeffnen
                              </button>
                            </div>
                          </article>
                          <article className="page-card plugin-widget-card plugin-frontend-action-card plugin-frontend-action-card--quickstart">
                            <strong>Plugin-Settings</strong>
                            <span>Konfigurierbare Gruppen und Felder dieses Plugins im Popup bearbeiten.</span>
                            <div className="model-settings-card__actions plugin-widget-card__actions">
                              <button type="button" className="action-btn action-btn--primary" onClick={() => setPluginPopupTab("settings")}>
                                Settings oeffnen
                              </button>
                            </div>
                          </article>
                        </div>
                      </article>

                      {selectedPluginFrontend?.page?.sections && selectedPluginFrontend.page.sections.length > 0 ? (
                        <div className="workspace-stack">
                          {selectedPluginFrontend.page.sections.map((section) => (
                            <section key={`plugin-frontend-page-section:${selectedPluginDescriptor?.id}:${section.id}`} className="page-card plugin-frontend-section-card plugin-frontend-page-section-card">
                              <div className="model-settings-card__header">
                                <strong>{section.title}</strong>
                              </div>
                              {section.description ? <span>{section.description}</span> : null}
                              <div className="settings-plugin-grid plugin-frontend-action-grid plugin-frontend-page-grid">
                                {section.cards.map((card) => (
                                  <article key={`plugin-frontend-page-card:${selectedPluginDescriptor?.id}:${section.id}:${card.id}`} className="page-card plugin-widget-card plugin-frontend-action-card plugin-frontend-page-card">
                                    <strong>{card.title}</strong>
                                    {card.description ? <span>{card.description}</span> : null}
                                    {card.bullets && card.bullets.length > 0 ? (
                                      <div className="plugin-frontend-page-card__bullets">
                                        {card.bullets.map((bullet) => (
                                          <span key={`plugin-frontend-page-card-bullet:${selectedPluginDescriptor?.id}:${section.id}:${card.id}:${bullet}`}>{bullet}</span>
                                        ))}
                                      </div>
                                    ) : null}
                                    <div className="model-settings-card__actions plugin-widget-card__actions">
                                      <button
                                        type="button"
                                        className="action-btn action-btn--primary"
                                        onClick={() => {
                                          if (!selectedPluginDescriptor) {
                                            return;
                                          }
                                          applyPluginFrontendAction(selectedPluginDescriptor.id, {
                                            id: card.id,
                                            label: card.title,
                                            description: card.description,
                                            openTab: card.openTab,
                                            pluginInput: card.pluginInput,
                                            pluginSettings: card.pluginSettings,
                                          });
                                        }}
                                      >
                                        {card.ctaLabel || "Oeffnen"}
                                      </button>
                                    </div>
                                  </article>
                                ))}
                              </div>
                            </section>
                          ))}
                        </div>
                      ) : null}

                      {selectedPluginFrontend?.sections && selectedPluginFrontend.sections.length > 0 ? (
                        <div className="workspace-stack">
                          {selectedPluginFrontend.sections.map((section) => (
                            <section key={`plugin-frontend-section:${selectedPluginDescriptor?.id}:${section.id}`} className="page-card plugin-frontend-section-card">
                              <div className="model-settings-card__header">
                                <strong>{section.title}</strong>
                              </div>
                              {section.description ? <span>{section.description}</span> : null}
                              <div className="settings-plugin-grid plugin-frontend-action-grid">
                                {section.actions.map((action) => (
                                  <article key={`plugin-frontend-action:${selectedPluginDescriptor?.id}:${section.id}:${action.id}`} className="page-card plugin-widget-card plugin-frontend-action-card">
                                    <strong>{action.label}</strong>
                                    <span>{action.description || "Oeffnet den hinterlegten Plugin-Frontend-Schritt."}</span>
                                    <div className="model-settings-card__actions plugin-widget-card__actions">
                                      <button
                                        type="button"
                                        className="action-btn action-btn--primary"
                                        onClick={() => {
                                          if (!selectedPluginDescriptor) {
                                            return;
                                          }
                                          applyPluginFrontendAction(selectedPluginDescriptor.id, action);
                                        }}
                                      >
                                        Oeffnen
                                      </button>
                                    </div>
                                  </article>
                                ))}
                              </div>
                            </section>
                          ))}
                        </div>
                      ) : null}

                      <section className="page-card plugin-frontend-section-card">
                        <div className="model-settings-card__header">
                          <strong>Verfuegbare Funktionen</strong>
                        </div>
                        <span>Alle im Plugin deklarierten Aktionen aus dem Eingangsschema. Jede Funktion kann direkt in den Runner uebernommen werden.</span>
                        <div className="settings-plugin-grid plugin-frontend-action-grid">
                          {selectedPluginActions.length > 0 ? selectedPluginActions.map((action) => (
                            <article key={`plugin-function:${selectedPluginDescriptor?.id}:${action.id}`} className="page-card plugin-widget-card plugin-frontend-action-card plugin-frontend-action-card--function">
                              <strong>{action.label}</strong>
                              <span>{action.description}</span>
                              <div className="model-settings-meta settings-plugin-card__meta">
                                <span>{String(action.pluginInput?.action ?? "Aktion")}</span>
                                <span>Runner-Preset</span>
                              </div>
                              <div className="model-settings-card__actions plugin-widget-card__actions">
                                <button
                                  type="button"
                                  className="action-btn action-btn--primary"
                                  onClick={() => {
                                    if (!selectedPluginDescriptor) {
                                      return;
                                    }
                                    applyPluginFrontendAction(selectedPluginDescriptor.id, action);
                                  }}
                                >
                                  Im Runner oeffnen
                                </button>
                              </div>
                            </article>
                          )) : (
                            <article className="page-card plugin-widget-card plugin-frontend-action-card plugin-frontend-action-card--function-empty">
                              <strong>Keine deklarierte Funktion gefunden</strong>
                              <span>Dieses Plugin liefert derzeit keine `action`-Liste im Eingangsschema. Nutze stattdessen den manuellen Runner oder die Settings.</span>
                            </article>
                          )}
                        </div>
                      </section>
                    </div>
                    ) : null}
                  </div>
                ) : null}

                {pluginPopupTab === "settings" ? (
                  <div className="plugin-popup__body">
                    <article className="page-card model-settings-card">
                      <div className="model-settings-card__header">
                        <strong>Plugin-Settings</strong>
                        <div className="model-settings-card__actions model-settings-card__actions--stacked">
                          <button
                            type="button"
                            className="ghost-btn"
                            disabled={!selectedPluginDescriptor || selectedPluginFields.length === 0}
                            onClick={() => {
                              const override = buildSelectedPluginSettingsOverride();
                              setPluginSoloSettingsJson(JSON.stringify(override, null, 2));
                            }}
                          >
                            Als Override uebernehmen
                          </button>
                          <button
                            type="button"
                            className="action-btn action-btn--primary"
                            disabled={!selectedPluginDescriptor || savingPluginId === selectedPluginDescriptor.id}
                            onClick={() => {
                              if (!selectedPluginDescriptor) {
                                return;
                              }
                              void onSavePluginSettings(selectedPluginDescriptor.id);
                            }}
                          >
                            {savingPluginId === selectedPluginDescriptor?.id ? "Speichere..." : "Settings speichern"}
                          </button>
                        </div>
                      </div>

                      {selectedPluginDescriptor && selectedPluginFields.length > 0 ? (
                        <div className="workspace-stack">
                          <div className="settings-plugin-subgroup-grid">
                            {Object.entries(selectedPluginGroupedFields).map(([groupName, groupFields]) => {
                              const groupKey = `${selectedPluginDescriptor.id}:${groupName}`;
                              const previewLabels = groupFields.slice(0, 3).map((field) => field.label);
                              return (
                                <section key={groupKey} className="model-group-card settings-plugin-subgroup-card">
                                  <button
                                    type="button"
                                    className="model-group-toggle settings-plugin-subgroup-card__toggle"
                                    onClick={() => {
                                      setSettingsPluginGroupPopup({
                                        pluginId: selectedPluginDescriptor.id,
                                        groupName,
                                      });
                                    }}
                                  >
                                    <span>
                                      {resolvePluginGroupIcon(groupName, symbolProfile)} {groupName}
                                    </span>
                                    <span className="model-group-toggle__meta">{groupFields.length} Felder · Popup oeffnen</span>
                                  </button>
                                  <div className="settings-plugin-subgroup-card__fields">
                                    <span className="settings-plugin-card__expectation">
                                      {buildPluginGroupExpectation(groupName, groupFields)}
                                    </span>
                                    <div className="model-settings-meta settings-plugin-card__meta">
                                      {previewLabels.map((label) => (
                                        <span key={`${groupKey}:${label}`}>{label}</span>
                                      ))}
                                      {groupFields.length > 3 ? <span>+ {groupFields.length - 3} weitere</span> : null}
                                    </div>
                                  </div>
                                </section>
                              );
                            })}
                          </div>
                        </div>
                      ) : (
                        <span>Fuer dieses Plugin sind aktuell keine konfigurierbaren Felder hinterlegt.</span>
                      )}
                    </article>
                  </div>
                ) : null}

                {pluginPopupTab === "manual" ? (
                  <div className="plugin-popup__body">
                    <article className="page-card model-settings-card">
                      <div className="model-settings-card__header">
                        <strong>Manuelle Plugin-Oberflaeche</strong>
                        <div className="model-settings-card__actions">
                          <button
                            type="button"
                            className="ghost-btn"
                            disabled={pluginSoloPending || !onExecutePlugin}
                            onClick={() => {
                              const pluginId = pluginSoloSelectedId.trim() || "business_letter";
                              setPluginSoloInputJson(JSON.stringify(buildDefaultPluginSoloInput(pluginId), null, 2));
                              setPluginSoloSettingsJson("{}");
                              setPluginSoloResultData(null);
                              setPluginSoloResultJson("");
                              setPluginSoloError(null);
                            }}
                          >
                            Zuruecksetzen
                          </button>
                          <button
                            type="button"
                            className="action-btn action-btn--primary"
                            disabled={pluginSoloPending || !onExecutePlugin}
                            onClick={() => {
                              void handleRunPluginSolo();
                            }}
                          >
                            {pluginSoloPending ? "Laeuft..." : "Plugin ausfuehren"}
                          </button>
                        </div>
                      </div>

                      <span>
                        Hier landet die manuelle Plugin-Oberflaeche. Aktuell ist der Solo-Runner aktiv,
                        inklusive serverseitiger Validierung ueber /api/plugins/execute.
                      </span>

                      <div className="model-profile-grid">
                        <label className="model-profile-field">
                          <span>Plugin</span>
                          <select
                            className="model-dir-input"
                            value={pluginSoloSelectedId}
                            onChange={(event) => {
                              const nextId = event.target.value;
                              setPluginSoloSelectedId(nextId);
                              setPluginSoloInputJson(JSON.stringify(buildDefaultPluginSoloInput(nextId), null, 2));
                              setPluginSoloResultData(null);
                              setPluginSoloResultJson("");
                              setPluginSoloError(null);
                            }}
                          >
                            {listedPlugins.map((plugin) => (
                              <option key={plugin.id} value={plugin.id}>
                                {plugin.name || plugin.id}
                              </option>
                            ))}
                          </select>
                        </label>
                      </div>

                      <label className="model-profile-field">
                        <span>Plugin-Input (JSON-Objekt)</span>
                        <textarea
                          className="model-dir-input"
                          rows={14}
                          value={pluginSoloInputJson}
                          onChange={(event) => setPluginSoloInputJson(event.target.value)}
                          spellCheck={false}
                        />
                      </label>

                      <label className="model-profile-field">
                        <span>Plugin-Settings Override (JSON-Objekt)</span>
                        <textarea
                          className="model-dir-input"
                          rows={8}
                          value={pluginSoloSettingsJson}
                          onChange={(event) => setPluginSoloSettingsJson(event.target.value)}
                          spellCheck={false}
                        />
                      </label>

                      {pluginSoloBusinessLetterSummary ? (
                        <div className="model-settings-meta" aria-label="Business-Letter-Solo-Run-Zusammenfassung">
                          <span>Dokumentnummer: {pluginSoloBusinessLetterSummary.documentNumber}</span>
                          <span>Status: {pluginSoloBusinessLetterSummary.status}</span>
                          <span>PDF-Datei: {pluginSoloBusinessLetterSummary.pdfFileName}</span>
                          <span>Template: {pluginSoloBusinessLetterSummary.layoutTemplate}</span>
                          <span>Logo vorhanden: {pluginSoloBusinessLetterSummary.logoPresent}</span>
                          <span>Logo-Position: {pluginSoloBusinessLetterSummary.logoPosition}</span>
                          <span>Versand blockiert: {pluginSoloBusinessLetterSummary.deliveryBlocked}</span>
                        </div>
                      ) : null}

                      {pluginSoloCalculatorSummary ? (
                        <div className="model-settings-meta" aria-label="Calculator-Solo-Run-Zusammenfassung">
                          <span>Ausdruck: {pluginSoloCalculatorSummary.expression}</span>
                          <span>Ergebnis: {pluginSoloCalculatorSummary.result}</span>
                          <span>Modus: {pluginSoloCalculatorSummary.angleMode}</span>
                          <span>Praezision: {pluginSoloCalculatorSummary.precision}</span>
                          <span>Aktion: {pluginSoloCalculatorSummary.action}</span>
                        </div>
                      ) : null}

                      {pluginSoloError ? <span className="field-error">{pluginSoloError}</span> : null}

                      <label className="model-profile-field">
                        <span>Antwort</span>
                        <textarea
                          className="model-dir-input"
                          rows={14}
                          value={pluginSoloResultJson}
                          readOnly
                          placeholder="Hier erscheint die Plugin-Antwort als JSON."
                          spellCheck={false}
                        />
                      </label>
                    </article>
                  </div>
                ) : null}
              </div>
            </div>
          ) : null}
        </div>
      </PageFrame>
    );
  }

  if (view === "Einstellungen") {
    return (
      <PageFrame title="Einstellungen">
        <div className="settings-layout">
          <nav className="settings-nav settings-nav--grid">
            {settingsGroups.map(([group]) => (
              <button
                key={group}
                className={`settings-nav-item settings-nav-item--card ${group === activeSettingsGroup ? "settings-nav-item--active" : ""}`}
                type="button"
                onClick={() => {
                  openSettingsGroup(group);
                }}
              >
                <div className="settings-nav-item__lead">
                  <span className="settings-nav-item__icon" aria-hidden="true">{resolveSettingsGroupIcon(group, symbolProfile)}</span>
                  <strong>{group}</strong>
                </div>
                <span>{settingsGroupDescriptions[group]}</span>
                <span className="settings-nav-item__hint">Kachel oeffnet Detailansicht dieser Gruppe.</span>
              </button>
            ))}
          </nav>
          <div className={`settings-content-shell ${isSettingsModalOpen ? "settings-content-shell--modal" : ""}`}>
            {isSettingsModalOpen ? (
              <button
                type="button"
                className="settings-content-backdrop"
                aria-label="Settings schliessen"
                onClick={() => setSettingsModalGroup(null)}
              />
            ) : null}
            <div className={`settings-content ${isSettingsModalOpen ? "settings-content--modal" : ""}`}>
              {isSettingsModalOpen ? (
                <div
                  className="settings-modal-header"
                  onKeyDown={(event) => {
                    if (isKeyboardInputTarget(event.target)) {
                      return;
                    }
                    if (event.key === "ArrowLeft") {
                      event.preventDefault();
                      moveSettingsGroup(-1);
                    }
                    if (event.key === "ArrowRight") {
                      event.preventDefault();
                      moveSettingsGroup(1);
                    }
                    if (event.key === "Home") {
                      event.preventDefault();
                      openSettingsGroup(settingsGroupNames[0]);
                    }
                    if (event.key === "End") {
                      event.preventDefault();
                      openSettingsGroup(settingsGroupNames[settingsGroupNames.length - 1]);
                    }
                  }}
                >
                  <div className="settings-modal-header__title">
                    <strong>{activeSettingsGroup}</strong>
                    <span>{activeSettingsGroupDescription}</span>
                    <div className="settings-modal-breadcrumbs" aria-label="Settings-Pfad">
                      <span>Einstellungen</span>
                      <span>/</span>
                      <span>{activeSettingsGroup}</span>
                    </div>
                  </div>
                  <div className="model-settings-card__actions settings-modal-header__actions">
                    <button type="button" className="ghost-btn" onClick={() => moveSettingsGroup(-1)}>Zurueck</button>
                    <select
                      className="model-dir-input settings-modal-header__select"
                      value={activeSettingsGroup}
                      onChange={(event) => openSettingsGroup(event.target.value as (typeof settingsGroups)[number][0])}
                    >
                      {settingsGroups.map(([group]) => (
                        <option key={`settings-modal:${group}`} value={group}>{group}</option>
                      ))}
                    </select>
                    <button type="button" className="ghost-btn" onClick={() => moveSettingsGroup(1)}>Weiter</button>
                    <button type="button" className="ghost-btn" autoFocus onClick={() => setSettingsModalGroup(null)}>Schliessen</button>
                  </div>
                </div>
              ) : null}
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

            {activeSettingsGroup === "Darstellung" ? (
              <article className="page-card model-settings-card">
                <div className="model-settings-card__header">
                  <strong>Darstellung</strong>
                </div>

                <span>Steuert die Symbolik und die Anzeigeart fuer Gruppen in den Settings.</span>

                <div className="model-profile-grid">
                  <label className="model-profile-field">
                    <span>Symbolprofil</span>
                    <select
                      className="model-dir-input"
                      value={symbolProfile}
                      onChange={(event) => {
                        const next = event.target.value;
                        if (next === "technisch" || next === "minimal" || next === "business") {
                          setSymbolProfile(next);
                        }
                      }}
                    >
                      <option value="technisch">Technisch</option>
                      <option value="minimal">Minimal</option>
                      <option value="business">Business-orientiert</option>
                    </select>
                  </label>

                  <label className="model-profile-field">
                    <span>Gruppendarstellung (Integrationen)</span>
                    <select
                      className="model-dir-input"
                      value={integrationDisplayMode}
                      onChange={(event) => {
                        const next = event.target.value;
                        if (next === "inline" || next === "popup") {
                          setIntegrationDisplayMode(next);
                          if (next === "inline") {
                            setIntegrationGroupPopup(null);
                          }
                        }
                      }}
                    >
                      <option value="inline">Inline</option>
                      <option value="popup">Popup</option>
                    </select>
                  </label>
                </div>

                <div className="model-settings-meta settings-plugin-card__meta" aria-label="Darstellungsvorschau">
                  <span>Aktives Symbolprofil: {symbolProfile}</span>
                  <span>Integrationen: {integrationDisplayMode === "popup" ? "Popup" : "Inline"}</span>
                  <span>Wird pro Benutzer lokal gespeichert</span>
                </div>
              </article>
            ) : null}

            {activeSettingsGroup === "Modelle" ? (
              <article className="page-card model-settings-card">
                <div className="model-settings-card__header">
                  <strong>Modelle</strong>
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

                <div className="model-settings-tabbar" role="tablist" aria-label="Modelleinstellungen">
                  {modelSettingsTabs.map(([tabId, label]) => (
                    <button
                      key={tabId}
                      type="button"
                      className={`section-chip ${activeModelSettingsTab === tabId ? "section-chip--active" : ""}`}
                      onClick={() => setActiveModelSettingsTab(tabId)}
                    >
                      {label}
                    </button>
                  ))}
                </div>

                {activeModelSettingsTab === "overview" ? (
                  <>
                    <div className="model-profile-grid model-profile-grid--model-overview">
                      <label className="model-profile-field">
                        <span>Suche</span>
                        <input
                          className="model-dir-input"
                          type="text"
                          placeholder="Name, Familie, Quelle..."
                          value={modelSearch}
                          onChange={(event) => setModelSearch(event.target.value)}
                          disabled={modelActionPending}
                        />
                      </label>

                      <label className="model-profile-field">
                        <span>Modellfamilie</span>
                        <select
                          className="model-dir-input"
                          value={modelFamilyFilter}
                          onChange={(event) => setModelFamilyFilter(event.target.value)}
                          disabled={modelActionPending}
                        >
                          <option value="all">Alle</option>
                          {availableModelFamilies.map((family) => (
                            <option key={family} value={family}>
                              {family}
                            </option>
                          ))}
                        </select>
                      </label>

                      <div className="model-profile-field model-filter-fieldset">
                        <span>Faehigkeiten</span>
                        <div className="model-filter-grid">
                          <label className="model-radio-wrap"><input type="checkbox" checked={filterTools} onChange={(event) => setFilterTools(event.target.checked)} />Tools</label>
                          <label className="model-radio-wrap"><input type="checkbox" checked={filterThinking} onChange={(event) => setFilterThinking(event.target.checked)} />Thinking</label>
                          <label className="model-radio-wrap"><input type="checkbox" checked={filterVision} onChange={(event) => setFilterVision(event.target.checked)} />Vision</label>
                          <label className="model-radio-wrap"><input type="checkbox" checked={filterAudio} onChange={(event) => setFilterAudio(event.target.checked)} />Audio</label>
                          <label className="model-radio-wrap"><input type="checkbox" checked={filterSpeech} onChange={(event) => setFilterSpeech(event.target.checked)} />Speech</label>
                          <label className="model-radio-wrap"><input type="checkbox" checked={filterOcr} onChange={(event) => setFilterOcr(event.target.checked)} />OCR</label>
                        </div>
                      </div>
                    </div>

                    <div className="model-settings-list">
                      {Object.entries(groupedModelEntries).map(([groupName, entries]) => {
                    const isCollapsed = collapsedModelGroups[groupName] ?? shouldCollapseModelGroupByDefault(groupName);
                    return (
                      <section key={groupName} className={`model-group-card ${isCollapsed ? "model-group-card--collapsed" : ""}`}>
                        <button
                          type="button"
                          className="model-group-toggle"
                          onClick={() => {
                            setCollapsedModelGroups((current) => ({ ...current, [groupName]: !isCollapsed }));
                          }}
                        >
                          <span>{groupName}</span>
                          <span className="model-group-toggle__meta">{entries.length} Modelle · {isCollapsed ? "eingeklappt" : "aufgeklappt"}</span>
                        </button>
                        {!isCollapsed ? entries.map((model) => {
                    const isSelected = model.id === selectedModelId;
                    const isActive = model.isActive;
                    const pullState = model.pullStatus?.state ?? null;
                    const isPulling = pullState === "queued" || pullState === "pulling" || pullState === "cancelling";
                    const isCloudDownloadRequired = model.category === "ollama_cloud" && !model.ollamaInstalled;
                    const canActivate = !isPulling && !isCloudDownloadRequired;
                    const canRetryPull = model.category === "ollama_cloud" && !model.ollamaInstalled && (pullState === "error" || pullState === "cancelled");
                    const capabilityBadges = ollamaCapabilityBadges(model);
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
                            <span>Quelle: {model.sourceLabel}</span>
                            {model.taskType ? <span>Task: {model.taskType}</span> : null}
                            {model.modelFormat ? <span>Format: {model.modelFormat}</span> : null}
                            {model.parameterSize ? <span>Parameter: {model.parameterSize}</span> : null}
                            {model.quantizationLevel ? <span>Quantisierung: {model.quantizationLevel}</span> : null}
                            {model.contextLength ? <span>Kontext: {model.contextLength}</span> : null}
                            {capabilityBadges.length > 0 ? <span>Faehigkeiten: {capabilityBadges.join(", ")}</span> : null}
                            {model.pullStatus?.detail ? (
                              <span>
                                Download: {model.pullStatus.progressPercent != null ? `${model.pullStatus.progressPercent}% - ` : ""}
                                {model.pullStatus.detail}
                              </span>
                            ) : null}
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
                              disabled={modelActionPending || !canActivate}
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
                            disabled={modelActionPending || pullState === "cancelling"}
                            onClick={() => {
                              if (isActive) {
                                void onDeactivateModel();
                                return;
                              }
                              if (isPulling) {
                                void onCancelPullModel(model.id);
                                return;
                              }
                              if (isCloudDownloadRequired) {
                                void onPullModel(model.id);
                                return;
                              }
                              void onActivateModel(model.id);
                            }}
                          >
                            {isActive
                              ? "Entladen"
                              : pullState === "cancelling"
                                ? "Bricht ab..."
                                : isPulling
                                  ? "Abbrechen"
                                  : canRetryPull
                                    ? "Retry"
                                    : isCloudDownloadRequired
                                      ? "Herunterladen"
                                      : "Laden"}
                          </button>
                        </div>
                      </div>
                    );
                  }) : null}
                      </section>
                    );
                  })}
                      {modelEntries.length === 0 ? <span>Keine Modelle gefunden. Bitte Scan starten.</span> : null}
                      {modelEntries.length > 0 && filteredModelEntries.length === 0 ? <span>Keine Modelle passen zu den aktuellen Filtern.</span> : null}
                    </div>
                  </>
                ) : null}

                {activeModelSettingsTab === "directories" ? (
                  <>
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
                  </>
                ) : null}

                {activeModelSettingsTab === "prompts" ? (
                  <>
                    <span>Diese Werte gelten nur fuer das aktuell ausgewaehlte Modell.</span>

                    <div className="model-profile-grid">
                      <div className="model-settings-card__actions model-settings-card__actions--stacked">
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

                      <label className="model-profile-field"><span>Temperatur</span><input className="model-dir-input" type="number" min="0" max="2" step="0.1" value={profileDraft.temperature} onChange={(event) => { setProfileDraft((current) => ({ ...current, temperature: event.target.value })); }} disabled={modelProfilePending || selectedModelId.length === 0} /></label>
                      <label className="model-profile-field"><span>Sampling Top-K</span><input className="model-dir-input" type="number" min="0" step="1" value={profileDraft.samplingTopK} onChange={(event) => { setProfileDraft((current) => ({ ...current, samplingTopK: event.target.value })); }} disabled={modelProfilePending || selectedModelId.length === 0} /></label>
                      <label className="model-profile-field"><span>Max New Tokens</span><input className="model-dir-input" type="number" min="1" step="1" value={profileDraft.maxNewTokens} onChange={(event) => { setProfileDraft((current) => ({ ...current, maxNewTokens: event.target.value })); }} disabled={modelProfilePending || selectedModelId.length === 0} /></label>
                      <label className="model-profile-field"><span>Retrieval Top-K</span><input className="model-dir-input" type="number" min="1" step="1" value={profileDraft.topK} onChange={(event) => { setProfileDraft((current) => ({ ...current, topK: event.target.value })); }} disabled={modelProfilePending || selectedModelId.length === 0} /></label>
                      <label className="model-profile-field"><span>Top-P</span><input className="model-dir-input" type="number" min="0.01" max="1" step="0.01" value={profileDraft.topP} onChange={(event) => { setProfileDraft((current) => ({ ...current, topP: event.target.value })); }} disabled={modelProfilePending || selectedModelId.length === 0} /></label>
                      <label className="model-profile-field"><span>Repetition Penalty</span><input className="model-dir-input" type="number" min="0.5" max="2" step="0.01" value={profileDraft.repetitionPenalty} onChange={(event) => { setProfileDraft((current) => ({ ...current, repetitionPenalty: event.target.value })); }} disabled={modelProfilePending || selectedModelId.length === 0} /></label>
                      <label className="model-profile-field"><span>Stop Sequences (kommagetrennt)</span><input className="model-dir-input" type="text" value={profileDraft.stopSequences} onChange={(event) => { setProfileDraft((current) => ({ ...current, stopSequences: event.target.value })); }} disabled={modelProfilePending || selectedModelId.length === 0} /></label>
                      <label className="model-profile-field"><span>Seed</span><input className="model-dir-input" type="number" min="0" step="1" value={profileDraft.seed} onChange={(event) => { setProfileDraft((current) => ({ ...current, seed: event.target.value })); }} disabled={modelProfilePending || selectedModelId.length === 0} /></label>

                      <label className="model-radio-wrap model-profile-toggle">
                        <input type="checkbox" checked={profileDraft.doSample} onChange={(event) => { setProfileDraft((current) => ({ ...current, doSample: event.target.checked })); }} disabled={modelProfilePending || selectedModelId.length === 0} />
                        do_sample
                      </label>

                      <label className="model-radio-wrap model-profile-toggle">
                        <input type="checkbox" checked={profileDraft.preferGpu} onChange={(event) => { setProfileDraft((current) => ({ ...current, preferGpu: event.target.checked })); }} disabled={modelProfilePending || selectedModelId.length === 0} />
                        GPU bevorzugen
                      </label>
                    </div>

                    {selectedModelId.length === 0 ? <span>Bitte zuerst ein Modell auswaehlen.</span> : null}
                  </>
                ) : null}
              </article>
            ) : null}

            {activeSettingsGroup === "Chat" ? (
              <article className="page-card model-settings-card">
                <div className="model-settings-card__header">
                  <strong>Chat-Einstellungen</strong>
                  <div className="model-settings-card__actions">
                    <button
                      type="button"
                      className="action-btn"
                      disabled={chatSettingsPending || chatCleanupPending}
                      onClick={() => {
                        void onCleanupObsoleteChatSettings();
                      }}
                    >
                      {chatCleanupPending ? "Bereinige..." : "Legacy-Keys bereinigen"}
                    </button>
                    <button
                      type="button"
                      className="action-btn action-btn--primary"
                      disabled={chatSettingsPending || chatCleanupPending}
                      onClick={() => {
                        void onSaveChatSettings(chatDraft);
                      }}
                    >
                      Speichern
                    </button>
                  </div>
                </div>

                <span>Chattypische Voreinstellungen fuer Orchestrierung, Spezialistenlogik und Kontextbudget.</span>

                {chatCleanupStats ? (
                  <span>
                    Letzte Bereinigung: {chatCleanupStats.deletedCount} entfernt, {chatCleanupStats.matchedCount} gefunden,
                    {" "}
                    {chatCleanupStats.remainingCount} verbleibend.
                  </span>
                ) : null}

                <div className="model-profile-grid">
                  <label className="model-profile-field model-profile-field--toggle"><span>Plugin-Orchestrierung aktiv</span><input type="checkbox" checked={chatDraft.pluginOrchestrationEnabled} onChange={(event) => setChatDraft((current) => ({ ...current, pluginOrchestrationEnabled: event.target.checked }))} disabled={chatSettingsPending} /></label>
                  <label className="model-profile-field model-profile-field--toggle"><span>Auto-Spezialist aktiv</span><input type="checkbox" checked={chatDraft.autoSpecialistEnabled} onChange={(event) => setChatDraft((current) => ({ ...current, autoSpecialistEnabled: event.target.checked }))} disabled={chatSettingsPending} /></label>
                  <label className="model-profile-field"><span>Context Limit Tokens</span><input className="model-dir-input" type="number" min="512" step="1" value={chatDraft.contextLimitTokens} onChange={(event) => setChatDraft((current) => ({ ...current, contextLimitTokens: event.target.value }))} disabled={chatSettingsPending} /></label>
                  <label className="model-profile-field"><span>Safety Margin Tokens</span><input className="model-dir-input" type="number" min="0" step="1" value={chatDraft.contextSafetyMarginTokens} onChange={(event) => setChatDraft((current) => ({ ...current, contextSafetyMarginTokens: event.target.value }))} disabled={chatSettingsPending} /></label>
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

            {activeSettingsGroup === "Integrationen" ? (
              <article className="page-card model-settings-card">
                <div className="model-settings-card__header">
                  <strong>Integrationen</strong>
                  <div className="model-settings-card__actions">
                    <button
                      type="button"
                      className="action-btn"
                      disabled={integrationSettingsPending || integrationBatchTesting}
                      onClick={() => {
                        void runAllIntegrationKeyTests();
                      }}
                    >
                      {integrationBatchTesting ? "Teste alle..." : "Alle Keys testen"}
                    </button>
                    <button
                      type="button"
                      className="action-btn action-btn--primary"
                      disabled={integrationSettingsPending}
                      onClick={() => {
                        void onSaveIntegrationSettings(integrationDraft);
                      }}
                    >
                      Speichern
                    </button>
                  </div>
                </div>

                <span>API-Schluessel sind gruppiert, einklappbar und werden in den Settings in der Datenbank gespeichert.</span>
                <span>Anzeigeart fuer Gruppen (Inline oder Popup) stellst du unter Einstellungen / Darstellung um.</span>

                {Object.keys(integrationBatchResults).length > 0 ? (
                  <div className="model-settings-list">
                    <article className="page-card">
                      <strong>Re-Validation Ergebnis</strong>
                      <span>
                        {(() => {
                          const entries = testableIntegrationKeyOrder
                            .map((key) => integrationBatchResults[key])
                            .filter((entry): entry is IntegrationBatchResult => Boolean(entry));
                          const okCount = entries.filter((entry) => entry.status === "ok").length;
                          const errorCount = entries.filter((entry) => entry.status === "error").length;
                          const skippedCount = entries.filter((entry) => entry.status === "skipped").length;
                          return `${okCount} OK, ${errorCount} Fehler, ${skippedCount} uebersprungen`;
                        })()}
                      </span>
                      <div className="model-settings-list">
                        {testableIntegrationKeyOrder.map((key) => {
                          const item = integrationBatchResults[key];
                          if (!item) {
                            return null;
                          }
                          const statusLabel = item.status === "ok" ? "OK" : item.status === "error" ? "Fehler" : "uebersprungen";
                          const testedAtLabel = item.testedAt
                            ? new Date(item.testedAt).toLocaleString("de-DE", {
                              dateStyle: "short",
                              timeStyle: "medium",
                            })
                            : "-";
                          return (
                            <div key={key} className="model-settings-row">
                              <div>
                                <strong>{integrationTestableKeyLabels[key]}</strong>
                                <span>{item.message}</span>
                                <span>Zuletzt getestet: {testedAtLabel}</span>
                                <span>Dauer: {formatDurationMs(item.durationMs)}</span>
                              </div>
                              <div className="model-settings-controls">
                                <span>{statusLabel}</span>
                                <button
                                  type="button"
                                  className="action-btn"
                                  disabled={integrationSettingsPending || integrationBatchTesting}
                                  onClick={() => {
                                    void (async () => {
                                      const startedAt = performance.now();
                                      const result = await applySingleIntegrationKeyTest(key, integrationDraft);
                                      const durationMs = performance.now() - startedAt;
                                      const testedAt = new Date().toISOString();
                                      const next: IntegrationBatchResult = result.skipped
                                        ? {
                                          status: "skipped",
                                          message: "Key fehlt",
                                          testedAt,
                                          durationMs,
                                        }
                                        : result.success
                                          ? {
                                            status: "ok",
                                            message: `OK (${result.provider})`,
                                            testedAt,
                                            durationMs,
                                          }
                                          : {
                                            status: "error",
                                            message: result.error ?? "Provider-Test fehlgeschlagen.",
                                            testedAt,
                                            durationMs,
                                          };

                                      commitIntegrationBatchResults({
                                        ...integrationBatchResults,
                                        [key]: next,
                                      });
                                    })();
                                  }}
                                >
                                  Erneut testen
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </article>
                  </div>
                ) : null}

                <div className="model-settings-tabbar integration-tabbar">
                  {integrationTabs.map((tab) => (
                    <button
                      key={tab.id}
                      type="button"
                      className={`section-chip ${activeIntegrationTab === tab.id ? "section-chip--active" : ""}`}
                      onClick={() => setActiveIntegrationTab(tab.id)}
                      disabled={integrationSettingsPending}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                <div className="model-settings-list integration-groups-list">
                  {integrationDisplayMode === "inline"
                    ? (integrationGroupsByTab[activeIntegrationTab] ?? []).map((group) => {
                        const stateKey = `${activeIntegrationTab}:${group.id}`;
                        const isCollapsed = collapsedIntegrationGroups[stateKey] ?? false;
                        return (
                          <article
                            key={stateKey}
                            className={`model-group-card integration-group-card ${isCollapsed ? "model-group-card--collapsed" : ""}`}
                          >
                            <button
                              type="button"
                              className="model-group-toggle"
                              onClick={() => {
                                setCollapsedIntegrationGroups((current) => ({
                                  ...current,
                                  [stateKey]: !(current[stateKey] ?? false),
                                }));
                              }}
                            >
                              <span>{group.title}</span>
                              <span className="model-group-toggle__meta">{isCollapsed ? "Aufklappen" : "Einklappen"}</span>
                            </button>

                            {!isCollapsed ? renderIntegrationGroupFields(group) : null}
                          </article>
                        );
                      })
                    : (
                        <div className="settings-plugin-grid integration-group-tile-grid" role="list" aria-label="Integrationsgruppen">
                          {(integrationGroupsByTab[activeIntegrationTab] ?? []).map((group) => (
                            <button
                              key={`integration-group-tile:${activeIntegrationTab}:${group.id}`}
                              type="button"
                              role="listitem"
                              className="settings-nav-item settings-nav-item--card integration-group-tile"
                              onClick={() => {
                                setIntegrationGroupPopup({ tabId: activeIntegrationTab, groupId: group.id });
                              }}
                            >
                              <div className="settings-nav-item__lead">
                                <span className="settings-nav-item__icon" aria-hidden="true">📄</span>
                                <strong>{group.title}</strong>
                              </div>
                              <span>{group.fields.length} Felder in dieser Gruppe.</span>
                              <span className="settings-nav-item__hint">Kachel oeffnet die komplette Feldansicht als Popup.</span>
                            </button>
                          ))}
                        </div>
                      )}
                </div>

                {integrationDisplayMode === "popup" && integrationPopupGroup ? (
                  <div
                    className="plugin-popup-overlay"
                    role="dialog"
                    aria-modal="true"
                    aria-label="Integrationsgruppe"
                    onClick={() => setIntegrationGroupPopup(null)}
                  >
                    <div className="plugin-popup" onClick={(event) => event.stopPropagation()}>
                      <div className="plugin-popup__header">
                        <div>
                          <strong>{integrationPopupGroup.title}</strong>
                          <span>{integrationPopupGroup.fields.length} Felder</span>
                        </div>
                        <div className="model-settings-card__actions">
                          <button type="button" className="ghost-btn" onClick={() => setIntegrationGroupPopup(null)}>
                            Schliessen
                          </button>
                        </div>
                      </div>
                      <div className="plugin-popup__body">
                        <article className="page-card model-settings-card">
                          {renderIntegrationGroupFields(integrationPopupGroup)}
                        </article>
                      </div>
                    </div>
                  </div>
                ) : null}
              </article>
            ) : null}

            {activeSettingsGroup === "Plugins" ? (
              <div className="workspace-stack">
                {configurablePluginDescriptors.length === 0 ? (
                  <article className="page-card model-settings-card">
                    <span>Keine Plugins mit konfigurierbaren Feldern gefunden.</span>
                  </article>
                ) : (
                  <div className="settings-plugin-grid settings-plugin-category-grid" role="list" aria-label="Plugin-Kategorien">
                    {pluginCategoryGroups.map((group) => {
                      const totalFields = group.plugins.reduce((sum, plugin) => sum + (plugin.settings_fields ?? []).length, 0);
                      const keyRequiredCount = group.plugins.filter((plugin) => plugin.api_key_required).length;
                      return (
                        <button
                          key={group.category}
                          type="button"
                          role="listitem"
                          className="settings-nav-item settings-nav-item--card plugin-category-tile"
                          onClick={() => {
                            setPluginCategoryOpenStates((current) => ({
                              ...current,
                              [group.category]: true,
                            }));
                            setSettingsPluginCategoryPopup(group.category);
                          }}
                        >
                          <div className="settings-nav-item__lead">
                            <span className="settings-nav-item__icon" aria-hidden="true">{resolvePluginCategoryIcon(group.category, symbolProfile)}</span>
                            <strong>{group.category}</strong>
                          </div>
                          <span>{buildPluginCategoryExpectation(group.plugins)}</span>
                          <div className="model-settings-meta settings-plugin-card__meta">
                            <span>{group.plugins.length} Plugins</span>
                            <span>{totalFields} Felder</span>
                            <span>{keyRequiredCount} mit API-Key</span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            ) : null}

            {settingsPopupCategoryGroup ? (
              <div
                className="plugin-popup-overlay"
                role="dialog"
                aria-modal="true"
                aria-label="Plugin-Kategorie"
                onClick={() => setSettingsPluginCategoryPopup(null)}
              >
                <div
                  className="plugin-popup"
                  onClick={(event) => {
                    event.stopPropagation();
                  }}
                >
                  <div className="plugin-popup__header">
                    <div>
                      <strong>{settingsPopupCategoryGroup.category}</strong>
                      <span>{settingsPopupCategoryGroup.plugins.length} Plugins in dieser Kategorie</span>
                    </div>
                    <div className="model-settings-card__actions">
                      <button type="button" className="ghost-btn" onClick={() => setSettingsPluginCategoryPopup(null)}>Schliessen</button>
                    </div>
                  </div>
                  <div className="plugin-popup__body">
                    <div className="settings-plugin-grid">
                      {settingsPopupCategoryGroup.plugins.map((plugin) => {
                        const fields = plugin.settings_fields ?? [];
                        const pluginName = plugin.name || plugin.id;
                        const logo = resolvePluginWidgetLogo(plugin.id);
                        const requiredFieldCount = fields.filter((field) => field.required).length;
                        const groupCount = new Set(fields.map((field) => field.group?.trim() || "Allgemein")).size;
                        const firstGroupName = fields[0]?.group?.trim() || "Allgemein";

                        return (
                          <article className="page-card plugin-widget-card settings-plugin-card settings-plugin-card--expanded" key={`${settingsPopupCategoryGroup.category}:${plugin.id}`}>
                            <div className="plugin-widget-card__head">
                              <div className="plugin-widget-card__logo" aria-hidden="true">
                                {logo ? (
                                  <img src={logo} alt="" className="plugin-widget-card__logo-image" />
                                ) : (
                                  <span>{pluginName.slice(0, 1).toUpperCase()}</span>
                                )}
                              </div>
                              <div className="plugin-widget-card__title">
                                <strong>{pluginName}</strong>
                                <span>{plugin.category || "Allgemein"}</span>
                              </div>
                            </div>
                            <span>{plugin.description || `Konfiguration fuer ${plugin.id}`}</span>
                            <span className="settings-plugin-card__expectation">
                              Hinter dieser Kachel: {groupCount} Gruppen mit {fields.length} Feldern. Erste Gruppe: {firstGroupName}.
                            </span>
                            <div className="model-settings-meta settings-plugin-card__meta">
                              <span>{fields.length} Felder</span>
                              <span>{groupCount} Gruppen</span>
                              <span>{requiredFieldCount} Pflichtfelder</span>
                              <span>{plugin.api_key_required ? "API-Key erforderlich" : "Keine Pflicht-Integration"}</span>
                            </div>
                            <div className="model-settings-card__actions plugin-widget-card__actions">
                              <button
                                type="button"
                                className="ghost-btn"
                                onClick={() => {
                                  setPluginSoloSelectedId(plugin.id);
                                  setSettingsPluginCategoryPopup(null);
                                  setSettingsPluginGroupPopup({
                                    pluginId: plugin.id,
                                    groupName: firstGroupName,
                                  });
                                }}
                              >
                                Gruppen anzeigen
                              </button>
                              <button
                                type="button"
                                className="ghost-btn"
                                onClick={() => {
                                  setSettingsPluginCategoryPopup(null);
                                  openPluginPopupForTab(plugin.id, "frontend");
                                }}
                              >
                                Frontend
                              </button>
                              <button
                                type="button"
                                className="ghost-btn"
                                onClick={() => {
                                  setSettingsPluginCategoryPopup(null);
                                  openPluginPopupForTab(plugin.id, "settings");
                                }}
                              >
                                Plugin oeffnen
                              </button>
                              <button
                                type="button"
                                className="action-btn action-btn--primary"
                                disabled={savingPluginId === plugin.id}
                                onClick={() => {
                                  void onSavePluginSettings(plugin.id);
                                }}
                              >
                                {savingPluginId === plugin.id ? "Speichere..." : "Speichern"}
                              </button>
                            </div>
                          </article>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            ) : null}

            {settingsPluginGroupPopup && settingsPopupPluginDescriptor ? (
              <div
                className="plugin-popup-overlay"
                role="dialog"
                aria-modal="true"
                aria-label="Plugin-Untergruppe"
                onClick={() => setSettingsPluginGroupPopup(null)}
              >
                <div
                  className="plugin-popup"
                  onClick={(event) => {
                    event.stopPropagation();
                  }}
                >
                  <div className="plugin-popup__header">
                    <div>
                      <strong>
                        {settingsPopupPluginDescriptor.name || settingsPopupPluginDescriptor.id} · {settingsPluginGroupPopup.groupName}
                      </strong>
                      <span>{settingsPopupGroupFields.length} Felder in dieser Untergruppe</span>
                    </div>
                    <div className="model-settings-card__actions">
                      <select
                        className="model-dir-input"
                        value={settingsPopupPluginDescriptor.id}
                        onChange={(event) => {
                          const nextPlugin = configurablePluginDescriptors.find((plugin) => plugin.id === event.target.value);
                          if (!nextPlugin) {
                            return;
                          }
                          const nextGroupName = nextPlugin.settings_fields?.[0]?.group?.trim() || "Allgemein";
                          setPluginSoloSelectedId(nextPlugin.id);
                          setSettingsPluginGroupPopup({ pluginId: nextPlugin.id, groupName: nextGroupName });
                        }}
                      >
                        {configurablePluginDescriptors.map((plugin) => (
                          <option key={`settings-popup-plugin:${plugin.id}`} value={plugin.id}>{plugin.name || plugin.id}</option>
                        ))}
                      </select>
                      <select
                        className="model-dir-input"
                        value={settingsPluginGroupPopup.groupName}
                        onChange={(event) => {
                          setSettingsPluginGroupPopup({
                            pluginId: settingsPopupPluginDescriptor.id,
                            groupName: event.target.value,
                          });
                        }}
                      >
                        {settingsPopupPluginGroupNames.map((groupName) => (
                          <option key={`settings-popup-group:${settingsPopupPluginDescriptor.id}:${groupName}`} value={groupName}>{groupName}</option>
                        ))}
                      </select>
                      <button
                        type="button"
                        className="action-btn action-btn--primary"
                        disabled={savingPluginId === settingsPopupPluginDescriptor.id}
                        onClick={() => {
                          void onSavePluginSettings(settingsPopupPluginDescriptor.id);
                        }}
                      >
                        {savingPluginId === settingsPopupPluginDescriptor.id ? "Speichere..." : "Speichern"}
                      </button>
                      <button type="button" className="ghost-btn" onClick={() => setSettingsPluginGroupPopup(null)}>Schliessen</button>
                    </div>
                  </div>
                  <div className="plugin-popup__body plugin-popup__body--deep">
                    <article className="page-card model-settings-card model-settings-card--deep">
                      <div className="settings-plugin-subgroup-grid" role="list" aria-label="Plugin-Untergruppen-Kacheln">
                        {settingsPopupPluginGroupNames.map((groupName) => {
                          const groupFields = settingsPopupPluginFields.filter(
                            (field) => (field.group?.trim() || "Allgemein") === groupName,
                          );
                          const isActiveGroup = settingsPluginGroupPopup.groupName === groupName;
                          const previewLabels = groupFields.slice(0, 2).map((field) => field.label);
                          return (
                            <button
                              key={`settings-popup-group-tile:${settingsPopupPluginDescriptor.id}:${groupName}`}
                              type="button"
                              role="listitem"
                              className={`settings-nav-item settings-nav-item--card settings-subgroup-tile ${isActiveGroup ? "settings-subgroup-tile--active" : ""}`}
                              onClick={() => {
                                setSettingsPluginGroupPopup({
                                  pluginId: settingsPopupPluginDescriptor.id,
                                  groupName,
                                });
                              }}
                            >
                              <div className="settings-nav-item__lead">
                                <span className="settings-nav-item__icon" aria-hidden="true">{resolvePluginGroupIcon(groupName, symbolProfile)}</span>
                                <strong>{groupName}</strong>
                              </div>
                              <span>{buildPluginGroupExpectation(groupName, groupFields)}</span>
                              <div className="model-settings-meta settings-plugin-card__meta settings-subgroup-tile__preview">
                                {previewLabels.map((label) => (
                                  <span key={`settings-popup-group-tile-preview:${settingsPopupPluginDescriptor.id}:${groupName}:${label}`}>{label}</span>
                                ))}
                                {groupFields.length > 2 ? <span>+ {groupFields.length - 2} weitere</span> : null}
                              </div>
                            </button>
                          );
                        })}
                      </div>
                      <div className="model-profile-grid">
                        {settingsPopupGroupFields.map((field) => {
                          const fallback =
                            field.default ?? (field.type === "boolean" ? false : field.type === "number" ? 0 : "");
                          const value = getPluginFieldValue(settingsPopupPluginDescriptor.id, field.key, field.type, fallback);
                          const fieldError = pluginSettingsErrors[settingsPopupPluginDescriptor.id]?.[field.key];
                          const dependencyHint = getPluginFieldDependencyHint(field, settingsPopupPluginFields);

                          if (field.type === "boolean") {
                            return (
                              <label
                                className={`model-profile-field ${fieldError ? "integration-field--error" : ""}`}
                                key={`${settingsPopupPluginDescriptor.id}:${field.key}`}
                              >
                                <span>
                                  {field.label}
                                  {field.required ? <strong className="plugin-field-required"> *</strong> : null}
                                </span>
                                <input
                                  type="checkbox"
                                  checked={value === true}
                                  onChange={(event) => onPluginSettingChange(settingsPopupPluginDescriptor.id, field.key, event.target.checked)}
                                  disabled={savingPluginId === settingsPopupPluginDescriptor.id}
                                />
                                {dependencyHint ? <small className="plugin-field-dependency-hint" aria-hidden="true">{dependencyHint}</small> : null}
                                {field.description ? <small className="integration-field-hint">{field.description}</small> : null}
                                {fieldError ? <small className="integration-field-hint integration-field-hint--error">{fieldError}</small> : null}
                              </label>
                            );
                          }

                          if (field.type === "select") {
                            const options = Array.isArray(field.options) ? field.options : [];
                            return (
                              <label
                                className={`model-profile-field ${fieldError ? "integration-field--error" : ""}`}
                                key={`${settingsPopupPluginDescriptor.id}:${field.key}`}
                              >
                                <span>
                                  {field.label}
                                  {field.required ? <strong className="plugin-field-required"> *</strong> : null}
                                </span>
                                <select
                                  className="model-dir-input"
                                  value={String(value ?? "")}
                                  onChange={(event) => {
                                    const selected = options.find((option) => String(option.value) === event.target.value);
                                    onPluginSettingChange(settingsPopupPluginDescriptor.id, field.key, selected ? selected.value : event.target.value);
                                  }}
                                  disabled={savingPluginId === settingsPopupPluginDescriptor.id}
                                >
                                  {options.map((option, index) => (
                                    <option key={`${settingsPopupPluginDescriptor.id}:${field.key}:option:${index}:${String(option.value)}`} value={String(option.value)}>
                                      {option.label}
                                    </option>
                                  ))}
                                </select>
                                {dependencyHint ? <small className="plugin-field-dependency-hint" aria-hidden="true">{dependencyHint}</small> : null}
                                {field.description ? <small className="integration-field-hint">{field.description}</small> : null}
                                {fieldError ? <small className="integration-field-hint integration-field-hint--error">{fieldError}</small> : null}
                              </label>
                            );
                          }

                          if (field.type === "text") {
                            return (
                              <label
                                className={`model-profile-field ${fieldError ? "integration-field--error" : ""}`}
                                key={`${settingsPopupPluginDescriptor.id}:${field.key}`}
                              >
                                <span>
                                  {field.label}
                                  {field.required ? <strong className="plugin-field-required"> *</strong> : null}
                                </span>
                                <textarea
                                  className="model-dir-input model-dir-textarea"
                                  value={String(value ?? "")}
                                  onChange={(event) => onPluginSettingChange(settingsPopupPluginDescriptor.id, field.key, event.target.value)}
                                  disabled={savingPluginId === settingsPopupPluginDescriptor.id}
                                />
                                {dependencyHint ? <small className="plugin-field-dependency-hint" aria-hidden="true">{dependencyHint}</small> : null}
                                {field.description ? <small className="integration-field-hint">{field.description}</small> : null}
                                {fieldError ? <small className="integration-field-hint integration-field-hint--error">{fieldError}</small> : null}
                              </label>
                            );
                          }

                          if (field.type === "password") {
                            return (
                              <label
                                className={`model-profile-field ${fieldError ? "integration-field--error" : ""}`}
                                key={`${settingsPopupPluginDescriptor.id}:${field.key}`}
                              >
                                <span>
                                  {field.label}
                                  {field.required ? <strong className="plugin-field-required"> *</strong> : null}
                                </span>
                                <input
                                  className="model-dir-input"
                                  type="password"
                                  autoComplete="new-password"
                                  value={String(value ?? "")}
                                  onChange={(event) => onPluginSettingChange(settingsPopupPluginDescriptor.id, field.key, event.target.value)}
                                  disabled={savingPluginId === settingsPopupPluginDescriptor.id}
                                />
                                {dependencyHint ? <small className="plugin-field-dependency-hint" aria-hidden="true">{dependencyHint}</small> : null}
                                {field.description ? <small className="integration-field-hint">{field.description}</small> : null}
                                {fieldError ? <small className="integration-field-hint integration-field-hint--error">{fieldError}</small> : null}
                              </label>
                            );
                          }

                          return (
                            <label
                              className={`model-profile-field ${fieldError ? "integration-field--error" : ""}`}
                              key={`${settingsPopupPluginDescriptor.id}:${field.key}`}
                            >
                              <span>
                                {field.label}
                                {field.required ? <strong className="plugin-field-required"> *</strong> : null}
                              </span>
                              <input
                                className="model-dir-input"
                                type={field.type === "number" ? "number" : "text"}
                                value={String(value ?? "")}
                                onChange={(event) => {
                                  if (field.type === "number") {
                                    const raw = event.target.value;
                                    onPluginSettingChange(settingsPopupPluginDescriptor.id, field.key, raw === "" ? "" : Number(raw));
                                    return;
                                  }
                                  onPluginSettingChange(settingsPopupPluginDescriptor.id, field.key, event.target.value);
                                }}
                                disabled={savingPluginId === settingsPopupPluginDescriptor.id}
                              />
                              {dependencyHint ? <small className="plugin-field-dependency-hint" aria-hidden="true">{dependencyHint}</small> : null}
                              {field.description ? <small className="integration-field-hint">{field.description}</small> : null}
                              {fieldError ? <small className="integration-field-hint integration-field-hint--error">{fieldError}</small> : null}
                            </label>
                          );
                        })}
                      </div>
                    </article>
                  </div>
                </div>
              </div>
            ) : null}

            {activeSettingsGroup === "Training" ? (
              <article className="page-card model-settings-card">
                <div className="model-settings-card__header">
                  <div className="training-title-block">
                    <strong>Training</strong>
                    <span>Datensätze vorbereiten, Modell weitertrainieren und Fortschritt prüfen.</span>
                  </div>
                  <div className="model-settings-card__actions">
                    {trainingWorkspaceTab === "overview" ? (
                      <button
                        type="button"
                        className="action-btn action-btn--primary"
                        disabled={trainingSettingsPending}
                        onClick={() => {
                          void onSaveTrainingSettings(trainingDraft);
                        }}
                      >
                        Einstellungen speichern
                      </button>
                    ) : (
                      <button type="button" className="ghost-btn" onClick={() => setTrainingWorkspaceTab("overview")}>
                        Zur Übersicht
                      </button>
                    )}
                  </div>
                </div>

                <div className="training-view-controls" role="group" aria-label="Trainingsansicht umschalten">
                  <button
                    type="button"
                    className={`section-chip ${trainingWorkspaceTab === "overview" ? "section-chip--active" : ""}`}
                    onClick={() => setTrainingWorkspaceTab("overview")}
                  >
                    1. Übersicht
                  </button>
                  <button
                    type="button"
                    className={`section-chip ${trainingWorkspaceTab === "import" ? "section-chip--active" : ""}`}
                    onClick={() => setTrainingWorkspaceTab("import")}
                  >
                    2. Daten importieren
                  </button>
                  <button
                    type="button"
                    className={`section-chip ${trainingWorkspaceTab === "datasets" ? "section-chip--active" : ""}`}
                    onClick={() => setTrainingWorkspaceTab("datasets")}
                  >
                    3. Datensätze
                  </button>
                  <button
                    type="button"
                    className={`section-chip ${trainingWorkspaceTab === "jobs" ? "section-chip--active" : ""}`}
                    onClick={() => setTrainingWorkspaceTab("jobs")}
                  >
                    4. Jobs & Fortschritt
                  </button>
                </div>

                {trainingWorkspaceTab === "overview" ? (
                  <div className="training-overview">
                <div className="training-status-grid" aria-label="Trainingsstatus">
                  <div className={`training-status-card ${trainingDraft.enabled ? "training-status-card--ok" : ""}`}>
                    <span>Training</span>
                    <strong>{trainingDraft.enabled ? "Aktiviert" : "Deaktiviert"}</strong>
                    <small>{trainingDraft.defaultTrainer || "Kein Trainer"}</small>
                  </div>
                  <div className="training-status-card">
                    <span>Fortlaufendes Modell</span>
                    <strong>{selectedContinualModel ? `#${selectedContinualModel.id}` : "Automatisch"}</strong>
                    <small>{selectedContinualModel?.name ?? "Wird beim ersten Lauf angelegt"}</small>
                  </div>
                  <div className="training-status-card">
                    <span>Bereite Datensätze</span>
                    <strong>{readyDatasetCount}</strong>
                    <small>{trainingDatasets.length - readyDatasetCount} archiviert</small>
                  </div>
                  <div className={`training-status-card ${activeTrainingJobsCount > 0 ? "training-status-card--busy" : ""}`}>
                    <span>Aktive Jobs</span>
                    <strong>{activeTrainingJobsCount}</strong>
                    <small>{activeTrainingJobsCount > 0 ? "Training läuft oder wartet" : "Queue ist frei"}</small>
                  </div>
                </div>
                <div className="training-batch-cta" aria-label="Training-Schnellstart">
                  <div className="training-batch-cta__copy">
                    <strong>Schnellstart</strong>
                    <span>
                      Speichert diese Einstellungen und trainiert danach alle noch nicht verarbeiteten vollständigen Ordner nacheinander.
                    </span>
                  </div>
                  <button
                    type="button"
                    className="action-btn action-btn--primary"
                    disabled={
                      trainingSettingsPending ||
                      trainingBatchPending ||
                      !trainingDraft.enabled ||
                      trainingDraft.baseModel.trim().length === 0
                    }
                    onClick={() => {
                      void onSaveTrainingSettings(trainingDraft).then(() => onBatchCreateTrainingJobs());
                    }}
                  >
                    {trainingBatchPending ? "Training wird eingereiht..." : "Alle neuen Ordner trainieren"}
                  </button>
                  <button
                    type="button"
                    className="action-btn"
                    disabled={
                      trainingSettingsPending ||
                      trainingBatchPending ||
                      !trainingDraft.enabled ||
                      trainingDraft.baseModel.trim().length === 0 ||
                      trainingDraft.projectId.length === 0
                    }
                    onClick={() => {
                      if (!window.confirm("Neuen Trainingszyklus wirklich direkt vom Basismodell starten? Alle vollständigen Ordner werden erneut gelernt.")) {
                        return;
                      }
                      void onSaveTrainingSettings(trainingDraft).then(() => onBatchCreateTrainingJobs(true));
                    }}
                  >
                    Neu vom Basismodell trainieren
                  </button>
                </div>

                <section className="training-config-section">
                  <div className="training-section-heading">
                    <div>
                      <strong>Grundeinstellungen</strong>
                      <span>Diese Auswahl genügt für den normalen Trainingsbetrieb.</span>
                    </div>
                    <button
                      type="button"
                      className="ghost-btn"
                      onClick={() => setShowTrainingAdvanced((current) => !current)}
                    >
                      {showTrainingAdvanced ? "Expertenmodus schließen" : "Expertenmodus öffnen"}
                    </button>
                  </div>
                <div className="model-profile-grid training-config-grid">
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
                    <span>Trainingsprofil</span>
                    <select
                      className="model-dir-input"
                      value={trainingDraft.trainingPreset}
                      onChange={(event) => applyTrainingPreset(event.target.value as TrainingSettingsDraft["trainingPreset"])}
                      disabled={trainingSettingsPending}
                    >
                      <option value="safe">Sicher – empfohlen für 12 GB VRAM</option>
                      <option value="balanced">Ausgewogen – mehr Lerndurchläufe</option>
                      <option value="intensive">Intensiv – langsam, höherer Speicherbedarf</option>
                      <option value="custom">Benutzerdefiniert</option>
                    </select>
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

                  <div className="training-model-summary">
                    <div>
                      <span>Ausgewähltes Basismodell</span>
                      <strong>{selectedConfiguredBaseModel?.name ?? (trainingDraft.baseModel || "Noch nicht festgelegt")}</strong>
                    </div>
                    {selectedConfiguredBaseModel ? (
                      <>
                        <span>{selectedConfiguredBaseModel.backend}</span>
                        <span>{selectedConfiguredBaseModel.loadStatus}</span>
                        <details className="training-details">
                          <summary>Modellpfad</summary>
                          <div className="training-file-map">{selectedConfiguredBaseModel.modelPath}</div>
                        </details>
                      </>
                    ) : null}
                  </div>

                  <label className="model-radio-wrap model-profile-toggle">
                    <input
                      type="checkbox"
                      checked={trainingDraft.continualTraining}
                      onChange={(event) => {
                        setTrainingDraft((current) => ({ ...current, continualTraining: event.target.checked }));
                      }}
                      disabled={trainingSettingsPending}
                    />
                    Ein Modell fortlaufend weitertrainieren
                  </label>

                  <label className="model-profile-field">
                    <span>Übergeordnetes Trainingsprojekt</span>
                    <select
                      className="model-dir-input"
                      value={trainingDraft.projectId}
                      onChange={(event) => setTrainingDraft((current) => ({ ...current, projectId: event.target.value }))}
                      disabled={trainingSettingsPending}
                    >
                      <option value="">Kein Projekt</option>
                      {projects.map((project) => (
                        <option key={project.id} value={project.id}>{project.name}</option>
                      ))}
                    </select>
                  </label>

                  <div className="model-profile-field training-project-actions">
                    <span>Projekt nachmelden oder übernehmen</span>
                    <div className="model-dir-add-row">
                      <input
                        className="model-dir-input"
                        value={newTrainingProjectName}
                        placeholder="z. B. Naturstein"
                        onChange={(event) => setNewTrainingProjectName(event.target.value)}
                        disabled={trainingSettingsPending}
                      />
                      <button
                        type="button"
                        className="ghost-btn"
                        disabled={newTrainingProjectName.trim().length === 0 || trainingSettingsPending}
                        onClick={() => {
                          const name = newTrainingProjectName.trim();
                          void onCreateProject(name).then((projectId) => {
                            if (typeof projectId === "number") {
                              setTrainingDraft((current) => ({ ...current, projectId: String(projectId) }));
                              setNewTrainingProjectName("");
                            }
                          });
                        }}
                      >
                        Projekt anlegen
                      </button>
                    </div>
                    <button
                      type="button"
                      className="ghost-btn"
                      disabled={trainingSettingsPending || trainingDraft.projectId.length === 0}
                      onClick={() => {
                        const projectId = Number(trainingDraft.projectId);
                        void onSaveTrainingSettings(trainingDraft).then(() => onAssignTrainingProject(projectId));
                      }}
                    >
                      Allen Datensätzen zuweisen (inkl. Archiv)
                    </button>
                  </div>

                  {!showTrainingAdvanced ? (
                    <div className="training-profile-summary">
                      <span>{trainingDraft.numTrainEpochs} Epoche(n) · LR {trainingDraft.learningRate} · Kontext {trainingDraft.maxSequenceLength}</span>
                      <span>LoRA r={trainingDraft.loraR}, α={trainingDraft.loraAlpha} · 4‑Bit {trainingDraft.loadIn4bit ? "aktiv" : "aus"}</span>
                      <span>Jobs werden {trainingDraft.archiveOnSuccess ? "nach Erfolg archiviert" : "nicht automatisch archiviert"}.</span>
                    </div>
                  ) : null}

                  {showTrainingAdvanced ? (
                    <>

                  <div className="training-subsection-title">
                    <strong>Ablauf und Speicherorte</strong>
                    <span>Queue, automatische Aktionen und Ablagepfade.</span>
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
                    <span>Max. parallele Jobs (fortlaufend immer 1)</span>
                    <input
                      className="model-dir-input"
                      type="number"
                      min="1"
                      step="1"
                      value={trainingDraft.maxConcurrentJobs}
                      onChange={(event) => {
                        setTrainingDraft((current) => ({ ...current, maxConcurrentJobs: event.target.value }));
                      }}
                      disabled={trainingSettingsPending || trainingDraft.continualTraining}
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
                      checked={trainingDraft.continualTraining || trainingDraft.autoRegisterModel}
                      onChange={(event) => {
                        setTrainingDraft((current) => ({ ...current, autoRegisterModel: event.target.checked }));
                      }}
                      disabled={trainingSettingsPending || trainingDraft.continualTraining}
                    />
                    Modell automatisch registrieren
                  </label>

                  <label className="model-radio-wrap model-profile-toggle">
                    <input
                      type="checkbox"
                      checked={trainingDraft.autoActivateModel}
                      onChange={(event) => setTrainingDraft((current) => ({ ...current, autoActivateModel: event.target.checked }))}
                      disabled={trainingSettingsPending}
                    />
                    Trainiertes Modell automatisch aktivieren
                  </label>

                  <label className="model-radio-wrap model-profile-toggle">
                    <input
                      type="checkbox"
                      checked={trainingDraft.archiveOnSuccess}
                      onChange={(event) => setTrainingDraft((current) => ({ ...current, archiveOnSuccess: event.target.checked }))}
                      disabled={trainingSettingsPending}
                    />
                    Erfolgreiche Jobs und Datasets archivieren
                  </label>

                  <label className="model-radio-wrap model-profile-toggle">
                    <input
                      type="checkbox"
                      checked={trainingDraft.deduplicateJobs}
                      onChange={(event) => setTrainingDraft((current) => ({ ...current, deduplicateJobs: event.target.checked }))}
                      disabled={trainingSettingsPending}
                    />
                    Doppeltes Training verhindern
                  </label>

                  <label className="model-profile-field">
                    <span>Fortlaufendes Modell</span>
                    <select
                      className="model-dir-input"
                      value={trainingDraft.continualModelId}
                      onChange={(event) => setTrainingDraft((current) => ({ ...current, continualModelId: event.target.value }))}
                      disabled={trainingSettingsPending || !trainingDraft.continualTraining}
                    >
                      <option value="">Beim ersten Training automatisch anlegen</option>
                      {modelEntries.filter((model) => model.backend === "transformers_peft").map((model) => (
                        <option key={`continual-${model.id}`} value={model.id}>#{model.id} {model.name}</option>
                      ))}
                    </select>
                  </label>

                  <div className="training-subsection-title">
                    <strong>Hyperparameter</strong>
                    <span>Nur ändern, wenn das gewählte Profil bewusst angepasst werden soll.</span>
                  </div>

                  {([
                    ["numTrainEpochs", "Epochen", "0.1", "20", "0.1"],
                    ["learningRate", "Lernrate", "0.0000001", "1", "0.00001"],
                    ["batchSize", "Batch-Größe pro Gerät", "1", "64", "1"],
                    ["gradientAccumulationSteps", "Gradienten-Akkumulation", "1", "256", "1"],
                    ["maxSequenceLength", "Max. Sequenzlänge", "128", "32768", "128"],
                    ["loraR", "LoRA-Rang (r)", "1", "1024", "1"],
                    ["loraAlpha", "LoRA Alpha", "1", "4096", "1"],
                    ["loraDropout", "LoRA Dropout", "0", "0.8", "0.01"],
                    ["warmupRatio", "Warmup-Ratio", "0", "0.5", "0.01"],
                    ["weightDecay", "Weight Decay", "0", "1", "0.01"],
                    ["evalSteps", "Evaluation alle Schritte", "1", "1000000", "1"],
                    ["saveSteps", "Checkpoint alle Schritte", "10", "1000000", "1"],
                    ["loggingSteps", "Logging alle Schritte", "1", "1000000", "1"],
                    ["maxSteps", "Max. Schritte (0 = automatisch)", "0", "10000000", "1"],
                    ["validationSplit", "Validierungsanteil", "0.02", "0.3", "0.01"],
                    ["seed", "Zufalls-Seed", "0", "2147483647", "1"],
                  ] as const).map(([key, label, min, max, step]) => (
                    <label className="model-profile-field" key={key}>
                      <span>{label}</span>
                      <input
                        className="model-dir-input"
                        type="number"
                        min={min}
                        max={max}
                        step={step}
                        value={trainingDraft[key]}
                        onChange={(event) => updateAdvancedTraining({ [key]: event.target.value })}
                        disabled={trainingSettingsPending}
                      />
                    </label>
                  ))}

                  <div className="training-subsection-title">
                    <strong>Adapter und Protokollierung</strong>
                    <span>Zielmodule, Quantisierung und erste Logausgabe.</span>
                  </div>

                  <label className="model-profile-field">
                    <span>LoRA-Zielmodule (kommagetrennt)</span>
                    <input
                      className="model-dir-input"
                      type="text"
                      value={trainingDraft.targetModules}
                      onChange={(event) => updateAdvancedTraining({ targetModules: event.target.value })}
                      disabled={trainingSettingsPending}
                    />
                  </label>

                  <label className="model-radio-wrap model-profile-toggle">
                    <input
                      type="checkbox"
                      checked={trainingDraft.loadIn4bit}
                      onChange={(event) => updateAdvancedTraining({ loadIn4bit: event.target.checked })}
                      disabled={trainingSettingsPending}
                    />
                    Basismodell in 4‑Bit laden
                  </label>

                  <label className="model-radio-wrap model-profile-toggle">
                    <input
                      type="checkbox"
                      checked={trainingDraft.loggingFirstStep}
                      onChange={(event) => updateAdvancedTraining({ loggingFirstStep: event.target.checked })}
                      disabled={trainingSettingsPending}
                    />
                    Ersten Trainingsschritt protokollieren
                  </label>

                  <label className="model-radio-wrap model-profile-toggle">
                    <input
                      type="checkbox"
                      checked={trainingDraft.loadBestModelAtEnd}
                      onChange={(event) => updateAdvancedTraining({ loadBestModelAtEnd: event.target.checked })}
                      disabled={trainingSettingsPending}
                    />
                    Bestes Modell am Ende laden
                  </label>

                  <label className="model-radio-wrap model-profile-toggle">
                    <input
                      type="checkbox"
                      checked={trainingDraft.greaterIsBetter}
                      onChange={(event) => updateAdvancedTraining({ greaterIsBetter: event.target.checked })}
                      disabled={trainingSettingsPending}
                    />
                    Metrik steigt (statt faellt)
                  </label>

                  <label className="model-profile-field">
                    <span>Best-Model-Metrik</span>
                    <input
                      className="model-dir-input"
                      type="text"
                      value={trainingDraft.metricForBestModel}
                      onChange={(event) => updateAdvancedTraining({ metricForBestModel: event.target.value })}
                      disabled={trainingSettingsPending}
                    />
                  </label>
                    </>
                  ) : null}
                </div>
                </section>
                  </div>
                ) : null}

                {trainingWorkspaceTab === "import" ? (
                  <div className="training-panel">
                    <div className="model-settings-card__header">
                      <div className="training-title-block">
                        <strong>Daten importieren</strong>
                        <span>Dateien aus dem Trainingsordner registrieren, hochladen oder per URL übernehmen.</span>
                      </div>
                    </div>

                    <div className="training-inline-heading">
                      <strong>Neuen Datensatz vorbereiten</strong>
                      <span>Name und optionale Projektzuordnung gelten für die folgenden Importwege.</span>
                    </div>
                    <div className="model-dir-add-row">
                  <input
                    className="model-dir-input"
                    type="text"
                    placeholder="Neues Dataset (optional bei ZIP/URL)"
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
                    disabled={trainingSettingsPending}
                    onClick={() => {
                      const projectId = newDatasetProjectId.trim().length > 0 ? Number(newDatasetProjectId) : null;
                      const datasetName = resolveDatasetName([uploadBundleFile?.name, datasetSourceUrl, existingTrainingFile, existingDatasetSourceFile]);
                      void onCreateTrainingDataset(datasetName, Number.isInteger(projectId) ? projectId : null).then(() => {
                        setNewDatasetName("");
                      });
                    }}
                  >
                    Leeres Dataset anlegen
                  </button>
                    </div>

                    <div className="model-settings-card__header">
                      <strong>1) Aus Ordner registrieren</strong>
                    </div>

                    <div className="model-dir-add-row">
                  <select
                    className="model-dir-input"
                    value={existingDatasetSourceFile}
                    onChange={(event) => setExistingDatasetSourceFile(event.target.value)}
                    disabled={trainingSettingsPending}
                    aria-label="Source-Datei aus Trainingsordner"
                  >
                    <option value="">Optionale Source-Datei</option>
                    {visibleDatasetFiles.map((file) => (
                      <option key={`source-${file.relativePath}`} value={file.relativePath}>
                        {file.relativePath}{file.isRegistered ? " (bereits registriert)" : ""}
                      </option>
                    ))}
                  </select>
                  <select
                    className="model-dir-input"
                    value={existingTrainingFile}
                    onChange={(event) => setExistingTrainingFile(event.target.value)}
                    disabled={trainingSettingsPending}
                    aria-label="Training-Datei aus Ordner"
                  >
                    <option value="">Optionale Training-Datei</option>
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
                    disabled={
                      trainingSettingsPending ||
                      (existingDatasetSourceFile.trim().length === 0 && existingTrainingFile.trim().length === 0)
                    }
                    onClick={() => {
                      const projectId = newDatasetProjectId.trim().length > 0 ? Number(newDatasetProjectId) : null;
                      const datasetName = resolveDatasetName([existingTrainingFile, existingDatasetSourceFile, existingValidationFile]);
                      const files: Partial<Record<"source" | "training" | "validation" | "test" | "manifest", string>> = {};
                      if (existingDatasetSourceFile.trim().length > 0) {
                        files.source = existingDatasetSourceFile;
                      }
                      if (existingTrainingFile.trim().length > 0) {
                        files.training = existingTrainingFile;
                      }
                      if (existingValidationFile.trim().length > 0) {
                        files.validation = existingValidationFile;
                      }
                      if (existingTestFile.trim().length > 0) {
                        files.test = existingTestFile;
                      }
                      if (existingManifestFile.trim().length > 0) {
                        files.manifest = existingManifestFile;
                      }
                      void onRegisterTrainingDatasetFile(
                        datasetName,
                        files,
                        Number.isInteger(projectId) ? projectId : null,
                      );
                    }}
                  >
                    Ordnerdateien registrieren
                  </button>
                    </div>

                    <div className="model-dir-add-row">
                  <select
                    className="model-dir-input"
                    value={existingTestFile}
                    onChange={(event) => setExistingTestFile(event.target.value)}
                    disabled={trainingSettingsPending}
                    aria-label="Testdatei aus Ordner"
                  >
                    <option value="">Optionale Testdatei</option>
                    {visibleDatasetFiles.map((file) => (
                      <option key={`test-${file.relativePath}`} value={file.relativePath}>
                        {file.relativePath}{file.isRegistered ? " (bereits registriert)" : ""}
                      </option>
                    ))}
                  </select>
                  <select
                    className="model-dir-input"
                    value={existingManifestFile}
                    onChange={(event) => setExistingManifestFile(event.target.value)}
                    disabled={trainingSettingsPending}
                    aria-label="Manifestdatei aus Ordner"
                  >
                    <option value="">Optionale Manifestdatei (.json)</option>
                    {visibleDatasetFiles.map((file) => (
                      <option key={`manifest-${file.relativePath}`} value={file.relativePath}>
                        {file.relativePath}{file.isRegistered ? " (bereits registriert)" : ""}
                      </option>
                    ))}
                  </select>
                    </div>

                    <div className="model-settings-card__header">
                      <strong>2) Rollen-Dateien hochladen</strong>
                    </div>

                    <div className="model-dir-add-row">
                  <input
                    className="model-dir-input"
                    type="file"
                    accept=".jsonl,.json,.csv,.md,.markdown,.txt,.yaml,.yml,.xml,.html,.htm,.pdf,.docx"
                    onChange={(event) => setUploadDatasetSourceFile(event.target.files?.[0] ?? null)}
                    disabled={trainingSettingsPending}
                  />
                  <input
                    className="model-dir-input"
                    type="file"
                    accept=".jsonl,.json,.csv,.md,.markdown,.txt,.yaml,.yml,.xml,.html,.htm,.pdf,.docx"
                    onChange={(event) => setUploadTrainingFile(event.target.files?.[0] ?? null)}
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
                    disabled={
                      trainingSettingsPending ||
                      (uploadDatasetSourceFile == null && uploadTrainingFile == null)
                    }
                    onClick={() => {
                      const projectId = newDatasetProjectId.trim().length > 0 ? Number(newDatasetProjectId) : null;
                      if (uploadDatasetSourceFile == null && uploadTrainingFile == null) {
                        return;
                      }
                      const datasetName = resolveDatasetName([
                        uploadTrainingFile?.name,
                        uploadDatasetSourceFile?.name,
                        uploadValidationFile?.name,
                        uploadTestFile?.name,
                      ]);
                      const files: Partial<Record<"source" | "training" | "validation" | "test" | "manifest", File | null>> = {
                        source: uploadDatasetSourceFile,
                        training: uploadTrainingFile,
                        validation: uploadValidationFile,
                        test: uploadTestFile,
                        manifest: uploadManifestFile,
                      };
                      void onUploadTrainingDataset(
                        datasetName,
                        files,
                        Number.isInteger(projectId) ? projectId : null,
                      ).then(() => {
                        setUploadDatasetSourceFile(null);
                        setUploadTrainingFile(null);
                        setUploadValidationFile(null);
                        setUploadTestFile(null);
                        setUploadManifestFile(null);
                      });
                    }}
                  >
                    Rollen-Dateien hochladen
                  </button>
                    </div>

                    <div className="model-dir-add-row">
                  <input
                    className="model-dir-input"
                    type="file"
                    accept=".jsonl,.json,.csv,.md,.markdown,.txt,.yaml,.yml,.xml,.html,.htm,.pdf,.docx"
                    onChange={(event) => setUploadTestFile(event.target.files?.[0] ?? null)}
                    disabled={trainingSettingsPending}
                  />
                  <input
                    className="model-dir-input"
                    type="file"
                    accept=".json"
                    onChange={(event) => setUploadManifestFile(event.target.files?.[0] ?? null)}
                    disabled={trainingSettingsPending}
                  />
                    </div>

                    <div className="model-settings-card__header">
                      <strong>3) ZIP-Bundle importieren</strong>
                    </div>

                    <div className="model-dir-add-row">
                  <input
                    className="model-dir-input"
                    type="file"
                    accept=".zip"
                    onChange={(event) => setUploadBundleFile(event.target.files?.[0] ?? null)}
                    disabled={trainingSettingsPending}
                  />
                  <button
                    type="button"
                    className="action-btn"
                    disabled={trainingSettingsPending || uploadBundleFile == null}
                    onClick={() => {
                      const projectId = newDatasetProjectId.trim().length > 0 ? Number(newDatasetProjectId) : null;
                      if (uploadBundleFile == null) {
                        return;
                      }
                      const datasetName = resolveDatasetName([uploadBundleFile.name]);
                      void onUploadTrainingDatasetBundle(
                        datasetName,
                        uploadBundleFile,
                        Number.isInteger(projectId) ? projectId : null,
                      ).then(() => setUploadBundleFile(null));
                    }}
                  >
                    ZIP importieren
                  </button>
                    </div>

                    <div className="model-settings-card__header">
                      <strong>4) URL als Training verwenden (z. B. Wikipedia)</strong>
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
                  <input
                    className="model-dir-input"
                    type="url"
                    placeholder="Optionale Testdatei URL"
                    value={datasetTestUrl}
                    onChange={(event) => setDatasetTestUrl(event.target.value)}
                    disabled={trainingSettingsPending}
                  />
                  <button
                    type="button"
                    className="action-btn"
                    disabled={trainingSettingsPending || datasetSourceUrl.trim().length === 0}
                    onClick={() => {
                      const projectId = newDatasetProjectId.trim().length > 0 ? Number(newDatasetProjectId) : null;
                      const datasetName = resolveDatasetName([deriveDatasetNameFromUrl(datasetSourceUrl)]);
                      void onImportTrainingDatasetFromUrl(
                        datasetName,
                        {
                          source: datasetSourceUrl.trim(),
                          validation: datasetValidationUrl.trim().length > 0 ? datasetValidationUrl.trim() : undefined,
                          test: datasetTestUrl.trim().length > 0 ? datasetTestUrl.trim() : undefined,
                        },
                        Number.isInteger(projectId) ? projectId : null,
                      );
                    }}
                  >
                    URL importieren
                  </button>
                    </div>
                  </div>
                ) : null}

                {trainingWorkspaceTab === "datasets" ? (
                  <div className="training-panel">
                    <div className="model-settings-card__header">
                      <div className="training-title-block">
                        <strong>Datensätze verwalten</strong>
                        <span>{visibleDatasets.length} in dieser Ansicht · {visibleDatasetFiles.length} Dateien im Trainingsordner</span>
                      </div>
                      <button type="button" className="ghost-btn" onClick={() => setShowRawTrainingFiles((current) => !current)}>
                        {showRawTrainingFiles ? "Rohdateien ausblenden" : "Rohdateien anzeigen"}
                      </button>
                    </div>

                    {showRawTrainingFiles ? (
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
                    ) : null}

                    <div className="model-settings-card__header">
                      <strong>Registrierte Datensätze</strong>
                      <div className="model-settings-controls">
                        <button
                          type="button"
                          className={`section-chip ${datasetViewMode === "active" ? "section-chip--active" : ""}`}
                          onClick={() => setDatasetViewMode("active")}
                        >
                          Aktiv
                        </button>
                        <button
                          type="button"
                          className={`section-chip ${datasetViewMode === "archived" ? "section-chip--active" : ""}`}
                          onClick={() => setDatasetViewMode("archived")}
                        >
                          Archiv
                        </button>
                      </div>
                    </div>

                    <div className="model-settings-list">
                  {visibleDatasets.map((dataset) => (
                    <div key={dataset.id} className="model-settings-row">
                      <div>
                        <strong>
                          #{dataset.id} {dataset.name}
                        </strong>
                        <div className="model-settings-meta">
                          <span>Status: {dataset.status}</span>
                          <span>Version: {dataset.version}</span>
                          <span>Quelle: {dataset.sourceType}</span>
                        </div>
                        <details className="training-details">
                          <summary>Dateizuordnung anzeigen</summary>
                          <div className="training-file-map">
                            <span>Source: {String(dataset.metadata.source_path ?? "-")}</span>
                            <span>Validation: {String(dataset.metadata.validation_source_path ?? "-")}</span>
                            <span>Test: {String(dataset.metadata.test_source_path ?? "-")}</span>
                            <span>
                            Rollen: {(() => {
                              const files = dataset.metadata.files;
                              if (typeof files !== "object" || files == null) {
                                return "-";
                              }
                              const entries = Object.entries(files as Record<string, unknown>)
                                .filter((entry): entry is [string, string] => typeof entry[1] === "string" && entry[1].length > 0)
                                .map(([role, filePath]) => `${role}=${filePath}`);
                              return entries.length > 0 ? entries.join(" | ") : "-";
                            })()}
                            </span>
                          </div>
                        </details>
                      </div>
                      <div className="model-settings-controls">
                        {dataset.status === "archived" ? (
                          <button
                            type="button"
                            className="ghost-btn"
                            onClick={() => {
                              void onUnarchiveTrainingDataset(dataset.id);
                            }}
                          >
                            Wiederherstellen
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="ghost-btn"
                            onClick={() => {
                              void onArchiveTrainingDataset(dataset.id);
                            }}
                          >
                            Archivieren
                          </button>
                        )}
                        <button
                          type="button"
                          className="action-btn action-btn--danger"
                          onClick={() => {
                            void onDeleteTrainingDataset(dataset.id);
                          }}
                        >
                          Loeschen
                        </button>
                      </div>
                    </div>
                  ))}
                  {visibleDatasets.length === 0 ? <span>Keine Datasets in dieser Ansicht vorhanden.</span> : null}
                    </div>
                  </div>
                ) : null}

                {trainingWorkspaceTab === "jobs" ? (
                  <div className="training-panel">
                    <div className="model-settings-card__header">
                      <strong>Training-Jobs</strong>
                      <div className="model-settings-controls">
                        <button
                          type="button"
                          className={`section-chip ${jobViewMode === "active" ? "section-chip--active" : ""}`}
                          onClick={() => setJobViewMode("active")}
                        >
                          Aktiv
                        </button>
                        <button
                          type="button"
                          className={`section-chip ${jobViewMode === "archived" ? "section-chip--active" : ""}`}
                          onClick={() => setJobViewMode("archived")}
                        >
                          Archiv
                        </button>
                      </div>
                    </div>

                    <div className="training-inline-heading">
                      <strong>Einzeljob starten</strong>
                      <span>Datensatz auswählen, optional prüfen und anschließend in die Queue stellen.</span>
                    </div>
                    <div className="model-dir-add-row training-job-create">
                  <select
                    className="model-dir-input"
                    aria-label="Dataset fuer neuen Training-Job"
                    title="Dataset fuer neuen Training-Job"
                    value={newJobDatasetId}
                    onChange={(event) => setNewJobDatasetId(event.target.value)}
                    disabled={trainingSettingsPending}
                  >
                    <option value="">Dataset waehlen</option>
                    {trainingDatasets.filter((dataset) => dataset.status !== "archived").map((dataset) => (
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
                      <span>
                        Target Modules ({trainingPreflightResult.targetModulesMode}): {trainingPreflightResult.resolvedTargetModules.length > 0 ? trainingPreflightResult.resolvedTargetModules.join(", ") : "-"}
                      </span>
                      <span>Quelle: {trainingPreflightResult.targetModulesSource}</span>
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
                  {visibleJobs.map((job) => (
                    <div key={job.id} className="model-settings-row">
                      <div>
                        <strong>
                          Job #{job.id} · Dataset #{job.datasetId}
                        </strong>
                        <div className="model-settings-meta">
                          <span>Status: {job.status}</span>
                          <span>Trainer: {job.trainerName}</span>
                          <span>Base Model: {job.baseModelId}</span>
                          <span>Dateien: {jobFilesSummary(job)}</span>
                        </div>
                        {isJobRunning(job.status) ? (
                          <div className="training-job-progress" role="status" aria-live="polite">
                            <div className="training-job-progress__meta">
                              <span>Fortschritt</span>
                              <span>{jobProgressLabel(job)}</span>
                            </div>
                            <div
                              className="training-job-progress__track"
                              role="progressbar"
                              aria-valuemin={0}
                              aria-valuemax={100}
                              aria-valuenow={Math.round(normalizeJobProgressPercent(job) ?? 0)}
                              aria-label={`Training Job ${job.id} Fortschritt`}
                            >
                              <div
                                className="training-job-progress__fill"
                                style={{ width: `${normalizeJobProgressPercent(job) ?? 0}%` }}
                              />
                            </div>
                          </div>
                        ) : null}
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
                        {job.status === "archived" ? (
                          <button
                            type="button"
                            className="ghost-btn"
                            onClick={() => {
                              void onUnarchiveTrainingJob(job.id);
                            }}
                          >
                            Wiederherstellen
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="ghost-btn"
                            onClick={() => {
                              void onArchiveTrainingJob(job.id);
                            }}
                          >
                            Archivieren
                          </button>
                        )}
                        <button
                          type="button"
                          className="action-btn action-btn--danger"
                          onClick={() => {
                            void onDeleteTrainingJob(job.id);
                          }}
                        >
                          Loeschen
                        </button>
                      </div>
                    </div>
                  ))}
                  {visibleJobs.length === 0 ? <span>Keine Jobs in dieser Ansicht vorhanden.</span> : null}
                    </div>

                    {selectedTrainingJob ? (
                      <article className="page-card">
                    <strong>Job-Details #{selectedTrainingJob.id}</strong>
                    <span>Status: {selectedTrainingJob.status}</span>
                    <span>Dataset: #{selectedTrainingJob.datasetId}</span>
                    <span>Trainer: {selectedTrainingJob.trainerName}</span>
                    <span>Base Model: {selectedTrainingJob.baseModelId}</span>
                    <span>Aktualisiert: {new Date(selectedTrainingJob.updatedAt).toLocaleString()}</span>
                    <span>Trainingsdateien: {jobFilesSummary(selectedTrainingJob)}</span>

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
                  </div>
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
            activeSettingsGroup !== "Training" &&
            activeSettingsGroup !== "Chat" &&
            activeSettingsGroup !== "Integrationen" &&
            activeSettingsGroup !== "Wissen" &&
            activeSettingsGroup !== "Logs" &&
            activeSettingsGroup !== "Benutzer" ? (
              <article className="page-card">
                <strong>{activeSettingsGroup}</strong>
                <span>{settingsGroups.find(([group]) => group === activeSettingsGroup)?.[1] ?? "Einstellungen"}</span>
                {activeSettingsGroup === "System" ? (
                  <div className="model-settings-card__actions">
                    <button
                      type="button"
                      className="action-btn action-btn--primary"
                      onClick={() => {
                        void onExportDiagnosticsReport();
                      }}
                    >
                      Diagnosebericht exportieren
                    </button>
                    <button
                      type="button"
                      className="action-btn action-btn--danger"
                      disabled={cleanStartPending}
                      onClick={() => {
                        void onCleanStartReset();
                      }}
                    >
                      {cleanStartPending ? "Neustart laeuft..." : "Neustart: Chats & Projekte loeschen"}
                    </button>
                    <span>
                      Loescht alle Chats und Projekte aus der Datenbank und startet mit leerem Workspace neu.
                    </span>
                  </div>
                ) : null}
              </article>
            ) : null}
          </div>
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
