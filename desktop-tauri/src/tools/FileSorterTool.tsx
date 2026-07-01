import { useEffect, useMemo, useRef, useState } from "react";
import { pickDirectory, runTool, type ToolResult, type ToolSettings } from "../api/tauri";

const categoryOptions = ["图片", "视频", "音频", "文档", "压缩包", "程序", "其他"];
const resolutionCategories = ["图片", "视频"];
const legacyModes: Record<string, string> = {
  "\u6309\u5927\u7c7b\u5206\u7c7b": "category",
  "\u6309\u5206\u8fa8\u7387\u5206\u7c7b": "resolution",
};

function initialMode(value: unknown): string {
  if (value === "category" || value === "resolution") {
    return value;
  }
  return typeof value === "string" ? legacyModes[value] ?? "category" : "category";
}

function categoriesFromSettings(settings: ToolSettings["categories"] | undefined): string[] {
  return categoryOptions.filter((category) => settings?.[category] ?? true);
}

function errorText(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return typeof error === "string" ? error : JSON.stringify(error);
}

function dataOf(result: ToolResult): ToolResult {
  return result.data ?? result;
}

function rowsOf(result: ToolResult): Array<Record<string, string | number | boolean>> {
  return dataOf(result).results ?? [];
}

function summaryOf(result: ToolResult): ToolResult {
  return dataOf(result).summary ?? dataOf(result);
}

