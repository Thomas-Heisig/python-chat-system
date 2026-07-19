import type { FrontendFieldKey } from "../documentTypeConfig";
import { parsePositiveNumber } from "./businessLetterResult";
import type { BusinessLetterValidationState } from "./types";

const FIELD_LABELS: Record<FrontendFieldKey, string> = {
  subject: "Betreff",
  buyerReference: "Käuferreferenz",
  paymentReference: "Zahlungsreferenz",
  offerValidUntil: "Angebotsgültigkeit",
  deliveryDate: "Liefer- / Leistungsdatum",
  dueDate: "Fälligkeitsdatum",
  invoiceNumber: "Rechnungsnummer",
  invoiceDate: "Rechnungsdatum",
  invoiceAmount: "Rechnungsbetrag",
  originalInvoiceNumber: "Ursprungsrechnung",
  orderNumber: "Auftragsnummer",
  projectReference: "Projektreferenz",
  serviceDescription: "Leistungs- / Fehlerbeschreibung",
  siteLocation: "Baustelle / Einsatzort",
  technician: "Monteur / Mitarbeiter",
  acceptanceResult: "Abnahmeergebnis",
  defectList: "Mängelliste",
  responseDeadline: "Rückmeldung bis",
  desiredResolution: "Gewünschte Lösung",
};

export function validateBusinessLetterForm(state: BusinessLetterValidationState): string[] {
  const errors: string[] = [];
  if (!state.customerName.trim()) {
    errors.push("Bitte einen Empfaenger angeben.");
  }
  if (!state.subject.trim()) {
    errors.push("Bitte einen Betreff angeben.");
  }
  if (state.requiresPositions && state.positions.some((position) => !position.description.trim())) {
    errors.push("Jede Position benötigt eine Beschreibung.");
  }
  if (state.requiresPositions) {
    for (const position of state.positions) {
      const quantity = parsePositiveNumber(position.quantity);
      const unitPrice = parsePositiveNumber(position.unitPrice);
      const taxRate = parsePositiveNumber(position.taxRate);
      if (quantity == null || quantity <= 0) {
        errors.push(`Position „${position.description || "ohne Bezeichnung"}“ benötigt eine Menge größer 0.`);
        break;
      }
      if (unitPrice == null || unitPrice < 0) {
        errors.push(`Position „${position.description || "ohne Bezeichnung"}“ hat einen ungültigen Einzelpreis.`);
        break;
      }
      if (taxRate == null || taxRate < 0 || taxRate > 100) {
        errors.push(`Position „${position.description || "ohne Bezeichnung"}“ hat einen ungültigen Steuersatz.`);
        break;
      }
    }
  }
  if (state.conversionAction && !state.sourceDocumentNumber.trim() && !state.sourceDocumentId.trim()) {
    errors.push("Bei Konvertierungsaktionen ist ein Quelldokument erforderlich.");
  }
  if (state.conversionAction && state.selectedReference && state.requiresPositions && state.selectedSourceLineIds.length === 0) {
    errors.push("Bitte mindestens eine Quellposition für das Folgedokument auswählen.");
  }
  if (state.conversionAction && state.activeConversionOption?.sourceKind && state.sourceDocumentKind.trim()) {
    if (state.sourceDocumentKind.trim().toLowerCase() !== state.activeConversionOption.sourceKind.toLowerCase()) {
      errors.push("Quelldokument-Typ passt nicht zur gewählten Konvertierungsaktion.");
    }
  }
  if (state.conversionAction && state.selectedReference && state.activeConversionOption?.sourceKind) {
    if (state.selectedReference.kind.toLowerCase() !== state.activeConversionOption.sourceKind.toLowerCase()) {
      errors.push("Ausgewähltes Referenzdokument passt nicht zur Konvertierungsaktion.");
    }
  }

  if (state.conversionAction && state.selectedReference && state.selectedSourceLineIds.length > 0) {
    for (const lineId of state.selectedSourceLineIds) {
      const sourceLine = state.selectedReference.positions.find((item) => item.lineId === lineId);
      const requested = parsePositiveNumber(state.sourcePositionQuantities[lineId]);
      if (!sourceLine || requested == null || requested <= 0) {
        errors.push("Übernahme-Mengen müssen numerisch und größer 0 sein.");
        break;
      }
      if (requested > sourceLine.quantity) {
        errors.push(`Teilmengen dürfen die Quellmenge nicht überschreiten (Position ${lineId}).`);
        break;
      }
    }
  }

  if (state.attachXml && !state.supportsEInvoice) {
    errors.push("XML-Ausgabe ist für diesen Dokumenttyp nicht zulässig.");
  }

  const normalizedKind = state.documentKind.toLowerCase();
  if (normalizedKind === "stornorechnung" && !state.originalInvoiceNumber.trim() && !state.sourceDocumentId.trim() && !state.sourceDocumentNumber.trim()) {
    errors.push("Stornorechnung benötigt eine Ursprungsrechnung.");
  }
  if (normalizedKind === "gutschrift" && !state.originalInvoiceNumber.trim() && !state.sourceDocumentId.trim() && !state.sourceDocumentNumber.trim()) {
    errors.push("Gutschrift benötigt ein Bezugsdokument.");
  }

  for (const requiredKey of state.requiredFields) {
    const fieldKey = requiredKey as FrontendFieldKey;
    const value = state.fieldChecks[requiredKey] ?? "";
    if (!value) {
      const fieldLabel = FIELD_LABELS[fieldKey] ?? requiredKey;
      errors.push(`Bitte das Feld „${fieldLabel}“ ausfüllen.`);
    }
  }
  return errors;
}
