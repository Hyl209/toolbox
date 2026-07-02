import { useEffect, useMemo, useRef, useState } from "react";
import { pickDirectory, runTool, type ToolInput, type ToolResult, type ToolSessionSnapshot, type ToolSettings } from "../api/tauri";
import { ActionBar, DirectoryPickerRow, RuntimeLogPanel, ToolHeading } from "../features/tools/components/CommonToolParts";
import { DownloadQueueTable, type DownloadQueueRow } from "../features/tools/components/DownloadQueueTable";
import { queueOverviewFromSession, queueRowsFromSession as buildQueueRows } from "../features/tools/downloadQueueState";
import { useDownloadRuntimeSession } from "../features/tools/hooks/useDownloadRuntimeSession";

type DirectRequest = {
  url: string;
  output_name: string;
  extra_headers: string[];
  referer: string;
  guess_filename: string;
};

type DirectTask = {
  source_url: string;
  target_title?: string;
};

type DirectResult = ToolResult & {
  available?: boolean;
  path?: string;
  default_connections?: number;
  requests?: DirectRequest[];
  valid?: boolean;
  errors?: string[];
  logs?: string[];
  success_count?: number;
  fail_count?: number;
  results?: Array<Record<string, unknown>>;
  data?: DirectResult;
};

function errorText(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return typeof error === "string" ? error : JSON.stringify(error);
}

function dataOf(result: ToolResult | null | undefined): DirectResult {
  const direct = (result ?? {}) as DirectResult;
  return (direct.data ?? direct) as DirectResult;
}

