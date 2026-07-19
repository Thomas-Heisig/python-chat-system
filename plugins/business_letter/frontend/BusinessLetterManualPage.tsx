import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { usePluginDraft } from "../../shared/frontend/usePluginDraft";
import "./BusinessLetterManualPage.css";
import {
  DOCUMENT_KIND_ORDER,
  DOCUMENT_TYPE_CONFIG,
  type DocumentKind,
  type FrontendFieldKey,
} from "./documentTypeConfig";
import { BusinessLetterHeader } from "./components/BusinessLetterHeader";
import { BusinessLetterSidebar } from "./components/BusinessLetterSidebar";
import { DocumentSection } from "./components/DocumentSection";
import { PositionSection } from "./components/PositionSection";
import { RelationshipSection } from "./components/RelationshipSection";
import { RecipientSection } from "./components/RecipientSection";
import { TextSection } from "./components/TextSection";
import { useBusinessLetterExecution } from "./hooks/useBusinessLetterExecution";
import { buildBusinessLetterPayload } from "./services/businessLetterPayload";
import {
  extractProjectCaseOverview,
  extractReferenceDocument,
  summarizeResult,
  shouldShowTechnicalResponse,
} from "./services/businessLetterResult";
import { validateBusinessLetterForm } from "./services/businessLetterValidation";

type Position = {
  id: string;
  description: string;
  quantity: number;
  unit: string;
  unitPrice: number;
  taxRate: number;
  stoneDetails: {
    materialType: string;
    tradeName: string;
    origin: string;
    color: string;
    surfaceFinish: string;
    thicknessMm: string;
    lengthMm: string;
    widthMm: string;
    edgeProfile: string;
    batch: string;
    blockNumber: string;
    measurementNumber: string;
    installationLocation: string;
  };
};

type ReferencePosition = {
  lineId: string;
  name: string;
  description: string;
  quantity: number;
  unitCode: string;
  priceNet: number;
  vatRate: number;
  stoneDetails: Record<string, unknown>;
};

type ReferenceDocument = {
  id: string;
  number: string;
  kind: string;
  subject: string;
  projectId: string;
  customerId: string;
  customerName: string;
  customerStreet: string;
  customerZip: string;
  customerCity: string;
  customerEmail: string;
  issueDate: string;
  dueDate: string;
  totalAmount: string;
  positions: ReferencePosition[];
};

type ExecutePayload = {
  pluginId: string;
  pluginInput?: Record<string, unknown>;
  pluginSettings?: Record<string, unknown>;
  userId?: number;
};

type BusinessLetterResultSummary = {
  documentType: string;
  documentNumber: string;
  status: string;
  pdfFile: string | null;
  xmlFile: string | null;
  validationStatus: string;
  warnings: string[];
  storageLocation: string | null;
  dispatchStatus: string | null;
  archiveStatus: string | null;
  sourceDocumentNumber: string | null;
  conversionAction: string | null;
  followUpDocuments: number;
  openAmount: string | null;
};

type QuantityChainLine = {
  lineId: string;
  name: string;
  sourceQuantity: string;
  deliveredQuantity: string;
  invoicedQuantity: string;
  openQuantity: string;
};

type ProjectTimelineEntry = {
  documentId: string;
  documentNumber: string;
  documentKind: string;
  status: string;
  createdAt: string;
  sourceDocumentNumber: string;
  payableAmount: string;
};

type ProjectCaseOverview = {
  projectId: string;
  customerId: string;
  statusView: {
    documentCount: number;
    statuses: Record<string, number>;
  };
  timeline: ProjectTimelineEntry[];
  quantityChain: {
    followUpDocuments: number;
    lines: QuantityChainLine[];
    totals: {
      deliveredQuantity: string;
      invoicedQuantity: string;
      openQuantity: string;
    };
  };
};

type Props = {
  currentUserId?: number;
  executePlugin?: (payload: ExecutePayload) => Promise<unknown>;
  onClose?: () => void;
};

type BusinessLetterDraft = {
  documentKind: DocumentKind;
  customerName: string;
  customerStreet: string;
  customerPostalCode: string;
  customerCity: string;
  customerEmail: string;
  subject: string;
  introText: string;
  closingText: string;
  buyerReference: string;
  paymentReference: string;
  dueDate: string;
  offerValidUntil: string;
  deliveryDate: string;
  invoiceNumber: string;
  invoiceDate: string;
  invoiceAmount: string;
  originalInvoiceNumber: string;
  orderNumber: string;
  projectReference: string;
  serviceDescription: string;
  siteLocation: string;
  technician: string;
  acceptanceResult: string;
  defectList: string;
  responseDeadline: string;
  desiredResolution: string;
  sourceDocumentId: string;
  sourceDocumentNumber: string;
  sourceDocumentKind: string;
  projectId: string;
  customerId: string;
  revisionOf: string;
  cancelsDocumentId: string;
  conversionAction: string;
  selectedReferenceId: string;
  selectedSourceLineIds: string[];
  sourcePositionQuantities: Record<string, string>;
  positions: Position[];
  attachPdf: boolean;
  attachXml: boolean;
  validateBeforeSend: boolean;
  saveDocument: boolean;
  referenceDocuments: ReferenceDocument[];
  savedAt: string;
};

