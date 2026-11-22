import { beforeEach, describe, expect, it, vi } from "vitest";

type Deferred<T> = {
  promise: Promise<T>;
  resolve: (value: T) => void;
  reject: (reason?: unknown) => void;
};

function createDeferred<T>(): Deferred<T> {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function makeOkResponse(): Response {
  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("sendPresenceHeartbeat", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  it("deduplicates concurrent heartbeat requests and allows a new request after completion", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const { sendPresenceHeartbeat, setAuthToken } = await import("./backend");
    setAuthToken(null);

    const firstRequestDeferred = createDeferred<Response>();
    fetchMock.mockReturnValueOnce(firstRequestDeferred.promise);

    const first = sendPresenceHeartbeat();
    const second = sendPresenceHeartbeat();

    expect(fetchMock).toHaveBeenCalledTimes(1);

    firstRequestDeferred.resolve(makeOkResponse());
    await Promise.all([first, second]);

    fetchMock.mockResolvedValueOnce(makeOkResponse());
    await sendPresenceHeartbeat();

    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("rehydrates the bearer token from localStorage after a module reset", async () => {
    window.localStorage.setItem("local-chat-auth-token", "stored-token");

    const fetchMock = vi.fn().mockResolvedValue(makeOkResponse());
    vi.stubGlobal("fetch", fetchMock);

    const { getAuthToken, sendPresenceHeartbeat } = await import("./backend");

    expect(getAuthToken()).toBe("stored-token");

    await sendPresenceHeartbeat();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit | undefined;
    expect(new Headers(init?.headers).get("Authorization")).toBe("Bearer stored-token");
  });
});

describe("settings scope parameters", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  describe("plugin frontend metadata", () => {
    beforeEach(() => {
      vi.resetModules();
      vi.unstubAllGlobals();
      window.localStorage.clear();
    });

    it("preserves valid tabs and rejects unsupported tabs for cards and actions", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
        items: [{
          id: "example",
          name: "Example",
          plugin_frontend: {
            page: {
              sections: [{
                id: "page",
                title: "Page",
                cards: [
                  { id: "valid-card", title: "Valid", openTab: "manual" },
                  { id: "invalid-card", title: "Invalid", openTab: "other" },
                ],
              }],
            },
            sections: [{
              id: "section",
              title: "Section",
              actions: [
                { id: "valid-action", label: "Valid", openTab: "settings" },
                { id: "invalid-action", label: "Invalid", openTab: "other" },
              ],
            }],
          },
        }],
      }), { status: 200 })));

      const { getPlugins } = await import("./backend");
      const [plugin] = await getPlugins();
      const cards = plugin.pluginFrontend?.page?.sections?.[0]?.cards;
      const actions = plugin.pluginFrontend?.sections?.[0]?.actions;
      expect(cards?.map((card) => card.openTab)).toEqual(["manual", undefined]);
      expect(actions?.map((action) => action.openTab)).toEqual(["settings", undefined]);
    });
  });

  it("passes team_id in getSetting query string", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ category: "plugins", key: "business_letter_profile", value: {} }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const { getSetting } = await import("./backend");
    await getSetting("plugins", "business_letter_profile", 11, 22);

    const calledUrl = String(fetchMock.mock.calls[0]?.[0] ?? "");
    expect(calledUrl).toContain("/api/settings/plugins/business_letter_profile");
    expect(calledUrl).toContain("user_id=11");
    expect(calledUrl).toContain("team_id=22");
  });

  it("passes team_id in updateSetting payload", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ updated: true, effect: "stored" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const { updateSetting } = await import("./backend");
    await updateSetting("plugins", "business_letter_profile", { default_payment_days: 14 }, 11, 22);

    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    const body = JSON.parse(String(init.body ?? "{}")) as Record<string, unknown>;
    expect(body.user_id).toBe(11);
    expect(body.team_id).toBe(22);
  });

  it("passes team_id in updatePluginSettings payload", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ updated: true, effect: "stored" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const { updatePluginSettings } = await import("./backend");
    await updatePluginSettings("business_letter", {
      settings: { default_payment_days: 21 },
      userId: 11,
      teamId: 22,
    });

    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    const body = JSON.parse(String(init.body ?? "{}")) as Record<string, unknown>;
    expect(body.category).toBe("plugins");
    expect(body.key).toBe("business_letter_profile");
    expect(body.user_id).toBe(11);
    expect(body.team_id).toBe(22);
  });
});
