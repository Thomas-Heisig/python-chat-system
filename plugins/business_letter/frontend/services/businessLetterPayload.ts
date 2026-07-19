import type { DocumentKind } from "../documentTypeConfig";
import type { ExecutePayload, Position, ReferenceDocument } from "./types";

export type BuildPayloadInput = {
  currentUserId?: number;
  documentKind: DocumentKind;
  customerName: string;
  customerStreet: string;
  customerPostalCode: string;
  customerCity: string;
  customerEmail: string;
  subject: string;
  buyerReference: string;
  paymentReference: string;
  projectReference: string;
  projectId: string;
  customerId: string;
  orderNumber: string;
  originalInvoiceNumber: string;
  sourceDocumentId: string;
  sourceDocumentNumber: string;
  sourceDocumentKind: string;
  revisionOf: string;
  cancelsDocumentId: string;
  conversionAction: string;
  invoiceNumber: string;
  invoiceDate: string;
  invoiceAmount: string;
  dueDate: string;
  deliveryDate: string;
  offerValidUntil: string;
  responseDeadline: string;
  introText: string;
  closingText: string;
  serviceDescription: string;
  acceptanceResult: string;
  defectList: string;
  desiredResolution: string;
  saveDocument: boolean;
  validateBeforeSend: boolean;
  attachPdf: boolean;
  attachXml: boolean;
  supportsEInvoice: boolean;
  requiresPositions: boolean;
  selectedReference: ReferenceDocument | null;
  selectedSourceLineIds: string[];
  sourcePositionQuantities: Record<string, string>;
  positions: Position[];
  technician: string;
  siteLocation: string;
};

