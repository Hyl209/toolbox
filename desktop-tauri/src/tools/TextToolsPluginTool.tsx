import { useMemo, useState } from "react";
import { runTool } from "../api/tauri";
import { uiText } from "../uiText";

type TextAction = "clean_lines" | "dedupe_lines" | "sort_lines" | "transform_case";
type CaseMode = "lower" | "upper" | "title";

const actionLabels: Record<TextAction, string> = {
  clean_lines: "\u6e05\u7406\u884c",
  dedupe_lines: "\u53bb\u91cd\u884c",
  sort_lines: "\u6392\u5e8f\u884c",
  transform_case: "\u8f6c\u5927\u5c0f",
};

const text = {
  title: "\u6587\u672c\u5de5\u5177",
  start: "\u8fd0\u884c",
  done: "\u8fd0\u884c\u5b8c\u6210",
  copied: "\u5df2\u590d\u5236",
  failed: "\u8fd0\u884c\u5931\u8d25",
  trim: "\u53bb\u9664\u9996\u5c3e\u7a7a\u767d",
  dropEmpty: "\u5220\u9664\u7a7a\u884c",
  caseSensitive: "\u533a\u5206\u5927\u5c0f\u5199",
  reverse: "\u5012\u5e8f\u6392\u5e8f",
  mode: "\u8f6c\u6362\u6a21\u5f0f",
  lower: "\u8f6c\u5c0f\u5199",
  upper: "\u8f6c\u5927\u5199",
  titleCase: "\u6807\u9898\u5927\u5c0f\u5199",
  input: "\u8f93\u5165",
  output: "\u8f93\u51fa",
  inputHint: "\u7c98\u8d34\u8981\u5904\u7406\u7684\u6587\u672c",
  outputHint: "\u5904\u7406\u7ed3\u679c\u663e\u793a\u5728\u8fd9\u91cc",
  current: "\u5f53\u524d\u52a8\u4f5c",
  clear: "\u6e05\u7a7a",
  copy: "\u590d\u5236",
  running: "\u8fd0\u884c\u4e2d",
  run: "\u8fd0\u884c",
  log: "\u8fd0\u884c\u65e5\u5fd7",
  recent: "\u6700\u8fd1 5 \u6761\u672c\u5730\u6267\u884c\u8bb0\u5f55",
  emptyLog: "\u6682\u65e0\u65e5\u5fd7",
};

function errorText(error: unknown): string {
  if (error instanceof Error) return error.message;
  return typeof error === "string" ? error : JSON.stringify(error);
}

function TextToolsPluginTool() {
  const [action, setAction] = useState<TextAction>("clean_lines");
  const [inputText, setInputText] = useState("  Alpha\n\nbeta\nAlpha  ");
  const [outputText, setOutputText] = useState("");
  const [trim, setTrim] = useState(true);
  const [dropEmpty, setDropEmpty] = useState(true);
  const [caseSensitive, setCaseSensitive] = useState(true);
  const [reverse, setReverse] = useState(false);
  const [caseMode, setCaseMode] = useState<CaseMode>("lower");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const inputStats = useMemo(() => uiText.common.charCount(inputText.length), [inputText.length]);
  const outputStats = useMemo(() => uiText.common.charCount(outputText.length), [outputText.length]);
  const canRun = Boolean(inputText.trim()) && !running;

  async function handleRun() {
    if (!canRun) return;
    setRunning(true);
    setError("");
    setLogs((items) => [`${text.start}\uff1a${actionLabels[action]}`, ...items].slice(0, 5));
    try {
      const result = await runTool("plugin:text_tools", {
        task_id: `plugin-text-${action}-${Date.now()}`,
        action,
        payload: { text: inputText, trim, drop_empty: dropEmpty, case_sensitive: caseSensitive, reverse, mode: caseMode },
      });
      const data = (result.data ?? result) as Record<string, unknown>;
      setOutputText(typeof data.text === "string" ? data.text : JSON.stringify(data, null, 2));
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
    <div className="base64-tool text-plugin-tool">
      <div className="tool-heading">
        <div>
          <p className="eyebrow">{uiText.common.pluginLabel("text_tools")}</p>
          <h2>{text.title}</h2>
        </div>
        <div className="mode-switch" role="group" aria-label={text.title}>
          {(["clean_lines", "dedupe_lines", "sort_lines", "transform_case"] as TextAction[]).map((item) => (
            <button className={action === item ? "active" : ""} disabled={running} key={item} onClick={() => setAction(item)} type="button">
              {actionLabels[item]}
            </button>
          ))}
        </div>
      </div>

      <div className="file-mode-card">
        <label className="check-row"><input checked={trim} disabled={running || action === "sort_lines"} onChange={(event) => setTrim(event.currentTarget.checked)} type="checkbox" />{text.trim}</label>
        <label className="check-row"><input checked={dropEmpty} disabled={running || action !== "clean_lines"} onChange={(event) => setDropEmpty(event.currentTarget.checked)} type="checkbox" />{text.dropEmpty}</label>
        <label className="check-row"><input checked={caseSensitive} disabled={running || action === "clean_lines" || action === "transform_case"} onChange={(event) => setCaseSensitive(event.currentTarget.checked)} type="checkbox" />{text.caseSensitive}</label>
        <label className="check-row"><input checked={reverse} disabled={running || action !== "sort_lines"} onChange={(event) => setReverse(event.currentTarget.checked)} type="checkbox" />{text.reverse}</label>
        <label className="field-block"><span>{text.mode}</span><select disabled={running || action !== "transform_case"} onChange={(event) => setCaseMode(event.currentTarget.value as CaseMode)} value={caseMode}><option value="lower">{text.lower}</option><option value="upper">{text.upper}</option><option value="title">{text.titleCase}</option></select></label>
      </div>

      <div className="editor-grid">
        <label className="field-block"><span>{text.input}<small>{inputStats}</small></span><textarea disabled={running} onChange={(event) => setInputText(event.currentTarget.value)} placeholder={text.inputHint} value={inputText} /></label>
        <label className="field-block output-field"><span>{text.output}<small>{outputStats}</small></span><textarea placeholder={text.outputHint} readOnly value={outputText} /></label>
      </div>

      <div className="actions-row">
        <div className="button-cluster">
          <button className="ghost-button" disabled={running || (!inputText && !outputText)} onClick={clearAll} type="button">{text.clear}</button>
          <button className="ghost-button" disabled={!outputText} onClick={copyOutput} type="button">{text.copy}</button>
          <button className="primary-button" disabled={!canRun} onClick={handleRun} type="button">{running ? text.running : text.run}</button>
        </div>
      </div>

      <section className="log-panel" aria-label={text.log}>
        <div><div className="panel-title">{uiText.common.runtime}</div></div>
        <div className="log-content">
          {error ? <div className="error-box">{error}</div> : null}
          {logs.length ? <ul>{logs.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul> : <p className="muted">{text.emptyLog}</p>}
        </div>
      </section>
    </div>
  );
}

export default TextToolsPluginTool;
