import { useState } from "react";
import type { DialogFilter, ToolResult } from "../api/tauri";
import { ActionBar, DirectoryPickerRow, MultiPathInput, ResultCards, RuntimeLogPanel, ToolHeading } from "../features/tools/components/CommonToolParts";
import { useLegacyBatchTool } from "../features/tools/hooks/useLegacyBatchTool";
import { uiText } from "../uiText";

type ImageItem = Record<string, string>;

const imageFilters: DialogFilter[] = [{ name: "Images", extensions: ["png", "jpg", "jpeg", "webp", "heic"] }];
const targetFormats = ["jpg", "png", "webp", "heic"];

function resultFiles(result: ToolResult): ImageItem[] {
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

function ImageConvertTool({ initialOutputDir = "" }: { initialOutputDir?: string }) {
  const [targetFormat, setTargetFormat] = useState("webp");
  const [quality, setQuality] = useState("90");
  const [targetSizeKb, setTargetSizeKb] = useState("");
  const [preserveAlpha, setPreserveAlpha] = useState(true);
  const [jpgBackground, setJpgBackground] = useState("white");
  const {
    inputText,
    setInputText,
    outputDir,
    setOutputDir,
    files,
    results,
    running,
    error,
    logs,
    paths,
    canList,
    canConvert,
    handleList,
    handleConvert,
    clearAll,
    chooseFiles: chooseImageFiles,
    chooseInputDir,
    chooseOutputDir,
  } = useLegacyBatchTool<ImageItem>({
    toolId: "imageconvert",
    initialOutputDir,
    parseFiles: resultFiles,
    parseResults: resultRows,
    fileTitle: "选择图片文件",
    fileFilters: imageFilters,
    inputDirTitle: "选择图片目录",
    outputDirTitle: "选择输出目录",
    listFoundLabel: (count) => `发现 ${count} 张图片`,
    listTargetLabel: "图片",
    convertTargetLabel: "文件",
    convertPayload: ({ paths, outputDir }) => ({
      paths,
      output_dir: outputDir,
      target_format: targetFormat,
      quality,
      preserve_alpha: preserveAlpha,
      jpg_background: jpgBackground,
      target_size_kb: targetSizeKb,
    }),
  });

  return (
    <div className="imageconvert-tool">
      <ToolHeading
        eyebrow="Legacy image converter"
        title="图片格式互转"
        statusLabel=""
      />

      <div className="editor-grid">
        <MultiPathInput
          label="输入图片或目录"
          countLabel={uiText.common.pathCount(paths.length)}
          value={inputText}
          disabled={running}
          placeholder={"E:\\images\\photo.png\nE:\\images-folder"}
          onChange={setInputText}
          actions={
            <>
              <button className="path-pick-button" disabled={running} onClick={chooseImageFiles} type="button">文件</button>
              <button className="path-pick-button" disabled={running} onClick={chooseInputDir} type="button">目录</button>
            </>
          }
        />

        <div className="file-mode-card compact-card">
          <DirectoryPickerRow label="输出目录" value={outputDir} disabled={running} onChange={setOutputDir} onPick={chooseOutputDir} />
          <label className="field-block">
            <span>目标格式</span>
            <select disabled={running} onChange={(event) => setTargetFormat(event.currentTarget.value)} value={targetFormat}>
              {targetFormats.map((format) => (
                <option key={format} value={format}>{format.toUpperCase()}</option>
              ))}
            </select>
          </label>
          <details className="direct-advanced-options">
            <summary>高级选项</summary>
            <div className="tool-result-grid">
              <label className="field-block">
                <span>质量（1-100）</span>
                <input disabled={running} onChange={(event) => setQuality(event.currentTarget.value)} value={quality} />
              </label>
              <label className="field-block">
                <span>目标体积 KB（可选）</span>
                <input disabled={running} onChange={(event) => setTargetSizeKb(event.currentTarget.value)} placeholder="留空则不限制" value={targetSizeKb} />
              </label>
              <label className="field-block">
                <span>JPG 背景</span>
                <select disabled={running} onChange={(event) => setJpgBackground(event.currentTarget.value)} value={jpgBackground}>
                  <option value="white">白色</option>
                  <option value="black">黑色</option>
                  <option value="transparent">透明按白色处理</option>
                </select>
              </label>
              <label className="check-row">
                <input checked={preserveAlpha} disabled={running} onChange={(event) => setPreserveAlpha(event.currentTarget.checked)} type="checkbox" />
                非 JPG 输出保留透明通道
              </label>
            </div>
          </details>
        </div>
      </div>

      <ActionBar
        secondary={<button className="ghost-button" disabled={running || (!files.length && !results.length && !error)} onClick={clearAll} type="button">清空</button>}
        tertiary={<button className="ghost-button" disabled={!canList} onClick={handleList} type="button">扫描</button>}
        primary={<button className="primary-button" disabled={!canConvert} onClick={() => void handleConvert()} type="button">{running ? "运行中" : "转换"}</button>}
      />

      <ResultCards
        cards={[
          {
            label: "扫描结果",
            value: files.length ? `${files.length} 张图片` : "等待扫描",
            detail: files[0]?.path || "显示支持的 JPG / PNG / WEBP / HEIC 输入",
          },
          {
            label: "转换结果",
            value: results.length ? `${results.length} 个文件` : "等待转换",
            detail: results[0]?.output || "输出文件路径会显示在这里",
          },
        ]}
      />

      {(files.length || results.length) ? (
        <section className="table-panel">
          <div className="panel-title">{results.length ? uiText.common.convertedFiles : uiText.common.detectedFiles}</div>
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
                    <span>{file.name || file.path}</span>
                    <strong>{file.path}</strong>
                  </div>
                ))}
          </div>
        </section>
      ) : null}

      <RuntimeLogPanel error={error} logs={logs} />
    </div>
  );
}

export default ImageConvertTool;