const BUSINESS_LETTER_PLUGIN_ID = "business_letter";

function isDraftShape(value: unknown): value is Partial<BusinessLetterDraft> {
  return typeof value === "object" && value != null;
}

function normalizeDraft(value: unknown): BusinessLetterDraft | null {
  if (!isDraftShape(value)) {
    return null;
  }
  const raw = value as Partial<BusinessLetterDraft>;
  const kind = String(raw.documentKind || "angebot") as DocumentKind;
  const config = DOCUMENT_TYPE_CONFIG[kind as DocumentKind];
  const safeKind = config ? kind : "angebot";
  const rawPositions = Array.isArray(raw.positions) ? raw.positions : [];
  const normalizedPositions = rawPositions.length > 0
    ? rawPositions.map((item) => {
      const position = item as Position;
      return {
        id: String(position.id || crypto.randomUUID()),
        description: String(position.description || ""),
        quantity: normalizeNumber(position.quantity, 1),
        unit: String(position.unit || "Stk."),
        unitPrice: normalizeNumber(position.unitPrice, 0),
        taxRate: normalizeNumber(position.taxRate, 19),
        stoneDetails: {
          materialType: String(position.stoneDetails?.materialType || ""),
          tradeName: String(position.stoneDetails?.tradeName || ""),
          origin: String(position.stoneDetails?.origin || ""),
          color: String(position.stoneDetails?.color || ""),
          surfaceFinish: String(position.stoneDetails?.surfaceFinish || ""),
          thicknessMm: String(position.stoneDetails?.thicknessMm || ""),
          lengthMm: String(position.stoneDetails?.lengthMm || ""),
          widthMm: String(position.stoneDetails?.widthMm || ""),
          edgeProfile: String(position.stoneDetails?.edgeProfile || ""),
          batch: String(position.stoneDetails?.batch || ""),
          blockNumber: String(position.stoneDetails?.blockNumber || ""),
          measurementNumber: String(position.stoneDetails?.measurementNumber || ""),
          installationLocation: String(position.stoneDetails?.installationLocation || ""),
        },
      } satisfies Position;
    })
    : [createPosition()];

  const rawReferences = Array.isArray(raw.referenceDocuments) ? raw.referenceDocuments : [];
  const referenceDocuments = rawReferences
    .filter((entry) => typeof entry === "object" && entry != null)
    .map((entry) => {
      const row = entry as ReferenceDocument;
      return {
        id: String(row.id || ""),
        number: String(row.number || ""),
        kind: String(row.kind || ""),
        subject: String(row.subject || ""),
        projectId: String(row.projectId || ""),
        customerId: String(row.customerId || ""),
        customerName: String(row.customerName || ""),
        customerStreet: String(row.customerStreet || ""),
        customerZip: String(row.customerZip || ""),
        customerCity: String(row.customerCity || ""),
        customerEmail: String(row.customerEmail || ""),
        issueDate: String(row.issueDate || ""),
        dueDate: String(row.dueDate || ""),
        totalAmount: String(row.totalAmount || ""),
        positions: Array.isArray(row.positions) ? row.positions : [],
      } satisfies ReferenceDocument;
    })
    .filter((entry) => entry.id.trim().length > 0);

  return {
    documentKind: safeKind,
    customerName: String(raw.customerName || ""),
    customerStreet: String(raw.customerStreet || ""),
    customerPostalCode: String(raw.customerPostalCode || ""),
    customerCity: String(raw.customerCity || ""),
    customerEmail: String(raw.customerEmail || ""),
    subject: String(raw.subject || ""),
    introText: String(raw.introText || ""),
    closingText: String(raw.closingText || ""),
    buyerReference: String(raw.buyerReference || ""),
    paymentReference: String(raw.paymentReference || ""),
    dueDate: String(raw.dueDate || ""),
    offerValidUntil: String(raw.offerValidUntil || ""),
    deliveryDate: String(raw.deliveryDate || ""),
    invoiceNumber: String(raw.invoiceNumber || ""),
    invoiceDate: String(raw.invoiceDate || ""),
    invoiceAmount: String(raw.invoiceAmount || ""),
    originalInvoiceNumber: String(raw.originalInvoiceNumber || ""),
    orderNumber: String(raw.orderNumber || ""),
    projectReference: String(raw.projectReference || ""),
    serviceDescription: String(raw.serviceDescription || ""),
    siteLocation: String(raw.siteLocation || ""),
    technician: String(raw.technician || ""),
    acceptanceResult: String(raw.acceptanceResult || ""),
    defectList: String(raw.defectList || ""),
    responseDeadline: String(raw.responseDeadline || ""),
    desiredResolution: String(raw.desiredResolution || ""),
    sourceDocumentId: String(raw.sourceDocumentId || ""),
    sourceDocumentNumber: String(raw.sourceDocumentNumber || ""),
    sourceDocumentKind: String(raw.sourceDocumentKind || ""),
    projectId: String(raw.projectId || ""),
    customerId: String(raw.customerId || ""),
    revisionOf: String(raw.revisionOf || ""),
    cancelsDocumentId: String(raw.cancelsDocumentId || ""),
    conversionAction: String(raw.conversionAction || ""),
    selectedReferenceId: String(raw.selectedReferenceId || ""),
    selectedSourceLineIds: Array.isArray(raw.selectedSourceLineIds)
      ? raw.selectedSourceLineIds.map((item) => String(item)).filter((item) => item.trim().length > 0)
      : [],
    sourcePositionQuantities:
      typeof raw.sourcePositionQuantities === "object" && raw.sourcePositionQuantities != null
        ? Object.fromEntries(
            Object.entries(raw.sourcePositionQuantities).map(([key, entry]) => [String(key), String(entry)]),
          )
        : {},
    positions: normalizedPositions,
    attachPdf: Boolean(raw.attachPdf),
    attachXml: Boolean(raw.attachXml),
    validateBeforeSend: Boolean(raw.validateBeforeSend),
    saveDocument: Boolean(raw.saveDocument),
    referenceDocuments,
    savedAt: String(raw.savedAt || ""),
  };
}

