import type { DocumentKind } from "../documentTypeConfig";

export type StoneDetails = {
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

export type Position = {
  id: string;
  description: string;
  quantity: number;
  unit: string;
  unitPrice: number;
  taxRate: number;
  stoneDetails: StoneDetails;
};

export type ReferencePosition = {
  lineId: string;
  name: string;
  description: string;
  quantity: number;
  unitCode: string;
  priceNet: number;
  vatRate: number;
  stoneDetails: Record<string, unknown>;
};

export type ReferenceDocument = {
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

export type ExecutePayload = {
  pluginId: string;
  pluginInput?: Record<string, unknown>;
  pluginSettings?: Record<string, unknown>;
  userId?: number;
};

export type ConversionOption = { value: string; label: string; sourceKind?: string; targetKind?: string };

export type BusinessLetterResultSummary = {
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

export type QuantityChainLine = {
  lineId: string;
  name: string;
  sourceQuantity: string;
  deliveredQuantity: string;
  invoicedQuantity: string;
  openQuantity: string;
};

export type ProjectTimelineEntry = {
  documentId: string;
  documentNumber: string;
  documentKind: string;
  status: string;
  createdAt: string;
  sourceDocumentNumber: string;
  payableAmount: string;
};

export type ProjectCaseOverview = {
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

export type BusinessLetterDraft = {
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

export type BusinessLetterValidationState = {
  documentKind: DocumentKind;
  customerName: string;
  subject: string;
  sourceDocumentNumber: string;
  sourceDocumentId: string;
  sourceDocumentKind: string;
  originalInvoiceNumber: string;
  conversionAction: string;
  selectedSourceLineIds: string[];
  sourcePositionQuantities: Record<string, string>;
  positions: Position[];
  selectedReference: ReferenceDocument | null;
  requiresPositions: boolean;
  supportsEInvoice: boolean;
  attachXml: boolean;
  activeConversionOption: ConversionOption | null;
  requiredFields: string[];
  fieldChecks: Record<string, string>;
};
