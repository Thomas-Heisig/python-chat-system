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
});
