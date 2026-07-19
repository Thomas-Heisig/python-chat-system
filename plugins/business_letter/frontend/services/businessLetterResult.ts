import type { BusinessLetterResultSummary, ProjectCaseOverview, ProjectTimelineEntry, QuantityChainLine, ReferenceDocument, ReferencePosition } from "./types";

function normalizeNumber(value: unknown, fallback = 0): number {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function unwrapPluginPayload(value: unknown): Record<string, unknown> | null {
  if (typeof value !== "object" || value == null) {
    return null;
  }
  const payload = value as Record<string, unknown>;
  if (payload.plugin_response && typeof payload.plugin_response === "object") {
    return payload.plugin_response as Record<string, unknown>;
  }
  return payload;
}

export function extractReferenceDocument(result: unknown): ReferenceDocument | null {
  const payload = unwrapPluginPayload(result);
  if (!payload) {
    return null;
  }

  const document = typeof payload.document === "object" && payload.document != null
    ? (payload.document as Record<string, unknown>)
    : null;
  const commercial = typeof payload.commercial_document === "object" && payload.commercial_document != null
    ? (payload.commercial_document as Record<string, unknown>)
    : null;
  const customerVisible = commercial && typeof commercial.customer_visible === "object" && commercial.customer_visible != null
    ? (commercial.customer_visible as Record<string, unknown>)
    : null;
  const relationships = document && typeof document.relationships === "object" && document.relationships != null
    ? (document.relationships as Record<string, unknown>)
    : {};
  const recipient = document && typeof document.recipient === "object" && document.recipient != null
    ? (document.recipient as Record<string, unknown>)
    : {};
  const reference = document && typeof document.reference === "object" && document.reference != null
    ? (document.reference as Record<string, unknown>)
    : {};

  const sourcePositionsRaw = Array.isArray(commercial?.positions)
    ? (commercial?.positions as Array<Record<string, unknown>>)
    : Array.isArray(document?.positions)
      ? (document?.positions as Array<Record<string, unknown>>)
      : [];

  const positions: ReferencePosition[] = sourcePositionsRaw.map((position, index) => {
    const lineId = String(position.line_id || index + 1);
    return {
      lineId,
      name: String(position.name || position.description || `Position ${index + 1}`),
      description: String(position.description || position.name || ""),
      quantity: normalizeNumber(position.quantity, 1),
      unitCode: String(position.unit_code || "C62"),
      priceNet: normalizeNumber(position.price_net, 0),
      vatRate: normalizeNumber(position.vat_rate, 19),
      stoneDetails: typeof position.stone_details === "object" && position.stone_details != null
        ? (position.stone_details as Record<string, unknown>)
        : {},
    };
  });

  const number = String(reference.document_number || payload.document_number || "").trim();
  const id = String(payload.document_id || "").trim();
  if (!id && !number) {
    return null;
  }

  const totals = customerVisible && typeof customerVisible.totals === "object" && customerVisible.totals != null
    ? (customerVisible.totals as Record<string, unknown>)
    : {};

  return {
    id: id || number,
    number,
    kind: String(payload.document_type || document?.document_type || customerVisible?.document_kind || "").trim().toLowerCase(),
    subject: String(document?.subject || "").trim(),
    projectId: String(relationships.project_id || "").trim(),
    customerId: String(relationships.customer_id || "").trim(),
    customerName: String(recipient.name || recipient.company || "").trim(),
    customerStreet: String(recipient.street || "").trim(),
    customerZip: String(recipient.postal_code || "").trim(),
    customerCity: String(recipient.city || "").trim(),
    customerEmail: String(recipient.email || "").trim(),
    issueDate: String(customerVisible?.issue_date || "").trim(),
    dueDate: String(customerVisible?.payment_due_date || "").trim(),
    totalAmount: String(totals.payable_amount || "").trim(),
    positions,
  };
}

export function summarizeResult(result: unknown): BusinessLetterResultSummary | null {
  const payload = unwrapPluginPayload(result);
  if (!payload) {
    return null;
  }
  const artifacts = Array.isArray(payload.artifacts) ? (payload.artifacts as Array<Record<string, unknown>>) : [];
  const pdfArtifact = artifacts.find((artifact) => String(artifact.kind || "") === "pdf");
  const xmlArtifact = artifacts.find((artifact) => String(artifact.kind || "").includes("xml"));
  const validation = typeof payload.validation === "object" && payload.validation != null ? (payload.validation as Record<string, unknown>) : {};
  const warnings = Array.isArray(validation.warnings) ? validation.warnings.filter((item): item is string => typeof item === "string") : [];
  const database = typeof payload.database === "object" && payload.database != null ? (payload.database as Record<string, unknown>) : {};
  const persisted = typeof database.persisted === "object" && database.persisted != null ? (database.persisted as Record<string, unknown>) : {};
  const dualSave = typeof persisted.dual_save === "object" && persisted.dual_save != null ? (persisted.dual_save as Record<string, unknown>) : {};
  const delivery = typeof payload.delivery === "object" && payload.delivery != null ? (payload.delivery as Record<string, unknown>) : {};
  const dispatch = typeof delivery.dispatch === "object" && delivery.dispatch != null ? (delivery.dispatch as Record<string, unknown>) : {};
  const conversion = typeof payload.conversion === "object" && payload.conversion != null ? (payload.conversion as Record<string, unknown>) : {};
  const document = typeof payload.document === "object" && payload.document != null ? (payload.document as Record<string, unknown>) : {};
  const relationships = typeof document.relationships === "object" && document.relationships != null ? (document.relationships as Record<string, unknown>) : {};
  return {
    documentType: String(payload.document_type || "-"),
    documentNumber: String(payload.document_id || payload.document_number || "-"),
    status: String(payload.status || "-"),
    pdfFile: pdfArtifact ? String(pdfArtifact.file_name || "") || null : null,
    xmlFile: xmlArtifact ? String(xmlArtifact.file_name || "") || null : null,
    validationStatus: String(validation.status || "-"),
    warnings,
    storageLocation: String(persisted.document_number || database.storage_key || "") || null,
    dispatchStatus: String(dispatch.status || "") || null,
    archiveStatus: String(dualSave.failure_mode || persisted.plugin_storage || "") || null,
    sourceDocumentNumber: String(relationships.source_document_number || "") || null,
    conversionAction: String(relationships.conversion_action || "") || null,
    followUpDocuments: normalizeNumber(conversion.follow_up_documents, 0),
    openAmount: String(conversion.open_amount || "") || null,
  };
}

export function extractProjectCaseOverview(result: unknown): ProjectCaseOverview | null {
  const payload = unwrapPluginPayload(result);
  if (!payload) {
    return null;
  }
  const projectCase = typeof payload.project_case === "object" && payload.project_case != null
    ? (payload.project_case as Record<string, unknown>)
    : null;
  if (!projectCase) {
    return null;
  }

  const statusView = typeof projectCase.status_view === "object" && projectCase.status_view != null
    ? (projectCase.status_view as Record<string, unknown>)
    : {};
  const rawStatuses = typeof statusView.statuses === "object" && statusView.statuses != null
    ? (statusView.statuses as Record<string, unknown>)
    : {};
  const statuses: Record<string, number> = {};
  Object.entries(rawStatuses).forEach(([key, value]) => {
    statuses[key] = normalizeNumber(value, 0);
  });

  const rawTimeline = Array.isArray(projectCase.timeline) ? (projectCase.timeline as Array<Record<string, unknown>>) : [];
  const timeline: ProjectTimelineEntry[] = rawTimeline.map((entry) => ({
    documentId: String(entry.document_id || ""),
    documentNumber: String(entry.document_number || ""),
    documentKind: String(entry.document_kind || ""),
    status: String(entry.status || ""),
    createdAt: String(entry.created_at || ""),
    sourceDocumentNumber: String(entry.source_document_number || ""),
    payableAmount: String(entry.payable_amount || ""),
  }));

  const rawChain = typeof projectCase.quantity_chain === "object" && projectCase.quantity_chain != null
    ? (projectCase.quantity_chain as Record<string, unknown>)
    : {};
  const rawTotals = typeof rawChain.totals === "object" && rawChain.totals != null
    ? (rawChain.totals as Record<string, unknown>)
    : {};
  const rawLines = Array.isArray(rawChain.lines) ? (rawChain.lines as Array<Record<string, unknown>>) : [];

  const lines: QuantityChainLine[] = rawLines.map((line) => ({
    lineId: String(line.line_id || ""),
    name: String(line.name || ""),
    sourceQuantity: String(line.source_quantity || "0"),
    deliveredQuantity: String(line.delivered_quantity || "0"),
    invoicedQuantity: String(line.invoiced_quantity || "0"),
    openQuantity: String(line.open_quantity || "0"),
  }));

  return {
    projectId: String(projectCase.project_id || ""),
    customerId: String(projectCase.customer_id || ""),
    statusView: {
      documentCount: normalizeNumber(statusView.document_count, 0),
      statuses,
    },
    timeline,
    quantityChain: {
      followUpDocuments: normalizeNumber(rawChain.follow_up_documents, 0),
      lines,
      totals: {
        deliveredQuantity: String(rawTotals.delivered_quantity || "0"),
        invoicedQuantity: String(rawTotals.invoiced_quantity || "0"),
        openQuantity: String(rawTotals.open_quantity || "0"),
      },
    },
  };
}

export function parsePositiveNumber(value: unknown): number | null {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return null;
  }
  return numeric;
}

export function shouldShowTechnicalResponse(isDev: boolean): boolean {
  return isDev;
}
