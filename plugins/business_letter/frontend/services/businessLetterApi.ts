const BUSINESS_LETTER_PLUGIN_ID = "business_letter";

export type ExecuteFunctionOptions = {
  userId?: number;
  pluginSettings?: Record<string, unknown>;
  idempotencyKey?: string;
  confirmed?: boolean;
  confirmationId?: string;
};

export type PendingConfirmation = {
  confirmation_id: string;
  user_id: number;
  team_id: number | null;
  plugin_id: string;
  function_name: string;
  arguments: Record<string, unknown>;
  arguments_hash: string;
  idempotency_key: string | null;
  status: string;
  expires_at: string;
};

export type PluginFunctionResponse = {
  status?: string;
  confirmation?: PendingConfirmation;
  plugin_response?: unknown;
  idempotency?: { status?: string; key?: string } | null;
  [key: string]: unknown;
};

function extractErrorMessage(body: unknown, fallback: string): string {
  if (!body || typeof body !== "object") {
    return fallback;
  }
  const payload = body as { detail?: unknown; message?: unknown };
  if (typeof payload.message === "string" && payload.message.trim()) {
    return payload.message;
  }
  if (typeof payload.detail === "string" && payload.detail.trim()) {
    return payload.detail;
  }
  if (payload.detail && typeof payload.detail === "object") {
    const detail = payload.detail as { message?: unknown };
    if (typeof detail.message === "string" && detail.message.trim()) {
      return detail.message;
    }
  }
  return fallback;
}

export async function executeBusinessLetterFunction(
  functionName: string,
  functionInput: Record<string, unknown>,
  options: ExecuteFunctionOptions = {},
): Promise<PluginFunctionResponse> {
  const body: Record<string, unknown> = {
    plugin_id: BUSINESS_LETTER_PLUGIN_ID,
    function_name: functionName,
    function_input: functionInput,
    plugin_settings: options.pluginSettings ?? {},
    user_id: options.userId ?? null,
    confirmed: Boolean(options.confirmed),
    dry_run: false,
  };

  if (options.confirmationId) {
    body.confirmation_id = options.confirmationId;
  }
  if (options.idempotencyKey) {
    body.idempotency_key = options.idempotencyKey;
  }

  const response = await fetch("/api/plugins/execute-function", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });

  const parsedBody = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(extractErrorMessage(parsedBody, `Plugin-Funktion fehlgeschlagen (${response.status}).`));
  }

  return (parsedBody ?? {}) as PluginFunctionResponse;
}

export async function confirmBusinessLetterExecution(
  confirmationId: string,
  userId: number,
): Promise<PluginFunctionResponse> {
  const response = await fetch(`/api/plugins/confirmations/${encodeURIComponent(confirmationId)}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ user_id: userId }),
  });

  const parsedBody = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(extractErrorMessage(parsedBody, `Bestätigung fehlgeschlagen (${response.status}).`));
  }

  return (parsedBody ?? {}) as PluginFunctionResponse;
}