function FileSorterTool({ initialSettings = {} }: { initialSettings?: ToolSettings }) {
  const didApplyInitial = useRef(false);
  const userTouchedRef = useRef(false);
  const [folderPath, setFolderPath] = useState(initialSettings.input_dir ?? "");
  const [mode, setMode] = useState(initialMode(initialSettings.mode));
  const [selectedCategories, setSelectedCategories] = useState<string[]>(() => categoriesFromSettings(initialSettings.categories));
  const [summary, setSummary] = useState<ToolResult | null>(null);
  const [results, setResults] = useState<Array<Record<string, string | number | boolean>>>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const visibleCategories = mode === "resolution" ? resolutionCategories : categoryOptions;
  const canRun = !running && Boolean(folderPath) && selectedCategories.some((item) => visibleCategories.includes(item));
  const selectedTotal = Number(summary?.selected_total_files ?? 0);
  const totalFiles = Number(summary?.total_files ?? 0);
  const countRows = useMemo(() => Object.entries(summary?.category_counts ?? {}).filter(([, count]) => Number(count) > 0), [summary]);

  useEffect(() => {
    if (didApplyInitial.current || userTouchedRef.current || !Object.keys(initialSettings).length) {
      return;
    }
    setFolderPath((current) => current || initialSettings.input_dir || "");
    setMode((current) => (current === "category" ? initialMode(initialSettings.mode) : current));
    setSelectedCategories(categoriesFromSettings(initialSettings.categories));
    didApplyInitial.current = true;
  }, [initialSettings]);

  function payload() {
    return {
      folder_path: folderPath,
      mode,
      selected_categories: selectedCategories.filter((item) => visibleCategories.includes(item)),
    };
  }

  async function chooseFolder() {
    const path = await pickDirectory({ title: "选择文件分类目录" });
    if (path) {
      userTouchedRef.current = true;
      setFolderPath(path);
    }
  }

  function toggleCategory(category: string) {
    userTouchedRef.current = true;
    setSelectedCategories((items) =>
      items.includes(category) ? items.filter((item) => item !== category) : [...items, category],
    );
  }

  function handleMode(nextMode: string) {
    userTouchedRef.current = true;
    setMode(nextMode);
    if (nextMode === "resolution") {
      setSelectedCategories((items) => items.filter((item) => resolutionCategories.includes(item)));
    }
  }

  async function handlePreview() {
    if (!canRun) {
      return;
    }
    setRunning(true);
    setError("");
    setResults([]);
    setLogs((items) => ["开始扫描分类摘要", ...items].slice(0, 5));
    try {
      const result = await runTool("filesorter", {
        task_id: `filesorter-preview-${Date.now()}`,
        action: "preview",
        payload: payload(),
      });
      const nextSummary = summaryOf(result);
      setSummary(nextSummary);
      setLogs((items) => [`扫描完成：${nextSummary.selected_total_files ?? 0} 个文件待分类`, ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`扫描失败：${message}`, ...items].slice(0, 5));
    } finally {
      setRunning(false);
    }
  }

  async function handleSort() {
    if (!canRun) {
      return;
    }
    setRunning(true);
    setError("");
    setLogs((items) => ["开始执行文件分类移动", ...items].slice(0, 5));
    try {
      const result = await runTool("filesorter", {
        task_id: `filesorter-sort-${Date.now()}`,
        action: "sort",
        payload: payload(),
      });
      const data = dataOf(result);
      const rows = rowsOf(result);
      setResults(rows);
      setSummary(data.summary ?? summary);
      setLogs((items) => [`分类完成：${data.success_count ?? rows.length} 个成功，${data.fail_count ?? 0} 个失败`, ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`分类失败：${message}`, ...items].slice(0, 5));
    } finally {
      setRunning(false);
    }
  }

  function clearAll() {
    setSummary(null);
    setResults([]);
    setError("");
    setLogs([]);
  }

  return (
    <div className="filesorter-tool">
      <div className="tool-heading">
        <div>
          <p className="eyebrow">Legacy file sorter</p>
          <h2>文件分类</h2>
          <p>复用旧版 file-sorter converter：先扫描目录第一层，再按大类或分辨率移动到对应文件夹。</p>
        </div>
        <span className="settings-mode-pill">{mode === "resolution" ? "按分辨率" : "按大类"}</span>
      </div>

      <div className="editor-grid">
        <div className="file-mode-card compact-card">
          <label className="field-block file-path-field">
            <span>文件夹</span>
            <div className="path-input-row">
              <input
                disabled={running}
                onChange={(event) => {
                  userTouchedRef.current = true;
                  setFolderPath(event.currentTarget.value);
                }}
                placeholder="E:\\files"
                value={folderPath}
              />
              <button className="path-pick-button" disabled={running} onClick={chooseFolder} type="button">
                选择
              </button>
            </div>
          </label>
          <label className="field-block">
            <span>分类模式</span>
            <select disabled={running} onChange={(event) => handleMode(event.currentTarget.value)} value={mode}>
              <option value="category">按大类分类</option>
              <option value="resolution">按分辨率分类</option>
            </select>
          </label>
        </div>

        <div className="file-mode-card compact-card">
          <span className="field-label">分类范围</span>
          <div className="chip-grid">
            {visibleCategories.map((category) => (
              <button
                className={`filter-chip ${selectedCategories.includes(category) ? "active" : ""}`}
                disabled={running}
                key={category}
                onClick={() => toggleCategory(category)}
                type="button"
              >
                {category}
              </button>
            ))}
          </div>
          <p className="muted">未勾选的文件保持原位；执行会真实移动文件。</p>
        </div>
      </div>

      <div className="actions-row">
        <div className="action-hint">预览只读取摘要；执行会创建分类目录并移动文件。</div>
        <div className="button-cluster">
          <button className="ghost-button" disabled={running || (!summary && !results.length && !error)} onClick={clearAll} type="button">
            清空结果
          </button>
          <button className="ghost-button" disabled={!canRun} onClick={handlePreview} type="button">
            扫描预览
          </button>
          <button className="primary-button" disabled={!canRun} onClick={handleSort} type="button">
            {running ? "运行中..." : "执行分类"}
          </button>
        </div>
      </div>

      <div className="editor-grid file-editor-grid">
        <div className="result-card">
          <span>目录文件</span>
          <strong>{summary ? `${selectedTotal} / ${totalFiles}` : "等待扫描"}</strong>
          <p>{folderPath || "选择旧版文件分类要处理的目录"}</p>
        </div>
        <div className="result-card">
          <span>分类结果</span>
          <strong>{results.length ? `${results.length} 条记录` : "暂无"}</strong>
          <p>{results[0]?.target_name || "结果会显示目标分类目录和文件名"}</p>
        </div>
      </div>

      {countRows.length ? (
        <section className="table-panel">
          <div className="panel-title">Category summary</div>
          <div className="result-list">
            {countRows.map(([category, count]) => (
              <div className="result-row" key={category}>
                <span>{category}</span>
                <strong>{count}</strong>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {results.length ? (
        <section className="table-panel">
          <div className="panel-title">Move results</div>
          <div className="result-list">
            {results.map((row, index) => (
              <div className="result-row" key={`${row.source_name}-${row.target_name}-${index}`}>
                <span>{String(row.source_name ?? row.source ?? "")}</span>
                <strong>{String(row.group_label ?? row.category ?? "")}\\{String(row.target_name ?? "")}</strong>
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

export default FileSorterTool;
