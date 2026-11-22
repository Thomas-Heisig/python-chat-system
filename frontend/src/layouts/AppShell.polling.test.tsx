import { StrictMode } from "react";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AppShell } from "./AppShell";

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

const backend = vi.hoisted(() => ({
  activateModel: vi.fn(),
  adminCreateUser: vi.fn(),
  adminDeleteUser: vi.fn(),
  adminKickUser: vi.fn(),
  adminUnlockUser: vi.fn(),
  adminUpdateUser: vi.fn(),
  createConversation: vi.fn(),
  assignConversationProject: vi.fn(),
  deleteConversation: vi.fn(),
  deactivateModel: vi.fn(),
  getCapabilities: vi.fn(),
  getConversations: vi.fn(),
  getHealthModel: vi.fn(),
  getMessages: vi.fn(),
  getModels: vi.fn(),
  getSetting: vi.fn(),
  getUsersPresence: vi.fn(),
  getWorkspaceAppointments: vi.fn(),
  getWorkspaceProjects: vi.fn(),
  getWorkspaceSources: vi.fn(),
  postUserOnlyMessage: vi.fn(),
  renameConversation: vi.fn(),
  scanModels: vi.fn(),
  sendMessageStream: vi.fn(),
  sendPresenceHeartbeat: vi.fn(),
  updateSetting: vi.fn(),
}));

vi.mock("../services/backend", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../services/backend")>();
  return {
    ...actual,
    ...backend,
  };
});

function renderAppShell(userId = 1) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <StrictMode>
        <AppShell
          currentUser={{
            id: userId,
            username: "tester",
            is_admin: false,
            is_active: true,
            created_at: "2026-07-10T00:00:00Z",
          }}
          onLogout={() => undefined}
        />
      </StrictMode>
    </QueryClientProvider>,
  );
}

