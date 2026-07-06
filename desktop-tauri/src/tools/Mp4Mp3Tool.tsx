import { useState } from "react";
import type { DialogFilter, ToolResult } from "../api/tauri";
import { ActionBar, DirectoryPickerRow, MultiPathInput, ResultCards, RuntimeLogPanel, ToolHeading } from "../features/tools/components/CommonToolParts";
import { useLegacyBatchTool } from "../features/tools/hooks/useLegacyBatchTool";
import { uiText } from "../uiText";

type VideoItem = Record<string, string>;

const mp4Filters: DialogFilter[] = [{ name: "MP4 videos", extensions: ["mp4"] }];

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
  const [overwrite, setOverwrite] = useState(true);
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
    chooseFiles: chooseMp4Files,
    chooseInputDir,
    chooseOutputDir,
  } = useLegacyBatchTool<VideoItem>({
    toolId: "mp4mp3",
    initialOutputDir,
    parseFiles: resultFiles,
    parseResults: resultRows,
    fileTitle: "选择 MP4 文件",
    fileFilters: mp4Filters,
    inputDirTitle: "选择 MP4 目录",
    outputDirTitle: "选择 MP3 输出目录",
    listFoundLabel: (count) => `发现 ${count} 个 MP4 文件`,
    listTargetLabel: "MP4",
    convertTargetLabel: "文件",
    convertPayload: ({ paths, outputDir }) => ({
      paths,
      output_dir: outputDir,
      overwrite,
    }),
  });

  return (
    <div className="mp4mp3-tool">
      <ToolHeading
        eyebrow="Legacy audio extractor"
        title="MP4 转 MP3"
        statusLabel=""
      />

      <div className="editor-grid">
        <MultiPathInput
          label="输入 MP4 或目录"
          countLabel={uiText.common.pathCount(paths.length)}
          value={inputText}
          disabled={running}
          placeholder={"E:\\videos\\clip.mp4\nE:\\video-folder"}
          onChange={setInputText}
          actions={
            <>
              <button className="path-pick-button" disabled={running} onClick={chooseMp4Files} type="button">文件</button>
              <button className="path-pick-button" disabled={running} onClick={chooseInputDir} type="button">目录</button>
            </>
          }
        />

        <div className="file-mode-card compact-card">
          <DirectoryPickerRow
            label="输出目录"
            value={outputDir}
            disabled={running}
            onChange={setOutputDir}
            onPick={chooseOutputDir}
          />
          <details className="direct-advanced-options">
            <summary>高级选项</summary>
            <div className="field-button-row">
              <label className="check-row">
                <input checked={overwrite} disabled={running} onChange={(event) => setOverwrite(event.currentTarget.checked)} type="checkbox" />
                覆盖同名 MP3
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
            value: files.length ? `${files.length} 个视频` : "等待扫描",
            detail: files[0]?.path || "显示支持的 MP4 输入",
          },
          {
            label: "转换结果",
            value: results.length ? `${results.length} 个 MP3` : "等待转换",
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

export default Mp4Mp3Tool;
