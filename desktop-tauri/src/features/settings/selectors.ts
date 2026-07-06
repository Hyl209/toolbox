import type { SettingsSnapshot, ToolItem, ToolSettings } from "../../api/tauri";
import {
  cloneDownloaderSettingsDraft,
  cloneThemeColors,
  cloneToolBehaviorDraft,
  cloneWordFormatterDraft,
  DEFAULT_DOWNLOADER_SETTINGS_DRAFT,
  DEFAULT_THEME_COLORS,
  DEFAULT_TOOL_OUTPUT_DIR_DRAFT,
  DEFAULT_WORD_FORMATTER_DRAFT,
  type DownloaderSettingsDraft,
  FILESORTER_CATEGORIES,
  type SettingsDraftState,
  THEME_NAMES,
  TOOL_OUTPUT_DIRS,
  type ToolBehaviorDraft,
  type ToolBehaviorSettingsId,
  type ToolOutputDirDraft,
  type ToolOutputDirId,
  type DownloaderSettingsId,
  WORD_FORMATTER_PAGE_KEYS,
  WORD_FORMATTER_STYLE_FIELDS,
  WORD_FORMATTER_STYLE_KEYS,
  type WordFormatterDraft,
} from "./models";
import { toolSettingsFromSnapshot } from "./models";

export function themeColorDraftsFromSnapshot(snapshot: SettingsSnapshot | null) {
  const drafts = cloneThemeColors();
  if (!snapshot) {
    return drafts;
  }
  const customColors = snapshot.theme.custom_colors;
  if (customColors) {
    THEME_NAMES.forEach((theme) => {
      drafts[theme] = { ...drafts[theme], ...customColors[theme] };
    });
    return drafts;
  }
  drafts[snapshot.ui.theme] = { ...drafts[snapshot.ui.theme], ...snapshot.theme.colors };
  return drafts;
}

export function toolOutputDirsFromSnapshot(snapshot: SettingsSnapshot | null): ToolOutputDirDraft {
  const drafts = { ...DEFAULT_TOOL_OUTPUT_DIR_DRAFT };
  TOOL_OUTPUT_DIRS.forEach(({ id }) => {
    drafts[id] = snapshot?.tool_settings?.[id]?.output_dir ?? "";
  });
  return drafts;
}

export function toolOutputDir(snapshot: SettingsSnapshot | null, toolId: ToolOutputDirId): string {
  return snapshot?.tool_settings?.[toolId]?.output_dir ?? "";
}

export function filesorterCategoriesFromSnapshot(settings?: ToolSettings): Record<string, boolean> {
  return Object.fromEntries(FILESORTER_CATEGORIES.map((category) => [category, settings?.categories?.[category] ?? true]));
}

export function toolBehaviorDraftsFromSnapshot(snapshot: SettingsSnapshot | null): ToolBehaviorDraft {
  const drafts = cloneToolBehaviorDraft();
  const settings = snapshot?.tool_settings ?? {};
  drafts.batchrename = {
    input_dir: settings.batchrename?.input_dir ?? drafts.batchrename.input_dir,
    prefix: settings.batchrename?.prefix ?? drafts.batchrename.prefix,
    group_mode: settings.batchrename?.group_mode ?? drafts.batchrename.group_mode,
    sort_mode: settings.batchrename?.sort_mode ?? drafts.batchrename.sort_mode,
    sort_order: settings.batchrename?.sort_order ?? drafts.batchrename.sort_order,
  };
  drafts.filesorter = {
    input_dir: settings.filesorter?.input_dir ?? drafts.filesorter.input_dir,
    mode: settings.filesorter?.mode ?? drafts.filesorter.mode,
    categories: filesorterCategoriesFromSnapshot(settings.filesorter),
  };
  drafts.same = {
    input_dir: settings.same?.input_dir ?? drafts.same.input_dir,
    recursive: settings.same?.recursive ?? drafts.same.recursive,
  };
  drafts.directdownloader = {
    connections: settings.directdownloader?.connections ?? drafts.directdownloader.connections,
    overwrite: settings.directdownloader?.overwrite ?? drafts.directdownloader.overwrite,
    output_subdir_by_filename: settings.directdownloader?.output_subdir_by_filename ?? drafts.directdownloader.output_subdir_by_filename,
    proxy_url: settings.directdownloader?.proxy_url ?? drafts.directdownloader.proxy_url,
    referer: settings.directdownloader?.referer ?? drafts.directdownloader.referer,
  };
  return drafts;
}

export function toolBehaviorSettings(snapshot: SettingsSnapshot | null, toolId: ToolBehaviorSettingsId): ToolSettings {
  return toolSettingsFromSnapshot(snapshot, toolId);
}

