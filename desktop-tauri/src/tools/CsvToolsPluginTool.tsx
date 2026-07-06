import { useMemo, useState } from "react";
import { runTool } from "../api/tauri";
import { uiText } from "../uiText";

type CsvAction = "format" | "to_tsv" | "to_json" | "summary";

const actionLabels: Record<CsvAction, string> = {
  format: "\u683c\u5f0f",
  to_tsv: "\u8f6cTSV",
  to_json: "JSON",
  summary: "\u6458\u8981",
};

const text = {
  title: "CSV \u5de5\u5177",
  delimiter: "\u5206\u9694\u7b26",
  hasHeader: "\u9996\u884c\u4f5c\u4e3a\u8868\u5934",
  input: "\u8f93\u5165",
  output: "\u8f93\u51fa",
  inputHint: "\u7c98\u8d34 CSV \u6587\u672c",
  outputHint: "\u5904\u7406\u7ed3\u679c\u663e\u793a\u5728\u8fd9\u91cc",
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
  if (typeof data.text === "string") return data.text;
  return JSON.stringify(data, null, 2);
}

function CsvToolsPluginTool() {
  const [action, setAction] = useState<CsvAction>("format");
  const [inputText, setInputText] = useState('name,score\n"Alice, A",10\nBob,9');
  const [delimiter, setDelimiter] = useState(",");
  const [hasHeader, setHasHeader] = useState(true);
  const [outputText, setOutputText] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const inputStats = useMemo(() => uiText.common.charCount(inputText.length), [inputText.length]);
  const outputStats = useMemo(() => uiText.common.charCount(outputText.length), [outputText.length]);
  const canRun = !running && Boolean(inputText.trim());

  async function handleRun() {
    if (!canRun) return;
    setRunning(true);
    setError("");
    setLogs((items) => [`${text.start}\uff1a${actionLabels[action]}`, ...items].slice(0, 5));
    try {
      const result = await runTool("plugin:csv_tools", {
        task_id: `plugin-csv-${action}-${Date.now()}`,
        action,
        payload: { text: inputText, delimiter: delimiter || ",", has_header: hasHeader },
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
    setInputText("");
    setOutputText("");
    setError("");
  }

  return (
    <div className="base64-tool csv-plugin-tool">
      <div className="tool-heading">
        <div>
          <p className="eyebrow">{uiText.common.pluginLabel("csv_tools")}</p>
          <h2>{text.title}</h2>
        </div>
        <div className="mode-switch" role="group" aria-label={text.title}>
          {(["format", "to_tsv", "to_json", "summary"] as CsvAction[]).map((item) => (
            <button className={action === item ? "active" : ""} disabled={running} key={item} onClick={() => setAction(item)} type="button">
              {actionLabels[item]}
            </button>
          ))}
        </div>
      </div>

      <div className="file-mode-card">
        <label className="field-block"><span>{text.delimiter}</span><input disabled={running} maxLength={1} onChange={(event) => setDelimiter(event.currentTarget.value)} value={delimiter} /></label>
        <label className="check-row"><input checked={hasHeader} disabled={running || action !== "to_json"} onChange={(event) => setHasHeader(event.currentTarget.checked)} type="checkbox" />{text.hasHeader}</label>
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

export default CsvToolsPluginTool;
