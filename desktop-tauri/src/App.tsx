import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { loadSettingsSnapshot, saveSettingsPatch, type SettingsPatch, type SettingsSnapshot, type ToolItem, type ToolSettings } from "./api/tauri";
import ToolShell from "./components/ToolShell";
import ArchiveExtractorPluginTool from "./tools/ArchiveExtractorPluginTool";
import BatchRenameTool from "./tools/BatchRenameTool";
import Base64Tool from "./tools/Base64Tool";
import CsvToolsPluginTool from "./tools/CsvToolsPluginTool";
import DirectDownloaderTool from "./tools/DirectDownloaderTool";
import FileHasherPluginTool from "./tools/FileHasherPluginTool";
import FileSorterTool from "./tools/FileSorterTool";
import ImageConvertTool from "./tools/ImageConvertTool";
import JsonToolsPluginTool from "./tools/JsonToolsPluginTool";
import Mp4Mp3Tool from "./tools/Mp4Mp3Tool";
import MusicTool from "./tools/MusicTool";
import PdfToolsTool from "./tools/PdfToolsTool";
import RegexToolsPluginTool from "./tools/RegexToolsPluginTool";
import SameTool from "./tools/SameTool";
import TextToolsPluginTool from "./tools/TextToolsPluginTool";
import TgDownloaderTool from "./tools/TgDownloaderTool";
import TimestampToolsPluginTool from "./tools/TimestampToolsPluginTool";
import UrlToolsPluginTool from "./tools/UrlToolsPluginTool";
import WebVideoDownloaderTool from "./tools/WebVideoDownloaderTool";
import WordFormatterTool from "./tools/WordFormatterTool";
import UuidToolsPluginTool from "./tools/UuidToolsPluginTool";
import ZipPngTool from "./tools/ZipPngTool";
import toolManifest from "./tools/manifest";
import "./styles.css";

const fallbackTools: ToolItem[] = toolManifest.map((tool) => ({ ...tool, enabled: true, source: "builtin" }));

const capabilityNotes: Record<string, string> = {
  tgdownloader: "\u90e8\u5206\u53ef\u7528 \u00b7 \u4e0b\u8f7d/\u767b\u5f55",
  webvideodownloader: "\u90e8\u5206\u53ef\u7528 \u00b7 \u4e0b\u8f7d/\u9884\u68c0",
};

const THEME_ZONES = ["window_bg", "surface_bg", "card_bg", "accent", "text_primary", "text_secondary", "input_bg"] as const;
const TOOL_OUTPUT_DIRS = [
  { id: "base64", label: "Base64" },
  { id: "music", label: "NCM" },
  { id: "zipandpng", label: "PNG" },
  { id: "mp4mp3", label: "MP4" },
  { id: "imageconvert", label: "Image" },
  { id: "pdftools", label: "PDF" },
  { id: "directdownloader", label: "Direct" },
  { id: "archive_extractor", label: "Archive Extractor" },
] as const;
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
const WORD_FORMATTER_STYLE_TITLES: Record<(typeof WORD_FORMATTER_STYLE_KEYS)[number], string> = {
  heading1: "Heading 1",
  heading2: "Heading 2",
  heading3: "Heading 3",
  heading4: "Heading 4",
  body: "Body",
  table: "Table",
};
type ThemeName = "dark" | "light";
type ThemeZone = (typeof THEME_ZONES)[number];
type ThemeColors = Record<ThemeZone, string>;
type ToolOutputDirId = (typeof TOOL_OUTPUT_DIRS)[number]["id"];
type ToolOutputDirDraft = Record<ToolOutputDirId, string>;
type WordFormatterPageKey = (typeof WORD_FORMATTER_PAGE_KEYS)[number];
type WordFormatterStyleKey = (typeof WORD_FORMATTER_STYLE_KEYS)[number];
type WordFormatterStyleField = (typeof WORD_FORMATTER_STYLE_FIELDS)[number];
type WordFormatterStyleDraft = Record<WordFormatterStyleField, string | boolean>;
type WordFormatterDraft = {
  output_dir: string;
  page: Record<WordFormatterPageKey, string>;
  styles: Record<WordFormatterStyleKey, WordFormatterStyleDraft>;
};
type ToolBehaviorDraft = {
  batchrename: {
    input_dir: string;
    prefix: string;
    group_mode: string;
    sort_mode: string;
    sort_order: string;
  };
  filesorter: {
    input_dir: string;
    mode: string;
    categories: Record<string, boolean>;
  };
  same: {
    input_dir: string;
    recursive: boolean;
  };
  directdownloader: {
    connections: string;
    overwrite: boolean;
    output_subdir_by_filename: boolean;
    proxy_url: string;
    referer: string;
  };
};
type DownloaderSettingsDraft = {
  webvideodownloader: {
    output_dir: string;
    proxy_host: string;
    proxy_port: string;
    overwrite: boolean;
    output_subdir_by_title: boolean;
    concurrent: string;
    cover_dir: string;
  };
  tgdownloader: {
    api_id: string;
    api_hash: string;
    phone: string;
    output_dir: string;
    proxy_host: string;
    proxy_port: string;
    recent_limit: string;
    all_messages: boolean;
    date_from: string;
    date_to: string;
    include_videos: boolean;
    include_photos: boolean;
    overwrite: boolean;
    output_subdir_by_title: boolean;
    concurrent: string;
    cover_dir: string;
  };
};

const DEFAULT_WORD_FORMATTER_DRAFT: WordFormatterDraft = {
  output_dir: "",
  page: {
    top_margin_cm: "2.54",
    bottom_margin_cm: "2.54",
    left_margin_cm: "3.18",
    right_margin_cm: "3.18",
    header_distance_cm: "1.5",
    footer_distance_cm: "1.75",
  },
  styles: {
    heading1: { font: "Microsoft YaHei", size_pt: "18", bold: true, line_spacing: "1.5", space_before_pt: "12", space_after_pt: "6", first_line_indent_cm: "0" },
    heading2: { font: "Microsoft YaHei", size_pt: "16", bold: true, line_spacing: "1.5", space_before_pt: "10", space_after_pt: "6", first_line_indent_cm: "0" },
    heading3: { font: "Microsoft YaHei", size_pt: "14", bold: true, line_spacing: "1.5", space_before_pt: "8", space_after_pt: "4", first_line_indent_cm: "0" },
    heading4: { font: "Microsoft YaHei", size_pt: "12", bold: true, line_spacing: "1.5", space_before_pt: "6", space_after_pt: "4", first_line_indent_cm: "0" },
    body: { font: "Microsoft YaHei", size_pt: "12", bold: false, line_spacing: "1.5", space_before_pt: "0", space_after_pt: "0", first_line_indent_cm: "0.74" },
    table: { font: "Microsoft YaHei", size_pt: "10.5", bold: false, line_spacing: "1.2", space_before_pt: "0", space_after_pt: "0", first_line_indent_cm: "0" },
  },
};

const WORD_FORMATTER_PAGE_SETTING_KEYS: Record<WordFormatterPageKey, string> = {
  top_margin_cm: "wordformatter/page/top_margin_cm",
  bottom_margin_cm: "wordformatter/page/bottom_margin_cm",
  left_margin_cm: "wordformatter/page/left_margin_cm",
  right_margin_cm: "wordformatter/page/right_margin_cm",
  header_distance_cm: "wordformatter/page/header_distance_cm",
  footer_distance_cm: "wordformatter/page/footer_distance_cm",
};

