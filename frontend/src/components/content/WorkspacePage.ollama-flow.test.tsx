import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { WorkspacePage } from "./WorkspacePage";

function openFirstPluginSettingsCard() {
  const collapsedButtons = screen.queryAllByRole("button", { name: "Einstellungen anzeigen" });
  if (collapsedButtons.length > 0) {
    fireEvent.click(collapsedButtons[0]);
  }
}

function buildBaseProps(overrides: Record<string, unknown> = {}) {
  const onActivateModel = vi.fn(async () => undefined);
  const onPullModel = vi.fn(async () => undefined);
  const onCancelPullModel = vi.fn(async () => undefined);
  const onScanModels = vi.fn(async () => undefined);

  const props: Record<string, unknown> = {
    view: "Einstellungen",
    projects: [],
    appointments: [],
    sources: [],
    modelEntries: [],
    selectedModelId: "",
    modelLoaded: false,
    modelActionPending: false,
    modelDirectoryPending: false,
    modelProfilePending: false,
    generalSettingsPending: false,
    cleanStartPending: false,
    chatSettingsPending: false,
    chatCleanupPending: false,
    knowledgeSettingsPending: false,
    integrationSettingsPending: false,
    logsSettingsPending: false,
    trainingSettingsPending: false,
    trainingBatchPending: false,
    trainingPreflightPending: false,
    modelDirectories: [],
    modelProfile: {
      systemPrompt: "",
      temperature: "0.7",
      samplingTopK: "6",
      maxNewTokens: "512",
      topK: "6",
      topP: "0.95",
      repetitionPenalty: "1.05",
      stopSequences: "",
      seed: "42",
      doSample: true,
      preferGpu: true,
    },
    generalSettings: { language: "de", theme: "system", timezone: "Europe/Berlin" },
    chatSettings: {
      pluginOrchestrationEnabled: true,
      autoSpecialistEnabled: false,
      contextLimitTokens: "8192",
      contextSafetyMarginTokens: "128",
    },
    chatCleanupStats: null,
    knowledgeSettings: {
      topK: "6",
      minScoreRatio: "0.5",
      minAbsoluteScore: "1000",
      minScoreGap: "400",
    },
    integrationSettings: {
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
      ollamaLocalEnabled: true,
      customProviderKeysJson: "{}",
    },
    integrationTestResults: {},
    logsSettings: { logLevel: "INFO" },
    pluginDescriptors: [],
    pluginSettingsDrafts: {},
    pluginSettingsErrors: {},
    savingPluginId: null,
    trainingSettings: {
      enabled: true,
      defaultTrainer: "reference",
      baseModel: "",
      projectId: "",
      artifactsDirectory: "./training-artifacts",
      datasetsDirectory: "./training-datasets",
      maxConcurrentJobs: "1",
      autoStartQueue: true,
      autoEvaluate: true,
      autoRegisterModel: false,
      autoActivateModel: true,
      continualTraining: false,
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
    },
    trainingPreflightResult: null,
    trainingDatasetFiles: [],
    trainingDatasets: [],
    trainingJobs: [],
    trainerOptions: [{ id: "reference", label: "Reference", available: true, reasonUnavailable: null, isSimulation: true }],
    trainingCompatibility: {},
    onFetchTrainingCompatibility: vi.fn(async () => ({})),
    onActivateModel,
    onPullModel,
    onCancelPullModel,
    onDeactivateModel: vi.fn(async () => undefined),
    onScanModels,
    onSetModelRelevance: vi.fn(async () => undefined),
    onSaveModelDirectories: vi.fn(async () => undefined),
    onSaveModelProfile: vi.fn(async () => undefined),
    onSaveGeneralSettings: vi.fn(async () => undefined),
    onCleanStartReset: vi.fn(async () => undefined),
    onSaveChatSettings: vi.fn(async () => undefined),
    onCleanupObsoleteChatSettings: vi.fn(async () => undefined),
    onSaveKnowledgeSettings: vi.fn(async () => undefined),
    onSaveIntegrationSettings: vi.fn(async () => undefined),
    onSaveIntegrationTestResults: vi.fn(async () => undefined),
    onSaveLogsSettings: vi.fn(async () => undefined),
    onPluginSettingChange: vi.fn(),
    onSavePluginSettings: vi.fn(async () => undefined),
    onSaveTrainingSettings: vi.fn(async () => undefined),
    onBatchCreateTrainingJobs: vi.fn(async () => undefined),
    onAssignTrainingProject: vi.fn(async () => undefined),
    onCreateTrainingDataset: vi.fn(async () => undefined),
    onRegisterTrainingDatasetFile: vi.fn(async () => undefined),
    onUploadTrainingDataset: vi.fn(async () => undefined),
    onImportTrainingDatasetFromUrl: vi.fn(async () => undefined),
    onUploadTrainingDatasetBundle: vi.fn(async () => undefined),
    onCreateTrainingJob: vi.fn(async () => undefined),
    onRunTrainingPreflight: vi.fn(async () => ({
      ready: true,
      modelId: null,
      modelName: null,
      modelFormat: null,
      trainer: "reference",
      targetModulesMode: "auto",
      resolvedTargetModules: [],
      targetModulesSource: "auto",
      cudaAvailable: false,
      supports4bit: false,
      datasetValid: true,
      warnings: [],
      errors: [],
    })),
    onCancelTrainingJob: vi.fn(async () => undefined),
    onRetryTrainingJob: vi.fn(async () => undefined),
    onArchiveTrainingDataset: vi.fn(async () => undefined),
    onDeleteTrainingDataset: vi.fn(async () => undefined),
    onUnarchiveTrainingDataset: vi.fn(async () => undefined),
    onArchiveTrainingJob: vi.fn(async () => undefined),
    onDeleteTrainingJob: vi.fn(async () => undefined),
    onUnarchiveTrainingJob: vi.fn(async () => undefined),
    currentUser: {
      id: 1,
      username: "tester",
      is_admin: false,
      is_active: true,
      created_at: "2026-07-17T00:00:00Z",
    },
    onAdminCreateUser: vi.fn(async () => undefined),
    onExportDiagnosticsReport: vi.fn(async () => undefined),
    selectedProjectId: null,
    onSelectProject: vi.fn(),
    onCreateProject: vi.fn(async () => undefined),
    onRenameProject: vi.fn(async () => undefined),
    onDeleteProject: vi.fn(async () => undefined),
    onUpdateProjectHierarchy: vi.fn(async () => undefined),
    onUploadWorkspaceSource: vi.fn(async () => undefined),
    onAssignSourceToProject: vi.fn(async () => undefined),
    ...overrides,
  };

  const rendered = render(<WorkspacePage {...(props as any)} />);
  return {
    ...rendered,
    onActivateModel,
    onPullModel,
    onCancelPullModel,
    onScanModels,
  };
}

