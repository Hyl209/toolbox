import type { ToolResult } from "../../../api/tauri";

/**
 * canRun 约定：所有工具的执行按钮 disabled 条件统一为
 *   const canRun = !running && Boolean(requiredField1) && Boolean(requiredField2);
 * 按钮文案：running ? "运行中" : "操作名"
 * 不要在运行期间抛异常，用 setError() 写入错误，由 RuntimeLogPanel 展示。
 */

export function errorText(error: unknown): string {
  if (error instanceof Error) return error.message;
  return typeof error === "string" ? error : JSON.stringify(error);
}

export function resultText(result: ToolResult): string {
  return result.text ?? result.data?.text ?? JSON.stringify(result, null, 2);
}

export function resultPath(result: ToolResult): string {
  return result.output_path ?? result.data?.output_path ?? "";
}

export function dataOf(result: ToolResult): ToolResult {
  return result.data ?? result;
}

export function rowsOf(result: ToolResult): Array<Record<string, string | number | boolean>> {
  return dataOf(result).results ?? [];
}

export function summaryOf(result: ToolResult): ToolResult {
  return dataOf(result).summary ?? dataOf(result);
}
