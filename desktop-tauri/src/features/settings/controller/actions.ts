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
  tool: ToolItem,
  enabled: boolean,
): DraftActionResult {
  if (tool.manifest_enabled === false && enabled) {
    return {
      next: current,
      notice: "该插件已在 manifest 中禁用，不能在此启用",
    };
  }
  const next = new Set(current.disabledPlugins);
  if (enabled) {
    next.delete(pluginConfigKey(tool));
  } else {
    next.add(pluginConfigKey(tool));
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
