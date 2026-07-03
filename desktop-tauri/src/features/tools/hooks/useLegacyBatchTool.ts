import { useEffect, useMemo, useState } from "react";
import { pickDirectory, pickFiles, runTool, type DialogFilter, type ToolResult } from "../../../api/tauri";

type BatchToolResultRow = { source: string; output: string };

type UseLegacyBatchToolOptions<TItem> = {
  toolId: string;
  initialOutputDir?: string;
  parseFiles: (result: ToolResult) => TItem[];
  parseResults: (result: ToolResult) => BatchToolResultRow[];
  fileTitle: string;
  fileFilters?: DialogFilter[];
  inputDirTitle: string;
  outputDirTitle: string;
  listFoundLabel: (count: number) => string;
  listTargetLabel: string;
  convertTargetLabel: string;
  listAction?: string;
  convertAction?: string;
  listPayload?: (paths: string[]) => Record<string, unknown>;
  convertPayload: (ctx: { paths: string[]; outputDir: string }) => Record<string, unknown>;
};

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

export function useLegacyBatchTool<TItem>({
  toolId,
  initialOutputDir = "",
  parseFiles,
  parseResults,
  fileTitle,
  fileFilters,
  inputDirTitle,
  outputDirTitle,
  listFoundLabel,
  listTargetLabel,
  convertTargetLabel,
  listAction = "list",
  convertAction = "convert",
  listPayload = (paths) => ({ paths }),
  convertPayload,
}: UseLegacyBatchToolOptions<TItem>) {
  const [inputText, setInputText] = useState("");
  const [outputDir, setOutputDir] = useState(initialOutputDir);
  const [files, setFiles] = useState<TItem[]>([]);
  const [results, setResults] = useState<BatchToolResultRow[]>([]);
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

  async function handleList() {
    if (!canList) {
      return;
    }
    setRunning(true);
    setError("");
    setFiles([]);
    setResults([]);
    setLogs((items) => [`扫描${listTargetLabel}：${paths.length} 个路径`, ...items].slice(0, 5));
    try {
      const result = await runTool(toolId, {
        task_id: `${toolId}-list-${Date.now()}`,
        action: listAction,
        payload: listPayload(paths),
      });
      const nextFiles = parseFiles(result);
      setFiles(nextFiles);
      setLogs((items) => [listFoundLabel(nextFiles.length), ...items].slice(0, 5));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`扫描失败：${message}`, ...items].slice(0, 5));
    } finally {
      setRunning(false);
    }
  }

  async function handleConvert(payloadOverride?: Record<string, unknown>) {
    if (!canConvert) {
      return;
    }
    setRunning(true);
    setError("");
    setResults([]);
    setLogs((items) => [`开始转换：${paths.length} 个路径`, ...items].slice(0, 5));
    try {
      const result = await runTool(toolId, {
        task_id: `${toolId}-convert-${Date.now()}`,
        action: convertAction,
        payload: payloadOverride ?? convertPayload({ paths, outputDir }),
      });
      const rows = parseResults(result);
      setResults(rows);
      setLogs((items) => [`转换完成：${rows.length} 个${convertTargetLabel}`, ...items].slice(0, 5));
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

  async function chooseFiles() {
    const picked = await pickFiles({ title: fileTitle, filters: fileFilters });
    if (picked?.length) {
      setInputText((current) => [...splitPaths(current), ...picked].join("\n"));
    }
  }

  async function chooseInputDir() {
    const path = await pickDirectory({ title: inputDirTitle });
    if (path) {
      setInputText((current) => [...splitPaths(current), path].join("\n"));
    }
  }

  async function chooseOutputDir() {
    const path = await pickDirectory({ title: outputDirTitle });
    if (path) {
      setOutputDir(path);
    }
  }

  return {
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
    chooseFiles,
    chooseInputDir,
    chooseOutputDir,
  };
}
