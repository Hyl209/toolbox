import type { ToolSessionSnapshot } from "../../api/tauri";
import type { DownloadQueueRow } from "./components/DownloadQueueTable";

type QueueTask = {
  source_url: string;
  target_title?: string;
};

type QueueResultRow = Record<string, unknown>;

type QueueStateOptions = {
  progressKinds: readonly string[];
  applyCompletedResult: (row: DownloadQueueRow, result: QueueResultRow) => void;
};

type ProgressMarker = {
  kind: string;
  payload: Record<string, string>;
};

export function parseProgressMarker(message: string): ProgressMarker | null {
  if (!message.startsWith("__HYL_PROGRESS__|")) {
    return null;
  }
  const [, kind = "", ...parts] = message.split("|");
  const payload: Record<string, string> = {};
  for (const part of parts) {
    const [key, ...rest] = part.split("=");
    if (key) {
      payload[key] = rest.join("=");
    }
  }
  return { kind, payload };
}

export function shortPathName(value: string): string {
  return value.split(/[\\/]/).pop() || value;
}

export function percentValue(value: string | undefined): number | undefined {
  if (!value) {
    return undefined;
  }
  const parsed = Number.parseFloat(value.replace("%", ""));
  return Number.isFinite(parsed) ? parsed : undefined;
}

function sessionResultRows(session: ToolSessionSnapshot | null): QueueResultRow[] {
  if (!session?.result || typeof session.result !== "object") {
    return [];
  }
  const direct = session.result as { results?: QueueResultRow[]; data?: { results?: QueueResultRow[] } };
  return direct.data?.results ?? direct.results ?? [];
}

function markerIndex(marker: ProgressMarker, fallbackIndex: number): number {
  const parsed = Number.parseInt(marker.payload.index ?? "", 10);
  return Number.isFinite(parsed) ? Math.max(0, parsed) : fallbackIndex;
}

export function queueRowsFromSession(tasks: QueueTask[], session: ToolSessionSnapshot | null, options: QueueStateOptions): DownloadQueueRow[] {
  const rows = tasks.map<DownloadQueueRow>((task) => ({
    source_url: task.source_url,
    fileName: task.target_title || shortPathName(task.source_url),
    status: "queued",
    detail: task.source_url,
  }));
  if (!session) {
    return rows;
  }

  function rowAt(index: number, url = "") {
    while (rows.length <= index) {
      const sourceUrl = url || `task-${rows.length + 1}`;
      rows.push({
        source_url: sourceUrl,
        fileName: shortPathName(sourceUrl),
        status: "queued",
        detail: sourceUrl,
      });
    }
    return rows[index];
  }

  let fallbackIndex = -1;
  let completedCount = 0;
  let activeIndex = -1;
  for (const event of session.progress_events) {
    const marker = parseProgressMarker(String(event.message ?? ""));
    if (!marker) {
      continue;
    }

    if (marker.kind === "task_start") {
      fallbackIndex = markerIndex(marker, fallbackIndex);
      activeIndex = fallbackIndex;
      const row = rowAt(fallbackIndex, marker.payload.url);
      row.status = session.status === "paused" ? "paused" : "running";
      row.detail = marker.payload.url || row.detail;
      continue;
    }

    if (options.progressKinds.includes(marker.kind)) {
      const currentIndex = markerIndex(marker, fallbackIndex);
      if (currentIndex < 0) {
        continue;
      }
      activeIndex = currentIndex;
      const row = rowAt(currentIndex);
      row.status = session.status === "paused" ? "paused" : "running";
      if (marker.payload.name) {
        row.fileName = marker.payload.name;
      }
      row.percent = percentValue(marker.payload.percent) ?? row.percent;
      row.speed = marker.payload.speed || row.speed;
      row.eta = marker.payload.eta || row.eta;
      continue;
    }

    if (marker.kind === "task_done") {
      completedCount = Math.max(completedCount, Number.parseInt(marker.payload.completed ?? "0", 10));
      const currentIndex = markerIndex(marker, -1);
      if (currentIndex >= 0) {
        activeIndex = currentIndex;
        const row = rowAt(currentIndex);
        row.status = "success";
        row.detail = "已完成";
        row.percent = 100;
      }
    }
  }

  if (completedCount > 0) {
    rows.forEach((row, index) => {
      if (index < completedCount && row.status === "queued") {
        row.status = "success";
        row.detail = "已完成";
        row.percent = 100;
      }
    });
  }

  if (session.status === "completed") {
    sessionResultRows(session).forEach((item, index) => {
      const row = rows[index];
      if (!row) {
        return;
      }
      options.applyCompletedResult(row, item);
    });
    return rows;
  }

  if (activeIndex >= 0 && activeIndex < rows.length) {
    if (session.status === "paused") {
      rows[activeIndex].status = "paused";
      rows[activeIndex].detail = "已暂停";
    } else if (session.status === "cancelled") {
      rows[activeIndex].status = "cancelled";
      rows[activeIndex].detail = "已取消";
    } else if (session.status === "failed") {
      rows[activeIndex].status = "failed";
      rows[activeIndex].detail = session.error || "failed";
    }
  }

  return rows;
}
