import { useState } from "react";
import type { DialogFilter, ToolResult } from "../api/tauri";
import { ActionBar, DirectoryPickerRow, MultiPathInput, ResultCards, RuntimeLogPanel, ToolHeading } from "../features/tools/components/CommonToolParts";
import { useLegacyBatchTool } from "../features/tools/hooks/useLegacyBatchTool";
import { uiText } from "../uiText";

type SongItem = Record<string, string>;

const ncmFilters: DialogFilter[] = [{ name: "NCM files", extensions: ["ncm"] }];

function resultFiles(result: ToolResult): SongItem[] {
  return (result.files ?? result.data?.files ?? []).map((row) => ({
    path: String(row.path ?? ""),
    name: String(row.name ?? ""),
    title: String(row.title ?? ""),
    artist: String(row.artist ?? ""),
  }));
}

function resultRows(result: ToolResult): Array<{ source: string; output: string }> {
  return (result.results ?? result.data?.results ?? []).map((row) => ({
    source: String(row.source ?? ""),
    output: String(row.output ?? ""),
  }));
}

function MusicTool({ initialOutputDir = "" }: { initialOutputDir?: string }) {
  const [overwrite, setOverwrite] = useState(false);
  const [deleteSource, setDeleteSource] = useState(false);
  const {
    inputText,
    setInputText,
    outputDir,
    setOutputDir,
    files: songs,
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
    chooseFiles: chooseNcmFiles,
    chooseInputDir,
    chooseOutputDir,
  } = useLegacyBatchTool<SongItem>({
    toolId: "music",
    initialOutputDir,
    parseFiles: resultFiles,
    parseResults: resultRows,
    fileTitle: "选择 NCM 文件",
    fileFilters: ncmFilters,
    inputDirTitle: "选择 NCM 文件夹",
    outputDirTitle: "选择 MP3 输出目录",
    listFoundLabel: (count) => `发现 ${count} 个 NCM 文件`,
    listTargetLabel: "NCM",
    convertTargetLabel: "文件",
    convertPayload: ({ paths, outputDir }) => ({
      paths,
      output_dir: outputDir,
      overwrite,
      delete_source: deleteSource,
    }),
  });

  return (
    <div className="music-tool">
      <ToolHeading
        eyebrow="Legacy NCM converter"
        title="NCM 转 MP3"
        description="将 NCM 转为 MP3。"
        statusLabel=""
      />

      <div className="editor-grid">
        <MultiPathInput
          label="输入路径"
          countLabel={uiText.common.pathCount(paths.length)}
          value={inputText}
          disabled={running}
          placeholder={"E:\\music\\song.ncm\nE:\\music-folder"}
          onChange={setInputText}
          actions={
            <>
              <button className="path-pick-button" disabled={running} onClick={chooseNcmFiles} type="button">文件</button>
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
            <div className="tool-result-grid field-button-row">
              <label className="check-row">
                <input checked={overwrite} disabled={running} onChange={(event) => setOverwrite(event.currentTarget.checked)} type="checkbox" />
                覆盖同名 MP3
              </label>
              <label className="check-row">
                <input checked={deleteSource} disabled={running} onChange={(event) => setDeleteSource(event.currentTarget.checked)} type="checkbox" />
                转换后删除源 NCM
              </label>
            </div>
          </details>
        </div>
      </div>

      <ActionBar
        hint="文件后转换。"
        secondary={<button className="ghost-button" disabled={running || (!songs.length && !results.length && !error)} onClick={clearAll} type="button">清空</button>}
        tertiary={<button className="ghost-button" disabled={!canList} onClick={handleList} type="button">扫描</button>}
        primary={<button className="primary-button" disabled={!canConvert} onClick={() => void handleConvert()} type="button">{running ? "运行中" : "转换"}</button>}
      />

      <ResultCards
        cards={[
          {
            label: "扫描结果",
            value: songs.length ? `${songs.length} 个文件` : "等待扫描",
            detail: songs[0]?.title ? `${songs[0].title}${songs[0].artist ? ` · ${songs[0].artist}` : ""}` : "显示 NCM 元数据和路径",
          },
          {
            label: "转换结果",
            value: results.length ? `${results.length} 个 MP3` : "等待转换",
            detail: results[0]?.output || "输出文件路径会显示在这里",
          },
        ]}
      />

      {(songs.length || results.length) ? (
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
              : songs.map((song) => (
                  <div className="result-row" key={song.path}>
                    <span>{song.title || song.path}</span>
                    <strong>{song.artist || song.path}</strong>
                  </div>
                ))}
          </div>
        </section>
      ) : null}

      <RuntimeLogPanel error={error} logs={logs} />
    </div>
  );
}

export default MusicTool;
