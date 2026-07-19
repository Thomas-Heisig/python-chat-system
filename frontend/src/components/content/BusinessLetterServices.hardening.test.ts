import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { shouldShowTechnicalResponse } from "../../../../plugins/business_letter/frontend/services/businessLetterResult";
import { validateBusinessLetterForm } from "../../../../plugins/business_letter/frontend/services/businessLetterValidation";

describe("Business letter hardening services", () => {
  it("has no unscoped global form selectors in plugin css", () => {
    const cssPath = resolve(process.cwd(), "../plugins/business_letter/frontend/BusinessLetterManualPage.css");
    const css = readFileSync(cssPath, "utf-8");

    expect(css.includes("\nlabel {")).toBe(false);
    expect(css.includes("\ninput,")).toBe(false);
    expect(css.includes("\nselect,")).toBe(false);
    expect(css.includes("\ntextarea {")).toBe(false);
    expect(css.includes(".business-letter-page label")).toBe(true);
  });

  it("blocks invalid quantities and source-kind mismatches", () => {
    const errors = validateBusinessLetterForm({
      documentKind: "rechnung",
      customerName: "Kunde",
      subject: "Rechnung",
      sourceDocumentNumber: "SRC-1",
      sourceDocumentId: "src-1",
      sourceDocumentKind: "angebot",
      originalInvoiceNumber: "",
      conversionAction: "lieferschein_to_rechnung",
      selectedSourceLineIds: ["10"],
      sourcePositionQuantities: { "10": "6" },
      positions: [
        {
          id: "1",
          description: "Pos",
          quantity: 0,
          unit: "Stk.",
          unitPrice: 10,
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
        },
      ],
      selectedReference: {
        id: "src-1",
        number: "L-100",
        kind: "lieferschein",
        subject: "Quelle",
        projectId: "P1",
        customerId: "C1",
        customerName: "Kunde",
        customerStreet: "Musterweg 1",
        customerZip: "12345",
        customerCity: "Berlin",
        customerEmail: "kunde@example.com",
        issueDate: "2026-01-01",
        dueDate: "2026-01-10",
        totalAmount: "120.00",
        positions: [
          {
            lineId: "10",
            name: "Pos",
            description: "Pos",
            quantity: 5,
            unitCode: "C62",
            priceNet: 10,
            vatRate: 19,
            stoneDetails: {},
          },
        ],
      },
      requiresPositions: true,
      supportsEInvoice: true,
      attachXml: false,
      activeConversionOption: {
        value: "lieferschein_to_rechnung",
        label: "Lieferschein -> Rechnung",
        sourceKind: "lieferschein",
      },
      requiredFields: [],
      fieldChecks: {},
    });

    expect(errors.some((item) => item.includes("Menge größer 0"))).toBe(true);
    expect(errors.some((item) => item.includes("Quelldokument-Typ"))).toBe(true);
    expect(errors.some((item) => item.includes("Teilmengen"))).toBe(true);
  });

  it("allows hiding technical json in production rendering mode", () => {
    expect(shouldShowTechnicalResponse(false)).toBe(false);
    expect(shouldShowTechnicalResponse(true)).toBe(true);
  });
});
