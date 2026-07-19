import { expect, test, type APIRequestContext, type Locator, type Page } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

type RegisteredUser = {
  id: number;
  username: string;
  token: string;
};

const AUTH_USER_STORAGE_KEY = "local-chat-auth-user";
const AUTH_TOKEN_STORAGE_KEY = "local-chat-auth-token";
const BACKEND_ORIGIN = "http://127.0.0.1:8010";
const E2E_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(E2E_DIR, "..", "..");
const PYTHON_EXE = resolve(REPO_ROOT, ".venv-chat", "Scripts", "python.exe");
const NUMBERING_DB_PATH = resolve(REPO_ROOT, "data", "database", "business_letter.sqlite3");

function resetBusinessLetterSequences(): void {
  const script = [
    "import sqlite3, sys, pathlib",
    "db_path = pathlib.Path(sys.argv[1])",
    "db_path.parent.mkdir(parents=True, exist_ok=True)",
    "connection = sqlite3.connect(db_path)",
    "connection.execute('CREATE TABLE IF NOT EXISTS number_sequences (tenant_id TEXT NOT NULL, sequence_kind TEXT NOT NULL, sequence_year INTEGER NOT NULL, current_value INTEGER NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (tenant_id, sequence_kind, sequence_year))')",
    "connection.execute('DELETE FROM number_sequences')",
    "connection.commit()",
    "connection.close()",
  ].join("; ");

  execFileSync(PYTHON_EXE, ["-c", script, NUMBERING_DB_PATH], { stdio: "pipe" });
}

async function registerUser(request: APIRequestContext, suffix: string): Promise<RegisteredUser> {
  const username = `pw-${suffix}-${Date.now()}`;
  const response = await request.post(`${BACKEND_ORIGIN}/api/auth/register`, {
    data: { username, password: "Test#2026" },
  });
  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  return {
    id: payload.user.id,
    username,
    token: payload.access_token,
  };
}

async function seedAuth(page: Page, user: RegisteredUser): Promise<void> {
  await page.addInitScript(
    ({ authUserKey, authTokenKey, authUser, authToken }) => {
      window.localStorage.setItem(authUserKey, JSON.stringify(authUser));
      window.localStorage.setItem(authTokenKey, authToken);
    },
    {
      authUserKey: AUTH_USER_STORAGE_KEY,
      authTokenKey: AUTH_TOKEN_STORAGE_KEY,
      authUser: {
        id: user.id,
        username: user.username,
        is_admin: false,
        is_active: true,
        created_at: new Date().toISOString(),
      },
      authToken: user.token,
    },
  );
}

function businessLetterDetailsLocator(page: Page): Locator {
  return page
    .locator(".plugin-settings-details")
    .filter({
      has: page.locator(".plugin-settings-summary strong", { hasText: /Gesch.?ftsbrief|business_letter/i }),
    })
    .first();
}

async function openBusinessLetterSettings(page: Page): Promise<Locator> {
  await page.goto("/");
  const settingsButton = page.locator(".header").getByRole("button", { name: "Einstellungen" });
  await expect(settingsButton).toBeVisible();
  await settingsButton.click();
  await page.locator(".settings-nav").getByRole("button", { name: "Plugins" }).first().click();

  const categoryDetails = page.locator(".plugin-category-details");
  await expect(categoryDetails.first()).toBeVisible();
  const categoryCount = await categoryDetails.count();
  for (let index = 0; index < categoryCount; index += 1) {
    const category = categoryDetails.nth(index);
    const isOpen = await category.evaluate((node) => (node as HTMLDetailsElement).open);
    if (!isOpen) {
      await category.locator(":scope > summary").click();
      await expect
        .poll(async () => category.evaluate((node) => (node as HTMLDetailsElement).open))
        .toBeTruthy();
    }
  }

  const businessLetterDetails = businessLetterDetailsLocator(page);
  const businessLetterSummary = businessLetterDetails.locator(":scope > summary");
  await expect(businessLetterSummary).toBeVisible();
  await businessLetterSummary.scrollIntoViewIfNeeded();

  const pluginOpen = await businessLetterDetails.evaluate((node) => (node as HTMLDetailsElement).open);
  if (!pluginOpen) {
    await businessLetterSummary.click();
  }

  await expect
    .poll(async () => businessLetterDetails.evaluate((node) => (node as HTMLDetailsElement).open))
    .toBeTruthy();
  await expect(businessLetterDetails.getByRole("button", { name: "Speichern" })).toBeVisible();
  return businessLetterDetails;
}

