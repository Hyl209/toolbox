import { useEffect, useMemo, useRef, useState } from "react";
import { pickDirectory, pickFiles, type DialogFilter, runTool, type ToolResult, type ToolSettings } from "../api/tauri";

type OutputRow = { source: string; output: string };
type WordConfig = {
  page: Record<string, number | string>;
  styles: Record<string, Record<string, number | string | boolean>>;
};

const wordFilters: DialogFilter[] = [{ name: "Word documents", extensions: ["docx"] }];

function errorText(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return typeof error === "string" ? error : JSON.stringify(error);
}

function splitPaths(text: string): string[] {
  return text
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function rowsOf(result: ToolResult): OutputRow[] {
  return (result.results ?? result.data?.results ?? []).map((row) => ({
    source: String(row.source ?? ""),
    output: String(row.output ?? ""),
  }));
}

function configOf(result: ToolResult): WordConfig | null {
  const data = (result.data ?? result) as ToolResult & { config?: WordConfig };
  return data.config ?? null;
}

function mergeWordConfig(base: WordConfig | null, settings: ToolSettings | undefined): WordConfig | null {
  if (!base) {
    return null;
  }
  const page = { ...base.page, ...(settings?.page ?? {}) };
  const styles: WordConfig["styles"] = {};
  Object.entries(base.styles).forEach(([styleKey, style]) => {
    styles[styleKey] = { ...style, ...(settings?.styles?.[styleKey] ?? {}) };
  });
  return { page, styles };
}

function WordFormatterTool({ initialSettings = {} }: { initialSettings?: ToolSettings }) {
  const [inputText, setInputText] = useState("");
  const [markdownText, setMarkdownText] = useState("");
  const [outputDir, setOutputDir] = useState(initialSettings.output_dir ?? "");
  const [outputMode, setOutputMode] = useState("copy");
  const [config, setConfig] = useState<WordConfig | null>(null);
  const [files, setFiles] = useState<Array<Record<string, string | number | boolean>>>([]);
  const [results, setResults] = useState<OutputRow[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);
  const configTouchedRef = useRef(false);
  const outputDirTouchedRef = useRef(false);

  const paths = useMemo(() => splitPaths(inputText), [inputText]);
  const canList = !running && paths.length > 0;
  const canFormat = !running && (paths.length > 0 || markdownText.trim().length > 0) && (outputMode === "overwrite" || Boolean(outputDir));

  useEffect(() => {
    let cancelled = false;
    runTool("wordformatter", { task_id: `wordformatter-config-${Date.now()}`, action: "default_config", payload: {} })
      .then((result) => {
        if (!cancelled) {
          setConfig((current) => (configTouchedRef.current && current ? current : mergeWordConfig(configOf(result), initialSettings)));
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(errorText(caught));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [initialSettings]);

  useEffect(() => {
    if (!configTouchedRef.current) {
      setConfig((current) => mergeWordConfig(current, initialSettings));
    }
    if (!outputDirTouchedRef.current) {
      setOutputDir((current) => current || initialSettings.output_dir || "");
    }
  }, [initialSettings]);

  async function chooseFiles() {
    const picked = await pickFiles({ title: "选择 Word 文档", filters: wordFilters });
    if (picked?.length) {
      setInputText((current) => [current, ...picked].filter(Boolean).join("\n"));
    }
  }

  async function chooseOutputDir() {
    const path = await pickDirectory({ title: "选择 Word 输出目录" });
    if (path) {
      outputDirTouchedRef.current = true;
      setOutputDir(path);
    }
  }

  function updatePage(key: string, value: string) {
    configTouchedRef.current = true;
    setConfig((current) => {
      if (!current) {
        return current;
      }
      return { ...current, page: { ...current.page, [key]: value } };
    });
  }

  function updateStyle(styleKey: string, field: string, value: string | boolean) {
    configTouchedRef.current = true;
    setConfig((current) => {
      if (!current) {
        return current;
      }
      return {
        ...current,
        styles: {
          ...current.styles,
          [styleKey]: { ...current.styles[styleKey], [field]: value },
        },
      };
    });
  }

  async function handleList() {
    if (!canList) {
      return;
    }
    setRunning(true);
    setError("");
    setLogs((items) => ["开始扫描 Word 输入", ...items].slice(0, 5));
    try {
      const result = await runTool("wordformatter", {
        task_id: `wordformatter-list-${Date.now()}`,
        action: "list",
        payload: { paths },
      });
      const rows = result.files ?? result.data?.files ?? [];
      setFiles(rows);
      setLogs((items) => [`扫描完成：${rows.length} 个 .docx`, ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`扫描失败：${message}`, ...items].slice(0, 5));
    } finally {
      setRunning(false);
    }
  }

  async function handleFormat() {
    if (!canFormat) {
      return;
    }
    setRunning(true);
    setError("");
    setResults([]);
    setLogs((items) => ["开始执行 Word 排版", ...items].slice(0, 5));
    try {
      const result = await runTool("wordformatter", {
        task_id: `wordformatter-format-${Date.now()}`,
        action: "format",
        payload: {
          paths,
          text: markdownText,
          output_dir: outputDir,
          output_mode: outputMode,
          config: config ?? {},
        },
      });
      const rows = rowsOf(result);
      setResults(rows);
      setLogs((items) => [`排版完成：${rows.length} 个输出`, ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`排版失败：${message}`, ...items].slice(0, 5));
    } finally {
      setRunning(false);
    }
  }

  function clearAll() {
    setFiles([]);
    setResults([]);
    setError("");
    setLogs([]);
  }

  const page = config?.page ?? {};
  const heading = config?.styles?.heading1 ?? {};
  const body = config?.styles?.body ?? {};

  return (
    <div className="wordformatter-tool">
      <div className="tool-heading">
        <div>
          <p className="eyebrow">Legacy Word formatter</p>
          <h2>Word 排版统一</h2>
          <p>复用旧版 word-formatter converter：支持 .docx 批量排版，也支持用 Markdown 标题文本生成 Word。</p>
        </div>
        <span className="settings-mode-pill">{outputMode === "overwrite" ? "原地覆盖" : "另存副本"}</span>
      </div>

      <div className="editor-grid">
        <div className="file-mode-card compact-card">
          <label className="field-block file-path-field">
            <span>Word 输入路径</span>
            <textarea disabled={running} onChange={(event) => setInputText(event.currentTarget.value)} placeholder="每行一个 .docx 或目录" value={inputText} />
          </label>
          <div className="button-cluster">
            <button className="ghost-button" disabled={running} onClick={chooseFiles} type="button">
              选择文件
            </button>
            <button className="ghost-button" disabled={!canList} onClick={handleList} type="button">
              扫描
            </button>
          </div>
        </div>

        <div className="file-mode-card compact-card">
          <label className="field-block">
            <span>Markdown 文本</span>
            <textarea disabled={running} onChange={(event) => setMarkdownText(event.currentTarget.value)} placeholder="# 标题&#10;正文内容" value={markdownText} />
          </label>
        </div>
      </div>

      <div className="editor-grid file-editor-grid">
        <div className="file-mode-card compact-card">
          <label className="field-block">
            <span>输出模式</span>
            <select disabled={running} onChange={(event) => setOutputMode(event.currentTarget.value)} value={outputMode}>
              <option value="copy">另存副本</option>
              <option value="overwrite">原地覆盖</option>
            </select>
          </label>
          <label className="field-block file-path-field">
            <span>输出目录</span>
            <div className="path-input-row">
              <input
                disabled={running || outputMode === "overwrite"}
                onChange={(event) => {
                  outputDirTouchedRef.current = true;
                  setOutputDir(event.currentTarget.value);
                }}
                value={outputDir}
              />
              <button className="path-pick-button" disabled={running || outputMode === "overwrite"} onClick={chooseOutputDir} type="button">
                选择
              </button>
            </div>
          </label>
        </div>

        <div className="file-mode-card compact-card">
          <span className="field-label">页面设置（cm）</span>
          <div className="mini-form-grid">
            {["top_margin_cm", "bottom_margin_cm", "left_margin_cm", "right_margin_cm"].map((key) => (
              <label className="field-block" key={key}>
                <span>{key.replace("_margin_cm", "")}</span>
                <input disabled={running || !config} onChange={(event) => updatePage(key, event.currentTarget.value)} value={String(page[key] ?? "")} />
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="editor-grid file-editor-grid">
        <div className="file-mode-card compact-card">
          <span className="field-label">标题 1 样式</span>
          <div className="mini-form-grid">
            <label className="field-block">
              <span>字体</span>
              <input disabled={running || !config} onChange={(event) => updateStyle("heading1", "font", event.currentTarget.value)} value={String(heading.font ?? "")} />
            </label>
            <label className="field-block">
              <span>字号</span>
              <input disabled={running || !config} onChange={(event) => updateStyle("heading1", "size_pt", event.currentTarget.value)} value={String(heading.size_pt ?? "")} />
            </label>
          </div>
        </div>
        <div className="file-mode-card compact-card">
          <span className="field-label">正文样式</span>
          <div className="mini-form-grid">
            <label className="field-block">
              <span>字体</span>
              <input disabled={running || !config} onChange={(event) => updateStyle("body", "font", event.currentTarget.value)} value={String(body.font ?? "")} />
            </label>
            <label className="field-block">
              <span>字号</span>
              <input disabled={running || !config} onChange={(event) => updateStyle("body", "size_pt", event.currentTarget.value)} value={String(body.size_pt ?? "")} />
            </label>
          </div>
        </div>
      </div>

      <div className="actions-row">
        <div className="action-hint">原地覆盖会真实改写源文件；另存副本需要输出目录。</div>
        <div className="button-cluster">
          <button className="ghost-button" disabled={running || (!files.length && !results.length && !error)} onClick={clearAll} type="button">
            清空结果
          </button>
          <button className="primary-button" disabled={!canFormat} onClick={handleFormat} type="button">
            {running ? "运行中..." : "执行排版"}
          </button>
        </div>
      </div>

      <div className="editor-grid file-editor-grid">
        <div className="result-card">
          <span>已识别文档</span>
          <strong>{files.length ? `${files.length} 个` : "等待扫描"}</strong>
          <p>{files[0]?.name || "可直接执行，sidecar 会再次按旧规则收集 .docx"}</p>
        </div>
        <div className="result-card">
          <span>输出结果</span>
          <strong>{results.length ? `${results.length} 个` : "暂无"}</strong>
          <p>{results[0]?.output || "输出路径会显示在这里"}</p>
        </div>
      </div>

      {results.length ? (
        <section className="table-panel">
          <div className="panel-title">Word outputs</div>
          <div className="result-list">
            {results.map((row, index) => (
              <div className="result-row" key={`${row.output}-${index}`}>
                <span>{row.source}</span>
                <strong>{row.output}</strong>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="log-panel" aria-label="运行日志">
        <div>
          <div className="panel-title">Runtime</div>
          <p className="muted">最近 5 条本地执行记录</p>
        </div>
        <div className="log-content">
          {error ? <div className="error-box">{error}</div> : null}
          {logs.length ? (
            <ul>
              {logs.map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="muted">暂无日志</p>
          )}
        </div>
      </section>
    </div>
  );
}

export default WordFormatterTool;
