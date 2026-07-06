import { useEffect, useMemo, useRef, useState } from "react";
import { pickDirectory, runTool, type ToolHistoryItem, type ToolInput, type ToolResult, type ToolSessionSnapshot, type ToolSettings } from "../api/tauri";
import { DownloadQueueTable, type DownloadQueueRow } from "../features/tools/components/DownloadQueueTable";
import { queueOverviewFromSession, queueRowsFromSession as buildQueueRows } from "../features/tools/downloadQueueState";
import { useDownloadRuntimeSession } from "../features/tools/hooks/useDownloadRuntimeSession";
import { uiText } from "../uiText";

type TgTask = {
  source_url: string;
  source_kind: string;
  target_title?: string;
  output_subdir?: string;
};

type TgResult = ToolResult & {
  urls?: string[];
  tasks?: TgTask[];
  url_count?: number;
  task_count?: number;
  valid?: boolean;
  errors?: string[];
  authorized?: boolean;
  sent?: boolean;
  phone_code_hash?: string;
  message?: string;
  results?: Array<Record<string, unknown>>;
  success_count?: number;
  fail_count?: number;
  logs?: string[];
  files?: string[];
  data?: TgResult;
};

function text(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return typeof error === "string" ? error : JSON.stringify(error);
}

function dataOf(result: ToolResult | null | undefined): TgResult {
  const direct = (result ?? {}) as TgResult;
  return (direct.data ?? direct) as TgResult;
}

function historyItemsOf(result: ToolResult | null | undefined): ToolHistoryItem[] {
  const direct = (result ?? {}) as ToolResult;
  return ((direct.data?.items ?? direct.items ?? []) as ToolHistoryItem[]);
}

function historyInputText(item: ToolHistoryItem, key: string): string {
  const value = item.input?.[key];
  return typeof value === "string" ? value : value == null ? "" : String(value);
}

