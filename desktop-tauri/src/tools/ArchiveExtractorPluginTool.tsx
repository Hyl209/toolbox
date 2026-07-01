import { useEffect, useMemo, useRef, useState } from "react";
import { pickDirectory, pickFile, runTool, type ToolSettings } from "../api/tauri";

type ArchiveAction = "detect" | "extract";

type ArchiveResult = {
  archive_path?: string;
  output_dir?: string;
  archive_type?: string;
  supported?: boolean;
  extracted_count?: number;
  files?: string[];
};

const actionLabels: Record<ArchiveAction, string> = {
  detect: "\u8bc6\u522b\u538b\u7f29\u5305",
  extract: "\u89e3\u538b\u6587\u4ef6",
};

const text = {
  title: "\u538b\u7f29\u5305\u89e3\u538b",
  desc: "\u590d\u7528\u65e7\u63d2\u4ef6 converter.py \u7684 zip\u3001tar\u30017z \u8bc6\u522b\u548c\u89e3\u538b\u80fd\u529b\uff1bReact \u53ea\u505a\u8f93\u5165\u3001\u72b6\u6001\u548c\u7ed3\u679c\u5c55\u793a\u3002",
  archivePath: "\u538b\u7f29\u5305\u8def\u5f84",
  outputDir: "\u8f93\u51fa\u76ee\u5f55",
  password: "\u5bc6\u7801\uff08\u53ef\u9009\uff09",
  browse: "\u6d4f\u89c8",
  pickArchive: "\u9009\u62e9\u538b\u7f29\u5305",
  pickOutput: "\u9009\u62e9\u89e3\u538b\u8f93\u51fa\u76ee\u5f55",
  current: "\u5f53\u524d\u52a8\u4f5c",
  run: "\u5f00\u59cb\u8fd0\u884c",
  running: "\u8fd0\u884c\u4e2d...",
  start: "\u5f00\u59cb\u8fd0\u884c",
  done: "\u8fd0\u884c\u5b8c\u6210",
  failed: "\u8fd0\u884c\u5931\u8d25",
  clear: "\u6e05\u7a7a",
  copy: "\u590d\u5236\u8f93\u51fa",
  copied: "\u5df2\u590d\u5236\u8f93\u51fa",
  archiveType: "\u538b\u7f29\u5305\u7c7b\u578b",
  supported: "\u652f\u6301\u72b6\u6001",
  supportedYes: "\u5df2\u652f\u6301",
  supportedNo: "\u672a\u8bc6\u522b",
  extractedCount: "\u89e3\u538b\u6761\u76ee",
  files: "\u6587\u4ef6\u5217\u8868",
  outputHint: "\u8fd0\u884c\u540e\u663e\u793a\u8bc6\u522b\u6216\u89e3\u538b\u7ed3\u679c",
  emptyFiles: "\u6682\u65e0\u6587\u4ef6",
  log: "\u8fd0\u884c\u65e5\u5fd7",
  recent: "\u6700\u8fd1 5 \u6761\u672c\u5730\u6267\u884c\u8bb0\u5f55",
  emptyLog: "\u6682\u65e0\u65e5\u5fd7",
};

function errorText(error: unknown): string {
  if (error instanceof Error) return error.message;
  return typeof error === "string" ? error : JSON.stringify(error);
}

function stringifyData(data: Record<string, unknown>): string {
  return JSON.stringify(data, null, 2);
}

