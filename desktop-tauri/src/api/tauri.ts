import { invoke } from "@tauri-apps/api/core";
import toolManifest from "../tools/manifest";

export type ToolInput = {
  task_id: string;
  action: string;
  payload: Record<string, unknown>;
};

export type ToolResult = {
  text?: string;
  output_path?: string;
  mime?: string;
  embedded?: {
    found?: boolean;
    filename?: string | null;
    file_size?: number;
    image_format?: string;
  };
  available?: boolean;
  message?: string;
  files?: Array<Record<string, string | number | boolean>>;
  plan?: Array<Record<string, string | number | boolean>>;
  results?: Array<Record<string, string | number | boolean>>;
  success_count?: number;
  fail_count?: number;
  skipped_count?: number;
  renamed_count?: number;
  total_files?: number;
  selected_total_files?: number;
  category_counts?: Record<string, number>;
  resolution_bucket_counts?: Record<string, number>;
  group_counts?: Record<string, number>;
  summary?: ToolResult;
  deleted?: Array<{ path: string; ok: boolean; message?: string }>;
  data?: {
    text?: string;
    output_path?: string;
    mime?: string;
    embedded?: ToolResult["embedded"];
    available?: boolean;
    message?: string;
    files?: ToolResult["files"];
    plan?: ToolResult["plan"];
    results?: ToolResult["results"];
    success_count?: number;
    fail_count?: number;
    skipped_count?: number;
    renamed_count?: number;
    total_files?: number;
    selected_total_files?: number;
    category_counts?: ToolResult["category_counts"];
    resolution_bucket_counts?: ToolResult["resolution_bucket_counts"];
    group_counts?: ToolResult["group_counts"];
    summary?: ToolResult;
    deleted?: ToolResult["deleted"];
  };
};

export type ToolItem = {
  id: string;
  title: string;
  category: string;
  supported_in_tauri: boolean;
  status: "ready" | "pending" | "planned";
  sidebar_label?: string;
  dir_name?: string;
  converter_file?: string;
  tab_file?: string;
  extra_files?: readonly string[];
  tab_kwargs?: Record<string, unknown>;
  source?: "builtin" | "plugin";
  enabled?: boolean;
  manifest_enabled?: boolean;
  description?: string;
  version?: string;
  plugin_name?: string;
  priority?: number;
};

export type WordFormatterStyleSettings = {
  font?: string;
  size_pt?: number | string;
  bold?: boolean;
  line_spacing?: number | string;
  space_before_pt?: number | string;
  space_after_pt?: number | string;
  first_line_indent_cm?: number | string;
};

export type ToolSettings = {
  output_dir?: string;
  page?: Record<string, number | string>;
  styles?: Record<string, WordFormatterStyleSettings>;
  input_dir?: string;
  prefix?: string;
  group_mode?: string;
  sort_mode?: string;
  sort_order?: string;
  mode?: string;
  categories?: Record<string, boolean>;
  recursive?: boolean;
  connections?: string;
  overwrite?: boolean;
  output_subdir_by_filename?: boolean;
  proxy_host?: string;
  proxy_port?: string;
  proxy_url?: string;
  referer?: string;
  api_id?: string;
  api_hash?: string;
  phone?: string;
  phone_code_hash?: string;
  recent_limit?: string;
  all_messages?: boolean;
  date_from?: string;
  date_to?: string;
  include_videos?: boolean;
  include_photos?: boolean;
  output_subdir_by_title?: boolean;
  concurrent?: string;
  cover_dir?: string;
};

export type SettingsSnapshot = {
  settings_path: string;
  ui: {
    theme: "dark" | "light";
    custom_theme_enabled: boolean;
  };
  auth: {
    remember_password: boolean;
    auto_login: boolean;
    last_user: string;
  };
  theme: {
    mode: "dark" | "light" | "custom";
    colors: Record<string, string>;
    custom_colors?: Record<"dark" | "light", Record<string, string>>;
  };
  disabled_tools: string[];
  disabled_plugins: string[];
  tool_settings: Record<string, ToolSettings>;
  sidebar_order: string[];
  tools: ToolItem[];
};

