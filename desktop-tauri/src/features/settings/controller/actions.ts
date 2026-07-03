import type { ToolItem } from "../../../api/tauri";
import {
  DEFAULT_THEME_COLORS,
  pluginConfigKey,
  type DownloaderSettingsId,
  type SettingsDraftState,
  type ThemeName,
  type ThemeZone,
  type ToolBehaviorSettingsId,
  type WordFormatterPageKey,
  type WordFormatterStyleField,
  type WordFormatterStyleKey,
} from "..";

export type DraftActionResult = {
  next: SettingsDraftState;
  notice?: string;
};

function pluginName(tool: ToolItem): string {
  return pluginConfigKey(tool);
}

function dependencyName(name: string): string {
  return name.replace(/^plugin:/, "");
}

function dependencyClosure(pluginTools: readonly ToolItem[], start: string): Set<string> {
  const byName = new Map(pluginTools.map((tool) => [pluginName(tool), tool]));
  const found = new Set<string>();
  const visit = (name: string) => {
    const tool = byName.get(name);
    for (const dep of tool?.dependencies ?? []) {
      const cleanDep = dependencyName(dep);
      if (!found.has(cleanDep)) {
        found.add(cleanDep);
        visit(cleanDep);
      }
    }
  };
  visit(start);
  return found;
}

function dependentClosure(pluginTools: readonly ToolItem[], start: string): Set<string> {
  const found = new Set<string>();
  let changed = true;
  while (changed) {
    changed = false;
    for (const tool of pluginTools) {
      const name = pluginName(tool);
      if (found.has(name) || name === start) {
        continue;
      }
      const deps = (tool.dependencies ?? []).map(dependencyName);
      if (deps.includes(start) || deps.some((dep) => found.has(dep))) {
        found.add(name);
        changed = true;
      }
    }
  }
  return found;
}

export function toggleBuiltinTool(
  current: SettingsDraftState,
  builtinTools: readonly ToolItem[],
  toolId: string,
  enabled: boolean,
): DraftActionResult {
  const next = new Set(current.disabledTools);
  if (enabled) {
    next.delete(toolId);
    return { next: { ...current, disabledTools: next } };
  }

  const enabledBuiltinCount = builtinTools.filter((tool) => tool.id !== toolId && !next.has(tool.id)).length;
  if (enabledBuiltinCount < 1) {
    return {
      next: current,
      notice: "至少保留一个内置工具启用",
    };
  }
  next.add(toolId);
  return { next: { ...current, disabledTools: next } };
}

export function togglePlugin(
  current: SettingsDraftState,
  pluginTools: readonly ToolItem[],
  tool: ToolItem,
  enabled: boolean,
): DraftActionResult {
  if (tool.manifest_enabled === false && enabled) {
    return {
      next: current,
      notice: "该插件已在 manifest 中禁用，不能在此启用",
    };
  }
  const name = pluginConfigKey(tool);
  const next = new Set(current.disabledPlugins);
  if (enabled) {
    next.delete(name);
    for (const dep of dependencyClosure(pluginTools, name)) {
      next.delete(dep);
    }
  } else {
    next.add(name);
    for (const depender of dependentClosure(pluginTools, name)) {
      next.add(depender);
    }
  }
  return { next: { ...current, disabledPlugins: next } };
}

export function updateRememberPassword(current: SettingsDraftState, checked: boolean): SettingsDraftState {
  return {
    ...current,
    rememberPassword: checked,
    autoLogin: checked ? current.autoLogin : false,
  };
}

export function updateAutoLogin(current: SettingsDraftState, checked: boolean): SettingsDraftState {
  return {
    ...current,
    autoLogin: checked,
    rememberPassword: checked ? true : current.rememberPassword,
  };
}

export function moveSidebarItem(current: SettingsDraftState, toolId: string, direction: -1 | 1): SettingsDraftState {
  const index = current.sidebarOrder.indexOf(toolId);
  const nextIndex = index + direction;
  if (index < 0 || nextIndex < 0 || nextIndex >= current.sidebarOrder.length) {
    return current;
  }
  const next = [...current.sidebarOrder];
  [next[index], next[nextIndex]] = [next[nextIndex], next[index]];
  return { ...current, sidebarOrder: next };
}

export function updateTheme(current: SettingsDraftState, value: ThemeName): SettingsDraftState {
  return { ...current, theme: value };
}

export function updateCustomThemeEnabled(current: SettingsDraftState, checked: boolean): SettingsDraftState {
  return { ...current, customThemeEnabled: checked };
}

export function updateThemeColor(current: SettingsDraftState, zone: ThemeZone, value: string): SettingsDraftState {
  return {
    ...current,
    themeColors: {
      ...current.themeColors,
      [current.theme]: {
        ...(current.themeColors[current.theme] ?? DEFAULT_THEME_COLORS[current.theme]),
        [zone]: value,
      },
    },
  };
}

export function updateToolOutputDir(current: SettingsDraftState, toolId: keyof SettingsDraftState["toolOutputDirs"], value: string): SettingsDraftState {
  return {
    ...current,
    toolOutputDirs: {
      ...current.toolOutputDirs,
      [toolId]: value,
    },
  };
}

export function updateToolBehavior<T extends ToolBehaviorSettingsId, K extends keyof SettingsDraftState["toolBehavior"][T]>(
  current: SettingsDraftState,
  toolId: T,
  key: K,
  value: SettingsDraftState["toolBehavior"][T][K],
): SettingsDraftState {
  return {
    ...current,
    toolBehavior: {
      ...current.toolBehavior,
      [toolId]: {
        ...current.toolBehavior[toolId],
        [key]: value,
      },
    },
  };
}

export function updateFilesorterCategory(current: SettingsDraftState, category: string, enabled: boolean): SettingsDraftState {
  return {
    ...current,
    toolBehavior: {
      ...current.toolBehavior,
      filesorter: {
        ...current.toolBehavior.filesorter,
        categories: {
          ...current.toolBehavior.filesorter.categories,
          [category]: enabled,
        },
      },
    },
  };
}

export function updateDownloader<T extends DownloaderSettingsId, K extends keyof SettingsDraftState["downloader"][T]>(
  current: SettingsDraftState,
  toolId: T,
  key: K,
  value: SettingsDraftState["downloader"][T][K],
): SettingsDraftState {
  return {
    ...current,
    downloader: {
      ...current.downloader,
      [toolId]: {
        ...current.downloader[toolId],
        [key]: value,
      },
    },
  };
}

export function updateWordFormatterOutputDir(current: SettingsDraftState, value: string): SettingsDraftState {
  return {
    ...current,
    wordFormatter: {
      ...current.wordFormatter,
      output_dir: value,
    },
  };
}

export function updateWordFormatterPage(current: SettingsDraftState, key: WordFormatterPageKey, value: string): SettingsDraftState {
  return {
    ...current,
    wordFormatter: {
      ...current.wordFormatter,
      page: {
        ...current.wordFormatter.page,
        [key]: value,
      },
    },
  };
}

export function updateWordFormatterStyle(
  current: SettingsDraftState,
  styleKey: WordFormatterStyleKey,
  field: WordFormatterStyleField,
  value: string | boolean,
): SettingsDraftState {
  return {
    ...current,
    wordFormatter: {
      ...current.wordFormatter,
      styles: {
        ...current.wordFormatter.styles,
        [styleKey]: {
          ...current.wordFormatter.styles[styleKey],
          [field]: value,
        },
      },
    },
  };
}
