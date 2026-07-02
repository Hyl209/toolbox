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

export function DownloadQueueTable({ rows, active, paused, onPause, onResume, onCancel }: DownloadQueueTableProps) {
  if (!rows.length) {
    return null;
  }

  return (
    <section className="download-table-panel" aria-label="下载队列">
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
          return (
            <div className="download-row" key={`${row.source_url}-${index}`}>
              <div className="download-file-cell">
                <span className="download-file-icon" aria-hidden="true">
                  <small>{fileExt(row.fileName)}</small>
                </span>
                <span className="download-file-text">
                  <strong title={row.fileName}>{row.fileName}</strong>
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
                    <button className="ghost-button mini-pill" disabled={paused ? false : row.status !== "running"} onClick={paused ? onResume : onPause} type="button">
                      {paused ? "继续" : "暂停"}
                    </button>
                    <button className="ghost-button mini-pill" onClick={onCancel} type="button">
                      取消
                    </button>
                  </>
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