function headerLines(text: string): string[] {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function splitProxyUrl(value: unknown): { host: string; port: string } {
  if (typeof value !== "string" || !value.trim()) {
    return { host: "", port: "" };
  }
  try {
    const parsed = new URL(value.includes("://") ? value : `http://${value}`);
    const hostWithMaybePort = parsed.host;
    const portAt = parsed.port ? hostWithMaybePort.lastIndexOf(":") : -1;
    const hostWithoutPort = portAt >= 0 ? hostWithMaybePort.slice(0, portAt) : hostWithMaybePort;
    const password = parsed.password ? `:${parsed.password}` : "";
    const auth = parsed.username ? `${parsed.username}${password}@` : "";
    return { host: `${parsed.protocol}//${auth}${hostWithoutPort}`, port: parsed.port };
  } catch {
    const cleaned = value.trim();
    const portAt = cleaned.lastIndexOf(":");
    if (portAt >= 0) {
      const port = cleaned.slice(portAt + 1);
      if (/^\d+$/.test(port)) {
        return { host: cleaned.slice(0, portAt), port };
      }
    }
    return { host: cleaned, port: "" };
  }
}

function tasksFromRequests(requests: DirectRequest[]): DirectTask[] {
  return requests.map((request) => ({
    source_url: request.url,
    target_title: request.output_name || request.guess_filename,
  }));
}

function queueRowsFromSession(tasks: DirectTask[], session: ToolSessionSnapshot | null): DownloadQueueRow[] {
  return buildQueueRows(tasks, session, {
    progressKinds: ["direct_aria2"],
    applyCompletedResult(row, item) {
      const success = Boolean(item.success);
      row.status = success ? "success" : "failed";
      row.percent = success ? 100 : row.percent;
      row.detail = success ? "已完成" : String(item.output ?? item.error ?? "失败");
    },
  });
}

function DirectDownloaderTool({ initialOutputDir = "", initialSettings = {} }: { initialOutputDir?: string; initialSettings?: ToolSettings }) {
  const didApplyInitial = useRef(false);
  const initialProxy = splitProxyUrl(initialSettings.proxy_url);
  const runtime = useDownloadRuntimeSession("directdownloader");
  const [urlText, setUrlText] = useState("");
  const [outputDir, setOutputDir] = useState(initialOutputDir);
  const [outputName, setOutputName] = useState("");
  const [connections, setConnections] = useState(initialSettings.connections ?? "16");
  const [proxyHost, setProxyHost] = useState(initialProxy.host);
  const [proxyPort, setProxyPort] = useState(initialProxy.port);
  const [referer, setReferer] = useState(initialSettings.referer ?? "");
  const [extraHeaders, setExtraHeaders] = useState("");
  const [overwrite, setOverwrite] = useState(initialSettings.overwrite ?? false);
  const [outputSubdirByFilename, setOutputSubdirByFilename] = useState(initialSettings.output_subdir_by_filename ?? false);
  const [requests, setRequests] = useState<DirectRequest[]>([]);
  const [tasks, setTasks] = useState<DirectTask[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const parsedHeaders = useMemo(() => headerLines(extraHeaders), [extraHeaders]);
  const busy = running || runtime.active;
  const canInspect = !busy && urlText.trim().length > 0;
  const canBuild = canInspect && outputDir.trim().length > 0;
  const queueRows = useMemo(() => queueRowsFromSession(tasks, runtime.session), [tasks, runtime.session]);
  const overview = useMemo(() => queueOverviewFromSession(tasks, runtime.session), [tasks, runtime.session]);
  const runtimeLogs = runtime.session?.logs?.length ? runtime.session.logs : logs;

  useEffect(() => {
    if (!initialOutputDir) {
      return;
    }
    setOutputDir((current) => current || initialOutputDir);
  }, [initialOutputDir]);

  useEffect(() => {
    if (didApplyInitial.current || !Object.keys(initialSettings).length) {
      return;
    }
    const proxy = splitProxyUrl(initialSettings.proxy_url);
    setConnections((current) => (current === "16" ? initialSettings.connections || current : current));
    setProxyHost((current) => current || proxy.host);
    setProxyPort((current) => current || proxy.port);
    setReferer((current) => current || initialSettings.referer || "");
    setOverwrite((current) => (current === false ? initialSettings.overwrite ?? current : current));
    setOutputSubdirByFilename((current) => (current === false ? initialSettings.output_subdir_by_filename ?? current : current));
    didApplyInitial.current = true;
  }, [initialSettings]);

  const payload = useMemo(
    () => ({
      url_text: urlText,
      output_dir: outputDir,
      output_name: outputName,
      connections,
      proxy_host: proxyHost,
      proxy_port: proxyPort,
      referer,
      extra_headers: parsedHeaders,
      overwrite,
      output_subdir_by_filename: outputSubdirByFilename,
    }),
    [connections, outputDir, outputName, outputSubdirByFilename, overwrite, parsedHeaders, proxyHost, proxyPort, referer, urlText],
  );

  useEffect(() => {
    let cancelled = false;
    runTool("directdownloader", { task_id: `direct-probe-${Date.now()}`, action: "probe", payload: {} })
      .then((result) => {
        if (cancelled) {
          return;
        }
        const data = dataOf(result);
        if (data.default_connections) {
          setConnections((current) => current || String(data.default_connections));
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(errorText(caught));
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function chooseOutputDir() {
    const path = await pickDirectory({ title: "选择直链下载输出目录" });
    if (path) {
      setOutputDir(path);
    }
  }

  async function handleParseValidate() {
    if (!canInspect) {
      return;
    }
    setRunning(true);
    setError("");
    setTasks([]);
    try {
      const parsed = dataOf(await runTool("directdownloader", { task_id: `direct-parse-${Date.now()}`, action: "parse", payload: { url_text: urlText } }));
      setRequests(parsed.requests ?? []);
      setTasks(tasksFromRequests(parsed.requests ?? []));
      const checked = dataOf(await runTool("directdownloader", { task_id: `direct-validate-${Date.now()}`, action: "validate", payload }));
      const issueCount = checked.errors?.length ?? 0;
      setLogs((items) => [`解析 ${parsed.requests?.length ?? 0} 条，校验${issueCount ? `发现 ${issueCount} 个问题` : "通过"}`, ...items].slice(0, 8));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`校验失败：${message}`, ...items].slice(0, 8));
    } finally {
      setRunning(false);
    }
  }

  async function handleDownload() {
    if (!canBuild) {
      return;
    }
    setRunning(true);
    setError("");
    try {
      let parsedRequests = requests;
      if (!parsedRequests.length) {
        const parsed = dataOf(await runTool("directdownloader", { task_id: `direct-parse-${Date.now()}`, action: "parse", payload: { url_text: urlText } }));
        parsedRequests = parsed.requests ?? [];
        setRequests(parsedRequests);
      }
      setTasks(tasksFromRequests(parsedRequests));
      const input: ToolInput = {
        task_id: `direct-download-${Date.now()}`,
        action: "download",
        payload,
      };
      await runtime.start(input);
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`下载失败：${message}`, ...items].slice(0, 8));
    } finally {
      setRunning(false);
    }
  }

  async function clearResults() {
    await runtime.clear();
    setRequests([]);
    setTasks([]);
    setError("");
    setLogs([]);
  }

  return (
    <div className="directdownloader-tool">
      <ToolHeading
        eyebrow="Legacy direct downloader"
        title="直链下载"
        description="粘贴真实直链，先校验，再直接下载。"
        statusLabel=""
      />

      <div className="editor-grid">
        <label className="field-block">
          <span>
            URL / aria2 命令
            <small>{requests.length ? `${requests.length} parsed` : "支持多行"}</small>
          </span>
          <textarea
            disabled={busy}
            onChange={(event) => setUrlText(event.currentTarget.value)}
            placeholder={'https://example.com/file.zip\naria2c "https://cdn.example.com/a.rar" --out "a.rar" --header "Cookie:a=b"'}
            value={urlText}
          />
        </label>

        <div className="file-mode-card compact-card">
          <DirectoryPickerRow label="输出目录" value={outputDir} disabled={busy} onChange={setOutputDir} onPick={chooseOutputDir} placeholder="E:\\downloads" />
          <label className="field-block file-path-field">
            <span>单文件名（多 URL 留空）</span>
            <input disabled={busy} onChange={(event) => setOutputName(event.currentTarget.value)} placeholder="archive.zip" value={outputName} />
          </label>
        </div>
      </div>

      <details className="file-mode-card direct-advanced-options">
        <summary>高级选项</summary>
        <div className="tool-result-grid">
          <label className="field-block file-path-field">
            <span>连接数</span>
            <input disabled={busy} onChange={(event) => setConnections(event.currentTarget.value)} placeholder="16" value={connections} />
          </label>
          <label className="field-block file-path-field">
            <span>代理 Host</span>
            <input disabled={busy} onChange={(event) => setProxyHost(event.currentTarget.value)} placeholder="127.0.0.1" value={proxyHost} />
          </label>
          <label className="field-block file-path-field">
            <span>代理 Port</span>
            <input disabled={busy} onChange={(event) => setProxyPort(event.currentTarget.value)} placeholder="7890" value={proxyPort} />
          </label>
          <label className="field-block file-path-field">
            <span>Referer</span>
            <input disabled={busy} onChange={(event) => setReferer(event.currentTarget.value)} placeholder="https://pan.example.com/" value={referer} />
          </label>
          <label className="field-block file-path-field">
            <span>额外 Headers（每行一个）</span>
            <textarea disabled={busy} onChange={(event) => setExtraHeaders(event.currentTarget.value)} placeholder="User-Agent:Mozilla/5.0" value={extraHeaders} />
          </label>
        </div>
        <div className="field-button-row">
          <label className="check-row">
            <input checked={overwrite} disabled={busy} onChange={(event) => setOverwrite(event.currentTarget.checked)} type="checkbox" />
            覆盖同名文件
          </label>
          <label className="check-row">
            <input checked={outputSubdirByFilename} disabled={busy} onChange={(event) => setOutputSubdirByFilename(event.currentTarget.checked)} type="checkbox" />
            按文件名建文件夹
          </label>
        </div>
      </details>

      <ActionBar
        hint="先校验，再下载。"
        secondary={<button className="ghost-button" disabled={busy || (!requests.length && !tasks.length && !error && !runtimeLogs.length)} onClick={() => void clearResults()} type="button">清空</button>}
        tertiary={<button className="ghost-button" disabled={!canInspect} onClick={handleParseValidate} type="button">校验</button>}
        primary={<button className="primary-button" disabled={!canBuild} onClick={handleDownload} type="button">{busy ? "运行中" : "下载"}</button>}
      />

      {overview.total > 0 ? (
        <section className="table-panel">
          <div className="panel-title">进度总览</div>
          <div className="result-list">
            <div className="result-row"><span>总任务数</span><strong>{overview.total}</strong></div>
            <div className="result-row"><span>当前任务</span><strong>{overview.current || "-"}</strong></div>
            <div className="result-row"><span>完成数</span><strong>{overview.completed}</strong></div>
            <div className="result-row"><span>失败数</span><strong>{overview.failed}</strong></div>
            <div className="result-row"><span>总进度</span><strong>{overview.summary}</strong></div>
          </div>
        </section>
      ) : null}

      <DownloadQueueTable
        active={runtime.active}
        onCancel={() => void runtime.control("cancel")}
        onPause={() => void runtime.control("pause")}
        onResume={() => void runtime.control("resume")}
        paused={runtime.paused}
        rows={queueRows}
      />

      <RuntimeLogPanel error={error || runtime.sessionError} logs={runtimeLogs} />
    </div>
  );
}

export default DirectDownloaderTool;