function createPosition(): Position {
  return {
    id: crypto.randomUUID(),
    description: "",
    quantity: 1,
    unit: "Stk.",
    unitPrice: 0,
    taxRate: 19,
    stoneDetails: {
      materialType: "",
      tradeName: "",
      origin: "",
      color: "",
      surfaceFinish: "",
      thicknessMm: "",
      lengthMm: "",
      widthMm: "",
      edgeProfile: "",
      batch: "",
      blockNumber: "",
      measurementNumber: "",
      installationLocation: "",
    },
  };
}

type ConversionOption = { value: string; label: string; sourceKind?: string; targetKind?: string };

const CONVERSION_ACTIONS: Partial<Record<DocumentKind, ConversionOption[]>> = {
  auftragsbestaetigung: [{ value: "angebot_to_auftragsbestaetigung", label: "Angebot -> Auftragsbestaetigung", sourceKind: "angebot", targetKind: "auftragsbestaetigung" }],
  lieferschein: [{ value: "auftragsbestaetigung_to_lieferschein", label: "Auftragsbestaetigung -> Lieferschein", sourceKind: "auftragsbestaetigung", targetKind: "lieferschein" }],
  rechnung: [{ value: "lieferschein_to_rechnung", label: "Lieferschein -> Rechnung", sourceKind: "lieferschein", targetKind: "rechnung" }],
  stornorechnung: [{ value: "rechnung_to_stornorechnung", label: "Rechnung -> Stornorechnung", sourceKind: "rechnung", targetKind: "stornorechnung" }],
  gutschrift: [{ value: "rechnung_to_gutschrift", label: "Rechnung -> Gutschrift", sourceKind: "rechnung", targetKind: "gutschrift" }],
  zahlungserinnerung: [{ value: "rechnung_to_zahlungserinnerung", label: "Rechnung -> Zahlungserinnerung", sourceKind: "rechnung", targetKind: "zahlungserinnerung" }],
  abnahmeprotokoll: [{ value: "montagebericht_to_abnahmeprotokoll", label: "Montagebericht -> Abnahmeprotokoll", sourceKind: "montagebericht", targetKind: "abnahmeprotokoll" }],
};

