import { useState } from "react";
import { runTool } from "../api/tauri";
import { uiText } from "../uiText";

type UuidAction = "generate" | "normalize" | "validate" | "describe";

const actionLabels: Record<UuidAction, string> = {
  generate: "\u751f\u6210",
  normalize: "\u89c4\u8303",
  validate: "\u6821\u9a8c",
  describe: "\u63cf\u8ff0",
};

const ui = {
  title: "UUID \u5de5\u5177",
  subtitle: "生成和校验 UUID。",
  actionAria: "UUID \u52a8\u4f5c",
  count: "\u751f\u6210\u6570\u91cf",
  uppercase: "\u5927\u5199",
  hyphenated: "\u4fdd\u7559\u8fde\u5b57\u7b26",
  input: "\u8f93\u5165",
  output: "\u8f93\u51fa",
  required: "\u5fc5\u586b",
  noInput: "\u751f\u6210\u6a21\u5f0f\u65e0\u9700\u8f93\u5165",
  inputPlaceholder: "\u7c98\u8d34 UUID\uff0c\u4f8b\u5982 550e8400-e29b-41d4-a716-446655440000",
  outputPlaceholder: "\u7ed3\u679c\u663e\u793a\u5728\u8fd9\u91cc",
  currentAction: "\u5f53\u524d\u52a8\u4f5c",
  clear: "\u6e05\u7a7a",
  copy: "\u590d\u5236",
  run: "\u8fd0\u884c",
  running: "\u8fd0\u884c\u4e2d",
  start: "\u8fd0\u884c",
  done: "\u8fd0\u884c\u5b8c\u6210",
  failed: "\u8fd0\u884c\u5931\u8d25",
  copied: "\u5df2\u590d\u5236",
  logAria: "\u8fd0\u884c\u65e5\u5fd7",
  recentLogs: "\u6700\u8fd1 5 \u6761\u672c\u5730\u6267\u884c\u8bb0\u5f55",
  noLogs: "\u6682\u65e0\u65e5\u5fd7",
};

function errorText(error: unknown): string {
  if (error instanceof Error) return error.message;
  return typeof error === "string" ? error : JSON.stringify(error);
}

function UuidToolsPluginTool() {
  const [action, setAction] = useState<UuidAction>("generate");
  const [inputText, setInputText] = useState("");
  const [outputText, setOutputText] = useState("");
  const [count, setCount] = useState(10);
  const [uppercase, setUppercase] = useState(false);
  const [hyphenated, setHyphenated] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const needsInput = action !== "generate";
  const canRun = !running && (!needsInput || Boolean(inputText.trim()));

  async function handleRun() {
    if (!canRun) return;
    setRunning(true);
    setError("");
    setLogs((items) => [`${ui.start}: ${actionLabels[action]}`, ...items].slice(0, 5));
    try {
      const result = await runTool("plugin:uuid_tools", {
        task_id: `plugin-uuid-${action}-${Date.now()}`,
        action,
        payload: { text: inputText, count, uppercase, hyphenated },
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
    <div className="base64-tool uuid-plugin-tool">
      <div className="tool-heading">
        <div><p className="eyebrow">{uiText.common.pluginLabel("uuid_tools")}</p><h2>{ui.title}</h2><p>{ui.subtitle}</p></div>
        <div className="mode-switch" role="group" aria-label={ui.actionAria}>
          {(["generate", "normalize", "validate", "describe"] as UuidAction[]).map((item) => (
            <button className={action === item ? "active" : ""} disabled={running} key={item} onClick={() => setAction(item)} type="button">{actionLabels[item]}</button>
          ))}
        </div>
      </div>

      <div className="file-mode-card">
        <label className="field-block"><span>{ui.count}</span><input disabled={running || action !== "generate"} max={500} min={1} onChange={(event) => setCount(Number(event.currentTarget.value))} type="number" value={count} /></label>
        <label className="check-row"><input checked={uppercase} disabled={running} onChange={(event) => setUppercase(event.currentTarget.checked)} type="checkbox" />{ui.uppercase}</label>
        <label className="check-row"><input checked={hyphenated} disabled={running} onChange={(event) => setHyphenated(event.currentTarget.checked)} type="checkbox" />{ui.hyphenated}</label>
      </div>

      <div className="editor-grid">
        <label className="field-block"><span>{ui.input}<small>{needsInput ? ui.required : ui.noInput}</small></span><textarea disabled={running || action === "generate"} onChange={(event) => setInputText(event.currentTarget.value)} placeholder={ui.inputPlaceholder} value={inputText} /></label>
        <label className="field-block output-field"><span>{ui.output}<small>{uiText.common.charCount(outputText.length)}</small></span><textarea placeholder={ui.outputPlaceholder} readOnly value={outputText} /></label>
      </div>

      <div className="actions-row">
        <div className="action-hint">{ui.currentAction}: {actionLabels[action]}</div>
        <div className="button-cluster">
          <button className="ghost-button" disabled={running || (!inputText && !outputText)} onClick={clearAll} type="button">{ui.clear}</button>
          <button className="ghost-button" disabled={!outputText} onClick={copyOutput} type="button">{ui.copy}</button>
          <button className="primary-button" disabled={!canRun} onClick={handleRun} type="button">{running ? ui.running : ui.run}</button>
        </div>
      </div>

      <section className="log-panel" aria-label={ui.logAria}>
        <div><div className="panel-title">{uiText.common.runtime}</div><p className="muted">{ui.recentLogs}</p></div>
        <div className="log-content">{error ? <div className="error-box">{error}</div> : null}{logs.length ? <ul>{logs.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul> : <p className="muted">{ui.noLogs}</p>}</div>
      </section>
    </div>
  );
}

export default UuidToolsPluginTool;
