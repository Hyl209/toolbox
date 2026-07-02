import toolManifest from "../tools/manifest";
import type { SettingsPatch, SettingsSnapshot, ToolSettings } from "./tauri";
import {
  patchBoolean,
  patchFilesorterCategories,
  patchString,
  patchVideoDownloaderSettings,
  patchWordFormatterSettings,
} from "./browserSettingsPatchers";

const browserThemeColors: Record<"dark" | "light", SettingsSnapshot["theme"]["colors"]> = {
  dark: {
    window_bg: "#1b1f25",
    surface_bg: "#1f2329",
    card_bg: "rgba(44, 50, 59, 0.70)",
    accent: "#6f95c7",
    text_primary: "#eef2f7",
    text_secondary: "#9aa6b5",
    input_bg: "#2a3038",
  },
  light: {
    window_bg: "#e5e9ef",
    surface_bg: "#eef1f5",
    card_bg: "rgba(255, 255, 255, 0.38)",
    accent: "#e4efff",
    text_primary: "#1f252d",
    text_secondary: "#697586",
    input_bg: "#eef1f5",
  },
};

const THEME_ZONES = ["window_bg", "surface_bg", "card_bg", "accent", "text_primary", "text_secondary", "input_bg"] as const;
const FILESORTER_CATEGORIES = ["图片", "视频", "音频", "文档", "压缩包", "程序", "其他"] as const;
const browserWordFormatterSettings: ToolSettings = {
  output_dir: "",
  page: {
    top_margin_cm: 2.54,
    bottom_margin_cm: 2.54,
    left_margin_cm: 3.18,
    right_margin_cm: 3.18,
    header_distance_cm: 1.5,
    footer_distance_cm: 1.75,
  },
  styles: {
    heading1: { font: "Microsoft YaHei", size_pt: 18, bold: true, line_spacing: 1.5, space_before_pt: 12, space_after_pt: 6, first_line_indent_cm: 0 },
    heading2: { font: "Microsoft YaHei", size_pt: 16, bold: true, line_spacing: 1.5, space_before_pt: 10, space_after_pt: 6, first_line_indent_cm: 0 },
    heading3: { font: "Microsoft YaHei", size_pt: 14, bold: true, line_spacing: 1.5, space_before_pt: 8, space_after_pt: 4, first_line_indent_cm: 0 },
    heading4: { font: "Microsoft YaHei", size_pt: 12, bold: true, line_spacing: 1.5, space_before_pt: 6, space_after_pt: 4, first_line_indent_cm: 0 },
    body: { font: "Microsoft YaHei", size_pt: 12, bold: false, line_spacing: 1.5, space_before_pt: 0, space_after_pt: 0, first_line_indent_cm: 0.74 },
    table: { font: "Microsoft YaHei", size_pt: 10.5, bold: false, line_spacing: 1.2, space_before_pt: 0, space_after_pt: 0, first_line_indent_cm: 0 },
  },
};

const browserCustomThemeColors: Record<"dark" | "light", SettingsSnapshot["theme"]["colors"]> = {
  dark: { ...browserThemeColors.dark },
  light: { ...browserThemeColors.light },
};

let browserCustomThemeEnabled = false;
let browserRememberPassword = false;
let browserAutoLogin = false;
const browserLastUser = "";
let browserToolSettings: SettingsSnapshot["tool_settings"] = {
  base64: { output_dir: "" },
  music: { output_dir: "" },
  zipandpng: { output_dir: "" },
  mp4mp3: { output_dir: "" },
  imageconvert: { output_dir: "" },
  pdftools: { output_dir: "" },
  wordformatter: JSON.parse(JSON.stringify(browserWordFormatterSettings)),
  batchrename: {
    input_dir: "",
    prefix: "批量命名",
    group_mode: "按后缀",
    sort_mode: "按命名",
    sort_order: "从小到大",
  },
  filesorter: { input_dir: "", mode: "按大类分类", categories: defaultFilesorterCategories() },
  archive_extractor: { output_dir: "" },
  same: { input_dir: "", recursive: true },
  directdownloader: {
    output_dir: "",
    connections: "16",
    overwrite: false,
    output_subdir_by_filename: false,
    proxy_url: "",
    referer: "",
  },
  webvideodownloader: {
    output_dir: "",
    proxy_host: "127.0.0.1",
    proxy_port: "",
    proxy_url: "",
    overwrite: false,
    output_subdir_by_title: false,
    concurrent: "1",
    cover_dir: "",
  },
  tgdownloader: {
    api_id: "",
    api_hash: "",
    phone: "",
    phone_code_hash: "",
    output_dir: "",
    proxy_host: "127.0.0.1",
    proxy_port: "",
    proxy_url: "",
    recent_limit: "500",
    all_messages: false,
    date_from: "",
    date_to: "",
    include_videos: true,
    include_photos: false,
    overwrite: false,
    output_subdir_by_title: false,
    concurrent: "1",
    cover_dir: "",
  },
};

