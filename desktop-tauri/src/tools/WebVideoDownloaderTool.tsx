import { useEffect, useMemo, useRef, useState } from "react";
import { pickDirectory, runTool, type ToolInput, type ToolResult, type ToolSessionSnapshot, type ToolSettings } from "../api/tauri";
import { DownloadQueueTable, type DownloadQueueRow } from "../features/tools/components/DownloadQueueTable";
import { queueRowsFromSession as buildQueueRows } from "../features/tools/downloadQueueState";
import { useDownloadRuntimeSession } from "../features/tools/hooks/useDownloadRuntimeSession";

type WebTask = {
  source_url: string;
  source_kind: string;
  target_title?: string;
  output_subdir?: string;
};

type InspectResult = {
  source_url: string;
  success: boolean;
  candidate_count: number;
  candidates: string[];
  source?: string;
  error?: string;
};

type DownloadResult = {
  source_url: string;
  success: boolean;
  error?: string;
  downloaded_count?: number;
  files?: string[];
};

type WebVideoResult = ToolResult & {
  urls?: string[];
  tasks?: WebTask[];
  url_count?: number;
  task_count?: number;
  valid?: boolean;
  errors?: string[];
  results?: InspectResult[];
  success_count?: number;
  fail_count?: number;
  logs?: string[];
  files?: string[];
  data?: WebVideoResult;
};

function text(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return typeof error === "string" ? error : JSON.stringify(error);
}

function dataOf(result: ToolResult | null | undefined): WebVideoResult {
  const direct = (result ?? {}) as WebVideoResult;
  return (direct.data ?? direct) as WebVideoResult;
}

function effectiveProxyUrl(proxyUrl: string, proxyHost: string, proxyPort: string): string {
  const host = proxyHost.trim();
  const port = proxyPort.trim();
  if (host && port) {
    if (host.includes("://")) {
      return host.replace(/(?::\d+)?(?:\/)?$/, `:${port}`);
    }
    return `http://${host.split(":")[0]}:${port}`;
  }
  const direct = proxyUrl.trim();
  if (direct && (direct.includes("://") || /:\d+$/.test(direct))) {
    return direct.includes("://") ? direct : `http://${direct}`;
  }
  return "";
}

function queueRowsFromSession(tasks: WebTask[], session: ToolSessionSnapshot | null): DownloadQueueRow[] {
  return buildQueueRows(tasks, session, {
    progressKinds: ["file", "web_status", "web_aria2", "web_percent"],
    applyCompletedResult(row, item) {
      const result = item as DownloadResult;
      row.status = result.success ? "success" : "failed";
      row.fileName = result.files?.[0] ? result.files[0].split(/[\\/]/).pop() || row.fileName : row.fileName;
      row.percent = result.success ? 100 : row.percent;
      row.detail = result.success ? `${result.downloaded_count ?? result.files?.length ?? 0} files` : result.error || "failed";
    },
  });
}

