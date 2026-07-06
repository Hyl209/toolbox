import { invoke } from "@tauri-apps/api/core";
import { loadBrowserSettingsSnapshot, runBrowserToolFallback, saveBrowserSettingsPatch } from "./browserFallback";

export type ToolInput = {
  task_id: string;
  action: string;
  payload: Record<string, unknown>;
};

export type AiImageProfile = {
  id: string;
  name: string;
  base_url: string;
  model: string;
  secret_ref: string;
  created_at: string;
  updated_at: string;
};

export type AiImageConfig = {
  selected_profile_id: string;
  output_dir: string;
  default_size: string;
  default_count: number;
  profiles: AiImageProfile[];
};

export type AiImageArtifact = {
  path: string;
  filename: string;
  mime: string;
  width?: number;
  height?: number;
};

export type AiImageHistoryItem = {
  id: string;
  created_at?: string;
  title?: string;
  prompt: string;
  negativePrompt?: string;
  size: string;
  quality?: string;
  outputFormat?: string;
  outputCompression?: number;
  background?: string;
  moderation?: string;
  referenceImages?: string[];
  count?: number;
  status?: "running" | "success" | "error";
  startedAt?: number;
  finishedAt?: number;
  outputDir?: string;
  images?: Array<AiImageArtifact>;
  error?: string;
};

export type ToolHistoryItem = {
  id: string;
  created_at?: string;
  status?: "success" | "error" | string;
  input?: Record<string, unknown>;
  output_dir?: string;
  files?: string[];
  success_count?: number;
  fail_count?: number;
  errors?: string[];
  results?: Array<Record<string, unknown>>;
};

export type ToolResult = {
  text?: string;
  output_path?: string;
  mime?: string;
  images?: Array<AiImageArtifact>;
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
  items?: Array<ToolHistoryItem | AiImageHistoryItem>;
  history_id?: string;
  data?: {
    text?: string;
    output_path?: string;
    mime?: string;
    images?: Array<AiImageArtifact>;
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
    items?: Array<ToolHistoryItem | AiImageHistoryItem>;
    history_id?: string;
  };
};

export type ToolSessionControlAction = "pause" | "resume" | "cancel" | "reconnect";

export type ToolActivityState = "ready" | "running" | "success" | "error";

export type ToolSessionSnapshot = {
  session_id: string;
  tool_id: string;
  status: "running" | "paused" | "completed" | "failed" | "cancelled";
  paused: boolean;
  pid?: number | null;
  result?: ToolResult | null;
  error?: string | null;
  exit_code?: number | null;
  logs: string[];
  progress_events: Array<Record<string, unknown>>;
  stderr?: string;
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
  dependencies?: string[];
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
  // 兼容旧版配置的派生字段；新 UI 以 host/port 为主。
  proxy_url?: string;
  referer?: string;
  api_id?: string;
  api_hash?: string;
  phone?: string;
  // 兼容旧版 Telegram 登录状态回写，新设置页暂不直接编辑。
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
    background_enabled: boolean;
    background_image: string;
    background_opacity: number;
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
    "ui/background_enabled"?: boolean;
    "ui/background_image"?: string;
    "ui/background_opacity"?: number;
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
    // 兼容旧版 Telegram 登录状态回写，新设置页暂不直接编辑。
    "video_downloader/phone_code_hash"?: string;
    "video_downloader/web/output_dir"?: string;
    "video_downloader/web/proxy_host"?: string;
    "video_downloader/web/proxy_port"?: string;
    // 兼容旧版配置的派生字段；新 UI 以 host/port 为主。
    "video_downloader/web/proxy_url"?: string;
    "video_downloader/web/overwrite"?: boolean;
    "video_downloader/web/output_subdir_by_title"?: boolean;
    "video_downloader/web/concurrent"?: string;
    "video_downloader/web/cover_dir"?: string;
    "video_downloader/telegram/output_dir"?: string;
    "video_downloader/telegram/proxy_host"?: string;
    "video_downloader/telegram/proxy_port"?: string;
    // 兼容旧版配置的派生字段；新 UI 以 host/port 为主。
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

export const TOOL_ACTIVITY_EVENT = "hyl-tool-activity";

type ToolActivityDetail = {
  toolId: string;
  state: ToolActivityState;
};

const SESSION_MANAGED_TOOL_IDS = new Set(["directdownloader", "webvideodownloader", "tgdownloader"]);

function isTauriRuntime(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in (window as TauriWindow);
}

function emitToolActivity(toolId: string, state: ToolActivityState) {
  if (typeof window === "undefined") {
    return;
  }
  window.dispatchEvent(new CustomEvent<ToolActivityDetail>(TOOL_ACTIVITY_EVENT, { detail: { toolId, state } }));
}

function shouldTrackToolAction(toolId: string, action: string): boolean {
  return !SESSION_MANAGED_TOOL_IDS.has(toolId) && !["probe", "probe_ocr", "default_config"].includes(action);
}

export function runTool(toolId: string, input: ToolInput): Promise<ToolResult> {
  if (!isTauriRuntime()) {
    return Promise.resolve(runBrowserToolFallback(toolId, input));
  }
  const tracked = shouldTrackToolAction(toolId, input.action);
  if (tracked) {
    emitToolActivity(toolId, "running");
  }
  return invoke<ToolResult>("run_tool", { toolId, input })
    .then((result) => {
      if (tracked) {
        emitToolActivity(toolId, "success");
      }
      return result;
    })
    .catch((error) => {
      if (tracked) {
        emitToolActivity(toolId, "error");
      }
      throw error;
    });
}

function unsupportedRuntimeSession(): never {
  throw new Error("download runtime sessions require the Tauri desktop runtime");
}

export function startToolSession(toolId: string, input: ToolInput): Promise<ToolSessionSnapshot> {
  if (!isTauriRuntime()) {
    unsupportedRuntimeSession();
  }
  emitToolActivity(toolId, "running");
  return invoke<ToolSessionSnapshot>("start_tool_session", { toolId, input });
}

export function pollToolSession(sessionId: string): Promise<ToolSessionSnapshot> {
  if (!isTauriRuntime()) {
    unsupportedRuntimeSession();
  }
  return invoke<ToolSessionSnapshot>("poll_tool_session", { sessionId });
}

export function controlToolSession(sessionId: string, action: ToolSessionControlAction): Promise<ToolSessionSnapshot> {
  if (!isTauriRuntime()) {
    unsupportedRuntimeSession();
  }
  return invoke<ToolSessionSnapshot>("control_tool_session", { sessionId, action });
}

export function cleanupToolSession(sessionId: string): Promise<{ session_id: string; removed: boolean }> {
  if (!isTauriRuntime()) {
    unsupportedRuntimeSession();
  }
  return invoke<{ session_id: string; removed: boolean }>("cleanup_tool_session", { sessionId });
}

export function loadSettingsSnapshot(): Promise<SettingsSnapshot> {
  if (!isTauriRuntime()) {
    return Promise.resolve(loadBrowserSettingsSnapshot());
  }
  return invoke<SettingsSnapshot>("load_settings_snapshot");
}

export function loadSupportImage(): Promise<string> {
  if (!isTauriRuntime()) {
    return Promise.resolve("");
  }
  return invoke<string>("load_support_image");
}

export function logoutCurrentUser(): Promise<void> {
  if (!isTauriRuntime()) {
    return Promise.resolve();
  }
  return invoke<void>("logout_current_user");
}

export function saveSettingsPatch(patch: SettingsPatch): Promise<SettingsSnapshot> {
  if (!isTauriRuntime()) {
    return Promise.resolve(saveBrowserSettingsPatch(patch));
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
