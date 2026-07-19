import { type FormEvent, useState } from "react";
import {
  confirmBusinessLetterExecution,
  executeBusinessLetterFunction,
  type PendingConfirmation,
  type PluginFunctionResponse,
} from "../services/businessLetterApi";
import type { DocumentKind } from "../documentTypeConfig";
import type { ExecutePayload, ReferenceDocument } from "../services/types";

type UseBusinessLetterExecutionInput = {
  currentUserId?: number;
  documentKind: DocumentKind;
  subject: string;
  projectId: string;
  customerId: string;
  sourceDocumentId: string;
  sourceDocumentNumber: string;
  selectedReference: ReferenceDocument | null;
  validateForm: () => string[];
  buildPayload: () => ExecutePayload;
};

export function useBusinessLetterExecution({
  currentUserId,
  documentKind,
  subject,
  projectId,
  customerId,
  sourceDocumentId,
  sourceDocumentNumber,
  selectedReference,
  validateForm,
  buildPayload,
}: UseBusinessLetterExecutionInput) {
  const [result, setResult] = useState<unknown>(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const [projectCaseLoading, setProjectCaseLoading] = useState(false);
  const [pendingConfirmation, setPendingConfirmation] = useState<PendingConfirmation | null>(null);
  const [submissionKey, setSubmissionKey] = useState<string>(() => crypto.randomUUID());

  const confirmPendingExecution = async () => {
    if (!pendingConfirmation) {
      return;
    }
    if (currentUserId == null) {
      setError("Bestätigung erfordert einen Benutzerkontext.");
      return;
    }

    setRunning(true);
    setError("");
    try {
      const response = await confirmBusinessLetterExecution(pendingConfirmation.confirmation_id, currentUserId);
      setResult(response);
      setPendingConfirmation(null);
      setSubmissionKey(crypto.randomUUID());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Bestätigung fehlgeschlagen.");
    } finally {
      setRunning(false);
    }
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setResult(null);
    setPendingConfirmation(null);

    const validationErrors = validateForm();
    if (validationErrors.length > 0) {
      setError(validationErrors[0]);
      return;
    }

    setRunning(true);
    try {
      const payload = buildPayload();
      const body = await executeBusinessLetterFunction("create_document", payload.pluginInput ?? {}, {
        userId: currentUserId,
        pluginSettings: payload.pluginSettings,
        idempotencyKey: submissionKey,
        confirmed: false,
      });
      if (body.status === "pending_confirmation") {
        setPendingConfirmation(body.confirmation ?? null);
        return;
      }
      setResult(body);
      setSubmissionKey(crypto.randomUUID());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unbekannter Fehler.");
    } finally {
      setRunning(false);
    }
  };

  const loadProjectCaseOverview = async (): Promise<PluginFunctionResponse | null> => {
    if (!projectId.trim() && !selectedReference?.projectId && !sourceDocumentId.trim() && !sourceDocumentNumber.trim()) {
      setError("Bitte zuerst Projekt- oder Quelldokument-Informationen setzen.");
      return null;
    }

    setError("");
    setProjectCaseLoading(true);
    try {
      const functionInput: Record<string, unknown> = {
        action: "project_case_overview",
        letter_type: documentKind,
        subject: subject.trim() || "Projektakte",
        document_kind: documentKind,
        project_id: projectId.trim() || selectedReference?.projectId || undefined,
        customer_id: customerId.trim() || selectedReference?.customerId || undefined,
        source_document_id: sourceDocumentId.trim() || selectedReference?.id || undefined,
        source_document_number: sourceDocumentNumber.trim() || selectedReference?.number || undefined,
      };
      const response = await executeBusinessLetterFunction("project_case_overview", functionInput, {
        userId: currentUserId,
        confirmed: false,
      });
      if (response.status === "pending_confirmation") {
        setPendingConfirmation(response.confirmation ?? null);
        return response;
      }
      setResult(response);
      return response;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Projektakte konnte nicht geladen werden.");
      return null;
    } finally {
      setProjectCaseLoading(false);
    }
  };

  return {
    result,
    setResult,
    error,
    setError,
    running,
    projectCaseLoading,
    pendingConfirmation,
    submit,
    confirmPendingExecution,
    loadProjectCaseOverview,
  };
}
