import { useEffect, useRef, useState } from "react";
import { pickDirectory, runTool, type ToolResult, type ToolSettings } from "../api/tauri";
import { uiText } from "../uiText";

const LEGACY_DEFAULT_PREFIX = "\u6279\u91cf\u547d\u540d";
const legacyGroupModes: Record<string, string> = {
  "\u6309\u540e\u7f00": "suffix",
  "\u6309\u7c7b\u578b": "type",
  "\u5168\u6587\u4ef6": "all",
};
const legacySortModes: Record<string, string> = {
  "\u6309\u547d\u540d": "name",
  "\u4fee\u6539\u65e5\u671f": "mtime",
  "\u6587\u4ef6\u5927\u5c0f": "size",
};
const legacySortOrders: Record<string, string> = {
  "\u4ece\u5c0f\u5230\u5927": "asc",
  "\u4ece\u5927\u5230\u5c0f": "desc",
};

function initialChoice(value: unknown, labels: Record<string, string>, fallback: string): string {
  if (typeof value !== "string") {
    return fallback;
  }
  if (Object.values(labels).includes(value)) {
    return value;
  }
  return labels[value] ?? fallback;
}

const groupOptions = [
  { value: "suffix", label: "按后缀分组" },
  { value: "type", label: "按类型分组" },
  { value: "all", label: "全文件" },
];

const sortOptions = [
  { value: "name", label: "按命名" },
  { value: "mtime", label: "按修改时间" },
  { value: "size", label: "按大小" },
];

const orderOptions = [
  { value: "asc", label: "从小到大" },
  { value: "desc", label: "从大到小" },
];

function errorText(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return typeof error === "string" ? error : JSON.stringify(error);
}

function resultPlan(result: ToolResult): Array<Record<string, string | number | boolean>> {
  return result.plan ?? result.data?.plan ?? [];
}

function resultRows(result: ToolResult): Array<Record<string, string | number | boolean>> {
  return result.results ?? result.data?.results ?? [];
}

function resultTotal(result: ToolResult): number {
  return Number(result.total_files ?? result.data?.total_files ?? 0);
}

