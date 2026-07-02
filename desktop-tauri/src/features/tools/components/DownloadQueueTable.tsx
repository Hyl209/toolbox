import { useState } from "react";

export type DownloadQueueRow = {
  source_url: string;
  fileName: string;
  detail: string;
  status: "queued" | "running" | "paused" | "success" | "failed" | "cancelled";
  percent?: number;
  speed?: string;
  eta?: string;
};

type DownloadQueueTableProps = {
  rows: DownloadQueueRow[];
  active: boolean;
  paused: boolean;
  onPause: () => void;
  onResume: () => void;
  onCancel: () => void;
  onRename?: (index: number, nextName: string) => void;
  onDelete?: (index: number) => void;
  className?: string;
  iconActions?: boolean;
};

const statusText: Record<DownloadQueueRow["status"], string> = {
  queued: "等待",
  running: "下载中",
  paused: "已暂停",
  success: "完成",
  failed: "失败",
  cancelled: "已取消",
};

function clampPercent(value: number | undefined, status: DownloadQueueRow["status"]) {
  if (status === "success") {
    return 100;
  }
  if (typeof value !== "number" || Number.isNaN(value)) {
    return status === "running" || status === "paused" ? 2 : 0;
  }
  return Math.max(0, Math.min(100, value));
}

function fileExt(name: string) {
  const clean = name.split(/[\\/]/).pop() || name;
  const ext = clean.includes(".") ? clean.split(".").pop() : "";
  return (ext || "FILE").slice(0, 4).toUpperCase();
}

export function DownloadQueueTable({ rows, active, paused, onPause, onResume, onCancel, onRename, onDelete, className = "", iconActions = false }: DownloadQueueTableProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editingName, setEditingName] = useState("");

  if (!rows.length) {
    return null;
  }

  function startRename(index: number, name: string) {
    if (active || !onRename) {
      return;
    }
    setEditingIndex(index);
    setEditingName(name);
  }

  function commitRename(index: number) {
    const next = editingName.trim();
    if (next) {
      onRename?.(index, next);
    }
    setEditingIndex(null);
    setEditingName("");
  }

  return (
    <section className={`download-table-panel ${className}`.trim()} aria-label="下载队列">
      <div className="download-table-head">
        <span>文件名</span>
        <span>进度</span>
        <span>速度</span>
        <span>剩余</span>
        <span>操作</span>
      </div>
      <div className="download-table-body">
        {rows.map((row, index) => {
          const percent = clampPercent(row.percent, row.status);
          const hasControls = active && (row.status === "running" || row.status === "paused");
          const canDelete = !active && row.status === "queued" && Boolean(onDelete);
          return (
            <div className="download-row" key={`${row.source_url}-${index}`}>
              <div className="download-file-cell">
                <span className="download-file-icon" aria-hidden="true">
                  <small>{fileExt(row.fileName)}</small>
                </span>
                <span className="download-file-text">
                  {editingIndex === index ? (
                    <input
                      autoFocus
                      className="download-name-input"
                      onBlur={() => commitRename(index)}
                      onChange={(event) => setEditingName(event.currentTarget.value)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") {
                          commitRename(index);
                        } else if (event.key === "Escape") {
                          setEditingIndex(null);
                          setEditingName("");
                        }
                      }}
                      value={editingName}
                    />
                  ) : (
                    <strong onDoubleClick={() => startRename(index, row.fileName)} title={row.fileName}>{row.fileName}</strong>
                  )}
                  <small title={row.detail}>{row.detail}</small>
                </span>
              </div>
              <div className="download-progress-cell">
                <span className="download-progress-track">
                  <span className="download-progress-fill" style={{ width: `${percent}%` }} />
                </span>
                <small>{row.status === "running" || row.status === "paused" || row.status === "success" ? `${Math.round(percent)}%` : statusText[row.status]}</small>
              </div>
              <span className="download-speed-pill">{row.speed || "-"}</span>
              <span className="download-eta">{row.eta || "-"}</span>
              <span className="download-row-actions">
                {hasControls ? (
                  <>
                    <button
                      aria-label={paused ? "继续" : "暂停"}
                      className={`ghost-button mini-pill${iconActions ? " icon-mini-pill" : ""}`}
                      disabled={paused ? false : row.status !== "running"}
                      onClick={paused ? onResume : onPause}
                      title={paused ? "继续" : "暂停"}
                      type="button"
                    >
                      {iconActions ? (paused ? "▶" : "⏸") : (paused ? "继续" : "暂停")}
                    </button>
                    <button
                      aria-label="取消"
                      className={`ghost-button mini-pill${iconActions ? " icon-mini-pill" : ""}`}
                      onClick={onCancel}
                      title="取消"
                      type="button"
                    >
                      {iconActions ? "✕" : "取消"}
                    </button>
                  </>
                ) : canDelete ? (
                  <button
                    aria-label="取消"
                    className={`ghost-button mini-pill${iconActions ? " icon-mini-pill" : ""}`}
                    onClick={() => onDelete?.(index)}
                    title="取消"
                    type="button"
                  >
                    {iconActions ? "✕" : "×"}
                  </button>
                ) : (
                  <small>{statusText[row.status]}</small>
                )}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
