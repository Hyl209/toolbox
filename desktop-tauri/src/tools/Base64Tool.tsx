import { useEffect, useMemo, useState } from "react";
import { pickDirectory, pickFile, type DialogFilter, runTool } from "../api/tauri";
import { ActionBar, RuntimeLogPanel } from "../features/tools/components/CommonToolParts";
import { errorText, resultPath, resultText } from "../features/tools/utils/toolResult";
import { uiText } from "../uiText";

type TextMode = "encode" | "decode";
type WorkMode = "text" | "file";
type FileMode = "encode_file" | "decode_file";

function actionForTextMode(mode: TextMode): string {
  return mode === "encode" ? "encode_text" : "decode_text";
}

const allFileFilters: DialogFilter[] = [];

function Base64Tool({ initialOutputDir = "" }: { initialOutputDir?: string }) {
  const [workMode, setWorkMode] = useState<WorkMode>("text");
  const [textMode, setTextMode] = useState<TextMode>("encode");
  const [fileMode, setFileMode] = useState<FileMode>("encode_file");
  const [inputText, setInputText] = useState("");
  const [outputText, setOutputText] = useState("");
  const [filePath, setFilePath] = useState("");
  const [outputDir, setOutputDir] = useState(initialOutputDir);
  const [outputName, setOutputName] = useState("output");
  const [dataUrl, setDataUrl] = useState(false);
  const [outputPath, setOutputPath] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const inputStats = useMemo(() => uiText.common.charCount(inputText.length), [inputText.length]);
  const outputStats = useMemo(() => uiText.common.charCount(outputText.length), [outputText.length]);
  const canRunText = Boolean(inputText) && !running;
  const canRunFile = !running && Boolean(outputDir) && Boolean(outputName) && (fileMode === "encode_file" ? Boolean(filePath) : Boolean(inputText));

  useEffect(() => {
    if (!initialOutputDir) {
      return;
    }
    setOutputDir((current) => current || initialOutputDir);
  }, [initialOutputDir]);

  async function handleRunText() {
    if (!canRunText) {
      return;
    }

    const action = actionForTextMode(textMode);
    const taskId = `base64-${textMode}-${Date.now()}`;
    setRunning(true);
    setError("");
    setOutputPath("");
    setLogs((items) => [`开始运行：${action}`, ...items].slice(0, 5));

    try {
      const result = await runTool("base64", {
        task_id: taskId,
        action,
        payload: { text: inputText },
      });
      setOutputText(resultText(result));
      setLogs((items) => ["运行完成", ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`运行失败：${message}`, ...items].slice(0, 5));
    } finally {
      setRunning(false);
    }
  }

  async function handleRunFile() {
    if (!canRunFile) {
      return;
    }

    const taskId = `base64-${fileMode}-${Date.now()}`;
    setRunning(true);
    setError("");
    setOutputPath("");
    setLogs((items) => [`开始运行：${fileMode}`, ...items].slice(0, 5));

    try {
      const result = await runTool("base64", {
        task_id: taskId,
        action: fileMode,
        payload: {
          text: inputText,
          file_path: filePath,
          output_dir: outputDir,
          output_name: outputName,
          data_url: dataUrl,
        },
      });
      const text = resultText(result);
      const path = resultPath(result);
      if (fileMode === "encode_file") {
        setOutputText(text);
      }
      setOutputPath(path);
      setLogs((items) => [path ? `已输出：${path}` : "运行完成", ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`运行失败：${message}`, ...items].slice(0, 5));
    } finally {
      setRunning(false);
    }
  }

  async function copyOutput() {
    if (!outputText) {
      return;
    }
    await navigator.clipboard.writeText(outputText);
    setLogs((items) => ["已复制", ...items].slice(0, 5));
  }

  function clearText() {
    setInputText("");
    setOutputText("");
    setOutputPath("");
    setError("");
  }

  async function chooseSourceFile() {
    const path = await pickFile({ title: "选择要编码的文件", filters: allFileFilters });
    if (path) {
      setFilePath(path);
      if (!outputName || outputName === "output") {
        const name = path.split(/[\/]/).pop()?.replace(/\.[^.]+$/, "");
        setOutputName(name || "output");
      }
    }
  }

  async function chooseOutputDir() {
    const path = await pickDirectory({ title: "选择输出目录" });
    if (path) {
      setOutputDir(path);
    }
  }

  return (
    <div className="base64-tool">
      <div className="tool-heading">
        <div>
          <p className="eyebrow">Base64 converter</p>
          <h2>Base64 编解码</h2>
        </div>
        <div className="mode-switch" role="group" aria-label="Base64 工作模式">
          <button className={workMode === "text" ? "active" : ""} disabled={running} onClick={() => setWorkMode("text")} type="button">
            文本
          </button>
          <button className={workMode === "file" ? "active" : ""} disabled={running} onClick={() => setWorkMode("file")} type="button">
            文件
          </button>
        </div>
      </div>

      {workMode === "text" ? (
        <>
          <div className="mode-switch inline-mode" role="group" aria-label="Base64 文本模式">
            <button className={textMode === "encode" ? "active" : ""} disabled={running} onClick={() => setTextMode("encode")} type="button">
              编码
            </button>
            <button className={textMode === "decode" ? "active" : ""} disabled={running} onClick={() => setTextMode("decode")} type="button">
              解码
            </button>
          </div>

          <div className="editor-grid">
            <label className="field-block">
              <span>
                输入
                <small>{inputStats}</small>
              </span>
              <textarea onChange={(event) => setInputText(event.currentTarget.value)} placeholder="Paste text here" value={inputText} />
            </label>

            <label className="field-block output-field">
              <span>
                输出
                <small>{outputStats}</small>
              </span>
              <textarea placeholder="Result appears here" readOnly value={outputText} />
            </label>
          </div>

          <ActionBar
            secondary={<button className="ghost-button" disabled={running || (!inputText && !outputText)} onClick={clearText} type="button">清空</button>}
            tertiary={<button className="ghost-button" disabled={!outputText} onClick={copyOutput} type="button">复制</button>}
            primary={<button className="primary-button" disabled={!canRunText} onClick={handleRunText} type="button">{running ? "运行中" : "转换"}</button>}
          />
        </>
      ) : (
        <>
          <div className="file-mode-card">
            <div className="mode-switch inline-mode" role="group" aria-label="Base64 文件模式">
              <button className={fileMode === "encode_file" ? "active" : ""} disabled={running} onClick={() => setFileMode("encode_file")} type="button">
                转码
              </button>
              <button className={fileMode === "decode_file" ? "active" : ""} disabled={running} onClick={() => setFileMode("decode_file")} type="button">
                还原
              </button>
            </div>
            <label className="field-block file-path-field">
              <span>源文件路径</span>
              <div className="path-input-row">
                <input disabled={fileMode !== "encode_file" || running} onChange={(event) => setFilePath(event.currentTarget.value)} placeholder="E:\\path\\sample.png" value={filePath} />
                <button className="path-pick-button" disabled={fileMode !== "encode_file" || running} onClick={chooseSourceFile} type="button">
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
              <input disabled={running} onChange={(event) => setOutputName(event.currentTarget.value)} placeholder="output" value={outputName} />
            </label>
            <label className="check-row">
              <input checked={dataUrl} disabled={fileMode !== "encode_file" || running} onChange={(event) => setDataUrl(event.currentTarget.checked)} type="checkbox" />
              输出 Data URL
            </label>
          </div>

          <div className="editor-grid file-editor-grid">
            <label className="field-block">
              <span>
                {fileMode === "encode_file" ? "Base64 输出预览" : "待还原 Base64"}
                <small>{inputStats}</small>
              </span>
              <textarea
                onChange={(event) => setInputText(event.currentTarget.value)}
                placeholder={fileMode === "encode_file" ? "编码后会显示在这里" : "粘贴 Base64 或 Data URL"}
                readOnly={fileMode === "encode_file"}
                value={fileMode === "encode_file" ? outputText : inputText}
              />
            </label>
            <div className="result-card">
              <span>输出路径</span>
              <strong>{outputPath || "等待运行"}</strong>
            </div>
          </div>

          <ActionBar
            secondary={<button className="ghost-button" disabled={running || (!inputText && !outputText && !outputPath)} onClick={clearText} type="button">清空</button>}
            tertiary={<button className="ghost-button" disabled={!outputText} onClick={copyOutput} type="button">复制</button>}
            primary={<button className="primary-button" disabled={!canRunFile} onClick={handleRunFile} type="button">{running ? "运行中" : "处理"}</button>}
          />
        </>
      )}

      <RuntimeLogPanel error={error} logs={logs} />
    </div>
  );
}

export default Base64Tool;