export type SettingsPatch = {
  task_id?: string;
  updates: {
    "ui/theme"?: "dark" | "light";
    "ui/custom_theme_enabled"?: boolean;
    "auth/remember_password"?: boolean;
    "auth/auto_login"?: boolean;
    "tools/disabled"?: string[];
    "plugins/disabled"?: string[];
    "base64/output_dir"?: string;
    "music/output_dir"?: string;
    "zipandpng/output_dir"?: string;
    "mp4mp3/output_dir"?: string;
    "imageconvert/output_dir"?: string;
    "pdftools/output_dir"?: string;
    "directdownloader/output_dir"?: string;
    "batchrename/input_dir"?: string;
    "batchrename/prefix"?: string;
    "batchrename/group_mode"?: string;
    "batchrename/sort_mode"?: string;
    "batchrename/sort_order"?: string;
    "filesorter/input_dir"?: string;
    "filesorter/mode"?: string;
    [key: `filesorter/category_${string}`]: boolean | undefined;
    "archive_extractor/output_dir"?: string;
    "same/input_dir"?: string;
    "same/recursive"?: boolean;
    "directdownloader/connections"?: string;
    "directdownloader/overwrite"?: boolean;
    "directdownloader/output_subdir_by_filename"?: boolean;
    "directdownloader/proxy_url"?: string;
    "directdownloader/referer"?: string;
    "wordformatter/output_dir"?: string;
    "wordformatter/page/top_margin_cm"?: number | string;
    "wordformatter/page/bottom_margin_cm"?: number | string;
    "wordformatter/page/left_margin_cm"?: number | string;
    "wordformatter/page/right_margin_cm"?: number | string;
    "wordformatter/page/header_distance_cm"?: number | string;
    "wordformatter/page/footer_distance_cm"?: number | string;
    "wordformatter/styles/heading1/font"?: string;
    "wordformatter/styles/heading1/bold"?: boolean | string;
    "wordformatter/styles/body/font"?: string;
    "wordformatter/styles/body/line_spacing"?: number | string;
    [key: `wordformatter/styles/${string}/${string}`]: unknown;
    "video_downloader/api_id"?: string;
    "video_downloader/api_hash"?: string;
    "video_downloader/phone"?: string;
    "video_downloader/phone_code_hash"?: string;
    "video_downloader/web/output_dir"?: string;
    "video_downloader/web/proxy_host"?: string;
    "video_downloader/web/proxy_port"?: string;
    "video_downloader/web/proxy_url"?: string;
    "video_downloader/web/overwrite"?: boolean;
    "video_downloader/web/output_subdir_by_title"?: boolean;
    "video_downloader/web/concurrent"?: string;
    "video_downloader/web/cover_dir"?: string;
    "video_downloader/telegram/output_dir"?: string;
    "video_downloader/telegram/proxy_host"?: string;
    "video_downloader/telegram/proxy_port"?: string;
    "video_downloader/telegram/proxy_url"?: string;
    "video_downloader/telegram/recent_limit"?: string;
    "video_downloader/telegram/all_messages"?: boolean;
    "video_downloader/telegram/date_from"?: string;
    "video_downloader/telegram/date_to"?: string;
    "video_downloader/telegram/include_videos"?: boolean;
    "video_downloader/telegram/include_photos"?: boolean;
    "video_downloader/telegram/overwrite"?: boolean;
    "video_downloader/telegram/output_subdir_by_title"?: boolean;
    "video_downloader/telegram/concurrent"?: string;
    "video_downloader/telegram/cover_dir"?: string;
    "sidebar/order"?: string[];
    [key: string]: unknown;
  };
};

export type DialogFilter = {
  name: string;
  extensions: string[];
};

export type PathDialogOptions = {
  title?: string;
  defaultPath?: string;
  filters?: DialogFilter[];
  multiple?: boolean;
};

type TauriWindow = Window & { __TAURI_INTERNALS__?: unknown };

function isTauriRuntime(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in (window as TauriWindow);
}

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

