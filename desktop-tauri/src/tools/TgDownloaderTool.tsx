import { useEffect, useMemo, useRef, useState } from "react";
import { pickDirectory, runTool, type ToolResult, type ToolSettings } from "../api/tauri";

type BackendStatus = {
  available?: boolean;
  label?: string;
  message?: string;
  path?: string;
};

type TgTask = {
  source_url: string;
  source_kind: string;
  target_title?: string;
  output_subdir?: string;
};

type TgResult = ToolResult & {
  backends?: Record<string, BackendStatus>;
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

function dataOf(result: ToolResult): TgResult {
  const direct = result as TgResult;
  return (direct.data ?? direct) as TgResult;
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

function TgDownloaderTool({ initialSettings = {} }: { initialSettings?: ToolSettings }) {
  const credentialsTouchedRef = useRef(false);
  const optionsTouchedRef = useRef(false);
  const outputDirTouchedRef = useRef(false);
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
  const [backends, setBackends] = useState<Record<string, BackendStatus>>({});
  const [urls, setUrls] = useState<string[]>([]);
  const [tasks, setTasks] = useState<TgTask[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [downloadFiles, setDownloadFiles] = useState<string[]>([]);
  const [downloadStats, setDownloadStats] = useState({ success: 0, fail: 0 });
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

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
  const telethonReady = Boolean(backends.telethon?.available);

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
    let cancelled = false;
    runTool("tgdownloader", { task_id: `tg-probe-${Date.now()}`, action: "probe", payload: {} })
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
    const path = await pickDirectory({ title: "\u9009\u62e9 TG \u4e0b\u8f7d\u8f93\u51fa\u76ee\u5f55" });
    if (path) {
      outputDirTouchedRef.current = true;
      setOutputDir(path);
    }
  }

  async function call(action: string, nextPayload: Record<string, unknown> = payload): Promise<TgResult> {
    const result = await runTool("tgdownloader", { task_id: `tg-${action}-${Date.now()}`, action, payload: nextPayload });
    return dataOf(result);
  }

  async function handleProbe() {
    setRunning(true);
    setError("");
    try {
      const data = await call("probe", {});
      setBackends(data.backends ?? {});
      setLogs((items) => ["probe ok", ...items].slice(0, 8));
    } catch (caught) {
      const message = text(caught);
      setError(message);
      setLogs((items) => [`probe failed: ${message}`, ...items].slice(0, 8));
    } finally {
      setRunning(false);
    }
  }

  async function handleDownload() {
    if (!urlText.trim() || !outputDir.trim()) {
      setError("\u8bf7\u5148\u586b\u5199 TG URL \u548c\u8f93\u51fa\u76ee\u5f55");
      return;
    }
    setRunning(true);
    setError("");
    try {
      const data = await call("download");
      setErrors(data.errors ?? []);
      setDownloadFiles(data.files ?? []);
      setDownloadStats({ success: data.success_count ?? 0, fail: data.fail_count ?? 0 });
      setLogs((items) =>
        [
          `download: ok=${data.success_count ?? 0}; fail=${data.fail_count ?? 0}`,
          ...(data.logs ?? []),
          ...items,
        ].slice(0, 50),
      );
    } catch (caught) {
      const message = text(caught);
      setError(message);
      setLogs((items) => [`download failed: ${message}`, ...items].slice(0, 50));
    } finally {
      setRunning(false);
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
      setLogs((items) => [`parse=${parsed.url_count ?? 0}; validate=${checked.valid ? "ok" : "bad"}`, ...items].slice(0, 8));
    } catch (caught) {
      const message = text(caught);
      setError(message);
      setLogs((items) => [`parse/validate failed: ${message}`, ...items].slice(0, 8));
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
      setLogs((items) => [`${action}: ${data.message ?? JSON.stringify(data)}`, ...items].slice(0, 8));
    } catch (caught) {
      const message = text(caught);
      setError(message);
      setLogs((items) => [`${action} failed: ${message}`, ...items].slice(0, 8));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="base64-tool">
      <div className="tool-heading">
        <div>
          <p className="eyebrow">Legacy Telegram downloader</p>
          <h2>{"\u0054\u0047\u4e0b\u8f7d"}</h2>
          <p>{"\u5df2\u63a5\u5165\uff1a\u73af\u5883\u63a2\u6d4b\u3001\u94fe\u63a5\u89e3\u6790\u3001\u8bf7\u6c42\u6821\u9a8c\u3001\u767b\u5f55\u6388\u6743\u3001\u4e0b\u8f7d\u6267\u884c\u3002"}</p>
        </div>
        <span className={`settings-mode-pill ${telethonReady ? "ready-pill" : ""}`}>{telethonReady ? "telethon ready" : "probe/login only"}</span>
      </div>

      <div className="info-box">
        {"\u4e0b\u8f7d\u6267\u884c\u5df2\u63a5\u5165\uff1b\u961f\u5217 / \u6682\u505c\u6062\u590d\u6682\u672a\u63a5\u5165\u3002\u672c\u9875\u53ea\u6536\u96c6\u8f93\u5165\u5e76\u8c03\u7528 sidecar\u3002"}
      </div>

      <div className="editor-grid">
        <label className="field-block">
          <span>API ID</span>
          <input disabled={running} onChange={(event) => { credentialsTouchedRef.current = true; setApiId(event.currentTarget.value); }} value={apiId} />
        </label>
        <label className="field-block">
          <span>API Hash</span>
          <input disabled={running} onChange={(event) => { credentialsTouchedRef.current = true; setApiHash(event.currentTarget.value); }} value={apiHash} />
        </label>
        <label className="field-block">
          <span>{"\u624b\u673a\u53f7"}</span>
          <input disabled={running} onChange={(event) => { credentialsTouchedRef.current = true; setPhone(event.currentTarget.value); }} placeholder="+10000000000" value={phone} />
        </label>
        <label className="field-block">
          <span>Session path</span>
          <input disabled={running} onChange={(event) => setSessionFile(event.currentTarget.value)} placeholder="default: telegram.session" value={sessionFile} />
        </label>
      </div>

      <div className="editor-grid">
        <label className="field-block">
          <span>
            {"TG URL / \u5206\u4eab\u6587\u672c"}
            <small>{urls.length ? `${urls.length} parsed` : "multi-line"}</small>
          </span>
          <textarea disabled={running} onChange={(event) => setUrlText(event.currentTarget.value)} placeholder="https://t.me/example/42" value={urlText} />
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
            <span>recent_limit</span>
            <input disabled={running} onChange={(event) => { optionsTouchedRef.current = true; setRecentLimit(event.currentTarget.value); }} value={recentLimit} />
          </label>
          <div className="settings-grid">
            <label className="check-row"><input checked={downloadAllMessages} disabled={running} onChange={(event) => { optionsTouchedRef.current = true; setDownloadAllMessages(event.currentTarget.checked); }} type="checkbox" />all messages</label>
            <label className="check-row"><input checked={includeVideos} disabled={running} onChange={(event) => { optionsTouchedRef.current = true; setIncludeVideos(event.currentTarget.checked); }} type="checkbox" />include videos</label>
            <label className="check-row"><input checked={includePhotos} disabled={running} onChange={(event) => { optionsTouchedRef.current = true; setIncludePhotos(event.currentTarget.checked); }} type="checkbox" />include photos</label>
          </div>
          <label className="field-block file-path-field"><span>date_from</span><input disabled={running} onChange={(event) => { optionsTouchedRef.current = true; setDateFrom(event.currentTarget.value); }} placeholder="YYYY-MM-DD" value={dateFrom} /></label>
          <label className="field-block file-path-field"><span>date_to</span><input disabled={running} onChange={(event) => { optionsTouchedRef.current = true; setDateTo(event.currentTarget.value); }} placeholder="YYYY-MM-DD" value={dateTo} /></label>
          <label className="field-block file-path-field"><span>proxy_host</span><input disabled={running} onChange={(event) => { optionsTouchedRef.current = true; setProxyHost(event.currentTarget.value); }} value={proxyHost} /></label>
          <label className="field-block file-path-field"><span>proxy_port</span><input disabled={running} onChange={(event) => { optionsTouchedRef.current = true; setProxyPort(event.currentTarget.value); }} value={proxyPort} /></label>
          <label className="field-block file-path-field"><span>proxy_url</span><input disabled={running} onChange={(event) => { optionsTouchedRef.current = true; setProxyUrl(event.currentTarget.value); }} value={proxyUrl} /></label>
          <label className="field-block file-path-field"><span>concurrent</span><select disabled={running} onChange={(event) => { optionsTouchedRef.current = true; setConcurrent(event.currentTarget.value); }} value={concurrent}>{["0", "1", "2", "3", "4", "5"].map((value) => <option key={value} value={value}>{value === "0" ? "auto" : value}</option>)}</select></label>
          <label className="check-row"><input checked={overwrite} disabled={running} onChange={(event) => { optionsTouchedRef.current = true; setOverwrite(event.currentTarget.checked); }} type="checkbox" />overwrite</label>
          <label className="check-row"><input checked={outputSubdirByTitle} disabled={running} onChange={(event) => { optionsTouchedRef.current = true; setOutputSubdirByTitle(event.currentTarget.checked); }} type="checkbox" />output subdir by title</label>
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

      <div className="settings-card">
        <span>{"\u767b\u5f55\u6388\u6743"}</span>
        <div className="editor-grid file-editor-grid">
          <label className="field-block"><span>{"\u9a8c\u8bc1\u7801"}</span><input disabled={running} onChange={(event) => setCode(event.currentTarget.value)} value={code} /></label>
          <label className="field-block"><span>phone_code_hash</span><input disabled={running} onChange={(event) => { credentialsTouchedRef.current = true; setPhoneCodeHash(event.currentTarget.value); }} value={phoneCodeHash} /></label>
          <label className="field-block"><span>2FA password</span><input disabled={running} onChange={(event) => setPassword(event.currentTarget.value)} type="password" value={password} /></label>
        </div>
      </div>

      <div className="actions-row">
        <div className="action-hint">{"React \u4e0d\u590d\u5236\u65e7 tab.py \u524d\u7aef\uff0c\u53ea\u8c03\u7528 sidecar action\u3002"}</div>
        <div className="button-cluster">
          <button className="ghost-button" disabled={running} onClick={handleProbe} type="button">{"\u63a2\u6d4b"}</button>
          <button className="ghost-button" disabled={running || !urlText.trim()} onClick={handleParseValidate} type="button">{"\u89e3\u6790 / \u6821\u9a8c"}</button>
          <button className="ghost-button" disabled={running} onClick={() => handleAuth("auth_status")} type="button">{"\u68c0\u67e5\u6388\u6743"}</button>
          <button className="ghost-button" disabled={running} onClick={() => handleAuth("send_code")} type="button">{"\u53d1\u9001\u9a8c\u8bc1\u7801"}</button>
          <button className="primary-button" disabled={running} onClick={() => handleAuth("complete_login")} type="button">{"\u5b8c\u6210\u767b\u5f55"}</button>
          <button className="primary-button" disabled={running || !urlText.trim() || !outputDir.trim()} onClick={handleDownload} type="button">{"\u5f00\u59cb\u4e0b\u8f7d"}</button>
        </div>
      </div>

      <div className="editor-grid file-editor-grid">
        <div className="result-card"><span>{"\u89e3\u6790\u7ed3\u679c"}</span><strong>{tasks.length ? `${tasks.length} tasks` : "waiting"}</strong><p>{tasks[0]?.source_kind || urls[0] || "-"}</p></div>
        <div className="result-card"><span>{"\u6821\u9a8c\u7ed3\u679c"}</span><strong>{errors.length ? `${errors.length} issues` : "no issues"}</strong><p>{errors[0] || "-"}</p></div>
        <div className="result-card"><span>{"\u4e0b\u8f7d\u7ed3\u679c"}</span><strong>{`${downloadStats.success} ok / ${downloadStats.fail} fail`}</strong><p>{downloadFiles[0] || "-"}</p></div>
      </div>

      <section className="log-panel" aria-label="Files">
        <div><div className="panel-title">Files</div><p className="muted">{"\u5df2\u4fdd\u5b58\u6587\u4ef6"}</p></div>
        <div className="log-content">
          {downloadFiles.length ? <ul>{downloadFiles.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="muted">{"\u6682\u65e0\u4e0b\u8f7d\u6587\u4ef6"}</p>}
        </div>
      </section>

      <section className="log-panel" aria-label="Runtime">
        <div><div className="panel-title">Runtime</div><p className="muted">{"\u6700\u8fd1\u7684 TG sidecar \u8c03\u7528\u8bb0\u5f55"}</p></div>
        <div className="log-content">
          {error ? <div className="error-box">{error}</div> : null}
          {logs.length ? <ul>{logs.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul> : <p className="muted">{"\u6682\u65e0\u65e5\u5fd7"}</p>}
        </div>
      </section>
    </div>
  );
}

export default TgDownloaderTool;
