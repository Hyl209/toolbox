import type { CSSProperties } from "react";
import type { SettingsSnapshot, ToolItem } from "../../api/tauri";
import { DEFAULT_THEME_COLORS, THEME_ZONES, type ThemeColors, type ThemeZone } from "./models";

const GLASS_MIN_ALPHA = 10;
const GLASS_MAX_ALPHA = 70;
const GLASS_MIN_BLUR = 4;
const GLASS_MAX_BLUR = 24;

function clampGlassAlpha(value: number): number {
  return Math.max(GLASS_MIN_ALPHA, Math.min(GLASS_MAX_ALPHA, Math.round(value)));
}

function cardColorAlphaPercent(value: string): number {
  const hexAlpha = value.trim().match(/^#[0-9a-f]{8}$/i)?.[0];
  if (hexAlpha) {
    return clampGlassAlpha((parseInt(hexAlpha.slice(7, 9), 16) / 255) * 100);
  }

  const rgbaAlpha = value.match(/^rgba\([^,]+,[^,]+,[^,]+,\s*([\d.]+)\s*\)$/i)?.[1];
  if (rgbaAlpha) {
    return clampGlassAlpha(Number(rgbaAlpha) * 100);
  }

  return GLASS_MAX_ALPHA;
}

function glassBlurPx(alphaPercent: number): number {
  const progress = (clampGlassAlpha(alphaPercent) - GLASS_MIN_ALPHA) / (GLASS_MAX_ALPHA - GLASS_MIN_ALPHA);
  return Math.ceil(GLASS_MIN_BLUR + (GLASS_MAX_BLUR - GLASS_MIN_BLUR) * progress);
}

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

export function themeStyleFromColors(colors: ThemeColors): CSSProperties {
  const quietBorder = `color-mix(in oklab, ${colors.text_secondary}, transparent 68%)`;
  const visibleScrollThumb = `color-mix(in oklab, ${colors.text_secondary}, transparent 58%)`;
  const activeScrollThumb = `color-mix(in oklab, ${colors.text_secondary}, transparent 38%)`;
  const glassAlphaPercent = cardColorAlphaPercent(colors.card_bg);
  const glassProgress = (glassAlphaPercent - GLASS_MIN_ALPHA) / (GLASS_MAX_ALPHA - GLASS_MIN_ALPHA);
  const glassEdgeAlpha = Math.round(30 + 40 * glassProgress);
  const glassShadowAlpha = Math.round(5 + 15 * glassProgress);
  const glassPanelShadowAlpha = Math.max(4, glassShadowAlpha - 4);

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
    "--glass-alpha": `${glassAlphaPercent}%`,
    "--glass-blur": `${glassBlurPx(glassAlphaPercent)}px`,
    "--glass-window-blur": `${glassBlurPx(glassAlphaPercent) + 20}px`,
    "--glass-saturation": `${Math.round(118 + 32 * glassProgress)}%`,
    "--glass-edge-alpha": `${glassEdgeAlpha}%`,
    "--glass-shadow-alpha": `${glassShadowAlpha}%`,
    "--glass-edge": `inset 0 1px 0 oklch(100% 0 0 / ${glassEdgeAlpha}%)`,
    "--glass-card-shadow": `0 18px 46px oklch(24% 0.02 255deg / ${glassShadowAlpha}%)`,
    "--glass-panel-shadow": `0 10px 24px oklch(26% 0.018 255deg / ${glassPanelShadowAlpha}%)`,
    "--glass-panel-bg": `color-mix(in oklab, ${colors.card_bg}, transparent ${Math.round(30 - 18 * glassProgress)}%)`,
    "--glass-soft-bg": `color-mix(in oklab, ${colors.card_bg}, transparent ${Math.round(42 - 24 * glassProgress)}%)`,
  } as CSSProperties;
}

export function themeStyle(snapshot: SettingsSnapshot | null): CSSProperties {
  if (!snapshot?.theme.colors) {
    return {};
  }
  const colors = Object.fromEntries(THEME_ZONES.map((zone) => [zone, themeColor(snapshot, zone)])) as ThemeColors;
  return themeStyleFromColors(colors);
}
