import { useMemo, useState } from "react";
import { runTool } from "../api/tauri";

type RegexAction = "extract" | "replace" | "summary";

const actionLabels: Record<RegexAction, string> = {
  extract: "\u63d0\u53d6",
  replace: "\u66ff\u6362",
  summary: "\u6458\u8981",
};

const text = {
  title: "\u6b63\u5219\u5de5\u5177",
  desc: "测试正则并提取文本。",
  pattern: "\u6b63\u5219\u8868\u8fbe\u5f0f",
  replacement: "\u66ff\u6362\u4e3a",
  group: "\u63d0\u53d6\u5206\u7ec4",
  ignoreCase: "\u5ffd\u7565\u5927\u5c0f\u5199",
  multiline: "\u591a\u884c\u6a21\u5f0f",
  input: "\u8f93\u5165",
  output: "\u8f93\u51fa",
  inputHint: "\u7c98\u8d34\u8981\u5339\u914d\u7684\u6587\u672c",
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

function dataToText(data: Record<string, unknown>): string {
  if (typeof data.text === "string" && !("matches" in data) && !("summary" in data)) return data.text;
  return JSON.stringify(data, null, 2);
}

function RegexToolsPluginTool() {
  const [action, setAction] = useState<RegexAction>("extract");
  const [inputText, setInputText] = useState("Alpha: 123\nbeta: 456");
  const [pattern, setPattern] = useState("(\\w+):\\s+(\\d+)");
  const [replacement, setReplacement] = useState("ticket-\\2");
  const [group, setGroup] = useState("0");
  const [ignoreCase, setIgnoreCase] = useState(false);
  const [multiline, setMultiline] = useState(true);
  const [outputText, setOutputText] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const inputStats = useMemo(() => `${inputText.length} chars`, [inputText.length]);
  const outputStats = useMemo(() => `${outputText.length} chars`, [outputText.length]);
  const canRun = !running && Boolean(inputText.trim()) && Boolean(pattern.trim());

  async function handleRun() {
    if (!canRun) return;
    setRunning(true);
    setError("");
    setLogs((items) => [`${text.start}\uff1a${actionLabels[action]}`, ...items].slice(0, 5));
    try {
      const result = await runTool("plugin:regex_tools", {
        task_id: `plugin-regex-${action}-${Date.now()}`,
        action,
        payload: {
          text: inputText,
          pattern,
          replacement,
          group,
          ignore_case: ignoreCase,
          multiline,
        },
      });
      const data = (result.data ?? result) as Record<string, unknown>;
      setOutputText(dataToText(data));
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
    setInputText("");
    setOutputText("");
    setError("");
  }

  return (
    <div className="base64-tool regex-plugin-tool">
      <div className="tool-heading">
        <div>
          <p className="eyebrow">Plugin - regex_tools</p>
          <h2>{text.title}</h2>
          <p>{text.desc}</p>
        </div>
        <div className="mode-switch" role="group" aria-label={text.title}>
          {(["extract", "replace", "summary"] as RegexAction[]).map((item) => (
            <button className={action === item ? "active" : ""} disabled={running} key={item} onClick={() => setAction(item)} type="button">
              {actionLabels[item]}
            </button>
          ))}
        </div>
      </div>

      <div className="file-mode-card">
        <label className="field-block"><span>{text.pattern}</span><input disabled={running} onChange={(event) => setPattern(event.currentTarget.value)} value={pattern} /></label>
        <label className="field-block"><span>{text.replacement}</span><input disabled={running || action !== "replace"} onChange={(event) => setReplacement(event.currentTarget.value)} value={replacement} /></label>
        <label className="field-block"><span>{text.group}</span><input disabled={running || action !== "extract"} onChange={(event) => setGroup(event.currentTarget.value)} value={group} /></label>
        <label className="check-row"><input checked={ignoreCase} disabled={running} onChange={(event) => setIgnoreCase(event.currentTarget.checked)} type="checkbox" />{text.ignoreCase}</label>
        <label className="check-row"><input checked={multiline} disabled={running} onChange={(event) => setMultiline(event.currentTarget.checked)} type="checkbox" />{text.multiline}</label>
      </div>

      <div className="editor-grid">
        <label className="field-block"><span>{text.input}<small>{inputStats}</small></span><textarea disabled={running} onChange={(event) => setInputText(event.currentTarget.value)} placeholder={text.inputHint} value={inputText} /></label>
        <label className="field-block output-field"><span>{text.output}<small>{outputStats}</small></span><textarea placeholder={text.outputHint} readOnly value={outputText} /></label>
      </div>

      <div className="actions-row">
        <div className="action-hint">{text.current}\uff1a{actionLabels[action]}</div>
        <div className="button-cluster">
          <button className="ghost-button" disabled={running || (!inputText && !outputText)} onClick={clearAll} type="button">{text.clear}</button>
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

export default RegexToolsPluginTool;