export function downloaderDraftFromSnapshot(snapshot: SettingsSnapshot | null): DownloaderSettingsDraft {
  const drafts = cloneDownloaderSettingsDraft();
  const web = snapshot?.tool_settings?.webvideodownloader ?? {};
  const tg = snapshot?.tool_settings?.tgdownloader ?? {};
  drafts.webvideodownloader = {
    output_dir: web.output_dir ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.webvideodownloader.output_dir,
    proxy_host: web.proxy_host ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.webvideodownloader.proxy_host,
    proxy_port: web.proxy_port ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.webvideodownloader.proxy_port,
    proxy_url: web.proxy_url ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.webvideodownloader.proxy_url,
    overwrite: web.overwrite ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.webvideodownloader.overwrite,
    output_subdir_by_title: web.output_subdir_by_title ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.webvideodownloader.output_subdir_by_title,
    concurrent: web.concurrent ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.webvideodownloader.concurrent,
    cover_dir: web.cover_dir ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.webvideodownloader.cover_dir,
  };
  drafts.tgdownloader = {
    api_id: tg.api_id ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.tgdownloader.api_id,
    api_hash: tg.api_hash ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.tgdownloader.api_hash,
    phone: tg.phone ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.tgdownloader.phone,
    output_dir: tg.output_dir ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.tgdownloader.output_dir,
    proxy_host: tg.proxy_host ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.tgdownloader.proxy_host,
    proxy_port: tg.proxy_port ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.tgdownloader.proxy_port,
    proxy_url: tg.proxy_url ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.tgdownloader.proxy_url,
    recent_limit: tg.recent_limit ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.tgdownloader.recent_limit,
    all_messages: tg.all_messages ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.tgdownloader.all_messages,
    date_from: tg.date_from ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.tgdownloader.date_from,
    date_to: tg.date_to ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.tgdownloader.date_to,
    include_videos: tg.include_videos ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.tgdownloader.include_videos,
    include_photos: tg.include_photos ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.tgdownloader.include_photos,
    overwrite: tg.overwrite ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.tgdownloader.overwrite,
    output_subdir_by_title: tg.output_subdir_by_title ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.tgdownloader.output_subdir_by_title,
    concurrent: tg.concurrent ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.tgdownloader.concurrent,
    cover_dir: tg.cover_dir ?? DEFAULT_DOWNLOADER_SETTINGS_DRAFT.tgdownloader.cover_dir,
  };
  return drafts;
}

export function downloaderSettings(snapshot: SettingsSnapshot | null, toolId: DownloaderSettingsId): ToolSettings {
  return toolSettingsFromSnapshot(snapshot, toolId);
}

export function wordFormatterDraftFromSnapshot(snapshot: SettingsSnapshot | null): WordFormatterDraft {
  const settings = snapshot?.tool_settings?.wordformatter ?? {};
  const draft = cloneWordFormatterDraft();
  draft.output_dir = settings.output_dir ?? DEFAULT_WORD_FORMATTER_DRAFT.output_dir;
  WORD_FORMATTER_PAGE_KEYS.forEach((key) => {
    const value = settings.page?.[key];
    draft.page[key] = value === undefined ? draft.page[key] : String(value);
  });
  WORD_FORMATTER_STYLE_KEYS.forEach((styleKey) => {
    WORD_FORMATTER_STYLE_FIELDS.forEach((field) => {
      const value = settings.styles?.[styleKey]?.[field];
      if (value !== undefined) {
        draft.styles[styleKey][field] = field === "bold" ? Boolean(value) : String(value);
      }
    });
  });
  return draft;
}

export function wordFormatterSettings(snapshot: SettingsSnapshot | null): ToolSettings {
  return toolSettingsFromSnapshot(snapshot, "wordformatter");
}

export function createSettingsDraftState(snapshot: SettingsSnapshot | null, fallbackTools: readonly ToolItem[] = []): SettingsDraftState {
  return {
    theme: snapshot?.ui.theme ?? "light",
    customThemeEnabled: snapshot?.ui.custom_theme_enabled ?? false,
    backgroundEnabled: snapshot?.ui.background_enabled ?? false,
    backgroundImage: snapshot?.ui.background_image ?? "",
    backgroundOpacity: snapshot?.ui.background_opacity ?? 100,
    rememberPassword: snapshot?.auth.remember_password ?? false,
    autoLogin: snapshot?.auth.auto_login ?? false,
    themeColors: themeColorDraftsFromSnapshot(snapshot),
    toolOutputDirs: toolOutputDirsFromSnapshot(snapshot),
    toolBehavior: toolBehaviorDraftsFromSnapshot(snapshot),
    downloader: downloaderDraftFromSnapshot(snapshot),
    wordFormatter: wordFormatterDraftFromSnapshot(snapshot),
    disabledTools: new Set(snapshot?.disabled_tools ?? []),
    disabledPlugins: new Set(snapshot?.disabled_plugins ?? []),
    sidebarOrder: (snapshot?.tools ?? fallbackTools).map((tool) => tool.id),
  };
}

export function activeThemeColors(snapshot: SettingsSnapshot | null) {
  if (!snapshot?.theme.colors) {
    return null;
  }
  return {
    ...DEFAULT_THEME_COLORS[snapshot.ui.theme],
    ...snapshot.theme.colors,
  };
}
