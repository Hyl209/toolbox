import { useMemo, useState } from "react";
import { runTool } from "../api/tauri";

type JsonAction = "format" | "minify" | "validate";

const actionLabels: Record<JsonAction, string> = {
  format: "\u683c\u5f0f\u5316",
  minify: "\u538b\u7f29",
  validate: "\u6821\u9a8c",
};

const ui = {
  title: "JSON \u5de5\u5177",
  subtitle: "\u590d\u7528\u65e7\u63d2\u4ef6 converter.py\uff0cTauri \u9875\u9762\u53ea\u8d1f\u8d23\u8f93\u5165\u3001\u8f93\u51fa\u548c\u8fd0\u884c\u72b6\u6001\u3002",
  actionAria: "JSON \u52a8\u4f5c",
  indent: "\u7f29\u8fdb",
  sortKeys: "\u6309 key \u6392\u5e8f",
  input: "\u8f93\u5165",
  output: "\u8f93\u51fa",
  inputPlaceholder: "\u7c98\u8d34 JSON \u6587\u672c",
  outputPlaceholder: "\u7ed3\u679c\u663e\u793a\u5728\u8fd9\u91cc",
  currentAction: "\u5f53\u524d\u52a8\u4f5c",
  clear: "\u6e05\u7a7a",
  copy: "\u590d\u5236\u8f93\u51fa",
  run: "\u8fd0\u884c",
  running: "\u8fd0\u884c\u4e2d...",
  start: "\u5f00\u59cb\u8fd0\u884c",
  done: "\u8fd0\u884c\u5b8c\u6210",
  failed: "\u8fd0\u884c\u5931\u8d25",
  copied: "\u5df2\u590d\u5236\u8f93\u51fa",
  logAria: "\u8fd0\u884c\u65e5\u5fd7",
  recentLogs: "\u6700\u8fd1 5 \u6761\u672c\u5730\u6267\u884c\u8bb0\u5f55",
  noLogs: "\u6682\u65e0\u65e5\u5fd7",
};

function errorText(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return typeof error === "string" ? error : JSON.stringify(error);
}

function JsonToolsPluginTool() {
  const [action, setAction] = useState<JsonAction>("format");
  const [inputText, setInputText] = useState('{"hello":"HYL"}');
  const [outputText, setOutputText] = useState("");
  const [indent, setIndent] = useState(2);
  const [sortKeys, setSortKeys] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const inputStats = useMemo(() => `${inputText.length} chars`, [inputText.length]);
  const outputStats = useMemo(() => `${outputText.length} chars`, [outputText.length]);
  const canRun = Boolean(inputText.trim()) && !running;

  async function handleRun(nextAction = action) {
    if (!canRun) {
      return;
    }
    setRunning(true);
    setError("");
    setLogs((items) => [`${ui.start}: ${actionLabels[nextAction]}`, ...items].slice(0, 5));
    try {
      const result = await runTool("plugin:json_tools", {
        task_id: `plugin-json-${nextAction}-${Date.now()}`,
        action: nextAction,
        payload: { text: inputText, indent, sort_keys: sortKeys },
      });
      const data = (result.data ?? result) as Record<string, unknown>;
      const text = typeof data.text === "string" ? data.text : JSON.stringify(data, null, 2);
      setOutputText(text);
      setLogs((items) => [ui.done, ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`${ui.failed}: ${message}`, ...items].slice(0, 5));
    } finally {
      setRunning(false);
    }
  }

  async function copyOutput() {
    if (!outputText) return;
    await navigator.clipboard.writeText(outputText);
    setLogs((items) => [ui.copied, ...items].slice(0, 5));
  }

  function clearAll() {
    setInputText("");
    setOutputText("");
    setError("");
  }

  return (
    <div className="base64-tool json-plugin-tool">
      <div className="tool-heading">
        <div>
          <p className="eyebrow">Plugin - JSON tools</p>
          <h2>{ui.title}</h2>
          <p>{ui.subtitle}</p>
        </div>
        <div className="mode-switch" role="group" aria-label={ui.actionAria}>
          {(["format", "minify", "validate"] as JsonAction[]).map((item) => (
            <button className={action === item ? "active" : ""} disabled={running} key={item} onClick={() => setAction(item)} type="button">
              {actionLabels[item]}
            </button>
          ))}
        </div>
      </div>

      <div className="file-mode-card">
        <label className="field-block">
          <span>{ui.indent}</span>
          <input disabled={running || action === "minify"} max={8} min={0} onChange={(event) => setIndent(Number(event.currentTarget.value))} type="number" value={indent} />
        </label>
        <label className="check-row">
          <input checked={sortKeys} disabled={running} onChange={(event) => setSortKeys(event.currentTarget.checked)} type="checkbox" />
          {ui.sortKeys}
        </label>
      </div>

      <div className="editor-grid">
        <label className="field-block">
          <span>{ui.input}<small>{inputStats}</small></span>
          <textarea disabled={running} onChange={(event) => setInputText(event.currentTarget.value)} placeholder={ui.inputPlaceholder} value={inputText} />
        </label>
        <label className="field-block output-field">
          <span>{ui.output}<small>{outputStats}</small></span>
          <textarea placeholder={ui.outputPlaceholder} readOnly value={outputText} />
        </label>
      </div>

      <div className="actions-row">
        <div className="action-hint">{ui.currentAction}: {actionLabels[action]}</div>
        <div className="button-cluster">
          <button className="ghost-button" disabled={running || (!inputText && !outputText)} onClick={clearAll} type="button">{ui.clear}</button>
          <button className="ghost-button" disabled={!outputText} onClick={copyOutput} type="button">{ui.copy}</button>
          <button className="primary-button" disabled={!canRun} onClick={() => handleRun()} type="button">{running ? ui.running : ui.run}</button>
        </div>
      </div>

      <section className="log-panel" aria-label={ui.logAria}>
        <div><div className="panel-title">Runtime</div><p className="muted">{ui.recentLogs}</p></div>
        <div className="log-content">
          {error ? <div className="error-box">{error}</div> : null}
          {logs.length ? <ul>{logs.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul> : <p className="muted">{ui.noLogs}</p>}
        </div>
      </section>
    </div>
  );
}

export default JsonToolsPluginTool;