function runBrowserToolFallback(toolId: string, input: ToolInput): ToolResult {
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

export function runTool(toolId: string, input: ToolInput): Promise<ToolResult> {
  if (!isTauriRuntime()) {
    return Promise.resolve(runBrowserToolFallback(toolId, input));
  }
  return invoke<ToolResult>("run_tool", { toolId, input });
}

const browserThemeColors: Record<"dark" | "light", SettingsSnapshot["theme"]["colors"]> = {
  dark: {
    window_bg: "#1b1f25",
    surface_bg: "#1f2329",
    card_bg: "rgba(44, 50, 59, 0.88)",
    accent: "#6f95c7",
    text_primary: "#eef2f7",
    text_secondary: "#9aa6b5",
    input_bg: "#2a3038",
  },
  light: {
    window_bg: "#e5e9ef",
    surface_bg: "#eef1f5",
    card_bg: "rgba(255, 255, 255, 0.76)",
    accent: "#e4efff",
    text_primary: "#1f252d",
    text_secondary: "#697586",
    input_bg: "#eef1f5",
  },
};

const THEME_ZONES = ["window_bg", "surface_bg", "card_bg", "accent", "text_primary", "text_secondary", "input_bg"] as const;
const FILESORTER_CATEGORIES = ["图片", "视频", "音频", "文档", "压缩包", "程序", "其他"] as const;
const WORD_FORMATTER_PAGE_KEYS = [
  "top_margin_cm",
  "bottom_margin_cm",
  "left_margin_cm",
  "right_margin_cm",
  "header_distance_cm",
  "footer_distance_cm",
] as const;
const WORD_FORMATTER_STYLE_KEYS = ["heading1", "heading2", "heading3", "heading4", "body", "table"] as const;
const WORD_FORMATTER_STYLE_FIELDS = ["font", "size_pt", "bold", "line_spacing", "space_before_pt", "space_after_pt", "first_line_indent_cm"] as const;
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
function defaultFilesorterCategories(): Record<string, boolean> {
  return Object.fromEntries(FILESORTER_CATEGORIES.map((category) => [category, true]));
}

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
    prefix: "\u6279\u91cf\u547d\u540d",
    group_mode: "\u6309\u540e\u7f00",
    sort_mode: "\u6309\u547d\u540d",
    sort_order: "\u4ece\u5c0f\u5230\u5927",
  },
  filesorter: { input_dir: "", mode: "\u6309\u5927\u7c7b\u5206\u7c7b", categories: defaultFilesorterCategories() },
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

function browserSettingsFallback(): SettingsSnapshot {
  browserSnapshot ??= buildBrowserSettingsSnapshot("light", [], []);
  return browserSnapshot;
}

export function loadSettingsSnapshot(): Promise<SettingsSnapshot> {
  if (!isTauriRuntime()) {
    return Promise.resolve(browserSettingsFallback());
  }
  return invoke<SettingsSnapshot>("load_settings_snapshot");
}

function patchString(updates: SettingsPatch["updates"], key: string, current = ""): string {
  const value = updates[key];
  return typeof value === "string" ? value : current;
}

function patchBoolean(updates: SettingsPatch["updates"], key: string, current = false): boolean {
  const value = updates[key];
  return typeof value === "boolean" ? value : current;
}

function patchNumberOrString(updates: SettingsPatch["updates"], key: string, current: number | string): number | string {
  const value = updates[key];
  return typeof value === "number" || typeof value === "string" ? value : current;
}

function patchWordFormatterBold(updates: SettingsPatch["updates"], key: string, current = false): boolean {
  const value = updates[key];
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (["true", "1", "yes"].includes(normalized)) {
      return true;
    }
    if (["false", "0", "no"].includes(normalized)) {
      return false;
    }
  }
  return current;
}

function patchWordFormatterSettings(updates: SettingsPatch["updates"], current: ToolSettings = browserWordFormatterSettings): ToolSettings {
  const page = { ...(browserWordFormatterSettings.page ?? {}), ...(current.page ?? {}) };
  WORD_FORMATTER_PAGE_KEYS.forEach((key) => {
    page[key] = patchNumberOrString(updates, `wordformatter/page/${key}`, page[key] ?? "");
  });
  const styles: Record<string, WordFormatterStyleSettings> = {};
  WORD_FORMATTER_STYLE_KEYS.forEach((styleKey) => {
    const baseStyle = browserWordFormatterSettings.styles?.[styleKey] ?? {};
    const currentStyle = current.styles?.[styleKey] ?? {};
    const nextStyle: WordFormatterStyleSettings = { ...baseStyle, ...currentStyle };
    WORD_FORMATTER_STYLE_FIELDS.forEach((field) => {
      const updateKey = `wordformatter/styles/${styleKey}/${field}`;
      if (field === "font") {
        nextStyle.font = patchString(updates, updateKey, String(nextStyle.font ?? ""));
      } else if (field === "bold") {
        nextStyle.bold = patchWordFormatterBold(updates, updateKey, Boolean(nextStyle.bold));
      } else {
        nextStyle[field] = patchNumberOrString(updates, updateKey, nextStyle[field] ?? "");
      }
    });
    styles[styleKey] = nextStyle;
  });
  return {
    output_dir: patchString(updates, "wordformatter/output_dir", current.output_dir ?? ""),
    page,
    styles,
  };
}

