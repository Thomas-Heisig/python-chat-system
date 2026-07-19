import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { BusinessLetterManualPage } from "../../../../plugins/business_letter/frontend/BusinessLetterManualPage";

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("BusinessLetterManualPage hardening", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("sends requests to execute-function using function_input", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ plugin_response: { status: "ok" } }),
    );

    const view = render(<BusinessLetterManualPage />);

    fireEvent.change(screen.getByLabelText(/Dokumenttyp/i), { target: { value: "anfrage" } });
    fireEvent.change(screen.getByLabelText(/Name \/ Firma/i), { target: { value: "Muster GmbH" } });
    fireEvent.change(screen.getByLabelText(/Betreff/i), { target: { value: "Testauftrag" } });

    const form = view.container.querySelector("form");
    expect(form).toBeTruthy();
    fireEvent.submit(form as HTMLFormElement);

    await waitFor(() => {
      const executeCalls = fetchMock.mock.calls.filter((entry) => String(entry[0]).includes("/api/plugins/execute-function"));
      expect(executeCalls.length).toBeGreaterThan(0);
    });

    const executeCall = fetchMock.mock.calls.find((entry) => String(entry[0]).includes("/api/plugins/execute-function"));
    expect(executeCall).toBeTruthy();
    const [url, options] = executeCall as [string, RequestInit];
    expect(url).toBe("/api/plugins/execute-function");
    expect(options.method).toBe("POST");

    const body = JSON.parse(String(options.body));
    expect(body.plugin_id).toBe("business_letter");
    expect(body.function_name).toBe("create_document");
    expect(body.confirmed).toBe(false);
    expect(body.function_input).toBeTypeOf("object");
    expect(body.arguments).toBeUndefined();
  });

  it("keeps idempotency key stable across failed retry of same submit attempt", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse({ detail: { message: "temporarily failed" } }, 500))
      .mockResolvedValueOnce(jsonResponse({ plugin_response: { status: "ok" } }, 200));

    const view = render(<BusinessLetterManualPage />);

    fireEvent.change(screen.getByLabelText(/Dokumenttyp/i), { target: { value: "anfrage" } });
    fireEvent.change(screen.getByLabelText(/Name \/ Firma/i), { target: { value: "Retry GmbH" } });
    fireEvent.change(screen.getByLabelText(/Betreff/i), { target: { value: "Retry Case" } });

    const form = view.container.querySelector("form");
    expect(form).toBeTruthy();

    fireEvent.submit(form as HTMLFormElement);
    await waitFor(() => {
      const executeCalls = fetchMock.mock.calls.filter((entry) => String(entry[0]).includes("/api/plugins/execute-function"));
      expect(executeCalls.length).toBe(1);
    });

    fireEvent.submit(form as HTMLFormElement);
    await waitFor(() => {
      const executeCalls = fetchMock.mock.calls.filter((entry) => String(entry[0]).includes("/api/plugins/execute-function"));
      expect(executeCalls.length).toBe(2);
    });

    const executeCalls = fetchMock.mock.calls.filter((entry) => String(entry[0]).includes("/api/plugins/execute-function"));
    const firstBody = JSON.parse(String((executeCalls[0] as [string, RequestInit])[1].body));
    const secondBody = JSON.parse(String((executeCalls[1] as [string, RequestInit])[1].body));

    expect(firstBody.idempotency_key).toBeTypeOf("string");
    expect(secondBody.idempotency_key).toBe(firstBody.idempotency_key);
  });

  it("renders document hint as note and not as editable input", () => {
    render(<BusinessLetterManualPage currentUserId={23} />);

    expect(screen.getByRole("note", { name: /Dokumenthinweis/i })).toBeTruthy();
    expect(screen.queryByRole("textbox", { name: /Dokumenthinweis/i })).toBeNull();
  });

  it("hides xml option for non e-invoice document types", () => {
    render(<BusinessLetterManualPage currentUserId={24} />);

    const documentType = screen.getByLabelText(/Dokumenttyp/i);
    fireEvent.change(documentType, { target: { value: "angebot" } });

    expect(screen.queryByLabelText(/E-Rechnungs-XML erzeugen/i)).toBeNull();
  });
});
