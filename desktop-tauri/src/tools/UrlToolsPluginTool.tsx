import { useMemo, useState } from "react";
import { runTool } from "../api/tauri";
import { uiText } from "../uiText";

type UrlAction = "encode" | "decode" | "parse_query" | "format_query" | "build_query" | "summarize";

const actionLabels: Record<UrlAction, string> = {
  encode: "\u7f16\u7801",
  decode: "\u89e3\u7801",
  parse_query: "\u89e3\u6790",
  format_query: "\u683c\u5f0f",
  build_query: "\u751f\u6210",
  summarize: "\u6458\u8981",
};

const text = {
  title: "URL \u5de5\u5177",
  desc: "处理 URL 和参数。",
  start: "\u8fd0\u884c",
  done: "\u8fd0\u884c\u5b8c\u6210",
  copied: "\u5df2\u590d\u5236",
  failed: "\u8fd0\u884c\u5931\u8d25",
  safe: "\u7f16\u7801\u4fdd\u7559\u5b57\u7b26",
  safeHint: "key=value",
  pairs: "\u53c2\u6570\u5217\u8868",
  input: "\u8f93\u5165",
  output: "\u8f93\u51fa",
  inputHint: "\u7c98\u8d34 URL\u3001\u67e5\u8be2\u4e32\u6216\u6587\u672c",
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

function parsePairs(value: string): string[][] {
  return value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const index = line.indexOf("=");
      return index >= 0 ? [line.slice(0, index).trim(), line.slice(index + 1).trim()] : [line, ""];
    });
}

function stringifyData(data: Record<string, unknown>): string {
  if (typeof data.text === "string") return data.text;
  if (Array.isArray(data.pairs)) {
    return data.pairs.map((item) => (Array.isArray(item) ? `${item[0]} = ${item[1] ?? ""}` : JSON.stringify(item))).join("\n");
  }
  return JSON.stringify(data, null, 2);
}

function UrlToolsPluginTool() {
  const [action, setAction] = useState<UrlAction>("encode");
  const [inputText, setInputText] = useState("https://example.com/search?q=HYL Tools&lang=zh");
  const [pairsText, setPairsText] = useState("q=HYL Tools\nlang=zh");
  const [safeChars, setSafeChars] = useState("");
  const [outputText, setOutputText] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const activeInput = action === "build_query" ? pairsText : inputText;
  const inputStats = useMemo(() => uiText.common.charCount(activeInput.length), [activeInput.length]);
  const outputStats = useMemo(() => uiText.common.charCount(outputText.length), [outputText.length]);
  const canRun = !running && Boolean(activeInput.trim());

  async function handleRun() {
    if (!canRun) return;
    setRunning(true);
    setError("");
    setLogs((items) => [`${text.start}\uff1a${actionLabels[action]}`, ...items].slice(0, 5));
    try {
      const result = await runTool("plugin:url_tools", {
        task_id: `plugin-url-${action}-${Date.now()}`,
        action,
        payload: { text: inputText, safe: safeChars, pairs: parsePairs(pairsText) },
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
    setPairsText("");
    setOutputText("");
    setError("");
  }

  return (
    <div className="base64-tool url-plugin-tool">
      <div className="tool-heading">
        <div>
          <p className="eyebrow">{uiText.common.pluginLabel("url_tools")}</p>
          <h2>{text.title}</h2>
          <p>{text.desc}</p>
        </div>
        <div className="mode-switch" role="group" aria-label={text.title}>
          {(["encode", "decode", "parse_query", "format_query", "build_query", "summarize"] as UrlAction[]).map((item) => (
            <button className={action === item ? "active" : ""} disabled={running} key={item} onClick={() => setAction(item)} type="button">
              {actionLabels[item]}
            </button>
          ))}
        </div>
      </div>

      <div className="file-mode-card">
        <label className="field-block"><span>{text.safe}</span><input disabled={running || action !== "encode"} onChange={(event) => setSafeChars(event.currentTarget.value)} placeholder="/?:" value={safeChars} /></label>
        <p className="muted">{text.safeHint}</p>
      </div>

      <div className="editor-grid">
        {action === "build_query" ? (
          <label className="field-block"><span>{text.pairs}<small>{inputStats}</small></span><textarea disabled={running} onChange={(event) => setPairsText(event.currentTarget.value)} placeholder="q=HYL Tools\nlang=zh" value={pairsText} /></label>
        ) : (
          <label className="field-block"><span>{text.input}<small>{inputStats}</small></span><textarea disabled={running} onChange={(event) => setInputText(event.currentTarget.value)} placeholder={text.inputHint} value={inputText} /></label>
        )}
        <label className="field-block output-field"><span>{text.output}<small>{outputStats}</small></span><textarea placeholder={text.outputHint} readOnly value={outputText} /></label>
      </div>

      <div className="actions-row">
        <div className="action-hint">{text.current}\uff1a{actionLabels[action]}</div>
        <div className="button-cluster">
          <button className="ghost-button" disabled={running || (!inputText && !pairsText && !outputText)} onClick={clearAll} type="button">{text.clear}</button>
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

export default UrlToolsPluginTool;