function patchFilesorterCategories(updates: SettingsPatch["updates"], current: ToolSettings["categories"] = {}): Record<string, boolean> {
  const categories = { ...defaultFilesorterCategories(), ...(current ?? {}) };
  FILESORTER_CATEGORIES.forEach((category) => {
    const value = updates[`filesorter/category_${category}`];
    if (typeof value === "boolean") {
      categories[category] = value;
    }
  });
  return categories;
}

function browserProxyUrl(host = "127.0.0.1", port = "", legacyProxyUrl = ""): string {
  const cleanHost = host.trim();
  const cleanPort = port.trim();
  const cleanLegacy = legacyProxyUrl.trim();
  if (!cleanHost && !cleanPort) {
    return cleanLegacy && cleanLegacy.includes(":") ? (cleanLegacy.includes("://") ? cleanLegacy : `http://${cleanLegacy}`) : "";
  }
  if (!cleanPort) {
    return cleanHost.includes("://") && /:\d+(?:\/)?$/.test(cleanHost) ? cleanHost : "";
  }
  if (cleanHost.includes("://")) {
    return cleanHost.replace(/(?::\d+)?(?:\/)?$/, `:${cleanPort}`);
  }
  return `http://${(cleanHost || "127.0.0.1").split(":")[0]}:${cleanPort}`;
}

function patchVideoDownloaderSettings(patch: SettingsPatch, current: SettingsSnapshot["tool_settings"]): Pick<SettingsSnapshot["tool_settings"], "webvideodownloader" | "tgdownloader"> {
  const web = current.webvideodownloader ?? {};
  const tg = current.tgdownloader ?? {};
  const webProxyHost = patchString(patch.updates, "video_downloader/web/proxy_host", web.proxy_host ?? "127.0.0.1");
  const webProxyPort = patchString(patch.updates, "video_downloader/web/proxy_port", web.proxy_port ?? "");
  const tgProxyHost = patchString(patch.updates, "video_downloader/telegram/proxy_host", tg.proxy_host ?? "127.0.0.1");
  const tgProxyPort = patchString(patch.updates, "video_downloader/telegram/proxy_port", tg.proxy_port ?? "");
  return {
    webvideodownloader: {
      output_dir: patchString(patch.updates, "video_downloader/web/output_dir", web.output_dir ?? ""),
      proxy_host: webProxyHost,
      proxy_port: webProxyPort,
      proxy_url: patchString(patch.updates, "video_downloader/web/proxy_url", browserProxyUrl(webProxyHost, webProxyPort, web.proxy_url ?? "")),
      overwrite: patchBoolean(patch.updates, "video_downloader/web/overwrite", web.overwrite ?? false),
      output_subdir_by_title: patchBoolean(patch.updates, "video_downloader/web/output_subdir_by_title", web.output_subdir_by_title ?? false),
      concurrent: patchString(patch.updates, "video_downloader/web/concurrent", web.concurrent ?? "1"),
      cover_dir: patchString(patch.updates, "video_downloader/web/cover_dir", web.cover_dir ?? ""),
    },
    tgdownloader: {
      api_id: patchString(patch.updates, "video_downloader/api_id", tg.api_id ?? ""),
      api_hash: patchString(patch.updates, "video_downloader/api_hash", tg.api_hash ?? ""),
      phone: patchString(patch.updates, "video_downloader/phone", tg.phone ?? ""),
      phone_code_hash: patchString(patch.updates, "video_downloader/phone_code_hash", tg.phone_code_hash ?? ""),
      output_dir: patchString(patch.updates, "video_downloader/telegram/output_dir", tg.output_dir ?? ""),
      proxy_host: tgProxyHost,
      proxy_port: tgProxyPort,
      proxy_url: patchString(patch.updates, "video_downloader/telegram/proxy_url", browserProxyUrl(tgProxyHost, tgProxyPort, tg.proxy_url ?? "")),
      recent_limit: patchString(patch.updates, "video_downloader/telegram/recent_limit", tg.recent_limit ?? "500"),
      all_messages: patchBoolean(patch.updates, "video_downloader/telegram/all_messages", tg.all_messages ?? false),
      date_from: patchString(patch.updates, "video_downloader/telegram/date_from", tg.date_from ?? ""),
      date_to: patchString(patch.updates, "video_downloader/telegram/date_to", tg.date_to ?? ""),
      include_videos: patchBoolean(patch.updates, "video_downloader/telegram/include_videos", tg.include_videos ?? true),
      include_photos: patchBoolean(patch.updates, "video_downloader/telegram/include_photos", tg.include_photos ?? false),
      overwrite: patchBoolean(patch.updates, "video_downloader/telegram/overwrite", tg.overwrite ?? false),
      output_subdir_by_title: patchBoolean(patch.updates, "video_downloader/telegram/output_subdir_by_title", tg.output_subdir_by_title ?? false),
      concurrent: patchString(patch.updates, "video_downloader/telegram/concurrent", tg.concurrent ?? "1"),
      cover_dir: patchString(patch.updates, "video_downloader/telegram/cover_dir", tg.cover_dir ?? ""),
    },
  };
}