let browserSnapshot: SettingsSnapshot | null = null;

function defaultFilesorterCategories(): Record<string, boolean> {
  return Object.fromEntries(FILESORTER_CATEGORIES.map((category) => [category, true]));
}

function orderTools<T extends { id: string }>(tools: T[], order: readonly string[]): T[] {
  const byId = new Map(tools.map((tool) => [tool.id, tool]));
  const ordered = order.flatMap((toolId) => {
    const tool = byId.get(toolId);
    return tool ? [tool] : [];
  });
  const used = new Set(ordered.map((tool) => tool.id));
  return [...ordered, ...tools.filter((tool) => !used.has(tool.id))];
}

function cloneToolSettings(settings: SettingsSnapshot["tool_settings"]): SettingsSnapshot["tool_settings"] {
  return JSON.parse(JSON.stringify(settings)) as SettingsSnapshot["tool_settings"];
}

function buildBrowserSettingsSnapshot(theme: "dark" | "light", disabledTools: string[], disabledPlugins: string[] = [], sidebarOrder: string[] = []): SettingsSnapshot {
  const disabledSet = new Set(disabledTools);
  const disabledPluginSet = new Set(disabledPlugins);
  const tools = toolManifest.map((tool) => ({
    ...tool,
    enabled: !disabledSet.has(tool.id),
    source: "builtin" as const,
  }));
  return {
    settings_path: "browser-preview",
    ui: {
      theme,
      custom_theme_enabled: browserCustomThemeEnabled,
    },
    auth: {
      remember_password: browserRememberPassword,
      auto_login: browserAutoLogin,
      last_user: browserLastUser,
    },
    theme: {
      mode: browserCustomThemeEnabled ? "custom" : theme,
      colors: browserCustomThemeEnabled ? { ...browserCustomThemeColors[theme] } : { ...browserThemeColors[theme] },
      custom_colors: {
        dark: { ...browserCustomThemeColors.dark },
        light: { ...browserCustomThemeColors.light },
      },
    },
    disabled_tools: [...disabledSet].sort(),
    disabled_plugins: [...disabledPluginSet].sort(),
    tool_settings: cloneToolSettings(browserToolSettings),
    sidebar_order: sidebarOrder,
    tools: orderTools(tools, sidebarOrder),
  };
}

export function loadBrowserSettingsSnapshot(): SettingsSnapshot {
  browserSnapshot ??= buildBrowserSettingsSnapshot("light", [], []);
  return browserSnapshot;
}