function WebVideoDownloaderTool({ initialSettings = {} }: { initialSettings?: ToolSettings }) {
  const outputDirTouchedRef = useRef(false);
  const settingsTouchedRef = useRef(false);
  const runtime = useDownloadRuntimeSession("webvideodownloader");
  const [urlText, setUrlText] = useState("");
  const [outputDir, setOutputDir] = useState(initialSettings.output_dir ?? "");
  const [proxyHost, setProxyHost] = useState(initialSettings.proxy_host ?? "127.0.0.1");
  const [proxyPort, setProxyPort] = useState(initialSettings.proxy_port ?? "");
  const [proxyUrl, setProxyUrl] = useState(initialSettings.proxy_url ?? "");
  const [overwrite, setOverwrite] = useState(initialSettings.overwrite ?? false);
  const [outputSubdirByTitle, setOutputSubdirByTitle] = useState(initialSettings.output_subdir_by_title ?? false);
  const [concurrent, setConcurrent] = useState(initialSettings.concurrent ?? "1");
  const [inspectAll, setInspectAll] = useState(false);
  const [urls, setUrls] = useState<string[]>([]);
  const [tasks, setTasks] = useState<WebTask[]>([]);
  const [inspectRows, setInspectRows] = useState<InspectResult[]>([]);
  const [downloadRows, setDownloadRows] = useState<DownloadResult[]>([]);
  const [downloadedFiles, setDownloadedFiles] = useState<string[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const busy = running || runtime.active;
  const paused = runtime.paused;
  const canRun = !busy && urlText.trim().length > 0;
  const payload = useMemo(
    () => ({
      text: urlText,
      output_dir: outputDir,
      options: {
        proxy_host: proxyHost,
        proxy_port: proxyPort,
        proxy_url: effectiveProxyUrl(proxyUrl, proxyHost, proxyPort),
        overwrite,
        output_subdir_by_title: outputSubdirByTitle,
        max_concurrent_downloads: Number.parseInt(concurrent || "1", 10) || 1,
        web_download_all_candidates: inspectAll,
      },
    }),
    [concurrent, inspectAll, outputDir, outputSubdirByTitle, overwrite, proxyHost, proxyPort, proxyUrl, urlText],
  );
  const queueRows = useMemo(() => queueRowsFromSession(tasks, runtime.session), [tasks, runtime.session]);
  const runtimeLogs = runtime.session?.logs?.length ? runtime.session.logs : logs;

  useEffect(() => {
    if (!outputDirTouchedRef.current) {
      setOutputDir(initialSettings.output_dir ?? "");
    }
    if (!settingsTouchedRef.current) {
      setProxyHost(initialSettings.proxy_host ?? "127.0.0.1");
      setProxyPort(initialSettings.proxy_port ?? "");
      setProxyUrl(initialSettings.proxy_url ?? "");
      setOverwrite(initialSettings.overwrite ?? false);
      setOutputSubdirByTitle(initialSettings.output_subdir_by_title ?? false);
      setConcurrent(initialSettings.concurrent ?? "1");
    }
  }, [initialSettings]);

  useEffect(() => {
    if (!runtime.session) {
      return;
    }
    if (runtime.session.status === "completed") {
      const data = dataOf(runtime.session.result);
      setDownloadRows((data.results ?? []) as DownloadResult[]);
      setDownloadedFiles(data.files ?? []);
      setError("");
    } else if (runtime.session.status === "failed") {
      setError(runtime.session.error ?? "download failed");
    } else if (runtime.session.status === "cancelled") {
      setError("");
    }
  }, [runtime.session]);

  async function chooseOutputDir() {
    const path = await pickDirectory({ title: "选择网页视频输出目录" });
    if (path) {
      outputDirTouchedRef.current = true;
      setOutputDir(path);
    }
  }

  async function handleParseValidate() {
    if (!canRun) {
      return;
    }
    setRunning(true);
    setError("");
    setInspectRows([]);
    setDownloadRows([]);
    setDownloadedFiles([]);
    try {
      const parsed = dataOf(await runTool("webvideodownloader", { task_id: `webvideo-parse-${Date.now()}`, action: "parse", payload: { text: urlText } }));
      setUrls(parsed.urls ?? []);
      setTasks(parsed.tasks ?? []);
      const checked = dataOf(await runTool("webvideodownloader", { task_id: `webvideo-validate-${Date.now()}`, action: "validate", payload }));
      setLogs((items) => [`parse=${parsed.url_count ?? 0}; validate=${checked.valid ? "ok" : "bad"}`, ...items].slice(0, 20));
    } catch (caught) {
      const message = text(caught);
      setError(message);
      setLogs((items) => [`parse/validate failed: ${message}`, ...items].slice(0, 20));
    } finally {
      setRunning(false);
    }
  }

  async function handleInspect() {
    if (!canRun) {
      return;
    }
    setRunning(true);
    setError("");
    try {
      const data = dataOf(await runTool("webvideodownloader", { task_id: `webvideo-inspect-${Date.now()}`, action: "inspect", payload }));
      setInspectRows(data.results ?? []);
      setLogs((items) => [...(data.logs ?? [`inspect success=${data.success_count ?? 0}; fail=${data.fail_count ?? 0}`]), ...items].slice(0, 20));
    } catch (caught) {
      const message = text(caught);
      setError(message);
      setLogs((items) => [`inspect failed: ${message}`, ...items].slice(0, 20));
    } finally {
      setRunning(false);
    }
  }

  async function handleDownload() {
    if (!canRun) {
      return;
    }
    if (!outputDir.trim()) {
      setError("请先选择输出目录");
      return;
    }
    setError("");
    setDownloadRows([]);
    setDownloadedFiles([]);
    const input: ToolInput = {
      task_id: `webvideo-download-${Date.now()}`,
      action: "download",
      payload,
    };
    try {
      await runtime.start(input);
    } catch (caught) {
      setError(text(caught));
    }
  }

  async function clearResults() {
    await runtime.clear();
    setUrls([]);
    setTasks([]);
    setInspectRows([]);
    setDownloadRows([]);
    setDownloadedFiles([]);
    setLogs([]);
    setError("");
  }

  return (
    <div className="base64-tool">
      <div className="tool-heading">
        <div>
          <h2>{"网页视频下载"}</h2>
          <p>下载网页视频。</p>
        </div>
      </div>

      <div className="editor-grid">
        <label className="field-block">
          <span>
            {"URL / 分享文本"}
            <small>{urls.length ? `${urls.length} parsed` : "multi-line"}</small>
          </span>
          <textarea disabled={busy} onChange={(event) => setUrlText(event.currentTarget.value)} placeholder="https://example.com/video" value={urlText} />
        </label>

        <div className="file-mode-card compact-card">
          <label className="field-block file-path-field">
            <span>{"输出目录"}</span>
            <div className="path-input-row">
              <input disabled={busy} onChange={(event) => { outputDirTouchedRef.current = true; setOutputDir(event.currentTarget.value); }} placeholder="E:\\downloads" value={outputDir} />
              <button className="path-pick-button" disabled={busy} onClick={chooseOutputDir} type="button">
                {"选择"}
              </button>
            </div>
          </label>
          <label className="field-block file-path-field">
            <span>{"Proxy Host"}</span>
            <input disabled={busy} onChange={(event) => { settingsTouchedRef.current = true; setProxyHost(event.currentTarget.value); }} placeholder="127.0.0.1" value={proxyHost} />
          </label>
          <label className="field-block file-path-field">
            <span>{"Proxy Port"}</span>
            <input disabled={busy} onChange={(event) => { settingsTouchedRef.current = true; setProxyPort(event.currentTarget.value); }} placeholder="7890" value={proxyPort} />
          </label>
          <label className="field-block file-path-field">
            <span>{"代理 URL"}</span>
            <input disabled={busy} onChange={(event) => { settingsTouchedRef.current = true; setProxyUrl(event.currentTarget.value); }} placeholder="http://127.0.0.1:7890" value={proxyUrl} />
          </label>
          <label className="field-block file-path-field">
            <span>{"Concurrent"}</span>
            <select disabled={busy} onChange={(event) => { settingsTouchedRef.current = true; setConcurrent(event.currentTarget.value); }} value={concurrent}>
              {["0", "1", "2", "3", "4", "5"].map((value) => (
                <option key={value} value={value}>{value === "0" ? "auto" : value}</option>
              ))}
            </select>
          </label>
          <label className="check-row">
            <input checked={overwrite} disabled={busy} onChange={(event) => { settingsTouchedRef.current = true; setOverwrite(event.currentTarget.checked); }} type="checkbox" />
            {"overwrite"}
          </label>
          <label className="check-row">
            <input checked={outputSubdirByTitle} disabled={busy} onChange={(event) => { settingsTouchedRef.current = true; setOutputSubdirByTitle(event.currentTarget.checked); }} type="checkbox" />
            {"output_subdir_by_title"}
          </label>
          <label className="check-row">
            <input checked={inspectAll} disabled={busy} onChange={(event) => setInspectAll(event.currentTarget.checked)} type="checkbox" />
            {"候选检查时传递 all candidates 选项"}
          </label>
        </div>
      </div>

      <div className="actions-row">
        <div className="button-cluster">
          <button className="ghost-button" disabled={busy || (!urls.length && !inspectRows.length && !downloadRows.length && !runtimeLogs.length && !error)} onClick={() => void clearResults()} type="button">
            {"清空"}
          </button>
          <button className="ghost-button" disabled={!canRun} onClick={handleParseValidate} type="button">
            {"校验"}
          </button>
          <button className="primary-button" disabled={!canRun} onClick={handleInspect} type="button">
            {"媒体"}
          </button>
          <button className="primary-button" disabled={!canRun || !outputDir.trim()} onClick={handleDownload} type="button">
            {"下载"}
          </button>

        </div>
      </div>

<DownloadQueueTable
        active={runtime.active}
        onCancel={() => void runtime.control("cancel")}
        onPause={() => void runtime.control("pause")}
        onResume={() => void runtime.control("resume")}
        paused={paused}
        rows={queueRows}
      />

      {inspectRows.length ? (
        <section className="table-panel">
          <div className="panel-title">{"媒体候选"}</div>
          <div className="result-list">
            {inspectRows.map((row, index) => (
              <div className="result-row" key={`${row.source_url}-${index}`}>
                <span>{row.source_url}</span>
                <strong>{row.success ? `${row.candidate_count} candidates (${row.source || "unknown"})` : row.error || "failed"}</strong>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {downloadRows.length || downloadedFiles.length ? (
        <section className="table-panel">
          <div className="panel-title">{"下载结果"}</div>
          <div className="result-list">
            {downloadRows.map((row, index) => (
              <div className="result-row" key={`${row.source_url}-${index}`}>
                <span>{row.source_url}</span>
                <strong>{row.success ? `${row.downloaded_count ?? row.files?.length ?? 0} files` : row.error || "failed"}</strong>
              </div>
            ))}
            {downloadedFiles.map((file, index) => (
              <div className="result-row" key={`${file}-${index}`}>
                <span>{file}</span>
                <strong>{"saved"}</strong>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="log-panel" aria-label="Runtime">
        <div>
          <div className="panel-title">Runtime</div>
          <p className="muted">{"最近的解析、校验、候选检查或下载记录"}</p>
        </div>
        <div className="log-content">
          {error ? <div className="error-box">{error}</div> : null}
          {runtimeLogs.length ? (
            <ul>
              {runtimeLogs.slice(-50).map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="muted">{"暂无日志"}</p>
          )}
        </div>
      </section>
    </div>
  );
}

export default WebVideoDownloaderTool;
