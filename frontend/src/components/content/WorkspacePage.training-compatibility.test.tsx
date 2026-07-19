import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { WorkspacePage } from "./WorkspacePage";

function renderWorkspacePage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const onFetchTrainingCompatibility = vi
    .fn<
      (trainerName: string) => Promise<Record<string, { compatible: boolean; reason: string | null }>>
    >()
    .mockImplementation(async (trainerName: string) => {
      if (trainerName === "peft_lora") {
        return {
          "1": { compatible: true, reason: null },
          "2": { compatible: false, reason: "peft_lora unterstuetzt keine GGUF-Modelle." },
        };
      }
      return {
        "1": { compatible: true, reason: null },
        "2": { compatible: true, reason: null },
      };
    });

  render(
    <QueryClientProvider client={queryClient}>
      <WorkspacePage
        view="Einstellungen"
        projects={[]}
        appointments={[]}
        sources={[]}
        modelEntries={[
          {
            id: "1",
            name: "qwen-transformers",
            modelPath: "F:/models/qwen",
            backend: "transformers",
            loadStatus: "unloaded",
            loaded: false,
            category: "lokal",
            sourceLabel: "",
            isActive: false,
            modelFormat: "transformers_safetensors",
            taskType: "text_generation",
            capabilities: {
              supportsInference: true,
              supportsTraining: true,
              supportsPeftTraining: true,
              supports4bit: true,
              supportsChat: true,
              supportsEmbeddings: false,
              supportsReranking: false,
              supportsVision: false,
              supportsAudio: false,
            },
          },
          {
            id: "2",
            name: "demo-gguf",
            modelPath: "F:/models/demo.gguf",
            backend: "llama_cpp",
            loadStatus: "unloaded",
            loaded: false,
            category: "lokal",
            sourceLabel: "",
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
        ]}
        selectedModelId="1"
        modelLoaded={true}
        modelActionPending={false}
        modelDirectoryPending={false}
        modelProfilePending={false}
        generalSettingsPending={false}
        trainingSettingsPending={false}
        trainingBatchPending={false}
        trainingPreflightPending={false}
        modelDirectories={[]}
        modelProfile={{
          systemPrompt: "",
          temperature: "0.1",
          samplingTopK: "6",
          maxNewTokens: "256",
          topK: "6",
          topP: "0.95",
          repetitionPenalty: "1.0",
          stopSequences: "",
          seed: "42",
          doSample: true,
          preferGpu: true,
        }}
        generalSettings={{
          language: "de",
          theme: "system",
          timezone: "Europe/Berlin",
        }}
        trainingSettings={{
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
          targetModules: "q_proj, k_proj, v_proj, o_proj",
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
        }}
        trainingPreflightResult={null}
        trainingDatasetFiles={[]}
        trainingDatasets={[]}
        trainingJobs={[]}
        trainerOptions={[
          { id: "reference", label: "Reference", available: true, reasonUnavailable: null, isSimulation: true },
          { id: "peft_lora", label: "PEFT LoRA", available: true, reasonUnavailable: null, isSimulation: false },
        ]}
        trainingCompatibility={{
          "1": { compatible: true, reason: null },
          "2": { compatible: true, reason: null },
        }}
        onFetchTrainingCompatibility={onFetchTrainingCompatibility}
        onActivateModel={async () => undefined}
        onDeactivateModel={async () => undefined}
        onScanModels={async () => undefined}
        onSetModelRelevance={async () => undefined}
        onSaveModelDirectories={async () => undefined}
        onSaveModelProfile={async () => undefined}
        onSaveGeneralSettings={async () => undefined}
        onSaveTrainingSettings={async () => undefined}
        onBatchCreateTrainingJobs={async () => undefined}
        onAssignTrainingProject={async () => undefined}
        onCreateTrainingDataset={async () => undefined}
        onRegisterTrainingDatasetFile={async () => undefined}
        onUploadTrainingDataset={async () => undefined}
        onImportTrainingDatasetFromUrl={async () => undefined}
        onUploadTrainingDatasetBundle={async () => undefined}
        onCreateTrainingJob={async () => undefined}
        onRunTrainingPreflight={async () => ({
          ready: true,
          modelId: 1,
          modelName: "qwen-transformers",
          modelFormat: "transformers_safetensors",
          trainer: "peft_lora",
          targetModulesMode: "auto",
          resolvedTargetModules: [],
          targetModulesSource: "auto",
          cudaAvailable: false,
          supports4bit: false,
          datasetValid: true,
          warnings: [],
          errors: [],
        })}
        onCancelTrainingJob={async () => undefined}
        onRetryTrainingJob={async () => undefined}
        onArchiveTrainingDataset={async () => undefined}
        onDeleteTrainingDataset={async () => undefined}
        onUnarchiveTrainingDataset={async () => undefined}
        onArchiveTrainingJob={async () => undefined}
        onDeleteTrainingJob={async () => undefined}
        onUnarchiveTrainingJob={async () => undefined}
        currentUser={{
          id: 1,
          username: "tester",
          is_admin: false,
          is_active: true,
          created_at: "2026-07-11T00:00:00Z",
        }}
        onAdminCreateUser={async () => undefined}
        onExportDiagnosticsReport={async () => undefined}
        selectedProjectId={null}
        onSelectProject={() => undefined}
        onCreateProject={async () => undefined}
        onRenameProject={async () => undefined}
        onDeleteProject={async () => undefined}
        onUpdateProjectHierarchy={async () => undefined}
        onUploadWorkspaceSource={async () => undefined}
        onAssignSourceToProject={async () => undefined}
        cleanStartPending={false}
        chatSettingsPending={false}
        chatCleanupPending={false}
        knowledgeSettingsPending={false}
        integrationSettingsPending={false}
        logsSettingsPending={false}
        chatSettings={{
          pluginOrchestrationEnabled: true,
          autoSpecialistEnabled: false,
          contextLimitTokens: "8192",
          contextSafetyMarginTokens: "128",
        }}
        chatCleanupStats={null}
        knowledgeSettings={{
          topK: "6",
          minScoreRatio: "0.5",
          minAbsoluteScore: "1000",
          minScoreGap: "400",
        }}
        integrationSettings={{
          chatgptApiKey: "", deeplApiKey: "", anthropicApiKey: "", googleAiApiKey: "", mistralApiKey: "",
          cohereApiKey: "", perplexityApiKey: "", groqApiKey: "", togetherApiKey: "", openrouterApiKey: "",
          huggingfaceApiKey: "", replicateApiKey: "", deepseekApiKey: "", xaiApiKey: "", elevenlabsApiKey: "",
          assemblyaiApiKey: "", tavilyApiKey: "", serpapiApiKey: "", googleMapsApiKey: "", mapboxApiKey: "",
          openweatherApiKey: "", weatherapiApiKey: "", tomorrowioApiKey: "", newsapiApiKey: "", twilioApiKey: "",
          sendgridApiKey: "", slackBotToken: "", discordBotToken: "", githubToken: "", notionApiKey: "",
          airtableApiKey: "", stripeSecretKey: "", azureOpenaiApiKey: "", awsBedrockApiKey: "", deepinfraApiKey: "",
          nvidiaNimApiKey: "", octoaiApiKey: "", fireworksApiKey: "", githubCopilotApiKey: "", stabilityApiKey: "",
          runwayApiKey: "", pikaApiKey: "", heygenApiKey: "", falApiKey: "", unstructuredApiKey: "",
          llamaparseApiKey: "", firecrawlApiKey: "", pineconeApiKey: "", weaviateApiKey: "", qdrantApiKey: "",
          cloudconvertApiKey: "", exaApiKey: "", braveSearchApiKey: "", bingSearchApiKey: "", gnewsApiKey: "",
          scrapingbeeApiKey: "", apifyApiKey: "", alphaVantageApiKey: "", yahooFinanceApiKey: "",
          openexchangeratesApiKey: "", whatsappBusinessApiKey: "", telegramBotToken: "", microsoftTeamsApiKey: "",
          calendlyApiKey: "", virustotalApiKey: "", hibpApiKey: "", ollamaLocalEnabled: false, customProviderKeysJson: "",
        }}
        integrationTestResults={{}}
        logsSettings={{ logLevel: "INFO" }}
        pluginDescriptors={[]}
        pluginSettingsDrafts={{}}
        pluginSettingsErrors={{}}
        savingPluginId={null}
        onPullModel={async () => undefined}
        onCancelPullModel={async () => undefined}
        onCleanStartReset={async () => undefined}
        onSaveChatSettings={async () => undefined}
        onCleanupObsoleteChatSettings={async () => undefined}
        onSaveKnowledgeSettings={async () => undefined}
        onSaveIntegrationSettings={async () => undefined}
        onSaveIntegrationTestResults={async () => undefined}
        onSaveLogsSettings={async () => undefined}
        onPluginSettingChange={() => undefined}
        onSavePluginSettings={async () => undefined}
      />
    </QueryClientProvider>,
  );

  return { onFetchTrainingCompatibility };
}

