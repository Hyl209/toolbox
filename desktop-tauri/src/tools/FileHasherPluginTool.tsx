import { useMemo, useState } from "react";
import { pickFile, runTool } from "../api/tauri";
import { uiText } from "../uiText";

type FileHasherAction = "calculate" | "verify";
type HashAlgorithm = "md5" | "sha1" | "sha256";

const algorithms: HashAlgorithm[] = ["md5", "sha1", "sha256"];

const actionLabels: Record<FileHasherAction, string> = {
  calculate: "\u8ba1\u7b97",
  verify: "\u6821\u9a8c",
};

const text = {
  title: "\u6587\u4ef6\u54c8\u5e0c\u6821\u9a8c",
  desc: "计算并校验。",
  path: "\u6587\u4ef6\u8def\u5f84",
  browse: "\u6d4f\u89c8",
  pickTitle: "\u9009\u62e9\u6587\u4ef6",
  algorithms: "\u8ba1\u7b97\u7b97\u6cd5",
  verifyAlgorithm: "\u6821\u9a8c\u7b97\u6cd5",
  expected: "\u671f\u671b\u6821\u9a8c\u503c",
  expectedHint: "\u7c98\u8d34 MD5 / SHA1 / SHA256",
  output: "\u8f93\u51fa",
  outputHint: "\u8fd0\u884c\u540e\u5728\u8fd9\u91cc\u663e\u793a\u7ed3\u679c",
  current: "\u5f53\u524d\u52a8\u4f5c",
  clear: "\u6e05\u7a7a",
  copy: "\u590d\u5236",
  running: "\u8fd0\u884c\u4e2d",
  run: "\u8fd0\u884c",
  start: "\u8fd0\u884c",
  done: "\u8fd0\u884c\u5b8c\u6210",
  failed: "\u8fd0\u884c\u5931\u8d25",
  copied: "\u5df2\u590d\u5236",
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

function FileHasherPluginTool() {
  const [action, setAction] = useState<FileHasherAction>("calculate");
  const [path, setPath] = useState("");
  const [selectedAlgorithms, setSelectedAlgorithms] = useState<HashAlgorithm[]>(algorithms);
  const [verifyAlgorithm, setVerifyAlgorithm] = useState("auto");
  const [expectedChecksum, setExpectedChecksum] = useState("");
  const [outputText, setOutputText] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const outputStats = useMemo(() => uiText.common.charCount(outputText.length), [outputText.length]);
  const canRun = !running && Boolean(path.trim()) && (action === "calculate" ? selectedAlgorithms.length > 0 : Boolean(expectedChecksum.trim()));

  function toggleAlgorithm(algorithm: HashAlgorithm) {
    setSelectedAlgorithms((items) => (items.includes(algorithm) ? items.filter((item) => item !== algorithm) : [...items, algorithm]));
  }

  async function browseFile() {
    const selected = await pickFile({ title: text.pickTitle });
    if (selected) {
      setPath(selected);
    }
  }

  async function handleRun() {
    if (!canRun) return;
    setRunning(true);
    setError("");
    setLogs((items) => [`${text.start}\uff1a${actionLabels[action]}`, ...items].slice(0, 5));
    try {
      const payload =
        action === "calculate"
          ? { path, algorithms: selectedAlgorithms }
          : { path, expected_checksum: expectedChecksum, algorithm: verifyAlgorithm || "auto" };
      const result = await runTool("plugin:file_hasher", {
        task_id: `plugin-file-hasher-${action}-${Date.now()}`,
        action,
        payload,
      });
      const data = (result.data ?? result) as Record<string, unknown>;
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
    setPath("");
    setExpectedChecksum("");
    setOutputText("");
    setError("");
  }

  return (
    <div className="base64-tool file-hasher-plugin-tool">
      <div className="tool-heading">
        <div>
          <p className="eyebrow">{uiText.common.pluginLabel("file_hasher")}</p>
          <h2>{text.title}</h2>
          <p>{text.desc}</p>
        </div>
        <div className="mode-switch" role="group" aria-label={text.title}>
          {(["calculate", "verify"] as FileHasherAction[]).map((item) => (
            <button className={action === item ? "active" : ""} disabled={running} key={item} onClick={() => setAction(item)} type="button">
              {actionLabels[item]}
            </button>
          ))}
        </div>
      </div>

      <div className="file-mode-card">
        <label className="field-block file-path-field">
          <span>{text.path}</span>
          <div className="path-input-row">
            <input disabled={running} onChange={(event) => setPath(event.currentTarget.value)} value={path} />
            <button className="path-pick-button" disabled={running} onClick={browseFile} type="button">{text.browse}</button>
          </div>
        </label>
        <div className="field-block">
          <span>{text.algorithms}</span>
          <div className="mode-switch" role="group" aria-label={text.algorithms}>
            {algorithms.map((algorithm) => (
              <button className={selectedAlgorithms.includes(algorithm) ? "active" : ""} disabled={running || action !== "calculate"} key={algorithm} onClick={() => toggleAlgorithm(algorithm)} type="button">
                {algorithm.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
        <label className="field-block">
          <span>{text.verifyAlgorithm}</span>
          <select disabled={running || action !== "verify"} onChange={(event) => setVerifyAlgorithm(event.currentTarget.value)} value={verifyAlgorithm}>
            <option value="auto">AUTO</option>
            {algorithms.map((algorithm) => <option key={algorithm} value={algorithm}>{algorithm.toUpperCase()}</option>)}
          </select>
        </label>
        <label className="field-block file-path-field">
          <span>{text.expected}</span>
          <input disabled={running || action !== "verify"} onChange={(event) => setExpectedChecksum(event.currentTarget.value)} placeholder={text.expectedHint} value={expectedChecksum} />
        </label>
      </div>

      <div className="editor-grid">
        <label className="field-block output-field">
          <span>{text.output}<small>{outputStats}</small></span>
          <textarea placeholder={text.outputHint} readOnly value={outputText} />
        </label>
      </div>

      <div className="actions-row">
        <div className="action-hint">{text.current}\uff1a{actionLabels[action]}</div>
        <div className="button-cluster">
          <button className="ghost-button" disabled={running || (!path && !outputText && !expectedChecksum)} onClick={clearAll} type="button">{text.clear}</button>
          <button className="ghost-button" disabled={!outputText} onClick={copyOutput} type="button">{text.copy}</button>
          <button className="primary-button" disabled={!canRun} onClick={handleRun} type="button">{running ? text.running : text.run}</button>
        </div>
      </div>

      <section className="log-panel" aria-label={text.log}>
        <div><div className="panel-title">{uiText.common.runtime}</div><p className="muted">{text.recent}</p></div>
        <div className="log-content">
          {error ? <div className="error-box">{error}</div> : null}
          {logs.length ? <ul>{logs.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul> : <p className="muted">{text.emptyLog}</p>}
        </div>
      </section>
    </div>
  );
}

export default FileHasherPluginTool;
