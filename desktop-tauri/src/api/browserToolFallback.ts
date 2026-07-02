import type { ToolInput, ToolResult } from "./tauri";

function encodeText(text: string): string {
  const bytes = new TextEncoder().encode(text);
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary);
}

function decodeText(text: string): string {
  const binary = atob(text);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

export function runBrowserToolFallback(toolId: string, input: ToolInput): ToolResult {
  if (toolId !== "base64") {
    throw new Error("该工具需要在 Tauri 桌面端运行");
  }

  if (input.action === "encode_text") {
    return { text: encodeText(String(input.payload.text ?? "")) };
  }

  if (input.action === "decode_text") {
    return { text: decodeText(String(input.payload.text ?? "").trim()) };
  }

  throw new Error(`不支持的 Base64 动作：${input.action}`);
}
