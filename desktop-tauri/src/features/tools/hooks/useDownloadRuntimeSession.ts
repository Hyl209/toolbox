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

function emitToolActivity(toolId: string, state: ToolActivityState) {
  if (typeof window === "undefined") {
    return;
  }
  window.dispatchEvent(new CustomEvent(TOOL_ACTIVITY_EVENT, { detail: { toolId, state } }));
}

export function useDownloadRuntimeSession(toolId: string) {
  const pollTimerRef = useRef<number | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const [session, setSession] = useState<ToolSessionSnapshot | null>(null);
  const [sessionError, setSessionError] = useState("");

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current !== null) {
      window.clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const refresh = useCallback(async (sessionId: string) => {
    const next = await pollToolSession(sessionId);
    setSession(next);
    if (!["running", "paused"].includes(next.status)) {
      stopPolling();
    }
    return next;
  }, [stopPolling]);

  const start = useCallback(async (input: ToolInput) => {
    stopPolling();
    setSessionError("");
    const previousSessionId = sessionIdRef.current;
    if (previousSessionId) {
      try {
        await cleanupToolSession(previousSessionId);
      } catch {
        // ignore stale cleanup failures
      }
    }
    const next = await startToolSession(toolId, input);
    sessionIdRef.current = next.session_id;
    setSession(next);
    pollTimerRef.current = window.setInterval(() => {
      void refresh(next.session_id).catch((caught) => {
        stopPolling();
        setSessionError(caught instanceof Error ? caught.message : String(caught));
      });
    }, 500);
    return next;
  }, [refresh, stopPolling, toolId]);

  const control = useCallback(async (action: ToolSessionControlAction) => {
    if (!session?.session_id) {
      return null;
    }
    const next = await controlToolSession(session.session_id, action);
    setSession(next);
    if (action === "resume") {
      emitToolActivity(toolId, "running");
    }
    if (action === "cancel") {
      emitToolActivity(toolId, "error");
    }
    return next;
  }, [session?.session_id, toolId]);

  const clear = useCallback(async () => {
    stopPolling();
    const sessionId = sessionIdRef.current;
    sessionIdRef.current = null;
    if (sessionId) {
      try {
        await cleanupToolSession(sessionId);
      } catch {
        // ignore cleanup failures after process exit
      }
    }
    setSession(null);
    setSessionError("");
  }, [stopPolling]);

  useEffect(() => () => {
    stopPolling();
    const sessionId = sessionIdRef.current;
    sessionIdRef.current = null;
    if (sessionId) {
      void cleanupToolSession(sessionId).catch(() => {
        // ignore cleanup failures after process exit
      });
    }
  }, [stopPolling]);

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