describe("WorkspacePage training compatibility", () => {
  it("shows one logical training step at a time", () => {
    renderWorkspacePage();

    fireEvent.click(screen.getByRole("button", { name: "Training" }));
    expect(screen.getByText("Schnellstart")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "2. Daten importieren" }));
    expect(screen.getByText("Neuen Datensatz vorbereiten")).toBeTruthy();
    expect(screen.queryByText("Schnellstart")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "4. Jobs & Fortschritt" }));
    expect(screen.getByText("Einzeljob starten")).toBeTruthy();
    expect(screen.queryByText("Neuen Datensatz vorbereiten")).toBeNull();
  });

  it("updates compatibility on trainer switch and disables incompatible model options", async () => {
    const { onFetchTrainingCompatibility } = renderWorkspacePage();

    fireEvent.click(screen.getByRole("button", { name: "Training" }));

    const trainerSelect = screen.getByLabelText("Standard-Trainer") as HTMLSelectElement;
    fireEvent.change(trainerSelect, { target: { value: "peft_lora" } });

    await waitFor(() => {
      expect(onFetchTrainingCompatibility).toHaveBeenCalledWith("peft_lora");
    });

    const baseModelSelect = screen.getByLabelText("Basis-Modell (Model Manager)") as HTMLSelectElement;
    const ggufOption = Array.from(baseModelSelect.options).find((option) => option.value === "demo-gguf");
    const transformersOption = Array.from(baseModelSelect.options).find((option) => option.value === "qwen-transformers");

    expect(ggufOption).toBeDefined();
    expect(transformersOption).toBeDefined();
    expect(ggufOption?.disabled).toBe(true);
    expect(transformersOption?.disabled).toBe(false);
  });
});
