import { useEffect, type MutableRefObject, useCallback, useState } from "react";
import { getSetting, updateSetting } from "../../../frontend/src/services/backend";

export type PluginDraftStatus = "idle" | "loading" | "saving" | "saved" | "error";

export type UsePluginDraftOptions<TDraft> = {
  pluginId: string;
  currentUserId?: number;
  draftSnapshot: TDraft;
  applyDraft: (draft: TDraft) => void;
  normalizeDraft: (raw: unknown) => TDraft | null;
  applyingDraftRef?: MutableRefObject<boolean>;
  autosaveDelayMs?: number;
};

export type UsePluginDraftResult = {
  draftStatus: PluginDraftStatus;
  draftMessage: string;
  saveDraftNow: () => Promise<void>;
  reloadDraftNow: () => Promise<void>;
};

export function usePluginDraft<TDraft>(options: UsePluginDraftOptions<TDraft>): UsePluginDraftResult {
  const {
    pluginId,
    currentUserId,
    draftSnapshot,
    applyDraft,
    normalizeDraft,
    applyingDraftRef,
    autosaveDelayMs = 700,
  } = options;

  const [draftInitialized, setDraftInitialized] = useState(false);
  const [draftStatus, setDraftStatus] = useState<PluginDraftStatus>("idle");
  const [draftMessage, setDraftMessage] = useState("");

  const draftKey = `${pluginId}_frontpage_draft`;

  const persistDraft = useCallback(
    async (snapshot: TDraft, saveMode: "silent" | "manual") => {
      if (currentUserId == null) {
        return;
      }

      if (saveMode === "manual") {
        setDraftStatus("saving");
        setDraftMessage("Entwurf wird gespeichert ...");
      }

      try {
        await updateSetting("plugins", draftKey, snapshot, currentUserId);
        if (saveMode === "manual") {
          setDraftStatus("saved");
          setDraftMessage("Entwurf gespeichert.");
        }
      } catch (reason) {
        setDraftStatus("error");
        setDraftMessage(reason instanceof Error ? reason.message : "Entwurf konnte nicht gespeichert werden.");
      }
    },
    [currentUserId, draftKey],
  );

  const reloadDraftNow = useCallback(async () => {
    if (currentUserId == null) {
      return;
    }

    setDraftStatus("loading");
    setDraftMessage("Entwurf wird neu geladen ...");

    try {
      const raw = await getSetting("plugins", draftKey, currentUserId);
      const normalized = normalizeDraft(raw);
      if (normalized) {
        applyDraft(normalized);
        setDraftStatus("saved");
        setDraftMessage("Entwurf geladen.");
        return;
      }
      setDraftStatus("idle");
      setDraftMessage("Kein gespeicherter Entwurf vorhanden.");
    } catch (reason) {
      setDraftStatus("error");
      setDraftMessage(reason instanceof Error ? reason.message : "Entwurf konnte nicht geladen werden.");
    }
  }, [applyDraft, currentUserId, draftKey, normalizeDraft]);

  const saveDraftNow = useCallback(async () => {
    await persistDraft(draftSnapshot, "manual");
  }, [draftSnapshot, persistDraft]);

  useEffect(() => {
    let cancelled = false;

    const loadInitialDraft = async () => {
      if (currentUserId == null) {
        setDraftInitialized(true);
        return;
      }

      setDraftStatus("loading");
      setDraftMessage("Entwurf wird geladen ...");
      try {
        const raw = await getSetting("plugins", draftKey, currentUserId);
        if (cancelled) {
          return;
        }
        const normalized = normalizeDraft(raw);
        if (normalized) {
          applyDraft(normalized);
          setDraftStatus("saved");
          setDraftMessage("Entwurf geladen.");
        } else {
          setDraftStatus("idle");
          setDraftMessage("");
        }
      } catch {
        if (!cancelled) {
          setDraftStatus("idle");
          setDraftMessage("");
        }
      } finally {
        if (!cancelled) {
          setDraftInitialized(true);
        }
      }
    };

    void loadInitialDraft();

    return () => {
      cancelled = true;
    };
  }, [applyDraft, currentUserId, draftKey, normalizeDraft]);

  useEffect(() => {
    if (!draftInitialized || currentUserId == null) {
      return;
    }

    if (applyingDraftRef?.current) {
      applyingDraftRef.current = false;
      return;
    }

    const timer = window.setTimeout(() => {
      void persistDraft(draftSnapshot, "silent");
    }, autosaveDelayMs);

    return () => {
      window.clearTimeout(timer);
    };
  }, [applyingDraftRef, autosaveDelayMs, currentUserId, draftInitialized, draftSnapshot, persistDraft]);

  return {
    draftStatus,
    draftMessage,
    saveDraftNow,
    reloadDraftNow,
  };
}