function normalizeNumber(value: unknown, fallback = 0): number {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

export function BusinessLetterManualPage({ currentUserId, executePlugin, onClose }: Props) {
  const applyingDraftRef = useRef(false);

  const [documentKind, setDocumentKind] = useState<DocumentKind>("angebot");
  const [customerName, setCustomerName] = useState("");
  const [customerStreet, setCustomerStreet] = useState("");
  const [customerPostalCode, setCustomerPostalCode] = useState("");
  const [customerCity, setCustomerCity] = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [introText, setIntroText] = useState("");
  const [closingText, setClosingText] = useState("");
  const [buyerReference, setBuyerReference] = useState("");
  const [paymentReference, setPaymentReference] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [offerValidUntil, setOfferValidUntil] = useState("");
  const [deliveryDate, setDeliveryDate] = useState("");
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [invoiceDate, setInvoiceDate] = useState("");
  const [invoiceAmount, setInvoiceAmount] = useState("");
  const [originalInvoiceNumber, setOriginalInvoiceNumber] = useState("");
  const [orderNumber, setOrderNumber] = useState("");
  const [projectReference, setProjectReference] = useState("");
  const [serviceDescription, setServiceDescription] = useState("");
  const [siteLocation, setSiteLocation] = useState("");
  const [technician, setTechnician] = useState("");
  const [acceptanceResult, setAcceptanceResult] = useState("");
  const [defectList, setDefectList] = useState("");
  const [responseDeadline, setResponseDeadline] = useState("");
  const [desiredResolution, setDesiredResolution] = useState("");
  const [sourceDocumentId, setSourceDocumentId] = useState("");
  const [sourceDocumentNumber, setSourceDocumentNumber] = useState("");
  const [sourceDocumentKind, setSourceDocumentKind] = useState("");
  const [projectId, setProjectId] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [revisionOf, setRevisionOf] = useState("");
  const [cancelsDocumentId, setCancelsDocumentId] = useState("");
  const [conversionAction, setConversionAction] = useState("");
  const [referenceDocuments, setReferenceDocuments] = useState<ReferenceDocument[]>([]);
  const [selectedReferenceId, setSelectedReferenceId] = useState("");
  const [selectedSourceLineIds, setSelectedSourceLineIds] = useState<string[]>([]);
  const [sourcePositionQuantities, setSourcePositionQuantities] = useState<Record<string, string>>({});
  const [positions, setPositions] = useState<Position[]>([createPosition()]);
  const [attachPdf, setAttachPdf] = useState(true);
  const [attachXml, setAttachXml] = useState(false);
  const [validateBeforeSend, setValidateBeforeSend] = useState(true);
  const [saveDocument, setSaveDocument] = useState(true);
  const [projectCase, setProjectCase] = useState<ProjectCaseOverview | null>(null);

  const config = DOCUMENT_TYPE_CONFIG[documentKind];
  const visibleFields = config.visibleFields;
  const conversionOptions = CONVERSION_ACTIONS[documentKind] ?? [];
  const selectedReference = referenceDocuments.find((item) => item.id === selectedReferenceId) ?? null;
  const activeConversionOption = conversionOptions.find((item) => item.value === conversionAction) ?? null;

  const handleDocumentSectionChange = useCallback(
    (field: "subject" | "buyerReference" | "paymentReference" | "offerValidUntil" | "deliveryDate" | "dueDate" | "invoiceNumber" | "invoiceDate" | "invoiceAmount" | "originalInvoiceNumber" | "orderNumber" | "projectReference", value: string) => {
      switch (field) {
        case "subject":
          setSubject(value);
          break;
        case "buyerReference":
          setBuyerReference(value);
          break;
        case "paymentReference":
          setPaymentReference(value);
          break;
        case "offerValidUntil":
          setOfferValidUntil(value);
          break;
        case "deliveryDate":
          setDeliveryDate(value);
          break;
        case "dueDate":
          setDueDate(value);
          break;
        case "invoiceNumber":
          setInvoiceNumber(value);
          break;
        case "invoiceDate":
          setInvoiceDate(value);
          break;
        case "invoiceAmount":
          setInvoiceAmount(value);
          break;
        case "originalInvoiceNumber":
          setOriginalInvoiceNumber(value);
          break;
        case "orderNumber":
          setOrderNumber(value);
          break;
        case "projectReference":
          setProjectReference(value);
          break;
      }
    },
    [],
  );

  const handleRecipientSectionChange = useCallback(
    (field: "name" | "street" | "postalCode" | "city" | "email", value: string) => {
      switch (field) {
        case "name":
          setCustomerName(value);
          break;
        case "street":
          setCustomerStreet(value);
          break;
        case "postalCode":
          setCustomerPostalCode(value);
          break;
        case "city":
          setCustomerCity(value);
          break;
        case "email":
          setCustomerEmail(value);
          break;
      }
    },
    [],
  );

  const handleTextSectionChange = useCallback(
    (field: "introText" | "closingText" | "serviceDescription" | "siteLocation" | "technician" | "acceptanceResult" | "defectList" | "responseDeadline" | "desiredResolution", value: string) => {
      switch (field) {
        case "introText":
          setIntroText(value);
          break;
        case "closingText":
          setClosingText(value);
          break;
        case "serviceDescription":
          setServiceDescription(value);
          break;
        case "siteLocation":
          setSiteLocation(value);
          break;
        case "technician":
          setTechnician(value);
          break;
        case "acceptanceResult":
          setAcceptanceResult(value);
          break;
        case "defectList":
          setDefectList(value);
          break;
        case "responseDeadline":
          setResponseDeadline(value);
          break;
        case "desiredResolution":
          setDesiredResolution(value);
          break;
      }
    },
    [],
  );

  const handleConversionActionChange = useCallback(
    (nextValue: string) => {
      setConversionAction(nextValue);
      const option = conversionOptions.find((entry) => entry.value === nextValue);
      setSourceDocumentKind(option?.sourceKind || "");
    },
    [conversionOptions],
  );

  const handleRelationshipFieldChange = useCallback(
    (
      field:
        | "sourceDocumentId"
        | "sourceDocumentNumber"
        | "sourceDocumentKind"
        | "projectId"
        | "customerId"
        | "revisionOf"
        | "cancelsDocumentId",
      value: string,
    ) => {
      switch (field) {
        case "sourceDocumentId":
          setSourceDocumentId(value);
          break;
        case "sourceDocumentNumber":
          setSourceDocumentNumber(value);
          break;
        case "sourceDocumentKind":
          setSourceDocumentKind(value);
          break;
        case "projectId":
          setProjectId(value);
          break;
        case "customerId":
          setCustomerId(value);
          break;
        case "revisionOf":
          setRevisionOf(value);
          break;
        case "cancelsDocumentId":
          setCancelsDocumentId(value);
          break;
      }
    },
    [],
  );

  const draftSnapshot = useMemo<BusinessLetterDraft>(
    () => ({
      documentKind,
      customerName,
      customerStreet,
      customerPostalCode,
      customerCity,
      customerEmail,
      subject,
      introText,
      closingText,
      buyerReference,
      paymentReference,
      dueDate,
      offerValidUntil,
      deliveryDate,
      invoiceNumber,
      invoiceDate,
      invoiceAmount,
      originalInvoiceNumber,
      orderNumber,
      projectReference,
      serviceDescription,
      siteLocation,
      technician,
      acceptanceResult,
      defectList,
      responseDeadline,
      desiredResolution,
      sourceDocumentId,
      sourceDocumentNumber,
      sourceDocumentKind,
      projectId,
      customerId,
      revisionOf,
      cancelsDocumentId,
      conversionAction,
      selectedReferenceId,
      selectedSourceLineIds,
      sourcePositionQuantities,
      positions,
      attachPdf,
      attachXml,
      validateBeforeSend,
      saveDocument,
      referenceDocuments,
      savedAt: new Date().toISOString(),
    }),
    [
      documentKind,
      customerName,
      customerStreet,
      customerPostalCode,
      customerCity,
      customerEmail,
      subject,
      introText,
      closingText,
      buyerReference,
      paymentReference,
      dueDate,
      offerValidUntil,
      deliveryDate,
      invoiceNumber,
      invoiceDate,
      invoiceAmount,
      originalInvoiceNumber,
      orderNumber,
      projectReference,
      serviceDescription,
      siteLocation,
      technician,
      acceptanceResult,
      defectList,
      responseDeadline,
      desiredResolution,
      sourceDocumentId,
      sourceDocumentNumber,
      sourceDocumentKind,
      projectId,
      customerId,
      revisionOf,
      cancelsDocumentId,
      conversionAction,
      selectedReferenceId,
      selectedSourceLineIds,
      sourcePositionQuantities,
      positions,
      attachPdf,
      attachXml,
      validateBeforeSend,
      saveDocument,
      referenceDocuments,
    ],
  );

  const applyDraft = useCallback((draft: BusinessLetterDraft) => {
    applyingDraftRef.current = true;
    setDocumentKind(draft.documentKind);
    setCustomerName(draft.customerName);
    setCustomerStreet(draft.customerStreet);
    setCustomerPostalCode(draft.customerPostalCode);
    setCustomerCity(draft.customerCity);
    setCustomerEmail(draft.customerEmail);
    setSubject(draft.subject);
    setIntroText(draft.introText);
    setClosingText(draft.closingText);
    setBuyerReference(draft.buyerReference);
    setPaymentReference(draft.paymentReference);
    setDueDate(draft.dueDate);
    setOfferValidUntil(draft.offerValidUntil);
    setDeliveryDate(draft.deliveryDate);
    setInvoiceNumber(draft.invoiceNumber);
    setInvoiceDate(draft.invoiceDate);
    setInvoiceAmount(draft.invoiceAmount);
    setOriginalInvoiceNumber(draft.originalInvoiceNumber);
    setOrderNumber(draft.orderNumber);
    setProjectReference(draft.projectReference);
    setServiceDescription(draft.serviceDescription);
    setSiteLocation(draft.siteLocation);
    setTechnician(draft.technician);
    setAcceptanceResult(draft.acceptanceResult);
    setDefectList(draft.defectList);
    setResponseDeadline(draft.responseDeadline);
    setDesiredResolution(draft.desiredResolution);
    setSourceDocumentId(draft.sourceDocumentId);
    setSourceDocumentNumber(draft.sourceDocumentNumber);
    setSourceDocumentKind(draft.sourceDocumentKind);
    setProjectId(draft.projectId);
    setCustomerId(draft.customerId);
    setRevisionOf(draft.revisionOf);
    setCancelsDocumentId(draft.cancelsDocumentId);
    setConversionAction(draft.conversionAction);
    setSelectedReferenceId(draft.selectedReferenceId);
    setSelectedSourceLineIds(draft.selectedSourceLineIds);
    setSourcePositionQuantities(draft.sourcePositionQuantities);
    setPositions(draft.positions.length > 0 ? draft.positions : [createPosition()]);
    setAttachPdf(draft.attachPdf);
    setAttachXml(draft.attachXml);
    setValidateBeforeSend(draft.validateBeforeSend);
    setSaveDocument(draft.saveDocument);
    setReferenceDocuments(draft.referenceDocuments);
  }, []);

  useEffect(() => {
    if (applyingDraftRef.current) {
      applyingDraftRef.current = false;
      return;
    }
    if (conversionOptions.length === 1) {
      setConversionAction(conversionOptions[0].value);
      setSourceDocumentKind(conversionOptions[0].sourceKind || "");
    } else if (conversionOptions.length === 0) {
      setConversionAction("");
      setSourceDocumentKind("");
    }
  }, [conversionOptions]);

  useEffect(() => {
    if (!config.supportsEInvoice && attachXml) {
      setAttachXml(false);
    }
  }, [attachXml, config.supportsEInvoice]);

  const { draftStatus, draftMessage, saveDraftNow, reloadDraftNow } = usePluginDraft<BusinessLetterDraft>({
    pluginId: BUSINESS_LETTER_PLUGIN_ID,
    currentUserId,
    draftSnapshot,
    applyDraft,
    normalizeDraft,
    applyingDraftRef,
    autosaveDelayMs: 700,
  });

  useEffect(() => {
    if (!selectedReference) {
      setSelectedSourceLineIds([]);
      setSourcePositionQuantities({});
      return;
    }
    const nextLineIds = selectedReference.positions.map((position) => position.lineId);
    const nextQuantities: Record<string, string> = {};
    selectedReference.positions.forEach((position) => {
      nextQuantities[position.lineId] = String(position.quantity || 0);
    });
    setSelectedSourceLineIds(nextLineIds);
    setSourcePositionQuantities(nextQuantities);
  }, [selectedReference]);

  const applyReferenceSelection = () => {
    if (!selectedReference) {
      return;
    }

    setSourceDocumentId(selectedReference.id);
    setSourceDocumentNumber(selectedReference.number);
    setSourceDocumentKind(selectedReference.kind);
    if (!projectId.trim() && selectedReference.projectId) {
      setProjectId(selectedReference.projectId);
    }
    if (!customerId.trim() && selectedReference.customerId) {
      setCustomerId(selectedReference.customerId);
    }
    if (!customerName.trim() && selectedReference.customerName) {
      setCustomerName(selectedReference.customerName);
    }
    if (!customerStreet.trim() && selectedReference.customerStreet) {
      setCustomerStreet(selectedReference.customerStreet);
    }
    if (!customerPostalCode.trim() && selectedReference.customerZip) {
      setCustomerPostalCode(selectedReference.customerZip);
    }
    if (!customerCity.trim() && selectedReference.customerCity) {
      setCustomerCity(selectedReference.customerCity);
    }
    if (!customerEmail.trim() && selectedReference.customerEmail) {
      setCustomerEmail(selectedReference.customerEmail);
    }

    const chosenOption = conversionOptions.find((item) => item.value === conversionAction) ?? conversionOptions[0];
    if (chosenOption) {
      setConversionAction(chosenOption.value);
      setSourceDocumentKind(chosenOption.sourceKind || selectedReference.kind);
    }

    if (config.requiresPositions && selectedReference.positions.length > 0) {
      const nextPositions = selectedReference.positions
        .filter((position) => selectedSourceLineIds.includes(position.lineId))
        .map((position) => {
          const quantityText = sourcePositionQuantities[position.lineId] ?? String(position.quantity || 0);
          return {
            id: crypto.randomUUID(),
            description: position.description || position.name,
            quantity: normalizeNumber(quantityText, position.quantity),
            unit: position.unitCode,
            unitPrice: position.priceNet,
            taxRate: position.vatRate,
            stoneDetails: {
              materialType: String(position.stoneDetails.material_type || ""),
              tradeName: String(position.stoneDetails.trade_name || ""),
              origin: String(position.stoneDetails.origin || ""),
              color: String(position.stoneDetails.color || ""),
              surfaceFinish: String(position.stoneDetails.surface_finish || ""),
              thicknessMm: String(position.stoneDetails.thickness_mm || ""),
              lengthMm: String(position.stoneDetails.length_mm || ""),
              widthMm: String(position.stoneDetails.width_mm || ""),
              edgeProfile: String(position.stoneDetails.edge_profile || ""),
              batch: String(position.stoneDetails.batch || ""),
              blockNumber: String(position.stoneDetails.block_number || ""),
              measurementNumber: String(position.stoneDetails.measurement_number || ""),
              installationLocation: String(position.stoneDetails.installation_location || ""),
            },
          } as Position;
        });
      if (nextPositions.length > 0) {
        setPositions(nextPositions);
      }
    }
  };

  const toggleSourceLineSelection = (lineId: string, checked: boolean) => {
    setSelectedSourceLineIds((current) => {
      if (checked) {
        return current.includes(lineId) ? current : [...current, lineId];
      }
      return current.filter((item) => item !== lineId);
    });
  };

  const updateSourceQuantity = (lineId: string, value: string) => {
    setSourcePositionQuantities((current) => ({ ...current, [lineId]: value }));
  };

  const totals = useMemo(() => {
    const net = positions.reduce((sum, position) => sum + position.quantity * position.unitPrice, 0);
    const tax = positions.reduce(
      (sum, position) => sum + position.quantity * position.unitPrice * (position.taxRate / 100),
      0,
    );
    return { net, tax, gross: net + tax };
  }, [positions]);

  const updatePosition = <K extends keyof Position>(id: string, key: K, value: Position[K]) => {
    setPositions((current) => current.map((position) => (position.id === id ? { ...position, [key]: value } : position)));
  };

  const updateStoneDetail = (id: string, key: keyof Position["stoneDetails"], value: string) => {
    setPositions((current) =>
      current.map((position) =>
        position.id === id
          ? { ...position, stoneDetails: { ...position.stoneDetails, [key]: value } }
          : position,
      ),
    );
  };

  const removePosition = (id: string) => {
    setPositions((current) => (current.length === 1 ? current : current.filter((item) => item.id !== id)));
  };

  const validateForm = (): string[] => {
    const fieldChecks: Record<FrontendFieldKey, string> = {
      subject: subject.trim(),
      buyerReference: buyerReference.trim(),
      paymentReference: paymentReference.trim(),
      offerValidUntil,
      deliveryDate,
      dueDate,
      invoiceNumber: invoiceNumber.trim(),
      invoiceDate,
      invoiceAmount: invoiceAmount.trim(),
      originalInvoiceNumber: originalInvoiceNumber.trim(),
      orderNumber: orderNumber.trim(),
      projectReference: projectReference.trim(),
      serviceDescription: serviceDescription.trim(),
      siteLocation: siteLocation.trim(),
      technician: technician.trim(),
      acceptanceResult: acceptanceResult.trim(),
      defectList: defectList.trim(),
      responseDeadline,
      desiredResolution: desiredResolution.trim(),
    };

    return validateBusinessLetterForm({
      documentKind,
      customerName,
      subject,
      sourceDocumentNumber,
      sourceDocumentId,
      sourceDocumentKind,
      originalInvoiceNumber,
      conversionAction,
      selectedSourceLineIds,
      sourcePositionQuantities,
      positions,
      selectedReference,
      requiresPositions: config.requiresPositions,
      supportsEInvoice: config.supportsEInvoice,
      attachXml,
      activeConversionOption,
      requiredFields: config.requiredFields,
      fieldChecks,
    });
  };

  const buildPayload = (): ExecutePayload =>
    buildBusinessLetterPayload({
      currentUserId,
      documentKind,
      customerName,
      customerStreet,
      customerPostalCode,
      customerCity,
      customerEmail,
      subject,
      buyerReference,
      paymentReference,
      projectReference,
      projectId,
      customerId,
      orderNumber,
      originalInvoiceNumber,
      sourceDocumentId,
      sourceDocumentNumber,
      sourceDocumentKind,
      revisionOf,
      cancelsDocumentId,
      conversionAction,
      invoiceNumber,
      invoiceDate,
      invoiceAmount,
      dueDate,
      deliveryDate,
      offerValidUntil,
      responseDeadline,
      introText,
      closingText,
      serviceDescription,
      acceptanceResult,
      defectList,
      desiredResolution,
      saveDocument,
      validateBeforeSend,
      attachPdf,
      attachXml,
      supportsEInvoice: config.supportsEInvoice,
      requiresPositions: config.requiresPositions,
      selectedReference,
      selectedSourceLineIds,
      sourcePositionQuantities,
      positions,
      technician,
      siteLocation,
    });

  const {
    result,
    error,
    running,
    projectCaseLoading,
    pendingConfirmation,
    submit,
    confirmPendingExecution,
    loadProjectCaseOverview,
  } = useBusinessLetterExecution({
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
  });

  useEffect(() => {
    const reference = extractReferenceDocument(result);
    if (!reference) {
      return;
    }
    setReferenceDocuments((current) => {
      const withoutCurrent = current.filter((item) => item.id !== reference.id);
      return [reference, ...withoutCurrent].slice(0, 20);
    });
  }, [result]);

  useEffect(() => {
    const nextProjectCase = extractProjectCaseOverview(result);
    if (!nextProjectCase) {
      return;
    }
    setProjectCase(nextProjectCase);
  }, [result]);

  const resultSummary = useMemo(() => summarizeResult(result), [result]);

  return (
    <div className="business-letter-page">
      <BusinessLetterHeader onClose={onClose} />

      <form className="business-letter-layout" onSubmit={submit}>
        <main className="business-letter-main">
          <DocumentSection
            value={{
              documentKind,
              subject,
              buyerReference,
              paymentReference,
              offerValidUntil,
              deliveryDate,
              dueDate,
              invoiceNumber,
              invoiceDate,
              invoiceAmount,
              originalInvoiceNumber,
              orderNumber,
              projectReference,
            }}
            visibleFields={visibleFields}
            hint={config.hint}
            onDocumentKindChange={setDocumentKind}
            onChange={handleDocumentSectionChange}
          />

          <RelationshipSection
            conversionOptions={conversionOptions}
            conversionAction={conversionAction}
            selectedReferenceId={selectedReferenceId}
            referenceDocuments={referenceDocuments}
            selectedReference={selectedReference}
            selectedSourceLineIds={selectedSourceLineIds}
            sourcePositionQuantities={sourcePositionQuantities}
            projectCase={projectCase}
            projectCaseLoading={projectCaseLoading}
            fields={{
              sourceDocumentId,
              sourceDocumentNumber,
              sourceDocumentKind,
              projectId,
              customerId,
              revisionOf,
              cancelsDocumentId,
            }}
            onConversionActionChange={handleConversionActionChange}
            onSelectedReferenceChange={setSelectedReferenceId}
            onApplyReferenceSelection={applyReferenceSelection}
            onLoadProjectCaseOverview={loadProjectCaseOverview}
            onToggleSourceLineSelection={toggleSourceLineSelection}
            onUpdateSourceQuantity={updateSourceQuantity}
            onRelationshipFieldChange={handleRelationshipFieldChange}
          />

          <RecipientSection
            value={{
              name: customerName,
              street: customerStreet,
              postalCode: customerPostalCode,
              city: customerCity,
              email: customerEmail,
            }}
            onChange={handleRecipientSectionChange}
          />

          {config.requiresPositions ? (
            <PositionSection
              positions={positions}
              onAddPosition={() => setPositions((current) => [...current, createPosition()])}
              onUpdatePosition={(id, key, value) => updatePosition(id, key, value as Position[typeof key])}
              onUpdateStoneDetail={updateStoneDetail}
              onRemovePosition={removePosition}
            />
          ) : null}

          <TextSection
            value={{
              introText,
              closingText,
              serviceDescription,
              siteLocation,
              technician,
              acceptanceResult,
              defectList,
              responseDeadline,
              desiredResolution,
            }}
            visibleFields={visibleFields}
            onChange={handleTextSectionChange}
          />
        </main>

        <BusinessLetterSidebar
          config={{
            label: config.label,
            category: config.category,
            requiresPositions: config.requiresPositions,
            supportsEInvoice: config.supportsEInvoice,
          }}
          positionsCount={positions.length}
          totals={totals}
          currentUserId={currentUserId}
          draftStatus={draftStatus}
          draftMessage={draftMessage}
          saveDraftNow={saveDraftNow}
          reloadDraftNow={reloadDraftNow}
          attachPdf={attachPdf}
          attachXml={attachXml}
          validateBeforeSend={validateBeforeSend}
          saveDocument={saveDocument}
          setAttachPdf={setAttachPdf}
          setAttachXml={setAttachXml}
          setValidateBeforeSend={setValidateBeforeSend}
          setSaveDocument={setSaveDocument}
          error={error}
          pendingConfirmation={pendingConfirmation}
          running={running}
          confirmPendingExecution={confirmPendingExecution}
          result={result}
          resultSummary={resultSummary}
          showTechnicalResponse={shouldShowTechnicalResponse(import.meta.env.DEV)}
        />
      </form>
    </div>
  );
}

export default BusinessLetterManualPage;