async function ensureBusinessLetterGroupVisible(details: Locator, groupName: RegExp, anchorLabel: string): Promise<void> {
  const anchorField = details.getByLabel(anchorLabel);
  if (await anchorField.isVisible().catch(() => false)) {
    return;
  }
  await details.getByRole("button", { name: groupName }).first().click();
  await expect(anchorField).toBeVisible();
}

async function saveBusinessLetterSettings(page: Page): Promise<void> {
  const [response] = await Promise.all([
    page.waitForResponse(
      (candidate) => candidate.url().includes("/api/settings") && candidate.request().method() === "POST",
    ),
    page
      .locator(".plugin-settings-details")
      .filter({ has: page.locator(".plugin-settings-summary strong", { hasText: /Gesch.?ftsbrief|business_letter/i }) })
      .first()
      .getByRole("button", { name: "Speichern" })
      .click(),
  ]);

  if (response.status() !== 200) {
    const bodyText = await response.text();
    throw new Error(`Saving plugin settings failed with ${response.status()}: ${bodyText}`);
  }
}

async function getPluginProfile(request: APIRequestContext, user: RegisteredUser): Promise<Record<string, unknown>> {
  const response = await request.get(`${BACKEND_ORIGIN}/api/settings/plugins/business_letter_profile?user_id=${user.id}`, {
    headers: { Authorization: `Bearer ${user.token}` },
  });
  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  return payload.value as Record<string, unknown>;
}

async function executeBusinessLetter(
  request: APIRequestContext,
  user: RegisteredUser,
  pluginInput: Record<string, unknown>,
): Promise<Record<string, any>> {
  const response = await request.post(`${BACKEND_ORIGIN}/api/plugins/execute`, {
    data: {
      plugin_id: "business_letter",
      plugin_input: pluginInput,
      plugin_settings: {},
      user_id: user.id,
    },
  });
  expect(response.ok()).toBeTruthy();
  return response.json();
}

function businessLetterPayload(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    letter_type: "angebot",
    subject: "Angebot fuer Fensterbank",
    communication_channel: "email",
    customer_company: "Kunde GmbH",
    customer_first_name: "Anna",
    customer_last_name: "Beispiel",
    customer_salutation: "Frau",
    customer_street: "Hauptweg 12",
    customer_zip: "10115",
    customer_city: "Berlin",
    customer_country: "Deutschland",
    recipient_email: "kunde@example.de",
    document_number: "DOC-PLAYWRIGHT-1001",
    buyer_reference: "BR-2026-PLAYWRIGHT",
    issue_date: "2026-07-18",
    payment_terms: "Zahlbar innerhalb von 14 Tagen.",
    payment_due_date: "2026-08-01",
    positions: [
      {
        name: "Fensterbank",
        quantity: "1",
        unit_code: "C62",
        price_net: "149.00",
        vat_category: "S",
        vat_rate: "19",
      },
    ],
    ...overrides,
  };
}