export function saveSettingsPatch(patch: SettingsPatch): Promise<SettingsSnapshot> {
  if (!isTauriRuntime()) {
    const current = browserSettingsFallback();
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
      wordformatter: patchWordFormatterSettings(patch.updates, current.tool_settings.wordformatter),
      batchrename: {
        input_dir: patchString(patch.updates, "batchrename/input_dir", current.tool_settings.batchrename?.input_dir ?? ""),
        prefix: patchString(patch.updates, "batchrename/prefix", current.tool_settings.batchrename?.prefix ?? "\u6279\u91cf\u547d\u540d"),
        group_mode: patchString(patch.updates, "batchrename/group_mode", current.tool_settings.batchrename?.group_mode ?? "\u6309\u540e\u7f00"),
        sort_mode: patchString(patch.updates, "batchrename/sort_mode", current.tool_settings.batchrename?.sort_mode ?? "\u6309\u547d\u540d"),
        sort_order: patchString(patch.updates, "batchrename/sort_order", current.tool_settings.batchrename?.sort_order ?? "\u4ece\u5c0f\u5230\u5927"),
      },
      filesorter: {
        input_dir: patchString(patch.updates, "filesorter/input_dir", current.tool_settings.filesorter?.input_dir ?? ""),
        mode: patchString(patch.updates, "filesorter/mode", current.tool_settings.filesorter?.mode ?? "\u6309\u5927\u7c7b\u5206\u7c7b"),
        categories: patchFilesorterCategories(patch.updates, current.tool_settings.filesorter?.categories),
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
    return Promise.resolve(browserSnapshot);
  }
  return invoke<SettingsSnapshot>("save_settings_patch", { input: patch });
}

async function pickPath(mode: "file" | "directory" | "save", options: PathDialogOptions = {}): Promise<string[] | null> {
  if (!isTauriRuntime()) {
    return null;
  }
  return invoke<string[] | null>("pick_path", {
    options: {
      mode,
      title: options.title,
      default_path: options.defaultPath,
      filters: options.filters ?? [],
      multiple: options.multiple ?? false,
    },
  });
}

export async function pickFile(options: PathDialogOptions = {}): Promise<string | null> {
  const paths = await pickPath("file", { ...options, multiple: false });
  return paths?.[0] ?? null;
}

export async function pickFiles(options: PathDialogOptions = {}): Promise<string[] | null> {
  return pickPath("file", { ...options, multiple: true });
}

export async function pickDirectory(options: PathDialogOptions = {}): Promise<string | null> {
  const paths = await pickPath("directory", options);
  return paths?.[0] ?? null;
}

export async function pickSaveFile(options: PathDialogOptions = {}): Promise<string | null> {
  const paths = await pickPath("save", options);
  return paths?.[0] ?? null;
}