const WORD_FORMATTER_STYLE_SETTING_KEYS: Record<WordFormatterStyleKey, Record<WordFormatterStyleField, string>> = {
  heading1: {
    font: "wordformatter/styles/heading1/font",
    size_pt: "wordformatter/styles/heading1/size_pt",
    bold: "wordformatter/styles/heading1/bold",
    line_spacing: "wordformatter/styles/heading1/line_spacing",
    space_before_pt: "wordformatter/styles/heading1/space_before_pt",
    space_after_pt: "wordformatter/styles/heading1/space_after_pt",
    first_line_indent_cm: "wordformatter/styles/heading1/first_line_indent_cm",
  },
  heading2: {
    font: "wordformatter/styles/heading2/font",
    size_pt: "wordformatter/styles/heading2/size_pt",
    bold: "wordformatter/styles/heading2/bold",
    line_spacing: "wordformatter/styles/heading2/line_spacing",
    space_before_pt: "wordformatter/styles/heading2/space_before_pt",
    space_after_pt: "wordformatter/styles/heading2/space_after_pt",
    first_line_indent_cm: "wordformatter/styles/heading2/first_line_indent_cm",
  },
  heading3: {
    font: "wordformatter/styles/heading3/font",
    size_pt: "wordformatter/styles/heading3/size_pt",
    bold: "wordformatter/styles/heading3/bold",
    line_spacing: "wordformatter/styles/heading3/line_spacing",
    space_before_pt: "wordformatter/styles/heading3/space_before_pt",
    space_after_pt: "wordformatter/styles/heading3/space_after_pt",
    first_line_indent_cm: "wordformatter/styles/heading3/first_line_indent_cm",
  },
  heading4: {
    font: "wordformatter/styles/heading4/font",
    size_pt: "wordformatter/styles/heading4/size_pt",
    bold: "wordformatter/styles/heading4/bold",
    line_spacing: "wordformatter/styles/heading4/line_spacing",
    space_before_pt: "wordformatter/styles/heading4/space_before_pt",
    space_after_pt: "wordformatter/styles/heading4/space_after_pt",
    first_line_indent_cm: "wordformatter/styles/heading4/first_line_indent_cm",
  },
  body: {
    font: "wordformatter/styles/body/font",
    size_pt: "wordformatter/styles/body/size_pt",
    bold: "wordformatter/styles/body/bold",
    line_spacing: "wordformatter/styles/body/line_spacing",
    space_before_pt: "wordformatter/styles/body/space_before_pt",
    space_after_pt: "wordformatter/styles/body/space_after_pt",
    first_line_indent_cm: "wordformatter/styles/body/first_line_indent_cm",
  },
  table: {
    font: "wordformatter/styles/table/font",
    size_pt: "wordformatter/styles/table/size_pt",
    bold: "wordformatter/styles/table/bold",
    line_spacing: "wordformatter/styles/table/line_spacing",
    space_before_pt: "wordformatter/styles/table/space_before_pt",
    space_after_pt: "wordformatter/styles/table/space_after_pt",
    first_line_indent_cm: "wordformatter/styles/table/first_line_indent_cm",
  },
};