test.describe("business letter settings e2e", () => {
  test.beforeEach(async () => {
    resetBusinessLetterSequences();
  });

  test("layout settings persist through UI reload and affect generated output", async ({ page, request }) => {
    const user = await registerUser(request, "layout");
    await seedAuth(page, user);
    let details = await openBusinessLetterSettings(page);

    await ensureBusinessLetterGroupVisible(details, /Dokumentlayout/, "Akzentfarbe");
    await details.getByLabel("Akzentfarbe").fill("#114477");
    await details.getByLabel("Logo-Breite (mm)").fill("52");
    const pageNumbers = details.getByLabel("Seitenzahlen aktiv");
    await pageNumbers.uncheck();
    await details.getByLabel("Standard-PDF-Dateiname").fill("e2e-layout-{document_number}.pdf");

    await saveBusinessLetterSettings(page);
    const stored = await getPluginProfile(request, user);
    expect(stored.accent_color).toBe("#114477");
    expect(stored.logo_width_mm).toBe(52);
    expect(stored.show_page_numbers).toBe(false);
    expect(stored.default_pdf_filename_pattern).toBe("e2e-layout-{document_number}.pdf");

    await page.reload();
    details = await openBusinessLetterSettings(page);
    await ensureBusinessLetterGroupVisible(details, /Dokumentlayout/, "Akzentfarbe");

    await expect(details.getByLabel("Akzentfarbe")).toHaveValue("#114477");
    await expect(details.getByLabel("Logo-Breite (mm)")).toHaveValue("52");
    await expect(details.getByLabel("Seitenzahlen aktiv")).not.toBeChecked();
    await expect(details.getByLabel("Standard-PDF-Dateiname")).toHaveValue("e2e-layout-{document_number}.pdf");

    const execution = await executeBusinessLetter(request, user, businessLetterPayload());
    const pluginResponse = execution.plugin_response;
    expect(String(pluginResponse.content.document_html)).toContain("#114477");
    const pdfArtifact = (pluginResponse.artifacts as Array<Record<string, unknown>>).find((artifact) => artifact.kind === "pdf");
    expect(pdfArtifact?.file_name).toBe("e2e-layout-DOC-PLAYWRIGHT-1001.pdf");
  });

  test("shipping settings persist through UI reload and affect mail output", async ({ page, request }) => {
    const user = await registerUser(request, "shipping");
    await seedAuth(page, user);
    let details = await openBusinessLetterSettings(page);

    await ensureBusinessLetterGroupVisible(details, /Kommunikation/, "Standard-E-Mail-Betreffmuster");
    await details.getByLabel("Standard-E-Mail-Betreffmuster").fill("{document_kind} {document_number} fuer {customer_company}");
    await details.getByLabel("Standard-CC").fill("vertrieb@example.de; kalkulation@example.de");
    await details.getByLabel("Standard-Antwortadresse").fill("reply@example.de");
    await details.getByLabel("HTML-E-Mail aktiv").uncheck();
    await details.getByLabel("PDF standardmäßig anhängen").check();
    await details.getByLabel("XML standardmäßig anhängen").check();

    await saveBusinessLetterSettings(page);
    const stored = await getPluginProfile(request, user);
    expect(stored.default_email_subject_template).toBe("{document_kind} {document_number} fuer {customer_company}");
    expect(stored.default_cc).toBe("vertrieb@example.de; kalkulation@example.de");
    expect(stored.default_reply_to_address).toBe("reply@example.de");
    expect(stored.default_email_html_enabled).toBe(false);
    expect(stored.default_attach_pdf).toBe(true);
    expect(stored.default_attach_xml).toBe(true);

    await page.reload();
    details = await openBusinessLetterSettings(page);
    await ensureBusinessLetterGroupVisible(details, /Kommunikation/, "Standard-E-Mail-Betreffmuster");
    await expect(details.getByLabel("Standard-E-Mail-Betreffmuster")).toHaveValue("{document_kind} {document_number} fuer {customer_company}");
    await expect(details.getByLabel("Standard-CC")).toHaveValue("vertrieb@example.de; kalkulation@example.de");
    await expect(details.getByLabel("Standard-Antwortadresse")).toHaveValue("reply@example.de");
    await expect(details.getByLabel("HTML-E-Mail aktiv")).not.toBeChecked();
    await expect(details.getByLabel("PDF standardmäßig anhängen")).toBeChecked();
    await expect(details.getByLabel("XML standardmäßig anhängen")).toBeChecked();

    const execution = await executeBusinessLetter(
      request,
      user,
      businessLetterPayload({
        document_kind: "rechnung",
        einvoice: { enabled: true, standard: "xrechnung" },
      }),
    );
    const pluginResponse = execution.plugin_response;
    expect(pluginResponse.email.subject).toBe("rechnung DOC-PLAYWRIGHT-1001 fuer Kunde GmbH");
    expect(pluginResponse.email.reply_to).toBe("reply@example.de");
    expect(pluginResponse.email.cc).toEqual(["vertrieb@example.de", "kalkulation@example.de"]);
    expect(pluginResponse.email.html_enabled).toBe(false);
    expect(pluginResponse.email.body_html).toBe("");
    const attachmentKinds = (pluginResponse.email.attachments as Array<Record<string, unknown>>).map((item) => String(item.kind || ""));
    expect(attachmentKinds).toContain("pdf");
    expect(pluginResponse.einvoice).toBeTruthy();
  });

  test("archival settings persist through UI reload and affect persisted metadata", async ({ page, request }) => {
    const user = await registerUser(request, "archive");
    await seedAuth(page, user);
    let details = await openBusinessLetterSettings(page);

    await ensureBusinessLetterGroupVisible(details, /Persistenz & Archivierung/, "Hashprüfung aktiv");
    await details.getByLabel("Hashprüfung aktiv").check();
    await details.getByLabel("Validierungsreports speichern").check();
    await details.getByLabel("PDF/XML gemeinsam archivieren").check();
    await details.getByLabel("Aufbewahrungsdauer (Tage)").fill("45");

    await saveBusinessLetterSettings(page);
    const stored = await getPluginProfile(request, user);
    expect(stored.enable_hash_verification).toBe(true);
    expect(stored.store_validation_reports).toBe(true);
    expect(stored.archive_pdf_xml_together).toBe(true);
    expect(stored.retention_days).toBe(45);

    await page.reload();
    details = await openBusinessLetterSettings(page);
    await ensureBusinessLetterGroupVisible(details, /Persistenz & Archivierung/, "Hashprüfung aktiv");
    await expect(details.getByLabel("Hashprüfung aktiv")).toBeChecked();
    await expect(details.getByLabel("Validierungsreports speichern")).toBeChecked();
    await expect(details.getByLabel("PDF/XML gemeinsam archivieren")).toBeChecked();
    await expect(details.getByLabel("Aufbewahrungsdauer (Tage)")).toHaveValue("45");

    const execution = await executeBusinessLetter(
      request,
      user,
      businessLetterPayload({
        persist_to_database: true,
        document_number: "DOC-PLAYWRIGHT-ARCHIVE-1",
        einvoice: { enabled: true, standard: "xrechnung" },
      }),
    );
    const pluginResponse = execution.plugin_response;
    const persisted = pluginResponse.database.persisted;
    expect(persisted.plugin_storage.document.retention_until).toBeTruthy();
    const groupedArtifacts = (persisted.plugin_storage.artifacts as Array<Record<string, unknown>>).filter(
      (artifact) => artifact.artifact_kind === "pdf" || artifact.artifact_kind === "xrechnung_xml",
    );
    expect(groupedArtifacts.length).toBeGreaterThanOrEqual(1);
    expect(groupedArtifacts.every((artifact) => artifact.hash_verified === true)).toBeTruthy();
    if (groupedArtifacts.length >= 2) {
      expect(new Set(groupedArtifacts.map((artifact) => artifact.archive_group)).size).toBe(1);
    }

    const validationReports = (persisted.plugin_storage.artifacts as Array<Record<string, unknown>>).filter(
      (artifact) => artifact.artifact_kind === "validation_report",
    );
    if (validationReports.length > 0) {
      expect(validationReports.every((artifact) => String(artifact.storage_key).includes("playwright-validation-reports") || String(artifact.storage_key).includes("validation"))).toBeTruthy();
    }
  });
});