function BatchRenameTool({ initialSettings = {} }: { initialSettings?: ToolSettings }) {
  const didApplyInitial = useRef(false);
  const [folderPath, setFolderPath] = useState(initialSettings.input_dir ?? "");
  const [prefix, setPrefix] = useState(initialSettings.prefix ?? LEGACY_DEFAULT_PREFIX);
  const [groupMode, setGroupMode] = useState(initialChoice(initialSettings.group_mode, legacyGroupModes, "suffix"));
  const [sortMode, setSortMode] = useState(initialChoice(initialSettings.sort_mode, legacySortModes, "name"));
  const [sortOrder, setSortOrder] = useState(initialChoice(initialSettings.sort_order, legacySortOrders, "asc"));
  const [plan, setPlan] = useState<Array<Record<string, string | number | boolean>>>([]);
  const [results, setResults] = useState<Array<Record<string, string | number | boolean>>>([]);
  const [totalFiles, setTotalFiles] = useState(0);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const canPreview = !running && Boolean(folderPath && prefix.trim());
  const canRename = canPreview && plan.length > 0;

  useEffect(() => {
    if (didApplyInitial.current || !Object.keys(initialSettings).length) {
      return;
    }
    setFolderPath((current) => current || initialSettings.input_dir || "");
    setPrefix((current) => (current === LEGACY_DEFAULT_PREFIX ? initialSettings.prefix || current : current));
    setGroupMode((current) => (current === "suffix" ? initialChoice(initialSettings.group_mode, legacyGroupModes, current) : current));
    setSortMode((current) => (current === "name" ? initialChoice(initialSettings.sort_mode, legacySortModes, current) : current));
    setSortOrder((current) => (current === "asc" ? initialChoice(initialSettings.sort_order, legacySortOrders, current) : current));
    didApplyInitial.current = true;
  }, [initialSettings]);

  async function chooseFolder() {
    const path = await pickDirectory({ title: "选择批量命名目录" });
    if (path) {
      setFolderPath(path);
    }
  }

  function payload() {
    return {
      folder_path: folderPath,
      prefix,
      group_mode: groupMode,
      sort_mode: sortMode,
      sort_order: sortOrder,
    };
  }

  async function handlePreview() {
    if (!canPreview) {
      return;
    }
    setRunning(true);
    setError("");
    setResults([]);
    setLogs((items) => ["开始生成命名预览", ...items].slice(0, 5));
    try {
      const result = await runTool("batchrename", {
        task_id: `batchrename-preview-${Date.now()}`,
        action: "preview",
        payload: payload(),
      });
      const nextPlan = resultPlan(result);
      setPlan(nextPlan);
      setTotalFiles(resultTotal(result));
      setLogs((items) => [`预览完成：${nextPlan.length} 个文件`, ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`预览失败：${message}`, ...items].slice(0, 5));
    } finally {
      setRunning(false);
    }
  }

  async function handleRename() {
    if (!canRename) {
      return;
    }
    setRunning(true);
    setError("");
    setLogs((items) => ["开始执行批量命名", ...items].slice(0, 5));
    try {
      const result = await runTool("batchrename", {
        task_id: `batchrename-rename-${Date.now()}`,
        action: "rename",
        payload: payload(),
      });
      const rows = resultRows(result);
      setResults(rows);
      setPlan([]);
      setLogs((items) => [`命名完成：${rows.length} 个文件`, ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`命名失败：${message}`, ...items].slice(0, 5));
    } finally {
      setRunning(false);
    }
  }

  function clearAll() {
    setPlan([]);
    setResults([]);
    setTotalFiles(0);
    setError("");
    setLogs([]);
  }

  return (
    <div className="batchrename-tool">
      <div className="tool-heading">
        <div>
          <p className="eyebrow">Legacy batch rename</p>
          <h2>批量命名</h2>
          <p>预览后批量重命名。</p>
        </div>
        <span className="settings-mode-pill">{plan.length ? "已预览" : "待预览"}</span>
      </div>

      <div className="editor-grid">
        <div className="file-mode-card compact-card">
          <label className="field-block file-path-field">
            <span>文件夹</span>
            <div className="path-input-row">
              <input disabled={running} onChange={(event) => setFolderPath(event.currentTarget.value)} placeholder="E:\\files" value={folderPath} />
              <button className="path-pick-button" disabled={running} onClick={chooseFolder} type="button">
                选择
              </button>
            </div>
          </label>
          <label className="field-block">
            <span>命名前缀</span>
            <input disabled={running} onChange={(event) => setPrefix(event.currentTarget.value)} value={prefix} />
          </label>
        </div>

        <div className="file-mode-card compact-card">
          <label className="field-block">
            <span>分组方式</span>
            <select disabled={running} onChange={(event) => setGroupMode(event.currentTarget.value)} value={groupMode}>
              {groupOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field-block">
            <span>排序方式</span>
            <select disabled={running} onChange={(event) => setSortMode(event.currentTarget.value)} value={sortMode}>
              {sortOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field-block">
            <span>排序方向</span>
            <select disabled={running} onChange={(event) => setSortOrder(event.currentTarget.value)} value={sortOrder}>
              {orderOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="actions-row">
        <div className="action-hint">预览不会改动文件；执行前请确认目标名。</div>
        <div className="button-cluster">
          <button className="ghost-button" disabled={running || (!plan.length && !results.length && !error)} onClick={clearAll} type="button">
            清空
          </button>
          <button className="ghost-button" disabled={!canPreview} onClick={handlePreview} type="button">
            预览
          </button>
          <button className="primary-button" disabled={!canRename} onClick={handleRename} type="button">
            {running ? "运行中" : "命名"}
          </button>
        </div>
      </div>

      <div className="editor-grid file-editor-grid">
        <div className="result-card">
          <span>文件数量</span>
          <strong>{totalFiles || plan.length || results.length || "等待预览"}</strong>
          <p>{folderPath || "\u9009\u62e9\u8981\u5904\u7406\u7684\u76ee\u5f55"}</p>
        </div>
        <div className="result-card">
          <span>执行结果</span>
          <strong>{results.length ? `${results.length} 个文件` : plan.length ? `${plan.length} 条计划` : "暂无"}</strong>
          <p>{results[0]?.target_name || plan[0]?.target_name || "结果会显示在这里"}</p>
        </div>
      </div>

      {(plan.length || results.length) ? (
        <section className="table-panel">
          <div className="panel-title">{results.length ? uiText.common.renameResults : uiText.common.previewPlan}</div>
          <div className="result-list">
            {(results.length ? results : plan).map((row, index) => (
              <div className="result-row" key={`${row.source_name}-${row.target_name}-${index}`}>
                <span>{String(row.source_name ?? row.source ?? "")}</span>
                <strong>{String(row.target_name ?? "")}</strong>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="log-panel" aria-label="运行日志">
        <div>
          <div className="panel-title">{uiText.common.runtime}</div>
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

export default BatchRenameTool;