const DEFAULT_THEME_COLORS: Record<ThemeName, ThemeColors> = {
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

function themeColorDraftsFromSnapshot(snapshot: SettingsSnapshot | null): Record<ThemeName, ThemeColors> {
  const drafts: Record<ThemeName, ThemeColors> = {
    dark: { ...DEFAULT_THEME_COLORS.dark },
    light: { ...DEFAULT_THEME_COLORS.light },
  };
  if (snapshot) {
    const customColors = snapshot.theme.custom_colors;
    if (customColors) {
      (["dark", "light"] as const).forEach((theme) => {
        drafts[theme] = { ...drafts[theme], ...customColors[theme] };
      });
    } else {
      drafts[snapshot.ui.theme] = { ...drafts[snapshot.ui.theme], ...snapshot.theme.colors };
    }
  }
  return drafts;
}

function firstSelectableTool(tools: readonly ToolItem[]): ToolItem {
  return tools.find((tool) => tool.enabled !== false) ?? tools[0];
}

function toolOutputDirsFromSnapshot(snapshot: SettingsSnapshot | null): ToolOutputDirDraft {
  return Object.fromEntries(
    TOOL_OUTPUT_DIRS.map((tool) => [tool.id, snapshot?.tool_settings?.[tool.id]?.output_dir ?? ""]),
  ) as ToolOutputDirDraft;
}

function toolOutputDir(snapshot: SettingsSnapshot | null, toolId: ToolOutputDirId): string {
  return snapshot?.tool_settings?.[toolId]?.output_dir ?? "";
}

function filesorterCategoriesFromSnapshot(settings?: ToolSettings): Record<string, boolean> {
  return Object.fromEntries(
    FILESORTER_CATEGORIES.map((category) => [category, settings?.categories?.[category] ?? true]),
  );
}

function toolBehaviorDraftsFromSnapshot(snapshot: SettingsSnapshot | null): ToolBehaviorDraft {
  const settings = snapshot?.tool_settings ?? {};
  return {
    batchrename: {
      input_dir: settings.batchrename?.input_dir ?? "",
      prefix: settings.batchrename?.prefix ?? "\u6279\u91cf\u547d\u540d",
      group_mode: settings.batchrename?.group_mode ?? "\u6309\u540e\u7f00",
      sort_mode: settings.batchrename?.sort_mode ?? "\u6309\u547d\u540d",
      sort_order: settings.batchrename?.sort_order ?? "\u4ece\u5c0f\u5230\u5927",
    },
    filesorter: {
      input_dir: settings.filesorter?.input_dir ?? "",
      mode: settings.filesorter?.mode ?? "\u6309\u5927\u7c7b\u5206\u7c7b",
      categories: filesorterCategoriesFromSnapshot(settings.filesorter),
    },
    same: {
      input_dir: settings.same?.input_dir ?? "",
      recursive: settings.same?.recursive ?? true,
    },
    directdownloader: {
      connections: settings.directdownloader?.connections ?? "16",
      overwrite: settings.directdownloader?.overwrite ?? false,
      output_subdir_by_filename: settings.directdownloader?.output_subdir_by_filename ?? false,
      proxy_url: settings.directdownloader?.proxy_url ?? "",
      referer: settings.directdownloader?.referer ?? "",
    },
  };
}

function toolBehaviorSettings(snapshot: SettingsSnapshot | null, toolId: "batchrename" | "filesorter" | "same" | "directdownloader"): ToolSettings {
  return snapshot?.tool_settings?.[toolId] ?? {};
}

function downloaderDraftFromSnapshot(snapshot: SettingsSnapshot | null): DownloaderSettingsDraft {
  const web = snapshot?.tool_settings?.webvideodownloader ?? {};
  const tg = snapshot?.tool_settings?.tgdownloader ?? {};
  return {
    webvideodownloader: {
      output_dir: web.output_dir ?? "",
      proxy_host: web.proxy_host ?? "127.0.0.1",
      proxy_port: web.proxy_port ?? "",
      overwrite: web.overwrite ?? false,
      output_subdir_by_title: web.output_subdir_by_title ?? false,
      concurrent: web.concurrent ?? "1",
      cover_dir: web.cover_dir ?? "",
    },
    tgdownloader: {
      api_id: tg.api_id ?? "",
      api_hash: tg.api_hash ?? "",
      phone: tg.phone ?? "",
      output_dir: tg.output_dir ?? "",
      proxy_host: tg.proxy_host ?? "127.0.0.1",
      proxy_port: tg.proxy_port ?? "",
      recent_limit: tg.recent_limit ?? "500",
      all_messages: tg.all_messages ?? false,
      date_from: tg.date_from ?? "",
      date_to: tg.date_to ?? "",
      include_videos: tg.include_videos ?? true,
      include_photos: tg.include_photos ?? false,
      overwrite: tg.overwrite ?? false,
      output_subdir_by_title: tg.output_subdir_by_title ?? false,
      concurrent: tg.concurrent ?? "1",
      cover_dir: tg.cover_dir ?? "",
    },
  };
}

function downloaderSettings(snapshot: SettingsSnapshot | null, toolId: "webvideodownloader" | "tgdownloader"): ToolSettings {
  return snapshot?.tool_settings?.[toolId] ?? {};
}

function wordFormatterDraftFromSnapshot(snapshot: SettingsSnapshot | null): WordFormatterDraft {
  const settings = snapshot?.tool_settings?.wordformatter ?? {};
  const draft: WordFormatterDraft = {
    output_dir: settings.output_dir ?? "",
    page: { ...DEFAULT_WORD_FORMATTER_DRAFT.page },
    styles: JSON.parse(JSON.stringify(DEFAULT_WORD_FORMATTER_DRAFT.styles)),
  };
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

function wordFormatterSettings(snapshot: SettingsSnapshot | null): ToolSettings {
  return snapshot?.tool_settings?.wordformatter ?? {};
}

function pluginConfigKey(tool: ToolItem): string {
  return tool.plugin_name ?? tool.id.replace(/^plugin:/, "");
}

function sidebarOrderForSave(snapshot: SettingsSnapshot, visibleOrder: string[], toolsById: Map<string, ToolItem>): string[] {
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

function toolDisplayName(tool: ToolItem): string {
  return tool.sidebar_label ?? tool.title;
}

function toolMetadata(tool: ToolItem): string[] {
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

function themeStyle(snapshot: SettingsSnapshot | null): CSSProperties {
  const colors = snapshot?.theme.colors;
  if (!colors) {
    return {};
  }
  return {
    "--legacy-window-bg": colors.window_bg,
    "--legacy-surface-bg": colors.surface_bg,
    "--legacy-card-bg": colors.card_bg,
    "--legacy-accent": colors.accent,
    "--legacy-text-primary": colors.text_primary,
    "--legacy-text-secondary": colors.text_secondary,
    "--legacy-input-bg": colors.input_bg,
  } as CSSProperties;
}

function SettingsPanel({
  snapshot,
  loading,
  error,
  onSaved,
}: {
  snapshot: SettingsSnapshot | null;
  loading: boolean;
  error: string;
  onSaved: (snapshot: SettingsSnapshot) => void;
}) {
  const [themeDraft, setThemeDraft] = useState<ThemeName>(snapshot?.ui.theme ?? "light");
  const [customThemeDraft, setCustomThemeDraft] = useState(snapshot?.ui.custom_theme_enabled ?? false);
  const [rememberPasswordDraft, setRememberPasswordDraft] = useState(snapshot?.auth.remember_password ?? false);
  const [autoLoginDraft, setAutoLoginDraft] = useState(snapshot?.auth.auto_login ?? false);
  const [themeColorsDraft, setThemeColorsDraft] = useState<Record<ThemeName, ThemeColors>>(() => themeColorDraftsFromSnapshot(snapshot));
  const [toolOutputDirDraft, setToolOutputDirDraft] = useState<ToolOutputDirDraft>(() => toolOutputDirsFromSnapshot(snapshot));
  const [toolBehaviorDraft, setToolBehaviorDraft] = useState<ToolBehaviorDraft>(() => toolBehaviorDraftsFromSnapshot(snapshot));
  const [downloaderDraft, setDownloaderDraft] = useState<DownloaderSettingsDraft>(() => downloaderDraftFromSnapshot(snapshot));
  const [wordFormatterDraft, setWordFormatterDraft] = useState<WordFormatterDraft>(() => wordFormatterDraftFromSnapshot(snapshot));
  const [disabledDraft, setDisabledDraft] = useState<Set<string>>(() => new Set(snapshot?.disabled_tools ?? []));
  const [disabledPluginDraft, setDisabledPluginDraft] = useState<Set<string>>(() => new Set(snapshot?.disabled_plugins ?? []));
  const [orderDraft, setOrderDraft] = useState<string[]>(() => (snapshot?.tools ?? fallbackTools).map((tool) => tool.id));
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    if (!snapshot) {
      return;
    }
    setThemeDraft(snapshot.ui.theme);
    setCustomThemeDraft(snapshot.ui.custom_theme_enabled);
    setRememberPasswordDraft(snapshot.auth.remember_password);
    setAutoLoginDraft(snapshot.auth.auto_login);
    setThemeColorsDraft(themeColorDraftsFromSnapshot(snapshot));
    setToolOutputDirDraft(toolOutputDirsFromSnapshot(snapshot));
    setToolBehaviorDraft(toolBehaviorDraftsFromSnapshot(snapshot));
    setDownloaderDraft(downloaderDraftFromSnapshot(snapshot));
    setWordFormatterDraft(wordFormatterDraftFromSnapshot(snapshot));
    setDisabledDraft(new Set(snapshot.disabled_tools));
    setDisabledPluginDraft(new Set(snapshot.disabled_plugins));
    setOrderDraft(snapshot.tools.map((tool) => tool.id));
    setNotice("");
  }, [snapshot]);

  const enabledTools = snapshot?.tools.filter((tool) => {
    if (tool.source === "plugin") {
      return tool.manifest_enabled !== false && !disabledPluginDraft.has(pluginConfigKey(tool));
    }
    return !disabledDraft.has(tool.id);
  }).length ?? fallbackTools.length;
  const disabledTools = disabledDraft.size;
  const disabledPlugins = disabledPluginDraft.size;
  const modeText = customThemeDraft ? "\u81ea\u5b9a\u4e49\u4e3b\u9898" : themeDraft === "dark" ? "\u591c\u665a\u6a21\u5f0f" : "\u767d\u5929\u6a21\u5f0f";
  const builtinTools = (snapshot?.tools ?? fallbackTools).filter((tool) => tool.source !== "plugin");
  const pluginTools = (snapshot?.tools ?? []).filter((tool) => tool.source === "plugin");
  const toolsById = useMemo(() => new Map((snapshot?.tools ?? fallbackTools).map((tool) => [tool.id, tool])), [snapshot]);
  const orderedTools = orderDraft.flatMap((toolId) => {
    const tool = toolsById.get(toolId);
    return tool ? [tool] : [];
  });

  function setToolEnabled(toolId: string, enabled: boolean) {
    const next = new Set(disabledDraft);
    if (enabled) {
      next.delete(toolId);
    } else {
      const enabledBuiltinCount = builtinTools.filter((tool) => tool.id !== toolId && !next.has(tool.id)).length;
      if (enabledBuiltinCount < 1) {
        setNotice("\u81f3\u5c11\u4fdd\u7559\u4e00\u4e2a\u5185\u7f6e\u5de5\u5177\u542f\u7528");
        return;
      }
      next.add(toolId);
    }
    setDisabledDraft(next);
    setNotice("");
  }

  function setPluginEnabled(tool: ToolItem, enabled: boolean) {
    if (tool.manifest_enabled === false && enabled) {
      setNotice("\u8be5\u63d2\u4ef6\u5df2\u5728 manifest \u4e2d\u7981\u7528\uff0c\u4e0d\u80fd\u5728\u6b64\u542f\u7528");
      return;
    }
    const key = pluginConfigKey(tool);
    const next = new Set(disabledPluginDraft);
    if (enabled) {
      next.delete(key);
    } else {
      next.add(key);
    }
    setDisabledPluginDraft(next);
    setNotice("");
  }

  function setRememberPassword(checked: boolean) {
    setRememberPasswordDraft(checked);
    if (!checked) {
      setAutoLoginDraft(false);
    }
    setNotice("");
  }

  function setAutoLogin(checked: boolean) {
    setAutoLoginDraft(checked);
    if (checked) {
      setRememberPasswordDraft(true);
    }
    setNotice("");
  }

  function moveSidebarItem(toolId: string, direction: -1 | 1) {
    const index = orderDraft.indexOf(toolId);
    const nextIndex = index + direction;
    if (index < 0 || nextIndex < 0 || nextIndex >= orderDraft.length) {
      return;
    }
    const next = [...orderDraft];
    [next[index], next[nextIndex]] = [next[nextIndex], next[index]];
    setOrderDraft(next);
    setNotice("");
  }

  function updateThemeColor(zone: ThemeZone, value: string) {
    setThemeColorsDraft((drafts) => ({
      ...drafts,
      [themeDraft]: {
        ...(drafts[themeDraft] ?? DEFAULT_THEME_COLORS[themeDraft]),
        [zone]: value,
      },
    }));
    setNotice("");
  }

  function updateToolOutputDir(toolId: ToolOutputDirId, value: string) {
    setToolOutputDirDraft((draft) => ({ ...draft, [toolId]: value }));
    setNotice("");
  }

  function updateToolBehavior<T extends keyof ToolBehaviorDraft, K extends keyof ToolBehaviorDraft[T]>(toolId: T, key: K, value: ToolBehaviorDraft[T][K]) {
    setToolBehaviorDraft((draft) => ({
      ...draft,
      [toolId]: {
        ...draft[toolId],
        [key]: value,
      },
    }));
    setNotice("");
  }

  function updateFilesorterCategory(category: string, enabled: boolean) {
    setToolBehaviorDraft((draft) => ({
      ...draft,
      filesorter: {
        ...draft.filesorter,
        categories: {
          ...draft.filesorter.categories,
          [category]: enabled,
        },
      },
    }));
    setNotice("");
  }

  function updateDownloader<T extends keyof DownloaderSettingsDraft, K extends keyof DownloaderSettingsDraft[T]>(toolId: T, key: K, value: DownloaderSettingsDraft[T][K]) {
    setDownloaderDraft((draft) => ({
      ...draft,
      [toolId]: {
        ...draft[toolId],
        [key]: value,
      },
    }));
    setNotice("");
  }

  function updateWordFormatterOutputDir(value: string) {
    setWordFormatterDraft((draft) => ({ ...draft, output_dir: value }));
    setNotice("");
  }

  function updateWordFormatterPage(key: WordFormatterPageKey, value: string) {
    setWordFormatterDraft((draft) => ({ ...draft, page: { ...draft.page, [key]: value } }));
    setNotice("");
  }

  function updateWordFormatterStyle(styleKey: WordFormatterStyleKey, field: WordFormatterStyleField, value: string | boolean) {
    setWordFormatterDraft((draft) => ({
      ...draft,
      styles: {
        ...draft.styles,
        [styleKey]: {
          ...draft.styles[styleKey],
          [field]: value,
        },
      },
    }));
    setNotice("");
  }

  function sidebarStatus(tool: ToolItem): string {
    if (tool.source === "plugin") {
      if (tool.manifest_enabled === false) {
        return "manifest \u5df2\u7981\u7528";
      }
      if (disabledPluginDraft.has(pluginConfigKey(tool))) {
        return "\u5df2\u7981\u7528";
      }
      return tool.status === "ready" ? "\u63d2\u4ef6 \u00b7 \u53ef\u7528" : "\u63d2\u4ef6 \u00b7 \u672a\u63a5\u5165";
    }
    if (tool.enabled === false || disabledDraft.has(tool.id)) {
      return "\u5df2\u7981\u7528";
    }
    return capabilityNotes[tool.id] ?? (tool.status === "ready" ? "\u5df2\u63a5\u5165" : "\u672a\u63a5\u5165");
  }

  async function saveSettings() {
    if (!snapshot || saving) {
      return;
    }
    setSaving(true);
    setNotice("");
    try {
      const updates: SettingsPatch["updates"] = {
        "ui/theme": themeDraft,
        "ui/custom_theme_enabled": customThemeDraft,
        "auth/remember_password": rememberPasswordDraft,
        "auth/auto_login": autoLoginDraft,
        "tools/disabled": [...disabledDraft].sort(),
        "plugins/disabled": [...disabledPluginDraft].sort(),
        "base64/output_dir": toolOutputDirDraft.base64,
        "music/output_dir": toolOutputDirDraft.music,
        "zipandpng/output_dir": toolOutputDirDraft.zipandpng,
        "mp4mp3/output_dir": toolOutputDirDraft.mp4mp3,
        "imageconvert/output_dir": toolOutputDirDraft.imageconvert,
        "pdftools/output_dir": toolOutputDirDraft.pdftools,
        "directdownloader/output_dir": toolOutputDirDraft.directdownloader,
        "archive_extractor/output_dir": toolOutputDirDraft.archive_extractor,
        "batchrename/input_dir": toolBehaviorDraft.batchrename.input_dir,
        "batchrename/prefix": toolBehaviorDraft.batchrename.prefix,
        "batchrename/group_mode": toolBehaviorDraft.batchrename.group_mode,
        "batchrename/sort_mode": toolBehaviorDraft.batchrename.sort_mode,
        "batchrename/sort_order": toolBehaviorDraft.batchrename.sort_order,
        "filesorter/input_dir": toolBehaviorDraft.filesorter.input_dir,
        "filesorter/mode": toolBehaviorDraft.filesorter.mode,
        "same/input_dir": toolBehaviorDraft.same.input_dir,
        "same/recursive": toolBehaviorDraft.same.recursive,
        "directdownloader/connections": toolBehaviorDraft.directdownloader.connections,
        "directdownloader/overwrite": toolBehaviorDraft.directdownloader.overwrite,
        "directdownloader/output_subdir_by_filename": toolBehaviorDraft.directdownloader.output_subdir_by_filename,
        "directdownloader/proxy_url": toolBehaviorDraft.directdownloader.proxy_url,
        "directdownloader/referer": toolBehaviorDraft.directdownloader.referer,
        "video_downloader/api_id": downloaderDraft.tgdownloader.api_id,
        "video_downloader/api_hash": downloaderDraft.tgdownloader.api_hash,
        "video_downloader/phone": downloaderDraft.tgdownloader.phone,
        "video_downloader/web/output_dir": downloaderDraft.webvideodownloader.output_dir,
        "video_downloader/web/proxy_host": downloaderDraft.webvideodownloader.proxy_host,
        "video_downloader/web/proxy_port": downloaderDraft.webvideodownloader.proxy_port,
        "video_downloader/web/overwrite": downloaderDraft.webvideodownloader.overwrite,
        "video_downloader/web/output_subdir_by_title": downloaderDraft.webvideodownloader.output_subdir_by_title,
        "video_downloader/web/concurrent": downloaderDraft.webvideodownloader.concurrent,
        "video_downloader/web/cover_dir": downloaderDraft.webvideodownloader.cover_dir,
        "video_downloader/telegram/output_dir": downloaderDraft.tgdownloader.output_dir,
        "video_downloader/telegram/proxy_host": downloaderDraft.tgdownloader.proxy_host,
        "video_downloader/telegram/proxy_port": downloaderDraft.tgdownloader.proxy_port,
        "video_downloader/telegram/recent_limit": downloaderDraft.tgdownloader.recent_limit,
        "video_downloader/telegram/all_messages": downloaderDraft.tgdownloader.all_messages,
        "video_downloader/telegram/date_from": downloaderDraft.tgdownloader.date_from,
        "video_downloader/telegram/date_to": downloaderDraft.tgdownloader.date_to,
        "video_downloader/telegram/include_videos": downloaderDraft.tgdownloader.include_videos,
        "video_downloader/telegram/include_photos": downloaderDraft.tgdownloader.include_photos,
        "video_downloader/telegram/overwrite": downloaderDraft.tgdownloader.overwrite,
        "video_downloader/telegram/output_subdir_by_title": downloaderDraft.tgdownloader.output_subdir_by_title,
        "video_downloader/telegram/concurrent": downloaderDraft.tgdownloader.concurrent,
        "video_downloader/telegram/cover_dir": downloaderDraft.tgdownloader.cover_dir,
        "wordformatter/output_dir": wordFormatterDraft.output_dir,
        "sidebar/order": sidebarOrderForSave(snapshot, orderDraft, toolsById),
      };
      WORD_FORMATTER_PAGE_KEYS.forEach((key) => {
        updates[WORD_FORMATTER_PAGE_SETTING_KEYS[key]] = wordFormatterDraft.page[key];
      });
      WORD_FORMATTER_STYLE_KEYS.forEach((styleKey) => {
        WORD_FORMATTER_STYLE_FIELDS.forEach((field) => {
          updates[WORD_FORMATTER_STYLE_SETTING_KEYS[styleKey][field]] = wordFormatterDraft.styles[styleKey][field];
        });
      });
      FILESORTER_CATEGORIES.forEach((category) => {
        updates[`filesorter/category_${category}`] = toolBehaviorDraft.filesorter.categories[category];
      });
      if (customThemeDraft) {
        THEME_ZONES.forEach((zone) => {
          updates[`theme/${themeDraft}/${zone}`] = themeColorsDraft[themeDraft]?.[zone] ?? DEFAULT_THEME_COLORS[themeDraft][zone];
        });
      }
      const next = await saveSettingsPatch({
        task_id: `settings-${Date.now()}`,
        updates,
      });
      onSaved(next);
      setNotice("\u5df2\u4fdd\u5b58");
    } catch (caught: unknown) {
      setNotice(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="settings-panel">
      <div className="tool-heading">
        <div>
          <p className="eyebrow">Legacy settings bridge</p>
          <h2>{"\u8bbe\u7f6e\u4e0e\u4e3b\u9898"}</h2>
          <p>{"\u5199\u56de\u65e7\u7248\u914d\u7f6e\uff0c\u4fdd\u5b58\u540e\u7acb\u5373\u5237\u65b0\u4fa7\u680f\u548c\u4e3b\u9898\u3002"}</p>
        </div>
        <span className="settings-mode-pill">{loading ? "\u8bfb\u53d6\u4e2d" : modeText}</span>
      </div>

      {error ? <div className="error-box">{error}</div> : null}
      {notice ? <div className="info-box">{notice}</div> : null}

      <div className="settings-grid">
        <section className="settings-card">
          <span>{"\u4e3b\u9898\u6765\u6e90"}</span>
          <strong>{modeText}</strong>
          <p>{snapshot?.settings_path ?? "browser-preview"}</p>
        </section>
        <section className="settings-card">
          <span>{"\u529f\u80fd\u72b6\u6001"}</span>
          <strong>{enabledTools} {"\u4e2a\u542f\u7528"}</strong>
          <p>{disabledTools} {"\u4e2a\u5185\u7f6e\u5de5\u5177\u7981\u7528\uff0c"}{disabledPlugins} {"\u4e2a\u63d2\u4ef6\u7981\u7528\u3002"}</p>
        </section>
        <section className="settings-card">
          <span>{"\u4fa7\u680f\u987a\u5e8f"}</span>
          <strong>{snapshot?.sidebar_order.length ?? 0} {"\u6761\u65e7\u987a\u5e8f"}</strong>
          <p>{"\u5df2\u6309\u65e7 `sidebar/order` \u5408\u5e76\u5185\u7f6e\u5de5\u5177\u4e0e\u63d2\u4ef6\u5165\u53e3\u3002"}</p>
        </section>
      </div>

      <section className="settings-card settings-wide-card">
        <span>{"\u8d26\u53f7\u504f\u597d"}</span>
        <p>
          {"\u4e0a\u6b21\u7528\u6237\uff1a"}{snapshot?.auth.last_user || "\u672a\u8bb0\u5f55"}
        </p>
        <div className="settings-tool-list">
          <label className="settings-toggle-row">
            <input checked={rememberPasswordDraft} onChange={(event) => setRememberPassword(event.target.checked)} type="checkbox" />
            <span>
              <b>{"\u8bb0\u4f4f\u5bc6\u7801\u504f\u597d"}</b>
              <small>{"\u4ec5\u5199\u56de\u65e7\u7248 auth/remember_password\uff0c\u4e0d\u5904\u7406\u771f\u5b9e\u5bc6\u7801\u3002"}</small>
            </span>
          </label>
          <label className="settings-toggle-row">
            <input checked={autoLoginDraft} onChange={(event) => setAutoLogin(event.target.checked)} type="checkbox" />
            <span>
              <b>{"\u81ea\u52a8\u767b\u5f55"}</b>
              <small>{"\u5f00\u542f\u65f6\u81ea\u52a8\u5f00\u542f\u8bb0\u4f4f\u5bc6\u7801\uff1b\u5173\u95ed\u8bb0\u4f4f\u5bc6\u7801\u4f1a\u53d6\u6d88\u81ea\u52a8\u767b\u5f55\u3002"}</small>
            </span>
          </label>
        </div>
      </section>

      <section className="settings-card settings-wide-card">
        <span>{"\u4e3b\u9898"}</span>
        <div className="settings-control-row">
          <div className="mode-switch">
            <button className={themeDraft === "dark" ? "active" : ""} onClick={() => setThemeDraft("dark")} type="button">
              {"\u6697\u8272"}
            </button>
            <button className={themeDraft === "light" ? "active" : ""} onClick={() => setThemeDraft("light")} type="button">
              {"\u4eae\u8272"}
            </button>
          </div>
          <label className="settings-toggle-row" style={{ margin: 0, minWidth: 250 }}>
            <input checked={customThemeDraft} onChange={(event) => setCustomThemeDraft(event.target.checked)} type="checkbox" />
            <span>
              <b>{"\u542f\u7528\u81ea\u5b9a\u4e49\u4e3b\u9898"}</b>
              <small>{customThemeDraft ? "\u4fdd\u5b58\u540e\u5199\u56de\u65e7\u7248 theme/*" : "\u5173\u95ed\u65f6\u4f7f\u7528\u65e7\u9ed8\u8ba4\u6697/\u4eae\u8272"}</small>
            </span>
          </label>
        </div>
      </section>

      <section className="settings-card settings-wide-card">
        <span>{"\u5de5\u5177\u9ed8\u8ba4\u76ee\u5f55"}</span>
        <p>{"\u5199\u56de\u5df2\u8fc1\u79fb\u5de5\u5177\u7684\u65e7\u7248 output_dir\uff0c\u7559\u7a7a\u53ef\u6e05\u7a7a\u9ed8\u8ba4\u76ee\u5f55\u3002"}</p>
        <div className="settings-tool-list">
          {TOOL_OUTPUT_DIRS.map((tool) => (
            <label className="settings-toggle-row tool-output-dir-row" key={tool.id}>
              <span>
                <b>{tool.label}</b>
                <small>{tool.id}/output_dir</small>
              </span>
              <input
                disabled={saving}
                onChange={(event) => updateToolOutputDir(tool.id, event.currentTarget.value)}
                placeholder="E:\\output"
                type="text"
                value={toolOutputDirDraft[tool.id]}
              />
            </label>
          ))}
        </div>
      </section>

      <section className="settings-card settings-wide-card">
        <span>{"\u4e0b\u8f7d\u5668\u504f\u597d"}</span>
        <p>{"Telegram \u8d26\u53f7\u504f\u597d\u5199\u56de\u65e7 video_downloader/* \u51ed\u636e\u952e\uff1b\u8fd9\u91cc\u4e0d\u5904\u7406\u5bc6\u7801\u3002Web/TG \u4ee3\u7406\u4ee5 host/port \u4e3a\u4e3b\uff0c\u65e7 proxy_url \u4ec5\u7531 bridge \u517c\u5bb9\u8bfb\u53d6\u3002"}</p>
        <div className="settings-tool-list">
          <strong>Web</strong>
          <div className="settings-control-row">
            <label className="field-block">
              <span>video_downloader/web/output_dir</span>
              <input disabled={saving} onChange={(event) => updateDownloader("webvideodownloader", "output_dir", event.currentTarget.value)} type="text" value={downloaderDraft.webvideodownloader.output_dir} />
            </label>
            <label className="field-block">
              <span>video_downloader/web/proxy_host</span>
              <input disabled={saving} onChange={(event) => updateDownloader("webvideodownloader", "proxy_host", event.currentTarget.value)} type="text" value={downloaderDraft.webvideodownloader.proxy_host} />
            </label>
            <label className="field-block">
              <span>video_downloader/web/proxy_port</span>
              <input disabled={saving} onChange={(event) => updateDownloader("webvideodownloader", "proxy_port", event.currentTarget.value)} type="text" value={downloaderDraft.webvideodownloader.proxy_port} />
            </label>
            <label className="field-block">
              <span>video_downloader/web/concurrent</span>
              <select disabled={saving} onChange={(event) => updateDownloader("webvideodownloader", "concurrent", event.currentTarget.value)} value={downloaderDraft.webvideodownloader.concurrent}>
                {["0", "1", "2", "3", "4", "5"].map((value) => (
                  <option key={value} value={value}>{value === "0" ? "auto" : value}</option>
                ))}
              </select>
            </label>
          </div>
          <div className="settings-control-row">
            <label className="settings-toggle-row">
              <input checked={downloaderDraft.webvideodownloader.overwrite} disabled={saving} onChange={(event) => updateDownloader("webvideodownloader", "overwrite", event.currentTarget.checked)} type="checkbox" />
              <span><b>video_downloader/web/overwrite</b><small>{"boolean -> 1/0"}</small></span>
            </label>
            <label className="settings-toggle-row">
              <input checked={downloaderDraft.webvideodownloader.output_subdir_by_title} disabled={saving} onChange={(event) => updateDownloader("webvideodownloader", "output_subdir_by_title", event.currentTarget.checked)} type="checkbox" />
              <span><b>video_downloader/web/output_subdir_by_title</b><small>{"boolean -> 1/0"}</small></span>
            </label>
          </div>
          <strong>Telegram</strong>
          <div className="settings-control-row">
            <label className="field-block">
              <span>video_downloader/api_id</span>
              <input disabled={saving} onChange={(event) => updateDownloader("tgdownloader", "api_id", event.currentTarget.value)} type="text" value={downloaderDraft.tgdownloader.api_id} />
            </label>
            <label className="field-block">
              <span>video_downloader/api_hash</span>
              <input disabled={saving} onChange={(event) => updateDownloader("tgdownloader", "api_hash", event.currentTarget.value)} type="text" value={downloaderDraft.tgdownloader.api_hash} />
            </label>
            <label className="field-block">
              <span>video_downloader/phone</span>
              <input disabled={saving} onChange={(event) => updateDownloader("tgdownloader", "phone", event.currentTarget.value)} type="text" value={downloaderDraft.tgdownloader.phone} />
            </label>
            <label className="field-block">
              <span>video_downloader/telegram/output_dir</span>
              <input disabled={saving} onChange={(event) => updateDownloader("tgdownloader", "output_dir", event.currentTarget.value)} type="text" value={downloaderDraft.tgdownloader.output_dir} />
            </label>
          </div>
          <div className="settings-control-row">
            <label className="field-block">
              <span>video_downloader/telegram/recent_limit</span>
              <input disabled={saving} onChange={(event) => updateDownloader("tgdownloader", "recent_limit", event.currentTarget.value)} type="text" value={downloaderDraft.tgdownloader.recent_limit} />
            </label>
            <label className="field-block">
              <span>video_downloader/telegram/date_from</span>
              <input disabled={saving} onChange={(event) => updateDownloader("tgdownloader", "date_from", event.currentTarget.value)} type="text" value={downloaderDraft.tgdownloader.date_from} />
            </label>
            <label className="field-block">
              <span>video_downloader/telegram/date_to</span>
              <input disabled={saving} onChange={(event) => updateDownloader("tgdownloader", "date_to", event.currentTarget.value)} type="text" value={downloaderDraft.tgdownloader.date_to} />
            </label>
            <label className="field-block">
              <span>video_downloader/telegram/concurrent</span>
              <select disabled={saving} onChange={(event) => updateDownloader("tgdownloader", "concurrent", event.currentTarget.value)} value={downloaderDraft.tgdownloader.concurrent}>
                {["0", "1", "2", "3", "4", "5"].map((value) => (
                  <option key={value} value={value}>{value === "0" ? "auto" : value}</option>
                ))}
              </select>
            </label>
          </div>
          <div className="settings-control-row">
            <label className="field-block">
              <span>video_downloader/telegram/proxy_host</span>
              <input disabled={saving} onChange={(event) => updateDownloader("tgdownloader", "proxy_host", event.currentTarget.value)} type="text" value={downloaderDraft.tgdownloader.proxy_host} />
            </label>
            <label className="field-block">
              <span>video_downloader/telegram/proxy_port</span>
              <input disabled={saving} onChange={(event) => updateDownloader("tgdownloader", "proxy_port", event.currentTarget.value)} type="text" value={downloaderDraft.tgdownloader.proxy_port} />
            </label>
          </div>
          <div className="settings-control-row">
            {[
              ["all_messages", "video_downloader/telegram/all_messages"],
              ["include_videos", "video_downloader/telegram/include_videos"],
              ["include_photos", "video_downloader/telegram/include_photos"],
              ["overwrite", "video_downloader/telegram/overwrite"],
              ["output_subdir_by_title", "video_downloader/telegram/output_subdir_by_title"],
            ].map(([key, label]) => (
              <label className="settings-toggle-row" key={key}>
                <input
                  checked={Boolean(downloaderDraft.tgdownloader[key as keyof DownloaderSettingsDraft["tgdownloader"]])}
                  disabled={saving}
                  onChange={(event) => updateDownloader("tgdownloader", key as keyof DownloaderSettingsDraft["tgdownloader"], event.currentTarget.checked)}
                  type="checkbox"
                />
                <span><b>{label}</b><small>{"boolean -> 1/0"}</small></span>
              </label>
            ))}
          </div>
        </div>
      </section>

      <section className="settings-card settings-wide-card">
        <span>Word Formatter</span>
        <p>{"\u5199\u56de\u65e7\u7248 wordformatter/output_dir\u3001page/* \u548c styles/* \u952e\uff0c\u4fdd\u6301 Tauri \u4e0e PyQt \u5171\u7528\u540c\u4e00\u5957\u914d\u7f6e\u3002"}</p>
        <div className="settings-tool-list">
          <label className="settings-toggle-row tool-output-dir-row">
            <span>
              <b>Output dir</b>
              <small>wordformatter/output_dir</small>
            </span>
            <input disabled={saving} onChange={(event) => updateWordFormatterOutputDir(event.currentTarget.value)} type="text" value={wordFormatterDraft.output_dir} />
          </label>
          <div className="settings-control-row">
            {WORD_FORMATTER_PAGE_KEYS.map((key) => (
              <label className="field-block" key={key}>
                <span>{WORD_FORMATTER_PAGE_SETTING_KEYS[key]}</span>
                <input disabled={saving} onChange={(event) => updateWordFormatterPage(key, event.currentTarget.value)} type="text" value={wordFormatterDraft.page[key]} />
              </label>
            ))}
          </div>
          {WORD_FORMATTER_STYLE_KEYS.map((styleKey) => (
            <div className="settings-tool-list" key={styleKey}>
              <strong>{WORD_FORMATTER_STYLE_TITLES[styleKey]}</strong>
              <div className="settings-control-row">
                {WORD_FORMATTER_STYLE_FIELDS.map((field) => (
                  <label className={field === "bold" ? "settings-toggle-row" : "field-block"} key={`${styleKey}-${field}`}>
                    {field === "bold" ? (
                      <>
                        <input
                          checked={Boolean(wordFormatterDraft.styles[styleKey].bold)}
                          disabled={saving}
                          onChange={(event) => updateWordFormatterStyle(styleKey, "bold", event.currentTarget.checked)}
                          type="checkbox"
                        />
                        <span>
                          <b>{WORD_FORMATTER_STYLE_SETTING_KEYS[styleKey].bold}</b>
                          <small>True/False</small>
                        </span>
                      </>
                    ) : (
                      <>
                        <span>{WORD_FORMATTER_STYLE_SETTING_KEYS[styleKey][field]}</span>
                        <input
                          disabled={saving}
                          onChange={(event) => updateWordFormatterStyle(styleKey, field, event.currentTarget.value)}
                          type="text"
                          value={String(wordFormatterDraft.styles[styleKey][field])}
                        />
                      </>
                    )}
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="settings-card settings-wide-card">
        <span>{"\u5de5\u5177\u884c\u4e3a\u504f\u597d"}</span>
        <p>{"\u5199\u56de\u6279\u91cf\u547d\u540d\u3001\u6587\u4ef6\u5206\u7c7b\u3001\u91cd\u590d\u6587\u4ef6\u548c\u76f4\u94fe\u4e0b\u8f7d\u7684\u65e7\u7248\u504f\u597d\u952e\u3002"}</p>
        <div className="settings-tool-list">
          <label className="settings-toggle-row tool-output-dir-row">
            <span>
              <b>Batch</b>
              <small>batchrename/input_dir</small>
            </span>
            <input disabled={saving} onChange={(event) => updateToolBehavior("batchrename", "input_dir", event.currentTarget.value)} type="text" value={toolBehaviorDraft.batchrename.input_dir} />
          </label>
          <label className="settings-toggle-row tool-output-dir-row">
            <span>
              <b>Batch prefix</b>
              <small>batchrename/prefix</small>
            </span>
            <input disabled={saving} onChange={(event) => updateToolBehavior("batchrename", "prefix", event.currentTarget.value)} type="text" value={toolBehaviorDraft.batchrename.prefix} />
          </label>
          <div className="settings-control-row">
            <label className="field-block">
              <span>batchrename/group_mode</span>
              <select disabled={saving} onChange={(event) => updateToolBehavior("batchrename", "group_mode", event.currentTarget.value)} value={toolBehaviorDraft.batchrename.group_mode}>
                <option value="\u6309\u540e\u7f00">{"\u6309\u540e\u7f00"}</option>
                <option value="\u6309\u7c7b\u578b">{"\u6309\u7c7b\u578b"}</option>
                <option value="\u5168\u6587\u4ef6">{"\u5168\u6587\u4ef6"}</option>
              </select>
            </label>
            <label className="field-block">
              <span>batchrename/sort_mode</span>
              <select disabled={saving} onChange={(event) => updateToolBehavior("batchrename", "sort_mode", event.currentTarget.value)} value={toolBehaviorDraft.batchrename.sort_mode}>
                <option value="\u6309\u547d\u540d">{"\u6309\u547d\u540d"}</option>
                <option value="\u4fee\u6539\u65e5\u671f">{"\u4fee\u6539\u65e5\u671f"}</option>
                <option value="\u6587\u4ef6\u5927\u5c0f">{"\u6587\u4ef6\u5927\u5c0f"}</option>
              </select>
            </label>
            <label className="field-block">
              <span>batchrename/sort_order</span>
              <select disabled={saving} onChange={(event) => updateToolBehavior("batchrename", "sort_order", event.currentTarget.value)} value={toolBehaviorDraft.batchrename.sort_order}>
                <option value="\u4ece\u5c0f\u5230\u5927">{"\u4ece\u5c0f\u5230\u5927"}</option>
                <option value="\u4ece\u5927\u5230\u5c0f">{"\u4ece\u5927\u5230\u5c0f"}</option>
              </select>
            </label>
          </div>
          <label className="settings-toggle-row tool-output-dir-row">
            <span>
              <b>File sorter</b>
              <small>filesorter/input_dir</small>
            </span>
            <input disabled={saving} onChange={(event) => updateToolBehavior("filesorter", "input_dir", event.currentTarget.value)} type="text" value={toolBehaviorDraft.filesorter.input_dir} />
          </label>
          <label className="field-block">
            <span>filesorter/mode</span>
            <select disabled={saving} onChange={(event) => updateToolBehavior("filesorter", "mode", event.currentTarget.value)} value={toolBehaviorDraft.filesorter.mode}>
              <option value="\u6309\u5927\u7c7b\u5206\u7c7b">{"\u6309\u5927\u7c7b\u5206\u7c7b"}</option>
              <option value="\u6309\u5206\u8fa8\u7387\u5206\u7c7b">{"\u6309\u5206\u8fa8\u7387\u5206\u7c7b"}</option>
            </select>
          </label>
          <div className="settings-control-row">
            {FILESORTER_CATEGORIES.map((category) => (
              <label className="settings-toggle-row" key={category}>
                <input
                  checked={toolBehaviorDraft.filesorter.categories[category]}
                  disabled={saving}
                  onChange={(event) => updateFilesorterCategory(category, event.currentTarget.checked)}
                  type="checkbox"
                />
                <span>
                  <b>{category}</b>
                  <small>{`filesorter/category_${category}`}</small>
                </span>
              </label>
            ))}
          </div>
          <label className="settings-toggle-row tool-output-dir-row">
            <span>
              <b>Same</b>
              <small>same/input_dir</small>
            </span>
            <input disabled={saving} onChange={(event) => updateToolBehavior("same", "input_dir", event.currentTarget.value)} type="text" value={toolBehaviorDraft.same.input_dir} />
          </label>
          <label className="settings-toggle-row">
            <input checked={toolBehaviorDraft.same.recursive} disabled={saving} onChange={(event) => updateToolBehavior("same", "recursive", event.currentTarget.checked)} type="checkbox" />
            <span>
              <b>same/recursive</b>
              <small>{"boolean -> 1/0"}</small>
            </span>
          </label>
          <div className="settings-control-row">
            <label className="field-block">
              <span>directdownloader/connections</span>
              <input disabled={saving} onChange={(event) => updateToolBehavior("directdownloader", "connections", event.currentTarget.value)} type="text" value={toolBehaviorDraft.directdownloader.connections} />
            </label>
            <label className="field-block">
              <span>directdownloader/proxy_url</span>
              <input disabled={saving} onChange={(event) => updateToolBehavior("directdownloader", "proxy_url", event.currentTarget.value)} type="text" value={toolBehaviorDraft.directdownloader.proxy_url} />
            </label>
            <label className="field-block">
              <span>directdownloader/referer</span>
              <input disabled={saving} onChange={(event) => updateToolBehavior("directdownloader", "referer", event.currentTarget.value)} type="text" value={toolBehaviorDraft.directdownloader.referer} />
            </label>
          </div>
          <label className="settings-toggle-row">
            <input checked={toolBehaviorDraft.directdownloader.overwrite} disabled={saving} onChange={(event) => updateToolBehavior("directdownloader", "overwrite", event.currentTarget.checked)} type="checkbox" />
            <span>
              <b>directdownloader/overwrite</b>
              <small>{"boolean -> 1/0"}</small>
            </span>
          </label>
          <label className="settings-toggle-row">
            <input checked={toolBehaviorDraft.directdownloader.output_subdir_by_filename} disabled={saving} onChange={(event) => updateToolBehavior("directdownloader", "output_subdir_by_filename", event.currentTarget.checked)} type="checkbox" />
            <span>
              <b>directdownloader/output_subdir_by_filename</b>
              <small>{"boolean -> 1/0"}</small>
            </span>
          </label>
        </div>
      </section>

      <section className="settings-card settings-wide-card">
        <span>{"\u5185\u7f6e\u5de5\u5177"}</span>
        <div className="settings-tool-list">
          {builtinTools.map((tool) => {
            const enabled = !disabledDraft.has(tool.id);
            return (
              <label className="settings-toggle-row" key={tool.id}>
                <input checked={enabled} onChange={(event) => setToolEnabled(tool.id, event.target.checked)} type="checkbox" />
                <span>
                  <b>{toolDisplayName(tool)}</b>
                  <small>{toolMetadata(tool).join(" \u00b7 ")}</small>
                </span>
              </label>
            );
          })}
        </div>
      </section>

      <section className="settings-card settings-wide-card">
        <span>{"\u4fa7\u680f\u987a\u5e8f"}</span>
        <p>{"\u5185\u7f6e\u5de5\u5177\u548c\u63d2\u4ef6\u90fd\u4f1a\u663e\u793a\uff1b\u4fdd\u5b58\u65f6\u540c\u6b65\u5199\u56de\u542f\u505c\u548c\u6392\u5e8f\u3002"}</p>
        <div className="sidebar-order-list">
          {orderedTools.map((tool, index) => (
            <div className="sidebar-order-row" key={tool.id}>
              <span className="sidebar-order-index">{index + 1}</span>
              <span className="sidebar-order-main">
                <b>{tool.sidebar_label ?? tool.title}</b>
                <small>
                  {[...toolMetadata(tool), sidebarStatus(tool)].filter(Boolean).join(" \u00b7 ")}
                </small>
              </span>
              <span className="sidebar-order-actions">
                <button disabled={index === 0 || saving} onClick={() => moveSidebarItem(tool.id, -1)} type="button">
                  {"\u4e0a\u79fb"}
                </button>
                <button disabled={index === orderedTools.length - 1 || saving} onClick={() => moveSidebarItem(tool.id, 1)} type="button">
                  {"\u4e0b\u79fb"}
                </button>
              </span>
            </div>
          ))}
        </div>
      </section>

      <section className="settings-card settings-wide-card">
        <span>{"\u63d2\u4ef6\u72b6\u6001"}</span>
        <p>{"\u5199\u56de\u65e7\u7248 plugins/disabled\uff1bmanifest \u5df2\u7981\u7528\u7684\u63d2\u4ef6\u4e0d\u80fd\u5728\u6b64\u542f\u7528\u3002"}</p>
        <div className="plugin-status-list">
          {pluginTools.length ? (
            pluginTools.map((tool) => {
              const enabled = tool.manifest_enabled !== false && !disabledPluginDraft.has(pluginConfigKey(tool));
              return (
                <label className="settings-toggle-row" key={tool.id}>
                  <input
                    checked={enabled}
                    disabled={tool.manifest_enabled === false}
                    onChange={(event) => setPluginEnabled(tool, event.target.checked)}
                    type="checkbox"
                  />
                  <span>
                    <b>{toolDisplayName(tool)}</b>
                    <small>
                      {[...toolMetadata(tool), tool.manifest_enabled === false ? "manifest \u5df2\u7981\u7528" : enabled ? "\u542f\u7528" : "\u5df2\u7981\u7528"].filter(Boolean).join(" \u00b7 ")}
                    </small>
                  </span>
                </label>
              );
            })
          ) : (
            <small>{"\u6682\u65e0\u63d2\u4ef6\u5165\u53e3"}</small>
          )}
        </div>
      </section>

      <section className="settings-card settings-wide-card">
        <span>{"\u4e3b\u9898\u8272\u6620\u5c04"}</span>
        <p>{customThemeDraft ? "\u7f16\u8f91\u540e\u4fdd\u5b58\u5230\u5f53\u524d\u6697/\u4eae\u4e3b\u9898\u7684\u65e7\u7248\u914d\u7f6e\u952e\u3002" : "\u53ef\u5148\u4fdd\u7559\u8349\u7a3f\uff1b\u5173\u95ed\u81ea\u5b9a\u4e49\u65f6\u4e0d\u5199\u5165 theme/*\u3002"}</p>
        <div className="theme-swatch-row">
          {THEME_ZONES.map((zone) => {
            const value = themeColorsDraft[themeDraft]?.[zone] ?? DEFAULT_THEME_COLORS[themeDraft][zone];
            return (
              <label className="theme-swatch" key={zone}>
                <i style={{ background: value }} />
                <b>{zone}</b>
                <input
                  aria-label={`${zone} color`}
                  onChange={(event) => updateThemeColor(zone, event.target.value)}
                  style={{
                    background: "color-mix(in oklab, var(--legacy-input-bg), transparent 12%)",
                    border: "1px solid color-mix(in oklab, var(--legacy-text-secondary), transparent 72%)",
                    borderRadius: 10,
                    color: "var(--legacy-text-primary)",
                    font: "inherit",
                    minWidth: 0,
                    padding: "7px 9px",
                    width: "100%",
                  }}
                  type="text"
                  value={value}
                />
              </label>
            );
          })}
        </div>
      </section>

      <div className="settings-save-row">
        <button className="primary-button" disabled={!snapshot || saving} onClick={saveSettings} type="button">
          {saving ? "\u4fdd\u5b58\u4e2d..." : "\u4fdd\u5b58\u8bbe\u7f6e"}
        </button>
      </div>
    </div>
  );
}

function App() {
  const [snapshot, setSnapshot] = useState<SettingsSnapshot | null>(null);
  const [settingsError, setSettingsError] = useState("");
  const [activeToolId, setActiveToolId] = useState(fallbackTools[0].id);
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    loadSettingsSnapshot()
      .then((data) => {
        if (cancelled) {
          return;
        }
        setSnapshot(data);
        setSettingsError("");
        const nextTool = firstSelectableTool(data.tools);
        if (nextTool) {
          setActiveToolId(nextTool.id);
        }
      })
      .catch((caught: unknown) => {
        if (cancelled) {
          return;
        }
        setSettingsError(caught instanceof Error ? caught.message : String(caught));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const tools = snapshot?.tools?.length ? snapshot.tools : fallbackTools;
  const activeTool = useMemo(() => tools.find((tool) => tool.id === activeToolId) ?? firstSelectableTool(tools), [activeToolId, tools]);

  function selectTool(toolId: string) {
    setSettingsOpen(false);
    setActiveToolId(toolId);
  }

  function handleSettingsSaved(nextSnapshot: SettingsSnapshot) {
    setSnapshot(nextSnapshot);
    const current = nextSnapshot.tools.find((tool) => tool.id === activeToolId);
    if (!current || current.enabled === false) {
      setActiveToolId(firstSelectableTool(nextSnapshot.tools).id);
    }
  }

  return (
    <div className="theme-root" style={themeStyle(snapshot)} data-theme-mode={snapshot?.theme.mode ?? "light"}>
      <ToolShell
        title="Hyl Toolbox"
        tools={tools}
        activeToolId={activeTool.id}
        onSelectTool={selectTool}
        onOpenSettings={() => setSettingsOpen(true)}
        settingsOpen={settingsOpen}
      >
        {settingsOpen ? (
          <SettingsPanel snapshot={snapshot} loading={!snapshot && !settingsError} error={settingsError} onSaved={handleSettingsSaved} />
        ) : activeTool.id === "music" ? (
          <MusicTool initialOutputDir={toolOutputDir(snapshot, "music")} />
        ) : activeTool.id === "imageconvert" ? (
          <ImageConvertTool initialOutputDir={toolOutputDir(snapshot, "imageconvert")} />
        ) : activeTool.id === "mp4mp3" ? (
          <Mp4Mp3Tool initialOutputDir={toolOutputDir(snapshot, "mp4mp3")} />
        ) : activeTool.id === "pdftools" ? (
          <PdfToolsTool initialOutputDir={toolOutputDir(snapshot, "pdftools")} />
        ) : activeTool.id === "batchrename" ? (
          <BatchRenameTool initialSettings={toolBehaviorSettings(snapshot, "batchrename")} />
        ) : activeTool.id === "filesorter" ? (
          <FileSorterTool initialSettings={toolBehaviorSettings(snapshot, "filesorter")} />
        ) : activeTool.id === "same" ? (
          <SameTool initialSettings={toolBehaviorSettings(snapshot, "same")} />
        ) : activeTool.id === "wordformatter" ? (
          <WordFormatterTool initialSettings={wordFormatterSettings(snapshot)} />
        ) : activeTool.id === "base64" ? (
          <Base64Tool initialOutputDir={toolOutputDir(snapshot, "base64")} />
        ) : activeTool.id === "directdownloader" ? (
          <DirectDownloaderTool initialOutputDir={toolOutputDir(snapshot, "directdownloader")} initialSettings={toolBehaviorSettings(snapshot, "directdownloader")} />
        ) : activeTool.id === "webvideodownloader" ? (
          <WebVideoDownloaderTool initialSettings={downloaderSettings(snapshot, "webvideodownloader")} />
        ) : activeTool.id === "tgdownloader" ? (
          <TgDownloaderTool initialSettings={downloaderSettings(snapshot, "tgdownloader")} />
        ) : activeTool.id === "zipandpng" ? (
          <ZipPngTool initialOutputDir={toolOutputDir(snapshot, "zipandpng")} />
        ) : activeTool.id === "plugin:json_tools" ? (
          <JsonToolsPluginTool />
        ) : activeTool.id === "plugin:regex_tools" ? (
          <RegexToolsPluginTool />
        ) : activeTool.id === "plugin:csv_tools" ? (
          <CsvToolsPluginTool />
        ) : activeTool.id === "plugin:file_hasher" ? (
          <FileHasherPluginTool />
        ) : activeTool.id === "plugin:archive_extractor" ? (
          <ArchiveExtractorPluginTool initialSettings={snapshot?.tool_settings?.archive_extractor ?? {}} />
        ) : activeTool.id === "plugin:text_tools" ? (
          <TextToolsPluginTool />
        ) : activeTool.id === "plugin:timestamp_tools" ? (
          <TimestampToolsPluginTool />
        ) : activeTool.id === "plugin:url_tools" ? (
          <UrlToolsPluginTool />
        ) : activeTool.id === "plugin:uuid_tools" ? (
          <UuidToolsPluginTool />
        ) : (
          <div className="empty-tool-panel">
            <div className="empty-orb" aria-hidden="true" />
            <p className="eyebrow">{activeTool.enabled === false ? "\u5df2\u7981\u7528" : "\u6682\u672a\u63a5\u5165"}</p>
            <h2>{activeTool.title}</h2>
            <p>{activeTool.enabled === false ? "\u8be5\u5165\u53e3\u5728\u65e7\u7248\u8bbe\u7f6e\u4e2d\u88ab\u7981\u7528\u3002" : "\u6682\u672a\u63a5\u5165\u3002\u5f53\u524d\u5148\u4fdd\u7559\u5165\u53e3\uff0c\u65b9\u4fbf\u540e\u7eed\u5e73\u6ed1\u8fc1\u79fb\u3002"}</p>
          </div>
        )}
      </ToolShell>
    </div>
  );
}

export default App;
