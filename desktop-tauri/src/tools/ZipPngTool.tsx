import { useEffect, useState } from "react";
import { pickDirectory, pickFile, pickSaveFile, type DialogFilter, runTool, type ToolResult } from "../api/tauri";

type Mode = "disguise" | "recover";

const imageFilters: DialogFilter[] = [{ name: "Images", extensions: ["png", "jpg", "jpeg", "gif", "webp"] }];
const allFileFilters: DialogFilter[] = [];

function errorText(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return typeof error === "string" ? error : JSON.stringify(error);
}

function outputPath(result: ToolResult): string {
  return result.output_path ?? result.data?.output_path ?? "";
}

function embeddedInfo(result: ToolResult): ToolResult["embedded"] {
  return result.embedded ?? result.data?.embedded;
}

function fileStem(path: string, fallback: string): string {
  const name = path.split(/[\\/]/).pop()?.replace(/\.[^.]+$/, "");
  return name || fallback;
}

function ZipPngTool({ initialOutputDir = "" }: { initialOutputDir?: string }) {
  const [mode, setMode] = useState<Mode>("disguise");
  const [coverPath, setCoverPath] = useState("");
  const [payloadPath, setPayloadPath] = useState("");
  const [imagePath, setImagePath] = useState("");
  const [outputDir, setOutputDir] = useState(initialOutputDir);
  const [outputName, setOutputName] = useState("hidden");
  const [recoverOutputPath, setRecoverOutputPath] = useState("");
  const [resultPath, setResultPath] = useState("");
  const [embedded, setEmbedded] = useState<ToolResult["embedded"]>();
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const canRun =
    !running &&
    (mode === "disguise"
      ? Boolean(coverPath && payloadPath && (outputDir || outputName))
      : Boolean(imagePath));

  useEffect(() => {
    if (!initialOutputDir) {
      return;
    }
    setOutputDir((current) => current || initialOutputDir);
  }, [initialOutputDir]);

  async function handleRun() {
    if (!canRun) {
      return;
    }
    setRunning(true);
    setError("");
    setResultPath("");
    setEmbedded(undefined);
    setLogs((items) => [`开始运行：${mode}`, ...items].slice(0, 5));

    try {
      const result = await runTool("zipandpng", {
        task_id: `zipandpng-${mode}-${Date.now()}`,
        action: mode,
        payload:
          mode === "disguise"
            ? {
                cover_path: coverPath,
                payload_path: payloadPath,
                output_dir: outputDir,
                output_name: outputName,
              }
            : {
                image_path: imagePath,
                output_path: recoverOutputPath,
              },
      });
      const path = outputPath(result);
      setResultPath(path);
      setEmbedded(embeddedInfo(result));
      setLogs((items) => [path ? `已输出：${path}` : "运行完成", ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`运行失败：${message}`, ...items].slice(0, 5));
    } finally {
      setRunning(false);
    }
  }

  function clearResult() {
    setResultPath("");
    setEmbedded(undefined);
    setError("");
  }

  async function chooseCover() {
    const path = await pickFile({ title: "选择封面图片", filters: imageFilters });
    if (path) {
      setCoverPath(path);
    }
  }

  async function choosePayload() {
    const path = await pickFile({ title: "选择要伪装的文件", filters: allFileFilters });
    if (path) {
      setPayloadPath(path);
      if (!outputName || outputName === "hidden") {
        setOutputName(fileStem(path, "hidden"));
      }
    }
  }

  async function chooseOutputDir() {
    const path = await pickDirectory({ title: "选择输出目录" });
    if (path) {
      setOutputDir(path);
    }
  }

  async function chooseImage() {
    const path = await pickFile({ title: "选择伪装图片", filters: imageFilters });
    if (path) {
      setImagePath(path);
    }
  }

  async function chooseRecoverOutput() {
    const path = await pickSaveFile({ title: "选择恢复输出文件" });
    if (path) {
      setRecoverOutputPath(path);
    }
  }

  return (
    <div className="zippng-tool">
      <div className="tool-heading">
        <div>
          <p className="eyebrow">Legacy file disguise</p>
          <h2>PNG 伪装</h2>
          <p>复用旧版 file-disguise 后端，把任意单文件附加到 PNG/JPG/GIF/WEBP 封面，并可从伪装图片恢复原文件。</p>
        </div>
        <div className="mode-switch" role="group" aria-label="PNG 伪装模式">
          <button className={mode === "disguise" ? "active" : ""} disabled={running} onClick={() => setMode("disguise")} type="button">
            伪装
          </button>
          <button className={mode === "recover" ? "active" : ""} disabled={running} onClick={() => setMode("recover")} type="button">
            恢复
          </button>
        </div>
      </div>

      <div className="file-mode-card">
        {mode === "disguise" ? (
          <>
            <label className="field-block file-path-field">
              <span>封面图片</span>
              <div className="path-input-row">
                <input disabled={running} onChange={(event) => setCoverPath(event.currentTarget.value)} placeholder="E:\\path\\cover.png" value={coverPath} />
                <button className="path-pick-button" disabled={running} onClick={chooseCover} type="button">
                  选择
                </button>
              </div>
            </label>
            <label className="field-block file-path-field">
              <span>要伪装的文件</span>
              <div className="path-input-row">
                <input disabled={running} onChange={(event) => setPayloadPath(event.currentTarget.value)} placeholder="E:\\path\\secret.zip" value={payloadPath} />
                <button className="path-pick-button" disabled={running} onClick={choosePayload} type="button">
                  选择
                </button>
              </div>
            </label>
            <label className="field-block file-path-field">
              <span>输出目录</span>
              <div className="path-input-row">
                <input disabled={running} onChange={(event) => setOutputDir(event.currentTarget.value)} placeholder="E:\\output" value={outputDir} />
                <button className="path-pick-button" disabled={running} onClick={chooseOutputDir} type="button">
                  选择
                </button>
              </div>
            </label>
            <label className="field-block file-path-field">
              <span>输出文件名</span>
              <input disabled={running} onChange={(event) => setOutputName(event.currentTarget.value)} placeholder="hidden" value={outputName} />
            </label>
          </>
        ) : (
          <>
            <label className="field-block file-path-field">
              <span>伪装图片</span>
              <div className="path-input-row">
                <input disabled={running} onChange={(event) => setImagePath(event.currentTarget.value)} placeholder="E:\\path\\hidden.png" value={imagePath} />
                <button className="path-pick-button" disabled={running} onClick={chooseImage} type="button">
                  选择
                </button>
              </div>
            </label>
            <label className="field-block file-path-field">
              <span>恢复输出路径（可选）</span>
              <div className="path-input-row">
                <input disabled={running} onChange={(event) => setRecoverOutputPath(event.currentTarget.value)} placeholder="留空则按内嵌文件名输出到图片旁边" value={recoverOutputPath} />
                <button className="path-pick-button" disabled={running} onClick={chooseRecoverOutput} type="button">
                  选择
                </button>
              </div>
            </label>
          </>
        )}
      </div>

      <div className="editor-grid file-editor-grid">
        <div className="result-card">
          <span>输出路径</span>
          <strong>{resultPath || "等待运行"}</strong>
          <p>{mode === "disguise" ? "图片封面 + 原始文件载荷" : "从图片中恢复内嵌文件"}</p>
        </div>
        <div className="result-card">
          <span>内嵌信息</span>
          <strong>{embedded?.found ? embedded.filename : "暂无"}</strong>
          <p>{embedded?.found ? `${embedded.image_format ?? "image"} · ${embedded.file_size ?? 0} bytes` : "运行后显示识别结果"}</p>
        </div>
      </div>

      <div className="actions-row">
        <div className="action-hint">{mode === "disguise" ? "任意文件 → 图片伪装" : "伪装图片 → 原始文件"}</div>
        <div className="button-cluster">
          <button className="ghost-button" disabled={running || (!resultPath && !error)} onClick={clearResult} type="button">
            清空结果
          </button>
          <button className="primary-button" disabled={!canRun} onClick={handleRun} type="button">
            {running ? "运行中..." : mode === "disguise" ? "开始伪装" : "开始恢复"}
          </button>
        </div>
      </div>

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

export default ZipPngTool;