describe("AppShell polling regression", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    backend.getCapabilities.mockResolvedValue({
      service: "test",
      version: "1",
      features: {
        "auth.users_presence": true,
        "auth.heartbeat": true,
      },
    });
    backend.getModels.mockResolvedValue([]);
    backend.getHealthModel.mockResolvedValue({ activeModelId: null, loaded: true, backend: null });
    backend.getWorkspaceProjects.mockResolvedValue([]);
    backend.getWorkspaceAppointments.mockResolvedValue([]);
    backend.getWorkspaceSources.mockResolvedValue([]);
    backend.getUsersPresence.mockResolvedValue([]);
    backend.sendPresenceHeartbeat.mockResolvedValue(undefined);
    backend.getSetting.mockResolvedValue(null);
    backend.getConversations.mockResolvedValue([
      {
        id: 100,
        title: "Chat 1",
        updatedAt: "2026-07-10T00:00:00Z",
        lastMessage: null,
        ownerUserId: 1,
        ownerUsername: "tester",
      },
    ]);
    backend.getMessages.mockResolvedValue([]);
    backend.createConversation.mockResolvedValue({ id: 101 });
    backend.updateSetting.mockResolvedValue({ updated: true, effect: "saved" });
  });

  it("keeps exactly one active poll interval per scheduler in React Strict Mode", async () => {
    let nextId = 1;
    const allActiveIds = new Set<number>();
    const callbacksByInterval = new Map<number, () => void>();
    const activeByDelay = new Map<number, Set<number>>();
    const maxActiveByDelay = new Map<number, number>();

    const setIntervalSpy = vi.spyOn(window, "setInterval").mockImplementation(((handler: TimerHandler, timeout?: number) => {
      const id = nextId++;
      const delay = Number(timeout ?? 0);
      const callback = (typeof handler === "function" ? handler : () => undefined) as () => void;
      callbacksByInterval.set(id, callback);
      allActiveIds.add(id);
      const bucket = activeByDelay.get(delay) ?? new Set<number>();
      bucket.add(id);
      activeByDelay.set(delay, bucket);
      maxActiveByDelay.set(delay, Math.max(maxActiveByDelay.get(delay) ?? 0, bucket.size));
      return id;
    }) as typeof window.setInterval);

    const clearIntervalSpy = vi.spyOn(window, "clearInterval").mockImplementation(((intervalId?: number) => {
      if (intervalId == null) {
        return;
      }
      allActiveIds.delete(intervalId);
      callbacksByInterval.delete(intervalId);
      for (const bucket of activeByDelay.values()) {
        bucket.delete(intervalId);
      }
    }) as typeof window.clearInterval);

    const rendered = renderAppShell();

    await waitFor(() => {
      expect(activeByDelay.get(20000)?.size ?? 0).toBe(1);
    });

    expect(maxActiveByDelay.get(3000) ?? 0).toBeLessThanOrEqual(1);
    expect(maxActiveByDelay.get(20000) ?? 0).toBeLessThanOrEqual(1);

    rendered.unmount();

    expect(allActiveIds.size).toBe(0);
    expect(setIntervalSpy).toHaveBeenCalled();
    expect(clearIntervalSpy).toHaveBeenCalled();
  });

  it("prevents overlapping heartbeat calls when presence polling ticks concurrently", async () => {
    let nextId = 1;
    const callbacksByDelay = new Map<number, () => void>();

    vi.spyOn(window, "setInterval").mockImplementation(((handler: TimerHandler, timeout?: number) => {
      const id = nextId++;
      const delay = Number(timeout ?? 0);
      const callback = (typeof handler === "function" ? handler : () => undefined) as () => void;
      callbacksByDelay.set(delay, callback);
      return id;
    }) as typeof window.setInterval);

    vi.spyOn(window, "clearInterval").mockImplementation(() => undefined);

    const heartbeatDeferred = createDeferred<void>();
    let heartbeatCalls = 0;
    backend.sendPresenceHeartbeat.mockImplementation(() => {
      heartbeatCalls += 1;
      if (heartbeatCalls === 1) {
        return Promise.resolve();
      }
      return heartbeatDeferred.promise;
    });

    renderAppShell();

    await waitFor(() => {
      expect(callbacksByDelay.has(20000)).toBe(true);
      expect(backend.getCapabilities).toHaveBeenCalled();
    });

    backend.sendPresenceHeartbeat.mockClear();
    backend.getUsersPresence.mockClear();

    const presenceTick = callbacksByDelay.get(20000);
    expect(presenceTick).toBeDefined();

    presenceTick?.();
    presenceTick?.();

    await waitFor(() => {
      expect(backend.sendPresenceHeartbeat).toHaveBeenCalledTimes(1);
    });

    heartbeatDeferred.resolve(undefined);

    await waitFor(() => {
      expect(backend.sendPresenceHeartbeat).toHaveBeenCalledTimes(1);
    });
  });

  it("loads conversation tree settings with the current user key", async () => {
    renderAppShell(3);

    await waitFor(() => {
      expect(
        backend.getSetting.mock.calls.some(
          (call: unknown[]) => call[0] === "chat" && call[1] === "conversation_tree_user_3" && call[2] === 3,
        ),
      ).toBe(true);
    });
  });

  it("loads and applies general settings to the document root", async () => {
    backend.getSetting.mockImplementation(async (category: string, key: string) => {
      if (category === "system" && key === "language") {
        return "en";
      }
      if (category === "system" && key === "theme") {
        return "dark";
      }
      if (category === "system" && key === "timezone") {
        return "America/New_York";
      }
      return null;
    });

    renderAppShell(4);

    await waitFor(() => {
      expect(document.documentElement.getAttribute("lang")).toBe("en");
      expect(document.documentElement.getAttribute("data-ui-theme")).toBe("dark");
      expect(document.documentElement.getAttribute("data-ui-theme-preference")).toBe("dark");
      expect(document.documentElement.getAttribute("data-user-timezone")).toBe("America/New_York");
    });

    expect(
      backend.getSetting.mock.calls.some(
        (call: unknown[]) => call[0] === "system" && call[1] === "language" && call[2] === 4,
      ),
    ).toBe(true);
    expect(
      backend.getSetting.mock.calls.some(
        (call: unknown[]) => call[0] === "system" && call[1] === "theme" && call[2] === 4,
      ),
    ).toBe(true);
    expect(
      backend.getSetting.mock.calls.some(
        (call: unknown[]) => call[0] === "system" && call[1] === "timezone" && call[2] === 4,
      ),
    ).toBe(true);
  });

  it("allows assigning a project to a visible conversation even when the current user is not the owner", async () => {
    backend.getWorkspaceProjects.mockResolvedValue([
      {
        id: 10,
        name: "Team / Alpha",
        chats: 0,
        documents: 0,
        parent_project_id: null,
        scope_kind: "project",
        depth: 0,
      },
    ]);
    backend.getConversations.mockResolvedValue([
      {
        id: 100,
        title: "Shared Chat",
        updatedAt: "2026-07-10T00:00:00Z",
        lastMessage: null,
        ownerUserId: 2,
        ownerUsername: "other-user",
        projectId: null,
      },
    ]);

    renderAppShell(1);

    const actionsButton = await screen.findByLabelText("Chat Shared Chat Aktionen");
    fireEvent.click(actionsButton);

    const projectSelect = await screen.findByLabelText("Projektzuordnung");
    fireEvent.change(projectSelect, { target: { value: "10" } });
    fireEvent.click(screen.getByRole("button", { name: "Projekt speichern" }));

    await waitFor(() => {
      expect(backend.assignConversationProject).toHaveBeenCalledWith(100, 10, 1);
    });
  });

  it("renders project folder controls in the chat sidebar", async () => {
    backend.getWorkspaceProjects.mockResolvedValue([
      {
        id: 10,
        name: "Heisig Naturstein",
        chats: 0,
        documents: 0,
        parent_project_id: null,
        scope_kind: "project",
        depth: 0,
      },
      {
        id: 11,
        name: "Angebote",
        chats: 0,
        documents: 0,
        parent_project_id: 10,
        scope_kind: "project",
        depth: 1,
      },
      {
        id: 12,
        name: "Kläner",
        chats: 0,
        documents: 0,
        parent_project_id: 11,
        scope_kind: "project",
        depth: 2,
      },
    ]);
    backend.getConversations.mockResolvedValue([
      {
        id: 100,
        title: "Angebot Kläner Lemwerder",
        updatedAt: "2026-07-10T00:00:00Z",
        lastMessage: null,
        ownerUserId: 1,
        ownerUsername: "tester",
        projectId: 12,
      },
    ]);
    backend.getWorkspaceSources.mockResolvedValue([
      {
        id: 1,
        file: "angebot-klaener-lemwerder.md",
        position: "Zeile 1",
        relevance: "95%",
        project_id: 12,
        project_name: "Kläner",
      },
      {
        id: 2,
        file: "angebote-vorlage.md",
        position: "Zeile 8",
        relevance: "81%",
        project_id: 11,
        project_name: "Angebote",
      },
    ]);

    renderAppShell(1);

    expect(await screen.findByRole("button", { name: "Projektordner Heisig Naturstein" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Alle Chats" })).toBeTruthy();
  });

  it("keeps the selected project filter when selecting a chat", async () => {
    backend.getWorkspaceProjects.mockResolvedValue([
      {
        id: 10,
        name: "Heisig Naturstein",
        chats: 0,
        documents: 0,
        parent_project_id: null,
        scope_kind: "project",
        depth: 0,
      },
      {
        id: 11,
        name: "Angebote",
        chats: 0,
        documents: 0,
        parent_project_id: 10,
        scope_kind: "project",
        depth: 1,
      },
      {
        id: 12,
        name: "Kläner",
        chats: 0,
        documents: 0,
        parent_project_id: 11,
        scope_kind: "project",
        depth: 2,
      },
    ]);
    backend.getConversations.mockResolvedValue([
      {
        id: 100,
        title: "Angebot Kläner Lemwerder",
        updatedAt: "2026-07-10T00:00:00Z",
        lastMessage: null,
        ownerUserId: 1,
        ownerUsername: "tester",
        projectId: 12,
      },
      {
        id: 101,
        title: "Rueckfragen Material",
        updatedAt: "2026-07-10T00:01:00Z",
        lastMessage: null,
        ownerUserId: 1,
        ownerUsername: "tester",
        projectId: 12,
      },
    ]);

    renderAppShell(1);

    fireEvent.click(await screen.findByRole("button", { name: "Projektordner Heisig Naturstein / Angebote / Kläner" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Projektordner Heisig Naturstein / Angebote / Kläner" }).getAttribute("aria-pressed")).toBe("true");
    });

    fireEvent.click(screen.getByRole("button", { name: "Rueckfragen Material" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Projektordner Heisig Naturstein / Angebote / Kläner" }).getAttribute("aria-pressed")).toBe("true");
    });
  });

  it.each([1280, 375])("shows only the active chat's project-scope sources at width %i", async (width) => {
    const previousWidth = window.innerWidth;
    window.innerWidth = width;
    try {
      backend.getWorkspaceProjects.mockResolvedValue([
        { id: 10, name: "Parent", chats: 0, documents: 0, parent_project_id: null },
        { id: 11, name: "Child", chats: 0, documents: 0, parent_project_id: 10 },
        { id: 12, name: "Other", chats: 0, documents: 0, parent_project_id: null },
      ]);
      backend.getConversations.mockResolvedValue([{
        id: 100,
        title: "Scoped chat",
        updatedAt: "2026-07-10T00:00:00Z",
        lastMessage: null,
        ownerUserId: 1,
        ownerUsername: "tester",
        projectId: 11,
      }]);
      backend.getWorkspaceSources.mockResolvedValue([
        { id: 1, file: "parent.txt", position: "1", relevance: "90%", project_id: 10 },
        { id: 2, file: "child.txt", position: "2", relevance: "80%", project_id: 11 },
        { id: 3, file: "other.txt", position: "3", relevance: "70%", project_id: 12 },
        { id: 4, file: "unassigned.txt", position: "4", relevance: "60%", project_id: null },
      ]);

      renderAppShell();
      expect(await screen.findByText("Projekt fuer diesen Chat: Parent / Child")).toBeTruthy();
      if (width < 1024) {
        fireEvent.click(screen.getByTitle("Kontext, Quellen und Werkzeuge anzeigen"));
      }
      const sidebar = await screen.findByRole("complementary", { name: "Informationsbereich" });
      fireEvent.click(within(sidebar).getByRole("button", { name: "Quellen" }));
      expect(within(sidebar).getByText("parent.txt")).toBeTruthy();
      expect(within(sidebar).getByText("child.txt")).toBeTruthy();
      expect(within(sidebar).queryByText("other.txt")).toBeNull();
      expect(within(sidebar).queryByText("unassigned.txt")).toBeNull();
    } finally {
      window.innerWidth = previousWidth;
    }
  });

  it("supports project selection and assignment in the mobile navigation", async () => {
    const previousWidth = window.innerWidth;
    window.innerWidth = 375;
    try {
      backend.getWorkspaceProjects.mockResolvedValue([
        { id: 10, name: "Team", chats: 0, documents: 0, parent_project_id: null },
      ]);
      backend.getConversations.mockResolvedValue([{
        id: 100,
        title: "Mobile chat",
        updatedAt: "2026-07-10T00:00:00Z",
        lastMessage: null,
        ownerUserId: 1,
        ownerUsername: "tester",
        projectId: null,
      }]);

      renderAppShell();
      fireEvent.click(await screen.findByRole("button", { name: "Navigation oeffnen" }));
      const navigation = await screen.findByRole("dialog", { name: "Navigation" });
      fireEvent.click(await within(navigation).findByLabelText("Chat Mobile chat Aktionen"));
      fireEvent.change(await within(navigation).findByLabelText("Projektzuordnung"), { target: { value: "10" } });
      fireEvent.click(within(navigation).getByRole("button", { name: "Projekt speichern" }));
      await waitFor(() => expect(backend.assignConversationProject).toHaveBeenCalledWith(100, 10, 1));

      fireEvent.click(within(navigation).getByRole("button", { name: "Projektordner Team" }));
      expect(within(navigation).getByRole("button", { name: "Projektordner Team" }).getAttribute("aria-pressed")).toBe("true");
    } finally {
      window.innerWidth = previousWidth;
    }
  });
});
