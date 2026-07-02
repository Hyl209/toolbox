import type { CSSProperties } from "react";
import type { SettingsSnapshot, ToolItem } from "../../api/tauri";
import { DEFAULT_THEME_COLORS, THEME_ZONES, type ThemeColors, type ThemeZone } from "./models";

function validThemeColor(value: unknown): value is string {
  if (typeof value !== "string" || !value.trim()) {
    return false;
  }
  if (typeof CSS !== "undefined" && CSS.supports("color", value)) {
    return true;
  }
  return /^#(?:[0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$/i.test(value) || /^(?:rgb|rgba|hsl|hsla|oklch|oklab|color-mix)\(/i.test(value);
}

function themeColor(snapshot: SettingsSnapshot, zone: ThemeZone): string {
  const fallback = DEFAULT_THEME_COLORS[snapshot.ui.theme][zone];
  const value = snapshot.theme.colors[zone];
  return validThemeColor(value) ? value : fallback;
}

export function firstSelectableTool(tools: readonly ToolItem[]): ToolItem {
  return tools.find((tool) => tool.enabled !== false) ?? tools[0];
}

export function pluginConfigKey(tool: ToolItem): string {
  return tool.plugin_name ?? tool.id.replace(/^plugin:/, "");
}

export function sidebarOrderForSave(snapshot: SettingsSnapshot, visibleOrder: string[], toolsById: ReadonlyMap<string, ToolItem>): string[] {
  const currentOrder = visibleOrder.filter((toolId) => toolsById.has(toolId));
  const mergedOrder: string[] = [];
  let currentIndex = 0;

  snapshot.sidebar_order.forEach((legacyToolId) => {
    if (!toolsById.has(legacyToolId)) {
      mergedOrder.push(legacyToolId);
      return;
    }
    const nextToolId = currentOrder[currentIndex];
    if (nextToolId) {
      mergedOrder.push(nextToolId);
      currentIndex += 1;
    }
  });

  currentOrder.slice(currentIndex).forEach((toolId) => {
    if (!mergedOrder.includes(toolId)) {
      mergedOrder.push(toolId);
    }
  });

  return mergedOrder;
}

export function toolDisplayName(tool: ToolItem): string {
  return tool.sidebar_label ?? tool.title;
}

export function toolMetadata(tool: ToolItem): string[] {
  const extraFiles = tool.extra_files?.length ? `extra_files: ${tool.extra_files.join(", ")}` : "";
  const tabKwargs = tool.tab_kwargs && Object.keys(tool.tab_kwargs).length ? `tab_kwargs: ${JSON.stringify(tool.tab_kwargs)}` : "";
  const priority = tool.priority === undefined ? "" : `priority: ${tool.priority}`;
  return [
    tool.title,
    tool.id,
    tool.dir_name ?? (tool.source === "plugin" ? pluginConfigKey(tool) : undefined),
    tool.converter_file,
    tool.tab_file,
    extraFiles,
    tabKwargs,
    tool.version,
    tool.description,
    priority,
  ].filter(Boolean) as string[];
}

export function themeStyle(snapshot: SettingsSnapshot | null): CSSProperties {
  if (!snapshot?.theme.colors) {
    return {};
  }
  const colors = Object.fromEntries(THEME_ZONES.map((zone) => [zone, themeColor(snapshot, zone)])) as ThemeColors;
  const quietBorder = `color-mix(in oklab, ${colors.text_secondary}, transparent 68%)`;
  const visibleScrollThumb = `color-mix(in oklab, ${colors.text_secondary}, transparent 58%)`;
  const activeScrollThumb = `color-mix(in oklab, ${colors.text_secondary}, transparent 38%)`;

  return {
    "--ink": colors.text_primary,
    "--ink-muted": colors.text_secondary,
    "--ink-soft": colors.text_secondary,
    "--surface": colors.surface_bg,
    "--surface-strong": colors.card_bg,
    "--surface-soft": colors.input_bg,
    "--hairline": quietBorder,
    "--accent": colors.accent,
    "--accent-strong": colors.accent,
    "--scroll-thumb": visibleScrollThumb,
    "--scroll-thumb-hover": activeScrollThumb,
    "--legacy-window-bg": colors.window_bg,
    "--legacy-surface-bg": colors.surface_bg,
    "--legacy-card-bg": colors.card_bg,
    "--legacy-accent": colors.accent,
    "--legacy-text-primary": colors.text_primary,
    "--legacy-text-secondary": colors.text_secondary,
    "--legacy-input-bg": colors.input_bg,
  } as CSSProperties;
}
