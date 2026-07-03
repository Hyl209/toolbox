import { useCallback, useEffect, useRef, useState } from "react";
import {
  cleanupToolSession,
  controlToolSession,
  pollToolSession,
  startToolSession,
  TOOL_ACTIVITY_EVENT,
  type ToolInput,
  type ToolActivityState,
  type ToolSessionControlAction,
  type ToolSessionSnapshot,
} from "../../../api/tauri";

const downloadRuntimeSessionCache = new Map<string, ToolSessionSnapshot>();

function cachedSessionForTool(toolId: string): ToolSessionSnapshot | null {
  return downloadRuntimeSessionCache.get(toolId) ?? null;
}

function saveCachedSession(toolId: string, session: ToolSessionSnapshot) {
  downloadRuntimeSessionCache.set(toolId, session);
}

function clearCachedSession(toolId: string) {
  downloadRuntimeSessionCache.delete(toolId);
}

function emitToolActivity(toolId: string, state: ToolActivityState) {
  if (typeof window === "undefined") {
    return;
  }
  window.dispatchEvent(new CustomEvent(TOOL_ACTIVITY_EVENT, { detail: { toolId, state } }));
}

export function useDownloadRuntimeSession(toolId: string) {
  const pollTimerRef = useRef<number | null>(null);
  const sessionIdRef = useRef<string | null>(cachedSessionForTool(toolId)?.session_id ?? null);
  const [session, setSession] = useState<ToolSessionSnapshot | null>(() => cachedSessionForTool(toolId));
  const [sessionError, setSessionError] = useState("");

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current !== null) {
      window.clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const refresh = useCallback(async (sessionId: string) => {
    const next = await pollToolSession(sessionId);
    saveCachedSession(toolId, next);
    sessionIdRef.current = next.session_id;
    setSession(next);
    if (!["running", "paused"].includes(next.status)) {
      stopPolling();
    }
    return next;
  }, [stopPolling, toolId]);

  const startPolling = useCallback((sessionId: string) => {
    if (pollTimerRef.current !== null) {
      return;
    }
    pollTimerRef.current = window.setInterval(() => {
      void refresh(sessionId).catch((caught) => {
        stopPolling();
        setSessionError(caught instanceof Error ? caught.message : String(caught));
      });
    }, 500);
  }, [refresh, stopPolling]);

  const start = useCallback(async (input: ToolInput) => {
    stopPolling();
    setSessionError("");
    const previousSessionId = sessionIdRef.current;
    if (previousSessionId) {
      try {
        await cleanupToolSession(previousSessionId);
      } catch (caught) {
        console.error("cleanupToolSession failed", caught);
      }
    }
    const next = await startToolSession(toolId, input);
    sessionIdRef.current = next.session_id;
    saveCachedSession(toolId, next);
    setSession(next);
    startPolling(next.session_id);
    return next;
  }, [startPolling, stopPolling, toolId]);

  const control = useCallback(async (action: ToolSessionControlAction) => {
    if (!session?.session_id) {
      return null;
    }
    const next = await controlToolSession(session.session_id, action);
    saveCachedSession(toolId, next);
    setSession(next);
    if (action === "resume") {
      emitToolActivity(toolId, "running");
      if (next.status === "running" || next.status === "paused") {
        startPolling(next.session_id);
      }
    }
    if (action === "cancel") {
      emitToolActivity(toolId, "error");
    }
    return next;
  }, [session?.session_id, startPolling, toolId]);

  const clear = useCallback(async () => {
    stopPolling();
    const sessionId = sessionIdRef.current;
    sessionIdRef.current = null;
    if (sessionId) {
      try {
        await cleanupToolSession(sessionId);
      } catch (caught) {
        console.error("cleanupToolSession failed", caught);
      }
    }
    setSession(null);
    setSessionError("");
    clearCachedSession(toolId);
  }, [stopPolling, toolId]);

  useEffect(() => () => {
    if (pollTimerRef.current !== null) {
      window.clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional mount-only effect per toolId;
  // refresh/startPolling are stable callbacks and must not re-trigger a cache restore mid-session
  useEffect(() => {
    const cached = cachedSessionForTool(toolId);
    sessionIdRef.current = cached?.session_id ?? null;
    setSession(cached);
    setSessionError("");
    if (cached && ["running", "paused"].includes(cached.status)) {
      void refresh(cached.session_id).catch((caught) => {
        setSessionError(caught instanceof Error ? caught.message : String(caught));
      });
      startPolling(cached.session_id);
    }
  }, [toolId]); // refresh/startPolling are stable per toolId; adding them would re-run on identity changes

  useEffect(() => {
    if (!session) {
      return;
    }
    if (session.status === "completed") {
      emitToolActivity(toolId, "success");
    } else if (session.status === "failed" || session.status === "cancelled") {
      emitToolActivity(toolId, "error");
    } else if (session.status === "running") {
      emitToolActivity(toolId, "running");
    }
  }, [session, toolId]);

  return {
    session,
    sessionError,
    start,
    refresh,
    control,
    clear,
    running: session?.status === "running",
    paused: session?.status === "paused",
    active: session ? ["running", "paused"].includes(session.status) : false,
  };
}
