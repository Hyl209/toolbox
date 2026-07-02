import { useEffect, useMemo, useRef, useState } from "react";
import { pickDirectory, pickFiles, runTool, type ToolInput, type ToolResult, type ToolSessionSnapshot, type ToolSettings } from "../api/tauri";
import { DownloadQueueTable, type DownloadQueueRow } from "../features/tools/components/DownloadQueueTable";
import { queueOverviewFromSession, queueRowsFromSession as buildQueueRows } from "../features/tools/downloadQueueState";
import { useDownloadRuntimeSession } from "../features/tools/hooks/useDownloadRuntimeSession";
import { uiText } from "../uiText";

type WebTask = {
  source_url: string;
  source_kind: string;
  target_title?: string;
  output_subdir?: string;
  source_page_url?: string;
  candidate_index?: number;
  candidate_total?: number;
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

type InspectCandidateRow = {
  page_url: string;
  candidate_url: string;
  index: number;
  total: number;
  source?: string;
  success: boolean;
  error?: string;
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

function inspectCandidateUrls(results: InspectResult[]): string[] {
  const seen = new Set();
  const urls: string[] = [];
  for (const result of results) {
    for (const raw of result.candidates ?? []) {
      const url = `${raw ?? ""}`.trim();
      if (!url || seen.has(url)) {
        continue;
      }
      seen.add(url);
      urls.push(url);
    }
  }
  return urls;
}

function inspectCandidateRows(results: InspectResult[]): InspectCandidateRow[] {
  const rows: InspectCandidateRow[] = [];
  for (const result of results) {
    const candidates = inspectCandidateUrls([result]);
    if (!result.success) {
      rows.push({
        page_url: result.source_url,
        candidate_url: "",
        index: 0,
        total: 0,
        source: result.source,
        success: false,
        error: result.error || "failed",
      });
      continue;
    }
    candidates.forEach((url, index) => {
      rows.push({
        page_url: result.source_url,
        candidate_url: url,
        index: index + 1,
        total: candidates.length,
        source: result.source,
        success: true,
      });
    });
  }
  return rows;
}

function sourceTitleFromUrl(url: string): string {
  let value = "";
  try {
    const parsed = new URL(url);
    const parts = parsed.pathname.split("/").filter(Boolean);
    value = decodeURIComponent(parts[parts.length - 1] || parsed.hostname || "video");
  } catch {
    value = url.split(/[/?#]/).filter(Boolean).pop() || "video";
  }
  value = value.replace(/\.[a-z0-9]{2,8}$/i, "");
  const cleaned = value.replace(/[<>:"/\\|?*\x00-\x1f]+/g, "_").replace(/\s+/g, "_").replace(/^_+|_+$/g, "");
  return cleaned || "video";
}

function numberedTitle(base: string, index: number, total: number): string {
  return total > 1 ? `${base}_${String(index).padStart(3, "0")}` : base;
}

function sanitizeTaskTitle(value: string, fallback = "video"): string {
  const cleaned = `${value ?? ""}`
    .replace(/[<>:"/\\|?*\x00-\x1f]+/g, "_")
    .replace(/\s+/g, "_")
    .replace(/^_+|_+$/g, "");
  return cleaned || fallback;
}

function taskTitleBase(title: string): string {
  const cleaned = sanitizeTaskTitle(title);
  return cleaned.replace(/_\d{3}$/i, "") || cleaned;
}

function taskGroupKey(task: WebTask): string {
  return `${task.source_page_url?.trim() || task.source_url}`;
}

function reindexGroupedTasks(tasks: WebTask[]): WebTask[] {
  const next = tasks.map((task) => ({ ...task }));
  const groups = new Map<string, number[]>();
  next.forEach((task, index) => {
    const key = taskGroupKey(task);
    groups.set(key, [...(groups.get(key) ?? []), index]);
  });
  for (const indices of groups.values()) {
    if (!indices.length) {
      continue;
    }
    const firstTask = next[indices[0]];
    const fallbackTitle = sourceTitleFromUrl(firstTask.source_page_url || firstTask.source_url);
    const base = taskTitleBase(firstTask.target_title || fallbackTitle);
    if (indices.length === 1) {
      next[indices[0]].target_title = base;
      continue;
    }
    indices.forEach((taskIndex, offset) => {
      next[taskIndex].target_title = numberedTitle(base, offset + 1, indices.length);
    });
  }
  return next;
}

function renameGroupedTaskTitles(tasks: WebTask[], index: number, nextTitle: string): WebTask[] {
  const cleaned = sanitizeTaskTitle(nextTitle, "");
  if (!cleaned) {
    return tasks;
  }
  const next = tasks.map((task) => ({ ...task }));
  const current = next[index];
  if (!current) {
    return next;
  }
  const indices = next
    .map((task, taskIndex) => (taskGroupKey(task) === taskGroupKey(current) ? taskIndex : -1))
    .filter((taskIndex) => taskIndex >= 0);
  if (indices.length <= 1) {
    next[index].target_title = cleaned;
    return reindexGroupedTasks(next);
  }
  indices.forEach((taskIndex, offset) => {
    next[taskIndex].target_title = numberedTitle(cleaned, offset + 1, indices.length);
  });
  return next;
}

function removeQueuedTask(tasks: WebTask[], index: number): WebTask[] {
  return reindexGroupedTasks(tasks.filter((_, taskIndex) => taskIndex !== index));
}

function applyTaskOutputSubdirs(tasks: WebTask[], enabled: boolean): WebTask[] {
  return tasks.map((task) => ({
    ...task,
    output_subdir: enabled ? taskTitleBase(task.target_title || sourceTitleFromUrl(task.source_page_url || task.source_url)) : "",
  }));
}

const removeQueuedTaskHelper = removeQueuedTask;

function candidateTasksFromInspectResults(results: InspectResult[]): WebTask[] {
  const seen = new Set();
  const tasks: WebTask[] = [];
  for (const result of results) {
    const candidates = inspectCandidateUrls([result]).filter((url) => {
      if (seen.has(url)) {
        return false;
      }
      seen.add(url);
      return true;
    });
    const base = sourceTitleFromUrl(result.source_url);
    candidates.forEach((source_url, index) => {
      tasks.push({
        source_url,
        source_kind: "web",
        target_title: numberedTitle(base, index + 1, candidates.length),
        source_page_url: result.source_url,
        candidate_index: index + 1,
        candidate_total: candidates.length,
      });
    });
  }
  return tasks;
}

function queueRowsFromSession(tasks: WebTask[], session: ToolSessionSnapshot | null): DownloadQueueRow[] {
  return buildQueueRows(tasks, session, {
    progressKinds: ["file", "web_status", "web_aria2", "web_percent"],
    applyCompletedResult(row, item) {
      const result = item as DownloadResult;
      row.status = result.success ? "success" : "failed";
      row.fileName = result.files?.[0] ? result.files[0].split(/[\\/]/).pop() || row.fileName : row.fileName;
      row.percent = result.success ? 100 : row.percent;
      row.detail = result.success ? uiText.common.fileCount(result.downloaded_count ?? result.files?.length ?? 0) : result.error || uiText.common.failed;
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
  const overview = useMemo(() => queueOverviewFromSession(tasks, runtime.session), [tasks, runtime.session]);
  const inspectCandidateList = useMemo(() => inspectCandidateRows(inspectRows), [inspectRows]);
  const runtimeLogs = runtime.session?.logs?.length ? runtime.session.logs : logs;

  function applyQueuedTasks(nextTasks: WebTask[]) {
    const normalized = applyTaskOutputSubdirs(reindexGroupedTasks(nextTasks), outputSubdirByTitle);
    const nextUrls = normalized.map((task) => task.source_url);
    setTasks(normalized);
    setUrls(nextUrls);
    setUrlText(nextUrls.join("\n"));
  }

  function renameTaskTitle(index: number, nextTitle: string) {
    const renamed = renameGroupedTaskTitles(tasks, index, nextTitle);
    if (renamed !== tasks) {
      applyQueuedTasks(renamed);
    }
  }

  function removeQueuedTask(index: number) {
    applyQueuedTasks(removeQueuedTaskHelper(tasks, index));
  }

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

  useEffect(() => {
    if (!tasks.length) {
      return;
    }
    setTasks((items) => applyTaskOutputSubdirs(items, outputSubdirByTitle));
  }, [outputSubdirByTitle]);

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
      if (checked.valid) {
        await inspectAndApplyCandidates();
      }
    } catch (caught) {
      const message = text(caught);
      setError(message);
      setLogs((items) => [`parse/validate failed: ${message}`, ...items].slice(0, 20));
    } finally {
      setRunning(false);
    }
  }

  async function inspectAndApplyCandidates(): Promise<{ urls: string[]; tasks: WebTask[] }> {
    const data = dataOf(await runTool("webvideodownloader", { task_id: `webvideo-inspect-${Date.now()}`, action: "inspect", payload }));
    const rows = data.results ?? [];
    const candidateTasks = candidateTasksFromInspectResults(rows);
    const candidateUrls = candidateTasks.map((task) => task.source_url);
    setInspectRows(rows);
    if (candidateUrls.length > 0) {
      applyQueuedTasks(candidateTasks);
    }
    setLogs((items) => [...(data.logs ?? [`inspect success=${data.success_count ?? 0}; fail=${data.fail_count ?? 0}`]), ...items].slice(0, 20));
    return { urls: candidateUrls, tasks: candidateTasks };
  }

  async function handleEmbedThumbnail() {
    const selected = await pickFiles({
      title: "选择要补封面的视频",
      filters: [{ name: "Video", extensions: ["mp4", "mkv", "webm", "mov"] }],
    });
    if (!selected?.length) {
      return;
    }
    setRunning(true);
    setError("");
    try {
      const jobs = selected.map((path, index) => {
        const task = tasks[index];
        const sourceUrl = `${task?.source_page_url || task?.source_url || ""}`.trim();
        return {
          path,
          source_url: sourceUrl,
          candidate_index: sourceUrl && task?.source_page_url ? task.candidate_index : undefined,
          thumbnail_mode: sourceUrl ? "web_then_frame" : "frame",
        };
      });
      const result = dataOf(
        await runTool("webvideodownloader", {
          task_id: `webvideo-cover-${Date.now()}`,
          action: "embed_thumbnail",
          payload: {
            jobs,
            options: {
              proxy_url: effectiveProxyUrl(proxyUrl, proxyHost, proxyPort),
            },
          },
        }),
      );
      setLogs((result.logs ?? []).slice(-50));
      setError("");
    } catch (caught) {
      setError(text(caught));
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
      await inspectAndApplyCandidates();
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
    setRunning(true);
    try {
      let downloadPayload: typeof payload & { tasks?: WebTask[] } = payload;
      let candidateTasks = tasks;
      let candidateUrls = candidateTasks.map((task) => task.source_url);
      if (!candidateUrls.length) {
        const inspected = await inspectAndApplyCandidates();
        candidateUrls = inspected.urls;
        candidateTasks = inspected.tasks;
      }
      if (candidateUrls.length) {
        const queuedTasks = applyTaskOutputSubdirs(candidateTasks, outputSubdirByTitle);
        downloadPayload = { ...payload, text: candidateUrls.join("\n") };
        downloadPayload = { ...downloadPayload, tasks: queuedTasks };
      }
      const input: ToolInput = {
        task_id: `webvideo-download-${Date.now()}`,
        action: "download",
        payload: downloadPayload,
      };
      await runtime.start(input);
    } catch (caught) {
      setError(text(caught));
    } finally {
      setRunning(false);
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
            <small>{urls.length ? uiText.common.parsedCount(urls.length) : uiText.common.multiLineHint}</small>
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
            <span>{uiText.web.proxyHost}</span>
            <input disabled={busy} onChange={(event) => { settingsTouchedRef.current = true; setProxyHost(event.currentTarget.value); }} placeholder="127.0.0.1" value={proxyHost} />
          </label>
          <label className="field-block file-path-field">
            <span>{uiText.web.proxyPort}</span>
            <input disabled={busy} onChange={(event) => { settingsTouchedRef.current = true; setProxyPort(event.currentTarget.value); }} placeholder="7890" value={proxyPort} />
          </label>
          <label className="field-block file-path-field">
            <span>{"代理 URL"}</span>
            <input disabled={busy} onChange={(event) => { settingsTouchedRef.current = true; setProxyUrl(event.currentTarget.value); }} placeholder="http://127.0.0.1:7890" value={proxyUrl} />
          </label>
          <label className="field-block file-path-field">
            <span>{uiText.web.concurrent}</span>
            <select disabled={busy} onChange={(event) => { settingsTouchedRef.current = true; setConcurrent(event.currentTarget.value); }} value={concurrent}>
              {["0", "1", "2", "3", "4", "5"].map((value) => (
                <option key={value} value={value}>{value === "0" ? "auto" : value}</option>
              ))}
            </select>
          </label>
          <label className="check-row">
            <input checked={overwrite} disabled={busy} onChange={(event) => { settingsTouchedRef.current = true; setOverwrite(event.currentTarget.checked); }} type="checkbox" />
            {uiText.web.overwrite}
          </label>
          <label className="check-row">
            <input checked={outputSubdirByTitle} disabled={busy} onChange={(event) => { settingsTouchedRef.current = true; setOutputSubdirByTitle(event.currentTarget.checked); }} type="checkbox" />
            {uiText.web.outputSubdirByTitle}
          </label>
          <label className="check-row">
            <input checked={inspectAll} disabled={busy} onChange={(event) => setInspectAll(event.currentTarget.checked)} type="checkbox" />
            {"候选检查时传递 all candidates 选项"}
          </label>
        </div>
      </div>

      {overview.total > 0 ? (
        <section className="table-panel queue-overview-panel">
          <div className="panel-title">{"进度总览"}</div>
          <div className="queue-overview-inline" role="status" aria-label="进度总览">
            <span><small>{"总任务"}</small><strong>{overview.total}</strong></span>
            <span><small>{"当前"}</small><strong>{overview.current || "-"}</strong></span>
            <span><small>{"完成"}</small><strong>{overview.completed}</strong></span>
            <span><small>{"失败"}</small><strong>{overview.failed}</strong></span>
            <span className="queue-overview-summary"><small>{"总进度"}</small><strong>{overview.summary}</strong></span>
          </div>
        </section>
      ) : null}

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
          <button className="ghost-button" disabled={busy} onClick={() => void handleEmbedThumbnail()} type="button">
            {"补封面"}
          </button>
          <button className="primary-button" disabled={!canRun || !outputDir.trim()} onClick={handleDownload} type="button">
            {"下载"}
          </button>

        </div>
      </div>

<DownloadQueueTable
        active={runtime.active}
        className="web-video-queue-table"
        iconActions
        onCancel={() => void runtime.control("cancel")}
        onDelete={removeQueuedTask}
        onPause={() => void runtime.control("pause")}
        onRename={renameTaskTitle}
        onResume={() => void runtime.control("resume")}
        paused={paused}
        rows={queueRows}
      />

      {inspectCandidateList.length ? (
        <section className="table-panel">
          <div className="panel-title">{"媒体候选"}</div>
          <div className="result-list">
            {inspectCandidateList.map((row, index) => (
              <div className="result-row" key={`${row.page_url}-${row.candidate_url}-${index}`}>
                <span>{row.success ? row.candidate_url : row.page_url}</span>
                <strong>{row.success ? `${row.index}/${row.total} (${row.source || "未知来源"})` : row.error || uiText.common.failed}</strong>
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
                <strong>{row.success ? uiText.common.fileCount(row.downloaded_count ?? row.files?.length ?? 0) : row.error || uiText.common.failed}</strong>
              </div>
            ))}
            {downloadedFiles.map((file, index) => (
              <div className="result-row" key={`${file}-${index}`}>
                <span>{file}</span>
                <strong>{uiText.common.saved}</strong>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="log-panel web-video-log-panel" aria-label={uiText.common.runtime}>
        <div className="web-video-log-header">
          <div className="panel-title">{uiText.common.runtime}</div>
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