function normalizeFiles(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function ArchiveExtractorPluginTool({ initialSettings = {} }: { initialSettings?: ToolSettings }) {
  const didApplyInitial = useRef(false);
  const outputDirTouchedRef = useRef(false);
  const [action, setAction] = useState<ArchiveAction>("detect");
  const [archivePath, setArchivePath] = useState("");
  const [outputDir, setOutputDir] = useState(initialSettings.output_dir ?? "");
  const [password, setPassword] = useState("");
  const [result, setResult] = useState<ArchiveResult | null>(null);
  const [outputText, setOutputText] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const filesText = useMemo(() => (result?.files?.length ? result.files.join("\n") : ""), [result]);
  const outputStats = useMemo(() => `${outputText.length} chars`, [outputText.length]);
  const canRun = !running && Boolean(archivePath.trim()) && (action === "detect" || Boolean(outputDir.trim()));

  useEffect(() => {
    if (didApplyInitial.current || outputDirTouchedRef.current || !initialSettings.output_dir) {
      return;
    }
    setOutputDir((current) => current || initialSettings.output_dir || "");
    didApplyInitial.current = true;
  }, [initialSettings]);

  async function browseArchive() {
    const selected = await pickFile({
      title: text.pickArchive,
      filters: [{ name: "Archive", extensions: ["zip", "tar", "gz", "tgz", "7z", "rar"] }],
    });
    if (selected) {
      setArchivePath(selected);
    }
  }

  async function browseOutputDir() {
    const selected = await pickDirectory({ title: text.pickOutput });
    if (selected) {
      outputDirTouchedRef.current = true;
      setOutputDir(selected);
    }
  }

  async function handleRun() {
    if (!canRun) return;
    setRunning(true);
    setError("");
    setLogs((items) => [`${text.start}\uff1a${actionLabels[action]}`, ...items].slice(0, 5));
    try {
      const payload =
        action === "detect"
          ? { archive_path: archivePath }
          : { archive_path: archivePath, output_dir: outputDir, password };
      const response = await runTool("plugin:archive_extractor", {
        task_id: `plugin-archive-extractor-${action}-${Date.now()}`,
        action,
        payload,
      });
      const data = (response.data ?? response) as Record<string, unknown>;
      const next: ArchiveResult = {
        archive_path: typeof data.archive_path === "string" ? data.archive_path : "",
        output_dir: typeof data.output_dir === "string" ? data.output_dir : "",
        archive_type: typeof data.archive_type === "string" ? data.archive_type : "",
        supported: typeof data.supported === "boolean" ? data.supported : undefined,
        extracted_count: typeof data.extracted_count === "number" ? data.extracted_count : undefined,
        files: normalizeFiles(data.files),
      };
      setResult(next);
      setOutputText(stringifyData(data));
      setLogs((items) => [text.done, ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`${text.failed}\uff1a${message}`, ...items].slice(0, 5));
    } finally {
      setRunning(false);
    }
  }

  async function copyOutput() {
    if (!outputText) return;
    await navigator.clipboard.writeText(outputText);
    setLogs((items) => [text.copied, ...items].slice(0, 5));
  }

  function clearAll() {
    setArchivePath("");
    outputDirTouchedRef.current = true;
    setOutputDir("");
    setPassword("");
    setResult(null);
    setOutputText("");
    setError("");
  }

  return (
    <div className="base64-tool archive-extractor-plugin-tool">
      <div className="tool-heading">
        <div>
          <p className="eyebrow">Plugin - archive_extractor</p>
          <h2>{text.title}</h2>
          <p>{text.desc}</p>
        </div>
        <div className="mode-switch" role="group" aria-label={text.title}>
          {(["detect", "extract"] as ArchiveAction[]).map((item) => (
            <button className={action === item ? "active" : ""} disabled={running} key={item} onClick={() => setAction(item)} type="button">
              {actionLabels[item]}
            </button>
          ))}
        </div>
      </div>

      <div className="file-mode-card">
        <label className="field-block file-path-field">
          <span>{text.archivePath}</span>
          <div className="path-input-row">
            <input disabled={running} onChange={(event) => setArchivePath(event.currentTarget.value)} value={archivePath} />
            <button className="path-pick-button" disabled={running} onClick={browseArchive} type="button">{text.browse}</button>
          </div>
        </label>
        <label className="field-block file-path-field">
          <span>{text.outputDir}</span>
          <div className="path-input-row">
            <input
              disabled={running || action !== "extract"}
              onChange={(event) => {
                outputDirTouchedRef.current = true;
                setOutputDir(event.currentTarget.value);
              }}
              value={outputDir}
            />
            <button className="path-pick-button" disabled={running || action !== "extract"} onClick={browseOutputDir} type="button">{text.browse}</button>
          </div>
        </label>
        <label className="field-block file-path-field">
          <span>{text.password}</span>
          <input disabled={running || action !== "extract"} onChange={(event) => setPassword(event.currentTarget.value)} type="password" value={password} />
        </label>
      </div>

      <div className="settings-grid">
        <section className="settings-card">
          <span>{text.archiveType}</span>
          <strong>{result?.archive_type || "-"}</strong>
          <p>{result?.archive_path || text.outputHint}</p>
        </section>
        <section className="settings-card">
          <span>{text.supported}</span>
          <strong>{result?.supported === false ? text.supportedNo : result?.archive_type ? text.supportedYes : "-"}</strong>
          <p>{result?.output_dir || outputDir || "-"}</p>
        </section>
        <section className="settings-card">
          <span>{text.extractedCount}</span>
          <strong>{result?.extracted_count ?? "-"}</strong>
          <p>{result?.files?.length ? `${result.files.length} files` : text.emptyFiles}</p>
        </section>
      </div>

      <div className="editor-grid">
        <label className="field-block output-field">
          <span>{text.files}<small>{outputStats}</small></span>
          <textarea placeholder={text.outputHint} readOnly value={filesText || outputText} />
        </label>
      </div>

      <div className="actions-row">
        <div className="action-hint">{text.current}\uff1a{actionLabels[action]}</div>
        <div className="button-cluster">
          <button className="ghost-button" disabled={running || (!archivePath && !outputDir && !outputText)} onClick={clearAll} type="button">{text.clear}</button>
          <button className="ghost-button" disabled={!outputText} onClick={copyOutput} type="button">{text.copy}</button>
          <button className="primary-button" disabled={!canRun} onClick={handleRun} type="button">{running ? text.running : text.run}</button>
        </div>
      </div>

      <section className="log-panel" aria-label={text.log}>
        <div><div className="panel-title">Runtime</div><p className="muted">{text.recent}</p></div>
        <div className="log-content">
          {error ? <div className="error-box">{error}</div> : null}
          {logs.length ? <ul>{logs.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul> : <p className="muted">{text.emptyLog}</p>}
        </div>
      </section>
    </div>
  );
}

export default ArchiveExtractorPluginTool;