describe("WorkspacePage Ollama flow", () => {
  it("triggers scan and selection/activation in model settings", () => {
    const { onActivateModel, onScanModels } = buildBaseProps({
      selectedModelId: "local-1",
      modelEntries: [
        {
          id: "local-1",
          name: "Local One",
          group: "Text / Chat",
          modelPath: "F:/models/local-1",
          backend: "llama_cpp",
          loadStatus: "unloaded",
          loaded: false,
          category: "lokal",
          sourceLabel: "Lokal",
          isActive: false,
          modelFormat: "gguf",
          taskType: "text_generation",
          capabilities: {
            supportsInference: true,
            supportsTraining: false,
            supportsPeftTraining: false,
            supports4bit: true,
            supportsChat: true,
            supportsEmbeddings: false,
            supportsReranking: false,
            supportsVision: false,
            supportsAudio: false,
          },
        },
        {
          id: "local-2",
          name: "Local Two",
          group: "Text / Chat",
          modelPath: "F:/models/local-2",
          backend: "llama_cpp",
          loadStatus: "unloaded",
          loaded: false,
          category: "lokal",
          sourceLabel: "Lokal",
          isActive: false,
          modelFormat: "gguf",
          taskType: "text_generation",
          capabilities: {
            supportsInference: true,
            supportsTraining: false,
            supportsPeftTraining: false,
            supports4bit: true,
            supportsChat: true,
            supportsEmbeddings: false,
            supportsReranking: false,
            supportsVision: false,
            supportsAudio: false,
          },
        },
      ],
    });

    fireEvent.click(screen.getByRole("button", { name: "Modelle" }));
    fireEvent.click(screen.getByRole("button", { name: "Scan aktualisieren" }));
    expect(onScanModels).toHaveBeenCalledTimes(1);

    const radios = screen.getAllByRole("radio", { name: "Auswaehlen" });
    fireEvent.click(radios[1]);
    expect(onActivateModel).toHaveBeenCalledWith("local-2");
  });

  it("handles cloud download, cancel and retry actions", async () => {
    const cloudBase = {
      id: "cloud-1",
      name: "qwen3:latest (Ollama Cloud)",
      group: "Text / Chat",
      modelPath: "ollama-cloud://qwen3:latest",
      backend: "ollama",
      loadStatus: "unloaded",
      loaded: false,
      category: "ollama_cloud",
      sourceLabel: "Ollama Cloud",
      isActive: false,
      ollamaInstalled: false,
      modelFormat: "ollama",
      taskType: "text_generation",
      capabilities: {
        supportsInference: false,
        supportsTraining: false,
        supportsPeftTraining: false,
        supports4bit: false,
        supportsChat: true,
        supportsEmbeddings: false,
        supportsReranking: false,
        supportsVision: false,
        supportsAudio: false,
      },
    };

    const initial = buildBaseProps({
      modelEntries: [cloudBase],
    });

    fireEvent.click(screen.getByRole("button", { name: "Modelle" }));
    fireEvent.click(await screen.findByRole("button", { name: "Herunterladen" }));
    expect(initial.onPullModel).toHaveBeenCalledWith("cloud-1");

    initial.unmount();

    const cancelling = buildBaseProps({
      modelEntries: [
        {
          ...cloudBase,
          pullStatus: {
            state: "pulling",
            detail: "Download laeuft",
            progressPercent: 30,
            total: 100,
            completed: 30,
            updatedAt: "2026-07-17T12:00:00Z",
          },
        },
      ],
    });
    fireEvent.click(screen.getByRole("button", { name: "Modelle" }));
    fireEvent.click(await screen.findByRole("button", { name: "Abbrechen" }));
    expect(cancelling.onCancelPullModel).toHaveBeenCalledWith("cloud-1");

    cancelling.unmount();

    const retry = buildBaseProps({
      modelEntries: [
        {
          ...cloudBase,
          pullStatus: {
            state: "cancelled",
            detail: "Download abgebrochen",
            progressPercent: null,
            total: null,
            completed: null,
            updatedAt: "2026-07-17T12:01:00Z",
          },
        },
      ],
    });
    fireEvent.click(screen.getByRole("button", { name: "Modelle" }));
    fireEvent.click(await screen.findByRole("button", { name: "Retry" }));
    expect(retry.onPullModel).toHaveBeenCalledWith("cloud-1");
  });

  it("keeps plugin select and boolean settings across save, reload and reopen", () => {
    window.localStorage.clear();

    const pluginSettingsDrafts: Record<string, Record<string, unknown>> = {
      business_letter: {
        default_einvoice_standard: "xrechnung",
        default_einvoice_enabled: false,
      },
    };

    const onPluginSettingChange = vi.fn((pluginId: string, fieldKey: string, value: unknown) => {
      pluginSettingsDrafts[pluginId] = {
        ...(pluginSettingsDrafts[pluginId] ?? {}),
        [fieldKey]: value,
      };
    });
    const onSavePluginSettings = vi.fn(async () => undefined);

    const first = buildBaseProps({
      pluginDescriptors: [
        {
          id: "business_letter",
          name: "Geschaeftsbrief",
          category: "Dokumente",
          description: "Plugin fuer Dokumente",
          settings_fields: [
            {
              key: "default_einvoice_standard",
              label: "E-Rechnung-Standard",
              type: "select",
              default: "xrechnung",
              options: [
                { label: "XRechnung", value: "xrechnung" },
                { label: "ZUGFeRD", value: "zugferd" },
              ],
            },
            {
              key: "default_einvoice_enabled",
              label: "E-Rechnung aktiv",
              type: "boolean",
              default: false,
            },
          ],
        },
      ],
      pluginSettingsDrafts,
      onPluginSettingChange,
      onSavePluginSettings,
    });

    fireEvent.click(screen.getByRole("button", { name: "Plugins" }));
    openFirstPluginSettingsCard();
    if (!screen.queryByLabelText("E-Rechnung-Standard")) {
      const subgroupToggle = document.querySelectorAll(".settings-plugin-subgroup-card .model-group-toggle")[0];
      if (subgroupToggle instanceof HTMLElement) {
        fireEvent.click(subgroupToggle);
      }
    }

    const standardSelect = screen.getByLabelText("E-Rechnung-Standard") as HTMLSelectElement;
    const enabledCheckbox = screen.getByLabelText("E-Rechnung aktiv") as HTMLInputElement;

    fireEvent.change(standardSelect, { target: { value: "zugferd" } });
    fireEvent.click(enabledCheckbox);

    expect(onPluginSettingChange).toHaveBeenCalledWith("business_letter", "default_einvoice_standard", "zugferd");
    expect(onPluginSettingChange).toHaveBeenCalledWith("business_letter", "default_einvoice_enabled", true);

    fireEvent.click(screen.getAllByRole("button", { name: "Speichern" })[0]);
    expect(onSavePluginSettings).toHaveBeenCalledWith("business_letter");

    first.unmount();

    const reloaded = buildBaseProps({
      pluginDescriptors: [
        {
          id: "business_letter",
          name: "Geschaeftsbrief",
          category: "Dokumente",
          description: "Plugin fuer Dokumente",
          settings_fields: [
            {
              key: "default_einvoice_standard",
              label: "E-Rechnung-Standard",
              type: "select",
              default: "xrechnung",
              options: [
                { label: "XRechnung", value: "xrechnung" },
                { label: "ZUGFeRD", value: "zugferd" },
              ],
            },
            {
              key: "default_einvoice_enabled",
              label: "E-Rechnung aktiv",
              type: "boolean",
              default: false,
            },
          ],
        },
      ],
      pluginSettingsDrafts: {
        business_letter: {
          default_einvoice_standard: pluginSettingsDrafts.business_letter.default_einvoice_standard,
          default_einvoice_enabled: pluginSettingsDrafts.business_letter.default_einvoice_enabled,
        },
      },
    });

    fireEvent.click(screen.getByRole("button", { name: "Plugins" }));
    openFirstPluginSettingsCard();
    if (!screen.queryByLabelText("E-Rechnung-Standard")) {
      const subgroupToggle = document.querySelectorAll(".settings-plugin-subgroup-card .model-group-toggle")[0];
      if (subgroupToggle instanceof HTMLElement) {
        fireEvent.click(subgroupToggle);
      }
    }

    const reloadedSelect = screen.getByLabelText("E-Rechnung-Standard") as HTMLSelectElement;
    const reloadedCheckbox = screen.getByLabelText("E-Rechnung aktiv") as HTMLInputElement;
    expect(reloadedSelect.value).toBe("zugferd");
    expect(reloadedCheckbox.checked).toBe(true);

    fireEvent.click(screen.getAllByRole("button", { name: "Einklappen" })[0]);
    openFirstPluginSettingsCard();
    if (!screen.queryByLabelText("E-Rechnung-Standard")) {
      const subgroupToggle = document.querySelectorAll(".settings-plugin-subgroup-card .model-group-toggle")[0];
      if (subgroupToggle instanceof HTMLElement) {
        fireEvent.click(subgroupToggle);
      }
    }

    const reopenedSelect = screen.getByLabelText("E-Rechnung-Standard") as HTMLSelectElement;
    const reopenedCheckbox = screen.getByLabelText("E-Rechnung aktiv") as HTMLInputElement;
    expect(reopenedSelect.value).toBe("zugferd");
    expect(reopenedCheckbox.checked).toBe(true);

    reloaded.unmount();
  });

  it("renders plugin setting groups collapsible and marks dependent fields", async () => {
    window.localStorage.clear();

    const pluginSettingsDrafts: Record<string, Record<string, unknown>> = {
      business_letter: {
        default_einvoice_enabled: false,
      },
    };

    const onPluginSettingChange = vi.fn((pluginId: string, fieldKey: string, value: unknown) => {
      pluginSettingsDrafts[pluginId] = {
        ...(pluginSettingsDrafts[pluginId] ?? {}),
        [fieldKey]: value,
      };
    });

    const pluginDescriptor = {
      id: "business_letter",
      name: "Geschaeftsbrief",
      category: "Dokumente",
      description: "Plugin fuer Dokumente",
      settings_fields: [
        {
          key: "default_einvoice_enabled",
          label: "E-Rechnung aktiv",
          type: "boolean",
          default: false,
          group: "E-Rechnung",
        },
        {
          key: "validator_profile",
          label: "Validatorprofil",
          type: "select",
          default: "auto",
          group: "E-Rechnung",
          visibleWhen: { field: "default_einvoice_enabled", truthy: true },
          options: [
            { label: "Auto", value: "auto" },
            { label: "XRechnung", value: "xrechnung" },
          ],
        },
        {
          key: "default_cc",
          label: "Standard-CC",
          type: "string",
          default: "",
          group: "Kommunikation",
        },
      ],
    };

    const view = buildBaseProps({
      pluginDescriptors: [
        pluginDescriptor,
      ],
      pluginSettingsDrafts,
      onPluginSettingChange,
    });

    fireEvent.click(screen.getByRole("button", { name: "Plugins" }));
    openFirstPluginSettingsCard();
    if (!screen.queryByLabelText("Validatorprofil")) {
      const subgroupToggle = document.querySelectorAll(".settings-plugin-subgroup-card .model-group-toggle")[0];
      if (subgroupToggle instanceof HTMLElement) {
        fireEvent.click(subgroupToggle);
      }
    }

    expect((await screen.findAllByText("Validatorprofil")).length).toBeGreaterThan(0);
    expect(screen.getByText(/abhaengig von E-Rechnung aktiv/i)).toBeTruthy();

    fireEvent.click(screen.getByLabelText("E-Rechnung aktiv"));
    view.unmount();

    const reloaded = buildBaseProps({
      pluginDescriptors: [pluginDescriptor],
      pluginSettingsDrafts,
      onPluginSettingChange,
    });

    fireEvent.click(screen.getByRole("button", { name: "Plugins" }));
    openFirstPluginSettingsCard();
    if (!screen.queryByLabelText("Validatorprofil")) {
      const subgroupToggle = document.querySelectorAll(".settings-plugin-subgroup-card .model-group-toggle")[0];
      if (subgroupToggle instanceof HTMLElement) {
        fireEvent.click(subgroupToggle);
      }
    }

    expect((await screen.findAllByText("Validatorprofil")).length).toBeGreaterThan(0);
    expect(screen.getByText(/abhaengig von E-Rechnung aktiv/i)).toBeTruthy();
    expect(screen.queryByLabelText("Standard-CC")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: /Kommunikation/ }));
    expect(screen.getByLabelText("Standard-CC")).toBeTruthy();

    reloaded.unmount();
  });

  it("shows numbering preview for business letter plugin settings", () => {
    buildBaseProps({
      pluginDescriptors: [
        {
          id: "business_letter",
          name: "Geschaeftsbrief",
          category: "Dokumente",
          description: "Plugin fuer Dokumente",
          settings_fields: [
            {
              key: "document_number_prefix",
              label: "Nummernkreis Praefix",
              type: "string",
              default: "ANG",
              group: "Nummernkreis & Persistenz",
            },
            {
              key: "document_number_pattern",
              label: "Nummernformat",
              type: "string",
              default: "{prefix}-{year}-{sequence_text}",
              group: "Nummernkreis & Persistenz",
            },
            {
              key: "document_number_width",
              label: "Nummern-Laufweite",
              type: "number",
              default: 4,
              group: "Nummernkreis & Persistenz",
            },
            {
              key: "document_number_start_value",
              label: "Nummernkreis Startwert",
              type: "number",
              default: 7,
              group: "Nummernkreis & Persistenz",
            },
          ],
        },
      ],
      pluginSettingsDrafts: {
        business_letter: {
          document_number_prefix: "ANG",
          document_number_pattern: "{prefix}-{year}-{sequence_text}",
          document_number_width: 4,
          document_number_start_value: 7,
        },
      },
    });

    fireEvent.click(screen.getByRole("button", { name: "Plugins" }));
    fireEvent.click(screen.getAllByText("Geschaeftsbrief")[0]);

    const currentYear = new Date().getFullYear();
    expect(screen.getByText(new RegExp(`Allgemein: ANG-${currentYear}-0007`))).toBeTruthy();
  });
});