export function buildBusinessLetterPayload(input: BuildPayloadInput): ExecutePayload {
  const pluginInput: Record<string, unknown> = {
    action: "create_document",
    letter_type: input.documentKind,
    document_kind: input.documentKind,
    customer: {
      name: input.customerName.trim(),
      street: input.customerStreet.trim(),
      postal_code: input.customerPostalCode.trim(),
      city: input.customerCity.trim(),
      email: input.customerEmail.trim() || undefined,
    },
    recipient_name: input.customerName.trim(),
    recipient_street: input.customerStreet.trim(),
    recipient_zip: input.customerPostalCode.trim(),
    recipient_city: input.customerCity.trim(),
    recipient_email: input.customerEmail.trim() || undefined,
    subject: input.subject.trim(),
    buyer_reference: input.buyerReference.trim() || undefined,
    payment_reference: input.paymentReference.trim() || undefined,
    project_reference: input.projectReference.trim() || undefined,
    project_id: input.projectId.trim() || undefined,
    customer_id: input.customerId.trim() || undefined,
    order_number: input.orderNumber.trim() || undefined,
    original_invoice_number: input.originalInvoiceNumber.trim() || undefined,
    source_document_id: input.sourceDocumentId.trim() || undefined,
    source_document_number: input.sourceDocumentNumber.trim() || undefined,
    source_document_kind: input.sourceDocumentKind.trim() || undefined,
    revision_of: input.revisionOf.trim() || undefined,
    cancels_document_id: input.cancelsDocumentId.trim() || undefined,
    conversion_action: input.conversionAction.trim() || undefined,
    invoice_number: input.invoiceNumber.trim() || undefined,
    invoice_date: input.invoiceDate || undefined,
    invoice_amount: input.invoiceAmount.trim() || undefined,
    due_date: input.dueDate || undefined,
    delivery_date: input.deliveryDate || undefined,
    offer_valid_until: input.offerValidUntil || undefined,
    response_deadline: input.responseDeadline || undefined,
    intro_text: input.introText.trim() || undefined,
    closing_text: input.closingText.trim() || undefined,
    content:
      [input.serviceDescription.trim(), input.acceptanceResult.trim(), input.defectList.trim(), input.desiredResolution.trim()]
        .filter(Boolean)
        .join("\n\n") || undefined,
    service_period_start: input.deliveryDate || undefined,
    generate_templates: true,
    persist_to_database: input.saveDocument,
    validate_before_send: input.validateBeforeSend,
    ready_for_sending: false,
    output: {
      attach_pdf: input.attachPdf,
      attach_xml: input.attachXml && input.supportsEInvoice,
      validate_before_send: input.validateBeforeSend,
      persist: input.saveDocument,
    },
  };

  if (input.selectedReference && input.conversionAction.trim()) {
    const selectedPositions = input.selectedReference.positions
      .filter((position) => input.selectedSourceLineIds.includes(position.lineId))
      .map((position) => ({
        line_id: position.lineId,
        name: position.name,
        description: position.description,
        quantity: input.sourcePositionQuantities[position.lineId] || String(position.quantity),
        unit_code: position.unitCode,
        price_net: position.priceNet,
        vat_category: "S",
        vat_rate: position.vatRate,
        stone_details: position.stoneDetails,
      }));

    pluginInput.source_document = {
      document_id: input.selectedReference.id,
      document_number: input.selectedReference.number,
      document_kind: input.selectedReference.kind,
      project_id: input.selectedReference.projectId || undefined,
      customer_id: input.selectedReference.customerId || undefined,
      document: {
        subject: input.selectedReference.subject,
        recipient: {
          name: input.selectedReference.customerName,
          street: input.selectedReference.customerStreet,
          postal_code: input.selectedReference.customerZip,
          city: input.selectedReference.customerCity,
          email: input.selectedReference.customerEmail,
        },
        relationships: {
          project_id: input.selectedReference.projectId,
          customer_id: input.selectedReference.customerId,
        },
      },
      commercial_document: {
        document_kind: input.selectedReference.kind,
        customer_visible: {
          issue_date: input.selectedReference.issueDate,
          payment_due_date: input.selectedReference.dueDate,
          totals: {
            payable_amount: input.selectedReference.totalAmount,
          },
        },
        positions: selectedPositions,
      },
    };
    pluginInput.source_position_line_ids = input.selectedSourceLineIds;
    pluginInput.source_position_quantities = input.sourcePositionQuantities;
  }

  if (input.requiresPositions) {
    pluginInput.positions = input.positions.map((position, index) => ({
      line_id: `${index + 1}`,
      name: position.description,
      quantity: position.quantity,
      unit_code: position.unit === "Stk." ? "C62" : position.unit,
      price_net: position.unitPrice,
      vat_category: "S",
      vat_rate: position.taxRate,
      stone_details: {
        material_type: position.stoneDetails.materialType || undefined,
        trade_name: position.stoneDetails.tradeName || undefined,
        origin: position.stoneDetails.origin || undefined,
        color: position.stoneDetails.color || undefined,
        surface_finish: position.stoneDetails.surfaceFinish || undefined,
        thickness_mm: position.stoneDetails.thicknessMm || undefined,
        length_mm: position.stoneDetails.lengthMm || undefined,
        width_mm: position.stoneDetails.widthMm || undefined,
        edge_profile: position.stoneDetails.edgeProfile || undefined,
        batch: position.stoneDetails.batch || undefined,
        block_number: position.stoneDetails.blockNumber || undefined,
        measurement_number: position.stoneDetails.measurementNumber || undefined,
        installation_location: position.stoneDetails.installationLocation || undefined,
      },
    }));
  }

  if (input.supportsEInvoice) {
    pluginInput.einvoice = {
      enabled: input.attachXml,
      standard: "xrechnung",
      profile: "en16931",
      syntax: "UBL",
    };
  }

  if (input.technician.trim()) {
    pluginInput.customer_contact = input.technician.trim();
  }
  if (input.siteLocation.trim()) {
    pluginInput.project_reference = input.siteLocation.trim();
  }

  return {
    pluginId: "business_letter",
    userId: input.currentUserId,
    pluginInput,
    pluginSettings: {
      default_attach_pdf: input.attachPdf,
      default_attach_xml: input.attachXml && input.supportsEInvoice,
      validate_before_send: input.validateBeforeSend,
    },
  };
}
