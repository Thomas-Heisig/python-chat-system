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
          artifactsDirectory: "./training-artifacts",
          datasetsDirectory: "./training-datasets",
          maxConcurrentJobs: "1",
          autoStartQueue: true,
          autoEvaluate: true,
          autoRegisterModel: false,
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
        onCreateTrainingDataset={async () => undefined}
        onRegisterTrainingDatasetFile={async () => undefined}
        onUploadTrainingDataset={async () => undefined}
        onImportTrainingDatasetFromUrl={async () => undefined}
        onCreateTrainingJob={async () => undefined}
        onRunTrainingPreflight={async () => ({
          ready: true,
          modelId: 1,
          modelName: "qwen-transformers",
          modelFormat: "transformers_safetensors",
          trainer: "peft_lora",
          cudaAvailable: false,
          supports4bit: false,
          datasetValid: true,
          warnings: [],
          errors: [],
        })}
        onCancelTrainingJob={async () => undefined}
        onRetryTrainingJob={async () => undefined}
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
        onUploadWorkspaceSource={async () => undefined}
      />
    </QueryClientProvider>,
  );

  return { onFetchTrainingCompatibility };
}

describe("WorkspacePage training compatibility", () => {
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
