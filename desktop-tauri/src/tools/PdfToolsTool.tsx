import { useEffect, useMemo, useState } from "react";
import { pickDirectory, pickFiles, type DialogFilter, runTool, type ToolResult } from "../api/tauri";

type OutputRow = { source: string; output: string };

const pdfFilters: DialogFilter[] = [{ name: "PDF files", extensions: ["pdf"] }];
const actionOptions = [
  { value: "merge", label: "合并" },
  { value: "split", label: "拆分" },
  { value: "images", label: "转图片" },
  { value: "text", label: "提取文本" },
];

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

function PdfToolsTool({ initialOutputDir = "" }: { initialOutputDir?: string }) {
  const [inputText, setInputText] = useState("");
  const [outputDir, setOutputDir] = useState(initialOutputDir);
  const [action, setAction] = useState("merge");
  const [pageRanges, setPageRanges] = useState("");
  const [imageFormat, setImageFormat] = useState("png");
  const [dpi, setDpi] = useState("150");
  const [textExportFormat, setTextExportFormat] = useState("txt");
  const [ocrFallback, setOcrFallback] = useState(false);
  const [ocrStatus, setOcrStatus] = useState("OCR 未检测");
  const [files, setFiles] = useState<Array<Record<string, string | number | boolean>>>([]);
  const [results, setResults] = useState<OutputRow[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const paths = useMemo(() => splitPaths(inputText), [inputText]);
  const canList = !running && paths.length > 0;
  const canRun = !running && paths.length > 0 && Boolean(outputDir);

  useEffect(() => {
    if (!initialOutputDir) {
      return;
    }
    setOutputDir((current) => current || initialOutputDir);
  }, [initialOutputDir]);

  useEffect(() => {
    let cancelled = false;
    runTool("pdftools", { task_id: `pdftools-probe-${Date.now()}`, action: "probe_ocr", payload: {} })
      .then((result) => {
        if (cancelled) {
          return;
        }
        const available = Boolean(result.available ?? result.data?.available);
        const message = String(result.message ?? result.data?.message ?? "");
        setOcrStatus(available ? "OCR 可用" : message || "OCR 不可用");
      })
      .catch((caught) => {
        if (!cancelled) {
          setOcrStatus(errorText(caught));
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function chooseFiles() {
    const picked = await pickFiles({ title: "选择 PDF 文件", filters: pdfFilters });
    if (picked?.length) {
      setInputText((current) => [current, ...picked].filter(Boolean).join("\n"));
    }
  }

  async function chooseOutputDir() {
    const path = await pickDirectory({ title: "选择 PDF 输出目录" });
    if (path) {
      setOutputDir(path);
    }
  }

  function payload() {
    return {
      paths,
      output_dir: outputDir,
      page_ranges: pageRanges,
      image_format: imageFormat,
      dpi,
      text_export_format: textExportFormat,
      ocr_fallback: ocrFallback,
    };
  }

  async function handleList() {
    if (!canList) {
      return;
    }
    setRunning(true);
    setError("");
    setLogs((items) => ["开始扫描 PDF 输入", ...items].slice(0, 5));
    try {
      const result = await runTool("pdftools", {
        task_id: `pdftools-list-${Date.now()}`,
        action: "list",
        payload: { paths },
      });
      const rows = result.files ?? result.data?.files ?? [];
      setFiles(rows);
      setLogs((items) => [`扫描完成：${rows.length} 个 PDF`, ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`扫描失败：${message}`, ...items].slice(0, 5));
    } finally {
      setRunning(false);
    }
  }

  async function handleRun() {
    if (!canRun) {
      return;
    }
    setRunning(true);
    setError("");
    setResults([]);
    setLogs((items) => [`开始执行 PDF ${action}`, ...items].slice(0, 5));
    try {
      const result = await runTool("pdftools", {
        task_id: `pdftools-${action}-${Date.now()}`,
        action,
        payload: payload(),
      });
      const rows = rowsOf(result);
      setResults(rows);
      setLogs((items) => [`处理完成：${rows.length} 个输出`, ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`处理失败：${message}`, ...items].slice(0, 5));
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

  return (
    <div className="pdftools-tool">
      <div className="tool-heading">
        <div>
          <p className="eyebrow">Legacy PDF tools</p>
          <h2>PDF 工具</h2>
          <p>复用旧版 pdf-tools converter：支持合并、拆分、转图片、导出 TXT / DOCX；OCR 作为可选外部依赖。</p>
        </div>
        <span className="settings-mode-pill">{actionOptions.find((item) => item.value === action)?.label}</span>
      </div>

      <div className="editor-grid">
        <div className="file-mode-card compact-card">
          <label className="field-block file-path-field">
            <span>PDF 输入路径</span>
            <textarea disabled={running} onChange={(event) => setInputText(event.currentTarget.value)} placeholder="每行一个 .pdf 或目录" value={inputText} />
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
            <span>操作</span>
            <select disabled={running} onChange={(event) => setAction(event.currentTarget.value)} value={action}>
              {actionOptions.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field-block file-path-field">
            <span>输出目录</span>
            <div className="path-input-row">
              <input disabled={running} onChange={(event) => setOutputDir(event.currentTarget.value)} value={outputDir} />
              <button className="path-pick-button" disabled={running} onClick={chooseOutputDir} type="button">
                选择
              </button>
            </div>
          </label>
        </div>
      </div>

      <div className="editor-grid file-editor-grid">
        <div className="file-mode-card compact-card">
          <span className="field-label">拆分 / 转图片</span>
          <div className="mini-form-grid">
            <label className="field-block">
              <span>页码范围</span>
              <input disabled={running || action !== "split"} onChange={(event) => setPageRanges(event.currentTarget.value)} placeholder="1-3,5" value={pageRanges} />
            </label>
            <label className="field-block">
              <span>DPI</span>
              <input disabled={running || action !== "images"} onChange={(event) => setDpi(event.currentTarget.value)} value={dpi} />
            </label>
          </div>
        </div>

        <div className="file-mode-card compact-card">
          <span className="field-label">图片 / 文本导出</span>
          <div className="mini-form-grid">
            <label className="field-block">
              <span>图片格式</span>
              <select disabled={running || action !== "images"} onChange={(event) => setImageFormat(event.currentTarget.value)} value={imageFormat}>
                <option value="png">png</option>
                <option value="jpg">jpg</option>
                <option value="webp">webp</option>
              </select>
            </label>
            <label className="field-block">
              <span>文本格式</span>
              <select disabled={running || action !== "text"} onChange={(event) => setTextExportFormat(event.currentTarget.value)} value={textExportFormat}>
                <option value="txt">txt</option>
                <option value="docx">docx</option>
              </select>
            </label>
          </div>
          <label className="check-row">
            <input checked={ocrFallback} disabled={running || action !== "text"} onChange={(event) => setOcrFallback(event.currentTarget.checked)} type="checkbox" />
            <span>文字层为空时启用 OCR</span>
          </label>
          <p className="muted">{ocrStatus}</p>
        </div>
      </div>

      <div className="actions-row">
        <div className="action-hint">合并需要至少两个 PDF；拆分、转图、提取文本只处理单个 PDF。</div>
        <div className="button-cluster">
          <button className="ghost-button" disabled={running || (!files.length && !results.length && !error)} onClick={clearAll} type="button">
            清空结果
          </button>
          <button className="primary-button" disabled={!canRun} onClick={handleRun} type="button">
            {running ? "运行中..." : "开始处理"}
          </button>
        </div>
      </div>

      <div className="editor-grid file-editor-grid">
        <div className="result-card">
          <span>已识别 PDF</span>
          <strong>{files.length ? `${files.length} 个` : "等待扫描"}</strong>
          <p>{files[0]?.name || "可直接执行，sidecar 会再次按旧规则收集 PDF"}</p>
        </div>
        <div className="result-card">
          <span>输出结果</span>
          <strong>{results.length ? `${results.length} 个` : "暂无"}</strong>
          <p>{results[0]?.output || "输出路径会显示在这里"}</p>
        </div>
      </div>

      {results.length ? (
        <section className="table-panel">
          <div className="panel-title">PDF outputs</div>
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

export default PdfToolsTool;
