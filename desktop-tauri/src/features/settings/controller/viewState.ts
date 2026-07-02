import type { ToolItem } from "../../../api/tauri";
import { CAPABILITY_NOTES } from "../../tools";
import { pluginConfigKey, type ThemeName } from "..";

export function settingsModeText(theme: ThemeName, customThemeEnabled: boolean): string {
  if (customThemeEnabled) {
    return "自定义主题";
  }
  return theme === "dark" ? "夜晚模式" : "白天模式";
}

export function sidebarStatus(tool: ToolItem, disabledTools: Set<string>, disabledPlugins: Set<string>): string {
  if (tool.source === "plugin") {
    if (tool.manifest_enabled === false) {
      return "manifest 已禁用";
    }
    if (disabledPlugins.has(pluginConfigKey(tool))) {
      return "已禁用";
    }
    return tool.status === "ready" ? "插件 · 可用" : "插件 · 待接入";
  }
  if (tool.enabled === false || disabledTools.has(tool.id)) {
    return "已禁用";
  }
  return CAPABILITY_NOTES[tool.id] ?? (tool.status === "ready" ? "已接入" : "待接入");
}
