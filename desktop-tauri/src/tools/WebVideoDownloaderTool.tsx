import { useEffect, useMemo, useRef, useState } from "react";
import { pickDirectory, runTool, type ToolResult, type ToolSettings } from "../api/tauri";

type BackendStatus = {
  available?: boolean;
  label?: string;
  message?: string;
  path?: string;
};

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
  backends?: Record<string, BackendStatus>;
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

function dataOf(result: ToolResult): WebVideoResult {
  const direct = result as WebVideoResult;
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

function WebVideoDownloaderTool({ initialSettings = {} }: { initialSettings?: ToolSettings }) {
  const outputDirTouchedRef = useRef(false);
  const settingsTouchedRef = useRef(false);
  const [urlText, setUrlText] = useState("");
  const [outputDir, setOutputDir] = useState(initialSettings.output_dir ?? "");
  const [proxyHost, setProxyHost] = useState(initialSettings.proxy_host ?? "127.0.0.1");
  const [proxyPort, setProxyPort] = useState(initialSettings.proxy_port ?? "");
  const [proxyUrl, setProxyUrl] = useState(initialSettings.proxy_url ?? "");
  const [overwrite, setOverwrite] = useState(initialSettings.overwrite ?? false);
  const [outputSubdirByTitle, setOutputSubdirByTitle] = useState(initialSettings.output_subdir_by_title ?? false);
  const [concurrent, setConcurrent] = useState(initialSettings.concurrent ?? "1");
  const [inspectAll, setInspectAll] = useState(false);
  const [backends, setBackends] = useState<Record<string, BackendStatus>>({});
  const [urls, setUrls] = useState<string[]>([]);
  const [tasks, setTasks] = useState<WebTask[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [inspectRows, setInspectRows] = useState<InspectResult[]>([]);
  const [downloadRows, setDownloadRows] = useState<DownloadResult[]>([]);
  const [downloadedFiles, setDownloadedFiles] = useState<string[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const canRun = !running && urlText.trim().length > 0;
  const backendReady = Boolean(backends.yt_dlp?.available);
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
    let cancelled = false;
    runTool("webvideodownloader", { task_id: `webvideo-probe-${Date.now()}`, action: "probe", payload: {} })
      .then((result) => {
        if (!cancelled) {
          setBackends(dataOf(result).backends ?? {});
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(text(caught));
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function chooseOutputDir() {
    const path = await pickDirectory({ title: "\u9009\u62e9\u7f51\u9875\u89c6\u9891\u8f93\u51fa\u76ee\u5f55" });
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
      setErrors(checked.errors ?? []);
      setLogs((items) => [`parse=${parsed.url_count ?? 0}; validate=${checked.valid ? "ok" : "bad"}`, ...items].slice(0, 8));
    } catch (caught) {
      const message = text(caught);
      setError(message);
      setLogs((items) => [`parse/validate failed: ${message}`, ...items].slice(0, 8));
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
      setLogs((items) => [...(data.logs ?? [`inspect success=${data.success_count ?? 0}; fail=${data.fail_count ?? 0}`]), ...items].slice(0, 8));
    } catch (caught) {
      const message = text(caught);
      setError(message);
      setLogs((items) => [`inspect failed: ${message}`, ...items].slice(0, 8));
    } finally {
      setRunning(false);
    }
  }

  async function handleDownload() {
    if (!canRun) {
      return;
    }
    if (!outputDir.trim()) {
      setError("\u8bf7\u5148\u9009\u62e9\u8f93\u51fa\u76ee\u5f55");
      return;
    }
    setRunning(true);
    setError("");
    try {
      const data = dataOf(await runTool("webvideodownloader", { task_id: `webvideo-download-${Date.now()}`, action: "download", payload }));
      setDownloadRows((data.results ?? []) as DownloadResult[]);
      setDownloadedFiles(data.files ?? []);
      setErrors(data.errors ?? []);
      setLogs((items) => [...(data.logs ?? [`download success=${data.success_count ?? 0}; fail=${data.fail_count ?? 0}`]), ...items].slice(0, 8));
    } catch (caught) {
      const message = text(caught);
      setError(message);
      setLogs((items) => [`download failed: ${message}`, ...items].slice(0, 8));
    } finally {
      setRunning(false);
    }
  }

  function clearResults() {
    setUrls([]);
    setTasks([]);
    setErrors([]);
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
          <p className="eyebrow">Legacy web video downloader</p>
          <h2>{"\u7f51\u9875\u89c6\u9891\u4e0b\u8f7d"}</h2>
          <p>{"\u5df2\u63a5\u5165\uff1a\u73af\u5883\u63a2\u6d4b\u3001\u94fe\u63a5\u89e3\u6790\u3001\u4e0b\u8f7d\u8bf7\u6c42\u6821\u9a8c\u3001\u5a92\u4f53\u5019\u9009\u68c0\u67e5\u3001\u4e0b\u8f7d\u6267\u884c\u3002"}</p>
        </div>
        <span className={`settings-mode-pill ${backendReady ? "ready-pill" : ""}`}>{backendReady ? "yt-dlp ready" : "probe only"}</span>
      </div>

      <div className="info-box">
        {"\u5df2\u63a5\u5165\u4e0b\u8f7d\u6267\u884c\uff1b\u961f\u5217 / \u6682\u505c\u6062\u590d\u6682\u672a\u63a5\u5165\u3002\u672c\u9875\u53ea\u8c03\u7528 sidecar \u5c55\u793a\u8f93\u5165\u3001\u72b6\u6001\u548c\u7ed3\u679c\u3002"}
      </div>

      <div className="editor-grid">
        <label className="field-block">
          <span>
            {"URL / \u5206\u4eab\u6587\u672c"}
            <small>{urls.length ? `${urls.length} parsed` : "multi-line"}</small>
          </span>
          <textarea disabled={running} onChange={(event) => setUrlText(event.currentTarget.value)} placeholder="https://example.com/video" value={urlText} />
        </label>

        <div className="file-mode-card compact-card">
          <label className="field-block file-path-field">
            <span>{"\u8f93\u51fa\u76ee\u5f55"}</span>
            <div className="path-input-row">
              <input disabled={running} onChange={(event) => { outputDirTouchedRef.current = true; setOutputDir(event.currentTarget.value); }} placeholder="E:\\downloads" value={outputDir} />
              <button className="path-pick-button" disabled={running} onClick={chooseOutputDir} type="button">
                {"\u9009\u62e9"}
              </button>
            </div>
          </label>
          <label className="field-block file-path-field">
            <span>{"Proxy Host"}</span>
            <input disabled={running} onChange={(event) => { settingsTouchedRef.current = true; setProxyHost(event.currentTarget.value); }} placeholder="127.0.0.1" value={proxyHost} />
          </label>
          <label className="field-block file-path-field">
            <span>{"Proxy Port"}</span>
            <input disabled={running} onChange={(event) => { settingsTouchedRef.current = true; setProxyPort(event.currentTarget.value); }} placeholder="7890" value={proxyPort} />
          </label>
          <label className="field-block file-path-field">
            <span>{"Legacy Proxy URL"}</span>
            <input disabled={running} onChange={(event) => { settingsTouchedRef.current = true; setProxyUrl(event.currentTarget.value); }} placeholder="http://127.0.0.1:7890" value={proxyUrl} />
          </label>
          <label className="field-block file-path-field">
            <span>{"Concurrent"}</span>
            <select disabled={running} onChange={(event) => { settingsTouchedRef.current = true; setConcurrent(event.currentTarget.value); }} value={concurrent}>
              {["0", "1", "2", "3", "4", "5"].map((value) => (
                <option key={value} value={value}>{value === "0" ? "auto" : value}</option>
              ))}
            </select>
          </label>
          <label className="check-row">
            <input checked={overwrite} disabled={running} onChange={(event) => { settingsTouchedRef.current = true; setOverwrite(event.currentTarget.checked); }} type="checkbox" />
            {"overwrite"}
          </label>
          <label className="check-row">
            <input checked={outputSubdirByTitle} disabled={running} onChange={(event) => { settingsTouchedRef.current = true; setOutputSubdirByTitle(event.currentTarget.checked); }} type="checkbox" />
            {"output_subdir_by_title"}
          </label>
          <label className="check-row">
            <input checked={inspectAll} disabled={running} onChange={(event) => setInspectAll(event.currentTarget.checked)} type="checkbox" />
            {"\u5019\u9009\u68c0\u67e5\u65f6\u4f20\u9012 all candidates \u9009\u9879"}
          </label>
        </div>
      </div>

      <div className="settings-card">
        <span>{"\u540e\u7aef\u63a2\u6d4b"}</span>
        <div className="tool-result-grid">
          {Object.entries(backends).map(([key, item]) => (
            <div className="result-card" key={key}>
              <span>{key}</span>
              <strong>{item.available ? "available" : "missing"}</strong>
              <p>{item.path || item.message || item.label || "-"}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="actions-row">
        <div className="action-hint">{"React \u4ec5\u6536\u96c6\u8f93\u5165\u5e76\u5c55\u793a\u7ed3\u679c\uff0c\u4e0d\u590d\u5236\u89e3\u6790 / \u4e0b\u8f7d\u903b\u8f91\u3002"}</div>
        <div className="button-cluster">
          <button className="ghost-button" disabled={running || (!urls.length && !inspectRows.length && !downloadRows.length && !logs.length && !error)} onClick={clearResults} type="button">
            {"\u6e05\u7a7a\u7ed3\u679c"}
          </button>
          <button className="ghost-button" disabled={!canRun} onClick={handleParseValidate} type="button">
            {running ? "running..." : "\u89e3\u6790 / \u6821\u9a8c"}
          </button>
          <button className="primary-button" disabled={!canRun} onClick={handleInspect} type="button">
            {running ? "running..." : "\u68c0\u67e5\u5a92\u4f53\u5019\u9009"}
          </button>
          <button className="primary-button" disabled={!canRun || !outputDir.trim()} onClick={handleDownload} type="button">
            {running ? "running..." : "\u5f00\u59cb\u4e0b\u8f7d"}
          </button>
        </div>
      </div>

      <div className="editor-grid file-editor-grid">
        <div className="result-card">
          <span>{"\u89e3\u6790\u7ed3\u679c"}</span>
          <strong>{tasks.length ? `${tasks.length} tasks` : "waiting"}</strong>
          <p>{tasks[0]?.target_title || urls[0] || "-"}</p>
        </div>
        <div className="result-card">
          <span>{"\u6821\u9a8c\u7ed3\u679c"}</span>
          <strong>{errors.length ? `${errors.length} issues` : "no issues"}</strong>
          <p>{errors[0] || "-"}</p>
        </div>
      </div>

      {inspectRows.length ? (
        <section className="table-panel">
          <div className="panel-title">{"\u5a92\u4f53\u5019\u9009"}</div>
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
          <div className="panel-title">{"\u4e0b\u8f7d\u7ed3\u679c"}</div>
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
          <p className="muted">{"\u6700\u8fd1\u7684\u89e3\u6790\u3001\u6821\u9a8c\u3001\u5019\u9009\u68c0\u67e5\u6216\u4e0b\u8f7d\u8bb0\u5f55"}</p>
        </div>
        <div className="log-content">
          {error ? <div className="error-box">{error}</div> : null}
          {logs.length ? (
            <ul>
              {logs.map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="muted">{"\u6682\u65e0\u65e5\u5fd7"}</p>
          )}
        </div>
      </section>
    </div>
  );
}

export default WebVideoDownloaderTool;
