import { useEffect, useMemo, useState } from "react";
import { pickDirectory, pickFiles, type DialogFilter, runTool, type ToolResult } from "../api/tauri";

type VideoItem = Record<string, string>;

const mp4Filters: DialogFilter[] = [{ name: "MP4 videos", extensions: ["mp4"] }];

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

function resultFiles(result: ToolResult): VideoItem[] {
  return (result.files ?? result.data?.files ?? []).map((row) => ({
    path: String(row.path ?? ""),
    name: String(row.name ?? ""),
  }));
}

function resultRows(result: ToolResult): Array<{ source: string; output: string }> {
  return (result.results ?? result.data?.results ?? []).map((row) => ({
    source: String(row.source ?? ""),
    output: String(row.output ?? ""),
  }));
}

function Mp4Mp3Tool({ initialOutputDir = "" }: { initialOutputDir?: string }) {
  const [inputText, setInputText] = useState("");
  const [outputDir, setOutputDir] = useState(initialOutputDir);
  const [overwrite, setOverwrite] = useState(true);
  const [available, setAvailable] = useState<boolean | null>(null);
  const [backendMessage, setBackendMessage] = useState("");
  const [files, setFiles] = useState<VideoItem[]>([]);
  const [results, setResults] = useState<Array<{ source: string; output: string }>>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const paths = useMemo(() => splitPaths(inputText), [inputText]);
  const canList = !running && paths.length > 0;
  const canConvert = !running && paths.length > 0 && Boolean(outputDir);

  useEffect(() => {
    if (!initialOutputDir) {
      return;
    }
    setOutputDir((current) => current || initialOutputDir);
  }, [initialOutputDir]);
  const backendLabel = available === null ? "检测中" : available ? "ffmpeg 可用" : "缺少 ffmpeg";

  useEffect(() => {
    let cancelled = false;
    runTool("mp4mp3", { task_id: `mp4mp3-probe-${Date.now()}`, action: "probe", payload: {} })
      .then((result) => {
        if (cancelled) {
          return;
        }
        setAvailable(Boolean(result.available ?? result.data?.available));
        setBackendMessage(String(result.message ?? result.data?.message ?? ""));
      })
      .catch((caught) => {
        if (cancelled) {
          return;
        }
        setAvailable(false);
        setBackendMessage(errorText(caught));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function chooseMp4Files() {
    const picked = await pickFiles({ title: "选择 MP4 文件", filters: mp4Filters });
    if (picked?.length) {
      setInputText((current) => [...splitPaths(current), ...picked].join("\n"));
    }
  }

  async function chooseInputDir() {
    const path = await pickDirectory({ title: "选择 MP4 目录" });
    if (path) {
      setInputText((current) => [...splitPaths(current), path].join("\n"));
    }
  }

  async function chooseOutputDir() {
    const path = await pickDirectory({ title: "选择 MP3 输出目录" });
    if (path) {
      setOutputDir(path);
    }
  }

  async function handleList() {
    if (!canList) {
      return;
    }
    setRunning(true);
    setError("");
    setFiles([]);
    setResults([]);
    setLogs((items) => [`扫描 MP4：${paths.length} 个路径`, ...items].slice(0, 5));
    try {
      const result = await runTool("mp4mp3", {
        task_id: `mp4mp3-list-${Date.now()}`,
        action: "list",
        payload: { paths },
      });
      const nextFiles = resultFiles(result);
      setFiles(nextFiles);
      setLogs((items) => [`发现 ${nextFiles.length} 个 MP4 文件`, ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`扫描失败：${message}`, ...items].slice(0, 5));
    } finally {
      setRunning(false);
    }
  }

  async function handleConvert() {
    if (!canConvert) {
      return;
    }
    setRunning(true);
    setError("");
    setResults([]);
    setLogs((items) => [`开始转换：${paths.length} 个路径`, ...items].slice(0, 5));
    try {
      const result = await runTool("mp4mp3", {
        task_id: `mp4mp3-convert-${Date.now()}`,
        action: "convert",
        payload: {
          paths,
          output_dir: outputDir,
          overwrite,
        },
      });
      const rows = resultRows(result);
      setResults(rows);
      setLogs((items) => [`转换完成：${rows.length} 个文件`, ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`转换失败：${message}`, ...items].slice(0, 5));
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
    <div className="mp4mp3-tool">
      <div className="tool-heading">
        <div>
          <p className="eyebrow">Legacy audio extractor</p>
          <h2>MP4 转 MP3</h2>
          <p>复用旧版 audio-extractor converter，通过 ffmpeg 抽取视频音频，不在前端重写转换逻辑。</p>
        </div>
        <span className={`settings-mode-pill ${available ? "ready-pill" : ""}`}>{backendLabel}</span>
      </div>

      {backendMessage ? <div className={available ? "info-box" : "error-box"}>{backendMessage}</div> : null}

      <div className="editor-grid">
        <label className="field-block">
          <span>
            输入 MP4 或目录
            <small>{paths.length} paths</small>
          </span>
          <textarea
            disabled={running}
            onChange={(event) => setInputText(event.currentTarget.value)}
            placeholder={"E:\\videos\\clip.mp4\nE:\\video-folder"}
            value={inputText}
          />
          <div className="field-button-row">
            <button className="path-pick-button" disabled={running} onClick={chooseMp4Files} type="button">
              选择文件
            </button>
            <button className="path-pick-button" disabled={running} onClick={chooseInputDir} type="button">
              选择目录
            </button>
          </div>
        </label>

        <div className="file-mode-card compact-card">
          <label className="field-block file-path-field">
            <span>输出目录</span>
            <div className="path-input-row">
              <input disabled={running} onChange={(event) => setOutputDir(event.currentTarget.value)} placeholder="E:\\output" value={outputDir} />
              <button className="path-pick-button" disabled={running} onClick={chooseOutputDir} type="button">
                选择
              </button>
            </div>
          </label>
          <label className="check-row">
            <input checked={overwrite} disabled={running} onChange={(event) => setOverwrite(event.currentTarget.checked)} type="checkbox" />
            覆盖同名 MP3
          </label>
        </div>
      </div>

      <div className="actions-row">
        <div className="action-hint">输出命名沿用旧版规则：每个 MP4 输出为同名 MP3。</div>
        <div className="button-cluster">
          <button className="ghost-button" disabled={running || (!files.length && !results.length && !error)} onClick={clearAll} type="button">
            清空结果
          </button>
          <button className="ghost-button" disabled={!canList} onClick={handleList} type="button">
            扫描 MP4
          </button>
          <button className="primary-button" disabled={!canConvert} onClick={handleConvert} type="button">
            {running ? "运行中..." : "开始转换"}
          </button>
        </div>
      </div>

      <div className="editor-grid file-editor-grid">
        <div className="result-card">
          <span>扫描结果</span>
          <strong>{files.length ? `${files.length} 个视频` : "等待扫描"}</strong>
          <p>{files[0]?.path || "显示支持的 MP4 输入"}</p>
        </div>
        <div className="result-card">
          <span>转换结果</span>
          <strong>{results.length ? `${results.length} 个 MP3` : "等待转换"}</strong>
          <p>{results[0]?.output || "输出文件路径会显示在这里"}</p>
        </div>
      </div>

      {(files.length || results.length) ? (
        <section className="table-panel">
          <div className="panel-title">{results.length ? "Converted files" : "Detected files"}</div>
          <div className="result-list">
            {results.length
              ? results.map((row) => (
                  <div className="result-row" key={`${row.source}-${row.output}`}>
                    <span>{row.source}</span>
                    <strong>{row.output}</strong>
                  </div>
                ))
              : files.map((file) => (
                  <div className="result-row" key={file.path}>
                    <span>{file.name}</span>
                    <strong>{file.size} bytes</strong>
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

export default Mp4Mp3Tool;
