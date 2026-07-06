import type { SettingsPatch, SettingsSnapshot, ToolItem } from "../../api/tauri";
import { sidebarOrderForSave } from "./helpers";
import {
  DEFAULT_THEME_COLORS,
  FILESORTER_CATEGORIES,
  type SettingsDraftState,
  THEME_NAMES,
  THEME_ZONES,
  WORD_FORMATTER_PAGE_KEYS,
  WORD_FORMATTER_PAGE_SETTING_KEYS,
  WORD_FORMATTER_STYLE_FIELDS,
  WORD_FORMATTER_STYLE_KEYS,
  WORD_FORMATTER_STYLE_SETTING_KEYS,
} from "./models";

export type BuildSettingsUpdatesInput = {
  snapshot: SettingsSnapshot;
  drafts: SettingsDraftState;
  toolsById: ReadonlyMap<string, ToolItem>;
};

export function buildSettingsUpdates({ snapshot, drafts, toolsById }: BuildSettingsUpdatesInput): SettingsPatch["updates"] {
  const updates: SettingsPatch["updates"] = {
    "ui/theme": drafts.theme,
    "ui/custom_theme_enabled": drafts.customThemeEnabled,
    "ui/background_enabled": drafts.backgroundEnabled,
    "ui/background_image": drafts.backgroundImage,
    "ui/background_opacity": drafts.backgroundOpacity,
    "auth/remember_password": drafts.rememberPassword,
    "auth/auto_login": drafts.autoLogin,
    "tools/disabled": [...drafts.disabledTools].sort(),
    "plugins/disabled": [...drafts.disabledPlugins].sort(),
    "base64/output_dir": drafts.toolOutputDirs.base64,
    "music/output_dir": drafts.toolOutputDirs.music,
    "zipandpng/output_dir": drafts.toolOutputDirs.zipandpng,
    "mp4mp3/output_dir": drafts.toolOutputDirs.mp4mp3,
    "imageconvert/output_dir": drafts.toolOutputDirs.imageconvert,
    "pdftools/output_dir": drafts.toolOutputDirs.pdftools,
    "directdownloader/output_dir": drafts.toolOutputDirs.directdownloader,
    "archive_extractor/output_dir": drafts.toolOutputDirs.archive_extractor,
    "batchrename/input_dir": drafts.toolBehavior.batchrename.input_dir,
    "batchrename/prefix": drafts.toolBehavior.batchrename.prefix,
    "batchrename/group_mode": drafts.toolBehavior.batchrename.group_mode,
    "batchrename/sort_mode": drafts.toolBehavior.batchrename.sort_mode,
    "batchrename/sort_order": drafts.toolBehavior.batchrename.sort_order,
    "filesorter/input_dir": drafts.toolBehavior.filesorter.input_dir,
    "filesorter/mode": drafts.toolBehavior.filesorter.mode,
    "same/input_dir": drafts.toolBehavior.same.input_dir,
    "same/recursive": drafts.toolBehavior.same.recursive,
    "directdownloader/connections": drafts.toolBehavior.directdownloader.connections,
    "directdownloader/overwrite": drafts.toolBehavior.directdownloader.overwrite,
    "directdownloader/output_subdir_by_filename": drafts.toolBehavior.directdownloader.output_subdir_by_filename,
    "directdownloader/proxy_url": drafts.toolBehavior.directdownloader.proxy_url,
    "directdownloader/referer": drafts.toolBehavior.directdownloader.referer,
    "video_downloader/api_id": drafts.downloader.tgdownloader.api_id,
    "video_downloader/api_hash": drafts.downloader.tgdownloader.api_hash,
    "video_downloader/phone": drafts.downloader.tgdownloader.phone,
    "video_downloader/web/output_dir": drafts.downloader.webvideodownloader.output_dir,
    "video_downloader/web/proxy_host": drafts.downloader.webvideodownloader.proxy_host,
    "video_downloader/web/proxy_port": drafts.downloader.webvideodownloader.proxy_port,
    "video_downloader/web/proxy_url": drafts.downloader.webvideodownloader.proxy_url,
    "video_downloader/web/overwrite": drafts.downloader.webvideodownloader.overwrite,
    "video_downloader/web/output_subdir_by_title": drafts.downloader.webvideodownloader.output_subdir_by_title,
    "video_downloader/web/concurrent": drafts.downloader.webvideodownloader.concurrent,
    "video_downloader/web/cover_dir": drafts.downloader.webvideodownloader.cover_dir,
    "video_downloader/telegram/output_dir": drafts.downloader.tgdownloader.output_dir,
    "video_downloader/telegram/proxy_host": drafts.downloader.tgdownloader.proxy_host,
    "video_downloader/telegram/proxy_port": drafts.downloader.tgdownloader.proxy_port,
    "video_downloader/telegram/proxy_url": drafts.downloader.tgdownloader.proxy_url,
    "video_downloader/telegram/recent_limit": drafts.downloader.tgdownloader.recent_limit,
    "video_downloader/telegram/all_messages": drafts.downloader.tgdownloader.all_messages,
    "video_downloader/telegram/date_from": drafts.downloader.tgdownloader.date_from,
    "video_downloader/telegram/date_to": drafts.downloader.tgdownloader.date_to,
    "video_downloader/telegram/include_videos": drafts.downloader.tgdownloader.include_videos,
    "video_downloader/telegram/include_photos": drafts.downloader.tgdownloader.include_photos,
    "video_downloader/telegram/overwrite": drafts.downloader.tgdownloader.overwrite,
    "video_downloader/telegram/output_subdir_by_title": drafts.downloader.tgdownloader.output_subdir_by_title,
    "video_downloader/telegram/concurrent": drafts.downloader.tgdownloader.concurrent,
    "video_downloader/telegram/cover_dir": drafts.downloader.tgdownloader.cover_dir,
    "wordformatter/output_dir": drafts.wordFormatter.output_dir,
    "sidebar/order": sidebarOrderForSave(snapshot, drafts.sidebarOrder, toolsById),
  };

  WORD_FORMATTER_PAGE_KEYS.forEach((key) => {
    updates[WORD_FORMATTER_PAGE_SETTING_KEYS[key]] = drafts.wordFormatter.page[key];
  });

  WORD_FORMATTER_STYLE_KEYS.forEach((styleKey) => {
    WORD_FORMATTER_STYLE_FIELDS.forEach((field) => {
      updates[WORD_FORMATTER_STYLE_SETTING_KEYS[styleKey][field]] = drafts.wordFormatter.styles[styleKey][field];
    });
  });

  FILESORTER_CATEGORIES.forEach((category) => {
    updates[`filesorter/category_${category}`] = drafts.toolBehavior.filesorter.categories[category];
  });

  THEME_NAMES.forEach((theme) => {
    THEME_ZONES.forEach((zone) => {
      updates[`theme/${theme}/${zone}`] = drafts.themeColors[theme]?.[zone] ?? DEFAULT_THEME_COLORS[theme][zone];
    });
  });

  return updates;
}

export function buildSettingsPatch(input: BuildSettingsUpdatesInput, taskId: string): SettingsPatch {
  return {
    task_id: taskId,
    updates: buildSettingsUpdates(input),
  };
}