export function saveBrowserSettingsPatch(patch: SettingsPatch): SettingsSnapshot {
  const current = loadBrowserSettingsSnapshot();
  const nextTheme = patch.updates["ui/theme"] === "dark" || patch.updates["ui/theme"] === "light" ? patch.updates["ui/theme"] : current.ui.theme;
  const nextDisabled = Array.isArray(patch.updates["tools/disabled"])
    ? patch.updates["tools/disabled"].filter((item): item is string => typeof item === "string")
    : current.disabled_tools;
  const nextDisabledPlugins = Array.isArray(patch.updates["plugins/disabled"])
    ? patch.updates["plugins/disabled"].filter((item): item is string => typeof item === "string")
    : current.disabled_plugins;
  const nextOrder = Array.isArray(patch.updates["sidebar/order"])
    ? patch.updates["sidebar/order"].filter((item): item is string => typeof item === "string")
    : current.sidebar_order;
  const rememberValue = patch.updates["auth/remember_password"];
  const autoLoginValue = patch.updates["auth/auto_login"];
  const rememberPatched = typeof rememberValue === "boolean";
  const autoPatched = typeof autoLoginValue === "boolean";
  browserRememberPassword = rememberPatched ? rememberValue : current.auth.remember_password;
  browserAutoLogin = autoPatched ? autoLoginValue : current.auth.auto_login;
  if (rememberPatched && !browserRememberPassword) {
    browserAutoLogin = false;
  } else if (autoPatched && browserAutoLogin) {
    browserRememberPassword = true;
  }
  browserCustomThemeEnabled = typeof patch.updates["ui/custom_theme_enabled"] === "boolean" ? patch.updates["ui/custom_theme_enabled"] : current.ui.custom_theme_enabled;
  browserToolSettings = {
    ...current.tool_settings,
    base64: { output_dir: typeof patch.updates["base64/output_dir"] === "string" ? patch.updates["base64/output_dir"] : current.tool_settings.base64?.output_dir ?? "" },
    music: { output_dir: typeof patch.updates["music/output_dir"] === "string" ? patch.updates["music/output_dir"] : current.tool_settings.music?.output_dir ?? "" },
    zipandpng: { output_dir: typeof patch.updates["zipandpng/output_dir"] === "string" ? patch.updates["zipandpng/output_dir"] : current.tool_settings.zipandpng?.output_dir ?? "" },
    mp4mp3: { output_dir: typeof patch.updates["mp4mp3/output_dir"] === "string" ? patch.updates["mp4mp3/output_dir"] : current.tool_settings.mp4mp3?.output_dir ?? "" },
    imageconvert: { output_dir: typeof patch.updates["imageconvert/output_dir"] === "string" ? patch.updates["imageconvert/output_dir"] : current.tool_settings.imageconvert?.output_dir ?? "" },
    pdftools: { output_dir: typeof patch.updates["pdftools/output_dir"] === "string" ? patch.updates["pdftools/output_dir"] : current.tool_settings.pdftools?.output_dir ?? "" },
    wordformatter: patchWordFormatterSettings(patch.updates, browserWordFormatterSettings, current.tool_settings.wordformatter),
    batchrename: {
      input_dir: patchString(patch.updates, "batchrename/input_dir", current.tool_settings.batchrename?.input_dir ?? ""),
      prefix: patchString(patch.updates, "batchrename/prefix", current.tool_settings.batchrename?.prefix ?? "批量命名"),
      group_mode: patchString(patch.updates, "batchrename/group_mode", current.tool_settings.batchrename?.group_mode ?? "按后缀"),
      sort_mode: patchString(patch.updates, "batchrename/sort_mode", current.tool_settings.batchrename?.sort_mode ?? "按命名"),
      sort_order: patchString(patch.updates, "batchrename/sort_order", current.tool_settings.batchrename?.sort_order ?? "从小到大"),
    },
    filesorter: {
      input_dir: patchString(patch.updates, "filesorter/input_dir", current.tool_settings.filesorter?.input_dir ?? ""),
      mode: patchString(patch.updates, "filesorter/mode", current.tool_settings.filesorter?.mode ?? "按大类分类"),
      categories: patchFilesorterCategories(patch.updates, current.tool_settings.filesorter?.categories, defaultFilesorterCategories),
    },
    archive_extractor: {
      output_dir: patchString(patch.updates, "archive_extractor/output_dir", current.tool_settings.archive_extractor?.output_dir ?? ""),
    },
    same: {
      input_dir: patchString(patch.updates, "same/input_dir", current.tool_settings.same?.input_dir ?? ""),
      recursive: patchBoolean(patch.updates, "same/recursive", current.tool_settings.same?.recursive ?? true),
    },
    directdownloader: {
      output_dir: typeof patch.updates["directdownloader/output_dir"] === "string" ? patch.updates["directdownloader/output_dir"] : current.tool_settings.directdownloader?.output_dir ?? "",
      connections: patchString(patch.updates, "directdownloader/connections", current.tool_settings.directdownloader?.connections ?? "16"),
      overwrite: patchBoolean(patch.updates, "directdownloader/overwrite", current.tool_settings.directdownloader?.overwrite ?? false),
      output_subdir_by_filename: patchBoolean(
        patch.updates,
        "directdownloader/output_subdir_by_filename",
        current.tool_settings.directdownloader?.output_subdir_by_filename ?? false,
      ),
      proxy_url: patchString(patch.updates, "directdownloader/proxy_url", current.tool_settings.directdownloader?.proxy_url ?? ""),
      referer: patchString(patch.updates, "directdownloader/referer", current.tool_settings.directdownloader?.referer ?? ""),
    },
    ...patchVideoDownloaderSettings(patch, current.tool_settings),
  };
  (["dark", "light"] as const).forEach((theme) => {
    THEME_ZONES.forEach((zone) => {
      const value = patch.updates[`theme/${theme}/${zone}`];
      if (typeof value === "string") {
        browserCustomThemeColors[theme][zone] = value;
      }
    });
  });
  browserSnapshot = buildBrowserSettingsSnapshot(nextTheme, nextDisabled, nextDisabledPlugins, nextOrder);
  return browserSnapshot;
}
