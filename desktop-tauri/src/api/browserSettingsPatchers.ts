import type { SettingsPatch, SettingsSnapshot, ToolSettings, WordFormatterStyleSettings } from "./tauri";

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

export function patchString(updates: SettingsPatch["updates"], key: string, current = ""): string {
  const value = updates[key];
  return typeof value === "string" ? value : current;
}

export function patchBoolean(updates: SettingsPatch["updates"], key: string, current = false): boolean {
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

export function patchWordFormatterSettings(
  updates: SettingsPatch["updates"],
  browserWordFormatterSettings: ToolSettings,
  current: ToolSettings = browserWordFormatterSettings,
): ToolSettings {
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

export function patchFilesorterCategories(
  updates: SettingsPatch["updates"],
  current: ToolSettings["categories"] = {},
  defaultFilesorterCategories: () => Record<string, boolean>,
): Record<string, boolean> {
  const categories = { ...defaultFilesorterCategories(), ...(current ?? {}) };
  FILESORTER_CATEGORIES.forEach((category) => {
    const value = updates[`filesorter/category_${category}`];
    if (typeof value === "boolean") {
      categories[category] = value;
    }
  });
  return categories;
}

export function browserProxyUrl(host = "127.0.0.1", port = "", legacyProxyUrl = ""): string {
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

export function patchVideoDownloaderSettings(
  patch: SettingsPatch,
  current: SettingsSnapshot["tool_settings"],
): Pick<SettingsSnapshot["tool_settings"], "webvideodownloader" | "tgdownloader"> {
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