function historyInputOptions(item: ToolHistoryItem): Record<string, unknown> {
  const value = item.input?.options;
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
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

function queueRowsFromSession(tasks: TgTask[], session: ToolSessionSnapshot | null): DownloadQueueRow[] {
  return buildQueueRows(tasks, session, {
    progressKinds: ["file", "tg_media"],
    applyCompletedResult(row, item) {
      const success = Boolean(item.success);
      const files = Array.isArray(item.files) ? item.files.map(String) : [];
      row.status = success ? "success" : "failed";
      row.fileName = files[0] ? files[0].split(/[\\/]/).pop() || row.fileName : row.fileName;
      row.percent = success ? 100 : row.percent;
      row.detail = success ? uiText.common.fileCount(files.length) : String(item.error ?? uiText.common.failed);
    },
  });
}

function TgDownloaderTool({ initialSettings = {} }: { initialSettings?: ToolSettings }) {
  const credentialsTouchedRef = useRef(false);
  const optionsTouchedRef = useRef(false);
  const outputDirTouchedRef = useRef(false);
  const runtime = useDownloadRuntimeSession("tgdownloader");
  const [apiId, setApiId] = useState(initialSettings.api_id ?? "");
  const [apiHash, setApiHash] = useState(initialSettings.api_hash ?? "");
  const [phone, setPhone] = useState(initialSettings.phone ?? "");
  const [sessionFile, setSessionFile] = useState("");
  const [urlText, setUrlText] = useState("");
  const [outputDir, setOutputDir] = useState(initialSettings.output_dir ?? "");
  const [recentLimit, setRecentLimit] = useState(initialSettings.recent_limit ?? "500");
  const [downloadAllMessages, setDownloadAllMessages] = useState(initialSettings.all_messages ?? false);
  const [dateFrom, setDateFrom] = useState(initialSettings.date_from ?? "");
  const [dateTo, setDateTo] = useState(initialSettings.date_to ?? "");
  const [includeVideos, setIncludeVideos] = useState(initialSettings.include_videos ?? true);
  const [includePhotos, setIncludePhotos] = useState(initialSettings.include_photos ?? false);
  const [proxyHost, setProxyHost] = useState(initialSettings.proxy_host ?? "127.0.0.1");
  const [proxyPort, setProxyPort] = useState(initialSettings.proxy_port ?? "");
  const [proxyUrl, setProxyUrl] = useState(initialSettings.proxy_url ?? "");
  const [concurrent, setConcurrent] = useState(initialSettings.concurrent ?? "1");
  const [overwrite, setOverwrite] = useState(initialSettings.overwrite ?? false);
  const [outputSubdirByTitle, setOutputSubdirByTitle] = useState(initialSettings.output_subdir_by_title ?? false);
  const [code, setCode] = useState("");
  const [phoneCodeHash, setPhoneCodeHash] = useState(initialSettings.phone_code_hash ?? "");
  const [password, setPassword] = useState("");
  const [urls, setUrls] = useState<string[]>([]);
  const [tasks, setTasks] = useState<TgTask[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [downloadFiles, setDownloadFiles] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<ToolHistoryItem[]>([]);

  const credentials = useMemo(
    () => ({ api_id: apiId, api_hash: apiHash, phone, phone_code_hash: phoneCodeHash, session_file: sessionFile }),
    [apiHash, apiId, phone, phoneCodeHash, sessionFile],
  );
  const options = useMemo(
    () => ({
      recent_limit: recentLimit,
      download_all_messages: downloadAllMessages,
      date_from: dateFrom,
      date_to: dateTo,
      include_videos: includeVideos,
      include_photos: includePhotos,
      proxy_host: proxyHost,
      proxy_port: proxyPort,
      proxy_url: effectiveProxyUrl(proxyUrl, proxyHost, proxyPort),
      max_concurrent_downloads: Number.parseInt(concurrent || "1", 10) || 1,
      overwrite,
      output_subdir_by_title: outputSubdirByTitle,
    }),
    [concurrent, dateFrom, dateTo, downloadAllMessages, includePhotos, includeVideos, outputSubdirByTitle, overwrite, proxyHost, proxyPort, proxyUrl, recentLimit],
  );
  const payload = useMemo(
    () => ({ text: urlText, output_dir: outputDir, credentials, options }),
    [credentials, options, outputDir, urlText],
  );
  const busy = running || runtime.active;
  const paused = runtime.paused;
  const queueRows = useMemo(() => queueRowsFromSession(tasks, runtime.session), [tasks, runtime.session]);
  const overview = useMemo(() => queueOverviewFromSession(tasks, runtime.session), [tasks, runtime.session]);
  const runtimeLogs = runtime.session?.logs?.length ? runtime.session.logs : logs;

  useEffect(() => {
    if (!credentialsTouchedRef.current) {
      setApiId(initialSettings.api_id ?? "");
      setApiHash(initialSettings.api_hash ?? "");
      setPhone(initialSettings.phone ?? "");
      setPhoneCodeHash(initialSettings.phone_code_hash ?? "");
    }
    if (!outputDirTouchedRef.current) {
      setOutputDir(initialSettings.output_dir ?? "");
    }
    if (!optionsTouchedRef.current) {
      setRecentLimit(initialSettings.recent_limit ?? "500");
      setDownloadAllMessages(initialSettings.all_messages ?? false);
      setDateFrom(initialSettings.date_from ?? "");
      setDateTo(initialSettings.date_to ?? "");
      setIncludeVideos(initialSettings.include_videos ?? true);
      setIncludePhotos(initialSettings.include_photos ?? false);
      setProxyHost(initialSettings.proxy_host ?? "127.0.0.1");
      setProxyPort(initialSettings.proxy_port ?? "");
      setProxyUrl(initialSettings.proxy_url ?? "");
      setConcurrent(initialSettings.concurrent ?? "1");
      setOverwrite(initialSettings.overwrite ?? false);
      setOutputSubdirByTitle(initialSettings.output_subdir_by_title ?? false);
    }
  }, [initialSettings]);

  useEffect(() => {
    void loadHistory();
  }, []);

  useEffect(() => {
    if (!runtime.session) {
      return;
    }
    if (runtime.session.status === "completed") {
      const data = dataOf(runtime.session.result);
      setErrors(data.errors ?? []);
      setDownloadFiles(data.files ?? []);
      setError("");
      void loadHistory();
    } else if (runtime.session.status === "failed") {
      setError(runtime.session.error ?? "download failed");
    } else if (runtime.session.status === "cancelled") {
      setError("");
    }
  }, [runtime.session]);

  async function chooseOutputDir() {
    const path = await pickDirectory({ title: "选择 TG 下载输出目录" });
    if (path) {
      outputDirTouchedRef.current = true;
      setOutputDir(path);
    }
  }

  async function call(action: string, nextPayload: Record<string, unknown> = payload): Promise<TgResult> {
    const result = await runTool("tgdownloader", { task_id: `tg-${action}-${Date.now()}`, action, payload: nextPayload });
    return dataOf(result);
  }

  async function handleDownload() {
    if (!urlText.trim() || !outputDir.trim()) {
      setError("请先填写 TG URL 和输出目录");
      return;
    }
    setError("");
    const input: ToolInput = {
      task_id: `tg-download-${Date.now()}`,
      action: "download",
      payload,
    };
    try {
      await runtime.start(input);
    } catch (caught) {
      setError(text(caught));
    }
  }

  async function handleParseValidate() {
    setRunning(true);
    setError("");
    try {
      const parsed = await call("parse", { text: urlText });
      setUrls(parsed.urls ?? []);
      setTasks(parsed.tasks ?? []);
      const checked = await call("validate");
      setErrors([...(parsed.errors ?? []), ...(checked.errors ?? [])]);
      setLogs((items) => [`parse=${parsed.url_count ?? 0}; validate=${checked.valid ? "ok" : "bad"}`, ...items].slice(0, 20));
    } catch (caught) {
      const message = text(caught);
      setError(message);
      setLogs((items) => [`parse/validate failed: ${message}`, ...items].slice(0, 20));
    } finally {
      setRunning(false);
    }
  }

  async function handleAuth(action: "auth_status" | "send_code" | "complete_login") {
    setRunning(true);
    setError("");
    try {
      const authPayload = action === "complete_login" ? { credentials, code, phone_code_hash: phoneCodeHash, password } : { credentials };
      const data = await call(action, authPayload);
      if (data.phone_code_hash) {
        setPhoneCodeHash(data.phone_code_hash);
      }
      setLogs((items) => [`${action}: ${data.message ?? JSON.stringify(data)}`, ...items].slice(0, 20));
    } catch (caught) {
      const message = text(caught);
      setError(message);
      setLogs((items) => [`${action} failed: ${message}`, ...items].slice(0, 20));
    } finally {
      setRunning(false);
    }
  }

  async function clearResults() {
    await runtime.clear();
    setUrls([]);
    setTasks([]);
    setErrors([]);
    setLogs([]);
    setDownloadFiles([]);
    setError("");
  }

  async function loadHistory() {
    try {
      const result = await runTool("tgdownloader", { task_id: `tg-history-load-${Date.now()}`, action: "load_history", payload: {} });
      setHistory(historyItemsOf(result));
    } catch (caught) {
      setLogs((items) => [`history failed: ${text(caught)}`, ...items].slice(0, 20));
    }
  }

  async function deleteHistoryItem(id: string) {
    const result = await runTool("tgdownloader", { task_id: `tg-history-delete-${Date.now()}`, action: "delete_history", payload: { id } });
    setHistory(historyItemsOf(result));
  }

  async function clearHistory() {
    const result = await runTool("tgdownloader", { task_id: `tg-history-clear-${Date.now()}`, action: "clear_history", payload: {} });
    setHistory(historyItemsOf(result));
  }

  function reuseHistoryItem(item: ToolHistoryItem) {
    const options = historyInputOptions(item);
    const urls = item.input?.urls;
    setUrlText(historyInputText(item, "text") || historyInputText(item, "url") || (Array.isArray(urls) ? urls.map(String).join("\n") : ""));
    setOutputDir(historyInputText(item, "output_dir"));
    setRecentLimit(String(options.recent_limit ?? recentLimit));
    setDownloadAllMessages(Boolean(options.download_all_messages));
    setDateFrom(typeof options.date_from === "string" ? options.date_from : "");
    setDateTo(typeof options.date_to === "string" ? options.date_to : "");
    setIncludeVideos(options.include_videos !== false);
    setIncludePhotos(Boolean(options.include_photos));
    setProxyUrl(typeof options.proxy_url === "string" ? options.proxy_url : "");
    setProxyHost(typeof options.proxy_host === "string" ? options.proxy_host : proxyHost);
    setProxyPort(typeof options.proxy_port === "string" ? options.proxy_port : proxyPort);
    setConcurrent(String(options.max_concurrent_downloads ?? concurrent));
    setOverwrite(Boolean(options.overwrite));
    setOutputSubdirByTitle(Boolean(options.output_subdir_by_title));
  }

  return (
    <div className="base64-tool">
      <div className="tool-heading">
        <div>
          <h2>{"TG下载"}</h2>
        </div>
      </div>

      <div className="editor-grid">
        <label className="field-block">
          <span>API ID</span>
          <input disabled={busy} onChange={(event) => { credentialsTouchedRef.current = true; setApiId(event.currentTarget.value); }} value={apiId} />
        </label>
        <label className="field-block">
          <span>API Hash</span>
          <input disabled={busy} onChange={(event) => { credentialsTouchedRef.current = true; setApiHash(event.currentTarget.value); }} value={apiHash} />
        </label>
        <label className="field-block">
          <span>{"手机号"}</span>
          <input disabled={busy} onChange={(event) => { credentialsTouchedRef.current = true; setPhone(event.currentTarget.value); }} placeholder="+10000000000" value={phone} />
        </label>
        <label className="field-block">
          <span>{uiText.tg.sessionPath}</span>
          <input disabled={busy} onChange={(event) => setSessionFile(event.currentTarget.value)} placeholder="default: telegram.session" value={sessionFile} />
        </label>
      </div>

      <div className="editor-grid">
        <label className="field-block">
          <span>
            {"TG URL / 分享文本"}
            <small>{urls.length ? uiText.common.parsedCount(urls.length) : uiText.common.multiLineHint}</small>
          </span>
          <textarea disabled={busy} onChange={(event) => setUrlText(event.currentTarget.value)} placeholder="https://t.me/example/42" value={urlText} />
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
            <span>{uiText.tg.recentLimit}</span>
            <input disabled={busy || downloadAllMessages} onChange={(event) => { optionsTouchedRef.current = true; setRecentLimit(event.currentTarget.value); }} value={recentLimit} />
          </label>
          <div className="settings-grid">
            <label className="check-row"><input checked={downloadAllMessages} disabled={busy} onChange={(event) => { optionsTouchedRef.current = true; setDownloadAllMessages(event.currentTarget.checked); }} type="checkbox" />{uiText.tg.allMessages}</label>
            <label className="check-row"><input checked={includeVideos} disabled={busy} onChange={(event) => { optionsTouchedRef.current = true; setIncludeVideos(event.currentTarget.checked); }} type="checkbox" />{uiText.tg.includeVideos}</label>
            <label className="check-row"><input checked={includePhotos} disabled={busy} onChange={(event) => { optionsTouchedRef.current = true; setIncludePhotos(event.currentTarget.checked); }} type="checkbox" />{uiText.tg.includePhotos}</label>
          </div>
          <label className="field-block file-path-field"><span>{uiText.tg.dateFrom}</span><input disabled={busy} onChange={(event) => { optionsTouchedRef.current = true; setDateFrom(event.currentTarget.value); }} placeholder="YYYY-MM-DD" value={dateFrom} /></label>
          <label className="field-block file-path-field"><span>{uiText.tg.dateTo}</span><input disabled={busy} onChange={(event) => { optionsTouchedRef.current = true; setDateTo(event.currentTarget.value); }} placeholder="YYYY-MM-DD" value={dateTo} /></label>
          <label className="field-block file-path-field"><span>{uiText.tg.proxyHost}</span><input disabled={busy} onChange={(event) => { optionsTouchedRef.current = true; setProxyHost(event.currentTarget.value); }} value={proxyHost} /></label>
          <label className="field-block file-path-field"><span>{uiText.tg.proxyPort}</span><input disabled={busy} onChange={(event) => { optionsTouchedRef.current = true; setProxyPort(event.currentTarget.value); }} value={proxyPort} /></label>
          <label className="field-block file-path-field"><span>{uiText.tg.proxyUrl}</span><input disabled={busy} onChange={(event) => { optionsTouchedRef.current = true; setProxyUrl(event.currentTarget.value); }} value={proxyUrl} /></label>
          <label className="field-block file-path-field"><span>{uiText.tg.concurrent}</span><select disabled={busy} onChange={(event) => { optionsTouchedRef.current = true; setConcurrent(event.currentTarget.value); }} value={concurrent}>{["0", "1", "2", "3", "4", "5"].map((value) => <option key={value} value={value}>{value === "0" ? "自动" : value}</option>)}</select></label>
          <label className="check-row"><input checked={overwrite} disabled={busy} onChange={(event) => { optionsTouchedRef.current = true; setOverwrite(event.currentTarget.checked); }} type="checkbox" />{uiText.tg.overwrite}</label>
          <label className="check-row"><input checked={outputSubdirByTitle} disabled={busy} onChange={(event) => { optionsTouchedRef.current = true; setOutputSubdirByTitle(event.currentTarget.checked); }} type="checkbox" />{uiText.tg.outputSubdirByTitle}</label>
        </div>
      </div>

      <div className="settings-card">
        <span>{"登录授权"}</span>
        <div className="editor-grid file-editor-grid">
          <label className="field-block"><span>{"验证码"}</span><input disabled={busy} onChange={(event) => setCode(event.currentTarget.value)} value={code} /></label>
          <label className="field-block"><span>{uiText.tg.phoneCodeHash}</span><input disabled={busy} onChange={(event) => { credentialsTouchedRef.current = true; setPhoneCodeHash(event.currentTarget.value); }} value={phoneCodeHash} /></label>
          <label className="field-block"><span>{uiText.tg.twoFactorPassword}</span><input disabled={busy} onChange={(event) => setPassword(event.currentTarget.value)} type="password" value={password} /></label>
        </div>
      </div>

      <div className="actions-row">
        <div className="button-cluster">
          <button className="ghost-button" disabled={busy || !urlText.trim()} onClick={handleParseValidate} type="button">{"校验"}</button>
          <button className="ghost-button" disabled={busy} onClick={() => void handleAuth("auth_status")} type="button">{"授权"}</button>
          <button className="ghost-button" disabled={busy} onClick={() => void handleAuth("send_code")} type="button">{"发码"}</button>
          <button className="primary-button" disabled={busy} onClick={() => void handleAuth("complete_login")} type="button">{"登录"}</button>
          <button className="primary-button" disabled={busy || !urlText.trim() || !outputDir.trim()} onClick={handleDownload} type="button">{"下载"}</button>

          <button className="ghost-button" disabled={busy || (!urls.length && !errors.length && !runtimeLogs.length && !downloadFiles.length)} onClick={() => void clearResults()} type="button">{"清空"}</button>
        </div>
      </div>

      {overview.total > 0 ? (
        <section className="table-panel">
          <div className="panel-title">{"进度总览"}</div>
          <div className="result-list">
            <div className="result-row"><span>{"总任务数"}</span><strong>{overview.total}</strong></div>
            <div className="result-row"><span>{"当前任务"}</span><strong>{overview.current || "-"}</strong></div>
            <div className="result-row"><span>{"完成数"}</span><strong>{overview.completed}</strong></div>
            <div className="result-row"><span>{"失败数"}</span><strong>{overview.failed}</strong></div>
            <div className="result-row"><span>{"总进度"}</span><strong>{overview.summary}</strong></div>
          </div>
        </section>
      ) : null}

<DownloadQueueTable
        active={runtime.active}
        onCancel={() => void runtime.control("cancel")}
        onPause={() => void runtime.control("pause")}
        onReconnect={() => void runtime.control("reconnect")}
        onResume={() => void runtime.control("resume")}
        paused={paused}
        rows={queueRows}
      />

      <section className="log-panel" aria-label={uiText.tg.downloadedFiles}>
        <div><div className="panel-title">{uiText.tg.downloadedFiles}</div><p className="muted">{"已保存文件"}</p></div>
        <div className="log-content">
          {downloadFiles.length ? <ul>{downloadFiles.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="muted">{"暂无下载文件"}</p>}
        </div>
      </section>

      <section className="table-panel">
        <div className="web-video-log-header">
          <div className="panel-title">历史记录</div>
          <button className="ghost-button" disabled={!history.length || busy} onClick={() => void clearHistory()} type="button">清空历史</button>
        </div>
        <div className="result-list">
          {history.length ? history.map((item) => {
            const urls = item.input?.urls;
            const title = historyInputText(item, "text") || historyInputText(item, "url") || (Array.isArray(urls) ? urls.map(String).join("\n") : item.files?.[0] || item.id);
            return (
              <div className="result-row" key={item.id}>
                <span>{title}</span>
                <strong>{item.status === "success" ? `成功 ${item.success_count ?? 0}` : `失败 ${item.fail_count ?? 0}`}</strong>
                <button className="ghost-button" disabled={busy} onClick={() => reuseHistoryItem(item)} type="button">复用</button>
                <button className="ghost-button" disabled={busy} onClick={() => void deleteHistoryItem(item.id)} type="button">删除</button>
              </div>
            );
          }) : <p className="muted">暂无历史记录</p>}
        </div>
      </section>

      <section className="log-panel" aria-label={uiText.common.runtime}>
        <div><div className="panel-title">{uiText.common.runtime}</div><p className="muted">{uiText.tg.recentRuntime}</p></div>
        <div className="log-content">
          {error ? <div className="error-box">{error}</div> : null}
          {runtimeLogs.length ? <ul>{runtimeLogs.slice(-50).map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul> : <p className="muted">{uiText.common.noLogs}</p>}
        </div>
      </section>
    </div>
  );
}

export default TgDownloaderTool;
