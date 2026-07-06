import { useEffect, useRef, useState } from "react";
import { pickDirectory, runTool, type ToolResult, type ToolSettings } from "../api/tauri";
import { uiText } from "../uiText";

type SameGroup = {
  keeper?: string;
  duplicates?: string[];
  files?: string[];
  match_mode?: string;
  size?: number;
  similarity?: number;
};

type SameResult = ToolResult & {
  root?: string;
  target_dir_name?: string;
  target_dir?: string;
  scanned_files?: number;
  duplicate_group_count?: number;
  duplicate_file_count?: number;
  recursive?: boolean;
  groups?: SameGroup[];
};

function errorText(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return typeof error === "string" ? error : JSON.stringify(error);
}

function dataOf(result: ToolResult): SameResult {
  return (result.data ?? result) as SameResult;
}

function basename(path: string | undefined): string {
  if (!path) {
    return "";
  }
  return path.split(/[\\/]/).pop() ?? path;
}

function SameTool({ initialSettings = {} }: { initialSettings?: ToolSettings }) {
  const didApplyInitial = useRef(false);
  const [folderPath, setFolderPath] = useState(initialSettings.input_dir ?? "");
  const [recursive, setRecursive] = useState(initialSettings.recursive ?? true);
  const [targetDirName, setTargetDirName] = useState("重复文件");
  const [scanResult, setScanResult] = useState<SameResult | null>(null);
  const [results, setResults] = useState<Array<Record<string, string | number | boolean>>>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const canScan = !running && Boolean(folderPath);
  const canMove = canScan && Boolean(scanResult?.duplicate_file_count);
  const groups = scanResult?.groups ?? [];

  useEffect(() => {
    if (didApplyInitial.current || !Object.keys(initialSettings).length) {
      return;
    }
    setFolderPath((current) => current || initialSettings.input_dir || "");
    setRecursive((current) => (current === true ? initialSettings.recursive ?? current : current));
    didApplyInitial.current = true;
  }, [initialSettings]);

  async function chooseFolder() {
    const path = await pickDirectory({ title: "选择重复文件扫描目录" });
    if (path) {
      setFolderPath(path);
    }
  }

  async function handleScan() {
    if (!canScan) {
      return;
    }
    setRunning(true);
    setError("");
    setResults([]);
    setLogs((items) => ["开始扫描重复文件", ...items].slice(0, 5));
    try {
      const result = await runTool("same", {
        task_id: `same-scan-${Date.now()}`,
        action: "scan",
        payload: {
          folder_path: folderPath,
          recursive,
          target_dir_name: targetDirName,
        },
      });
      const data = dataOf(result);
      setScanResult(data);
      setLogs((items) => [`扫描完成：${data.duplicate_group_count ?? 0} 组，${data.duplicate_file_count ?? 0} 个待移动`, ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`扫描失败：${message}`, ...items].slice(0, 5));
    } finally {
      setRunning(false);
    }
  }

  async function handleMove() {
    if (!canMove || !scanResult) {
      return;
    }
    setRunning(true);
    setError("");
    setLogs((items) => ["开始移动重复文件", ...items].slice(0, 5));
    try {
      const result = await runTool("same", {
        task_id: `same-move-${Date.now()}`,
        action: "move",
        payload: {
          folder_path: folderPath,
          scan_result: scanResult,
        },
      });
      const data = dataOf(result);
      const rows = data.results ?? [];
      setResults(rows);
      setLogs((items) => [`移动完成：${data.success_count ?? rows.length} 个成功，${data.fail_count ?? 0} 个失败`, ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`移动失败：${message}`, ...items].slice(0, 5));
    } finally {
      setRunning(false);
    }
  }

  function clearAll() {
    setScanResult(null);
    setResults([]);
    setError("");
    setLogs([]);
  }

  return (
    <div className="same-tool">
      <div className="tool-heading">
        <div>
          <p className="eyebrow">Legacy duplicate finder</p>
          <h2>重复文件</h2>
        </div>
        <span className="settings-mode-pill">{recursive ? "递归扫描" : "仅第一层"}</span>
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
            <span>移动目标目录名</span>
            <input disabled={running} onChange={(event) => setTargetDirName(event.currentTarget.value)} value={targetDirName} />
          </label>
        </div>

        <div className="file-mode-card compact-card">
          <label className="check-row">
            <input checked={recursive} disabled={running} onChange={(event) => setRecursive(event.currentTarget.checked)} type="checkbox" />
            <span>递归扫描子目录</span>
          </label>
        </div>
      </div>

      <div className="actions-row">
        <div className="button-cluster">
          <button className="ghost-button" disabled={running || (!scanResult && !results.length && !error)} onClick={clearAll} type="button">
            清空
          </button>
          <button className="ghost-button" disabled={!canScan} onClick={handleScan} type="button">
            检测
          </button>
          <button className="primary-button" disabled={!canMove} onClick={handleMove} type="button">
            {running ? "运行中" : "移动重复件"}
          </button>
        </div>
      </div>

      <div className="editor-grid file-editor-grid">
        <div className="result-card">
          <span>扫描结果</span>
          <strong>{scanResult ? `${scanResult.duplicate_group_count ?? 0} 组` : "等待扫描"}</strong>
          <p>{scanResult ? `??? ${scanResult.scanned_files ?? 0} ???` : folderPath || "\u9009\u62e9\u8981\u68c0\u6d4b\u7684\u76ee\u5f55"}</p>
        </div>
        <div className="result-card">
          <span>待移动</span>
          <strong>{scanResult ? `${scanResult.duplicate_file_count ?? 0} 个文件` : "暂无"}</strong>
          <p>{scanResult?.target_dir ?? "移动后进入目标目录"}</p>
        </div>
      </div>

      {groups.length ? (
        <section className="table-panel">
          <div className="panel-title">Duplicate groups</div>
          <div className="result-list">
            {groups.map((group, index) => (
              <div className="result-row" key={`${group.keeper}-${index}`}>
                <span>保留 {basename(group.keeper)}</span>
                <strong>移动 {(group.duplicates ?? []).map((item) => basename(item)).join(", ")}</strong>
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
              <div className="result-row" key={`${row.source}-${row.target_path}-${index}`}>
                <span>{basename(String(row.source ?? ""))}</span>
                <strong>{String(row.target_path ?? row.error ?? "")}</strong>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="log-panel" aria-label={uiText.common.runtime}>
        <div>
          <div className="panel-title">{uiText.common.runtime}</div>
          <p className="muted">{uiText.common.recentLocal}</p>
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
            <p className="muted">{uiText.common.noLogs}</p>
          )}
        </div>
      </section>
    </div>
  );
}

export default SameTool;
