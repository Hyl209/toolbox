import { useEffect, useMemo, useState } from "react";
import { pickDirectory, pickFiles, type DialogFilter, runTool, type ToolResult } from "../api/tauri";
import { ActionBar, DirectoryPickerRow, MultiPathInput, ResultCards, RuntimeLogPanel, ToolHeading } from "../features/tools/components/CommonToolParts";
import { uiText } from "../uiText";

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
      <ToolHeading
        eyebrow="Legacy PDF tools"
        title="PDF 工具"
        statusLabel={actionOptions.find((item) => item.value === action)?.label ?? action}
      />

      <div className="editor-grid">
        <div className="file-mode-card compact-card">
          <MultiPathInput
            label="PDF 输入路径"
            countLabel={uiText.common.pathCount(paths.length)}
            value={inputText}
            disabled={running}
            placeholder="每行一个 .pdf 或目录"
            onChange={setInputText}
          />
          <div className="button-cluster">
            <button className="ghost-button" disabled={running} onClick={chooseFiles} type="button">文件</button>
            <button className="ghost-button" disabled={!canList} onClick={handleList} type="button">扫描</button>
          </div>
        </div>

        <div className="file-mode-card compact-card">
          <label className="field-block">
            <span>操作</span>
            <select disabled={running} onChange={(event) => setAction(event.currentTarget.value)} value={action}>
              {actionOptions.map((item) => (
                <option key={item.value} value={item.value}>{item.label}</option>
              ))}
            </select>
          </label>
          <DirectoryPickerRow label="输出目录" value={outputDir} disabled={running} onChange={setOutputDir} onPick={chooseOutputDir} />
          <details className="direct-advanced-options">
            <summary>高级选项</summary>
            <div className="tool-result-grid">
              <label className="field-block">
                <span>页码范围（拆分）</span>
                <input disabled={running || action !== "split"} onChange={(event) => setPageRanges(event.currentTarget.value)} placeholder="1-3,5" value={pageRanges} />
              </label>
              <label className="field-block">
                <span>DPI（转图片）</span>
                <input disabled={running || action !== "images"} onChange={(event) => setDpi(event.currentTarget.value)} value={dpi} />
              </label>
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
              <label className="check-row">
                <input checked={ocrFallback} disabled={running || action !== "text"} onChange={(event) => setOcrFallback(event.currentTarget.checked)} type="checkbox" />
                <span>文字层为空时启用 OCR</span>
              </label>
            </div>
          </details>
        </div>
      </div>

      <ActionBar
        secondary={<button className="ghost-button" disabled={running || (!files.length && !results.length && !error)} onClick={clearAll} type="button">清空</button>}
        primary={<button className="primary-button" disabled={!canRun} onClick={handleRun} type="button">{running ? "运行中" : "处理"}</button>}
      />

      <ResultCards
        cards={[
          {
            label: "已识别 PDF",
            value: files.length ? `${files.length} 个` : "等待扫描",
            detail: String(files[0]?.name ?? "可直接执行，sidecar 会再次按旧规则收集 PDF"),
          },
          {
            label: "输出结果",
            value: results.length ? `${results.length} 个` : "暂无",
            detail: results[0]?.output || "输出路径会显示在这里",
          },
        ]}
      />

      {results.length ? (
        <section className="table-panel">
          <div className="panel-title">{uiText.common.pdfOutputs}</div>
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

      <RuntimeLogPanel error={error} logs={logs} />
    </div>
  );
}

export default PdfToolsTool;
