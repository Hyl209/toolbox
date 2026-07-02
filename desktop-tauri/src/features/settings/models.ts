import type { SettingsPatch, SettingsSnapshot, ToolSettings } from "../../api/tauri";

export const THEME_NAMES = ["dark", "light"] as const;
export type ThemeName = (typeof THEME_NAMES)[number];

export const THEME_ZONES = ["window_bg", "surface_bg", "card_bg", "accent", "text_primary", "text_secondary", "input_bg"] as const;
export type ThemeZone = (typeof THEME_ZONES)[number];
export type ThemeColors = Record<ThemeZone, string>;

export const TOOL_OUTPUT_DIRS = [
  { id: "base64", label: "Base64 图片" },
  { id: "music", label: "NCM 转换" },
  { id: "zipandpng", label: "PNG 伪装" },
  { id: "mp4mp3", label: "MP4 转 MP3" },
  { id: "imageconvert", label: "图片格式转换" },
  { id: "pdftools", label: "PDF 工具" },
  { id: "directdownloader", label: "直链下载" },
  { id: "archive_extractor", label: "解压工具" },
] as const;
export type ToolOutputDirId = (typeof TOOL_OUTPUT_DIRS)[number]["id"];
export type ToolOutputDirDraft = Record<ToolOutputDirId, string>;

export const FILESORTER_CATEGORIES = ["图片", "视频", "音频", "文档", "压缩包", "程序", "其他"] as const;

export const WORD_FORMATTER_PAGE_KEYS = [
  "top_margin_cm",
  "bottom_margin_cm",
  "left_margin_cm",
  "right_margin_cm",
  "header_distance_cm",
  "footer_distance_cm",
] as const;
export type WordFormatterPageKey = (typeof WORD_FORMATTER_PAGE_KEYS)[number];

export const WORD_FORMATTER_STYLE_KEYS = ["heading1", "heading2", "heading3", "heading4", "body", "table"] as const;
export type WordFormatterStyleKey = (typeof WORD_FORMATTER_STYLE_KEYS)[number];

export const WORD_FORMATTER_STYLE_FIELDS = ["font", "size_pt", "bold", "line_spacing", "space_before_pt", "space_after_pt", "first_line_indent_cm"] as const;
export type WordFormatterStyleField = (typeof WORD_FORMATTER_STYLE_FIELDS)[number];

export const WORD_FORMATTER_STYLE_TITLES: Record<WordFormatterStyleKey, string> = {
  heading1: "标题 1",
  heading2: "标题 2",
  heading3: "标题 3",
  heading4: "标题 4",
  body: "正文",
  table: "表格",
};

export const THEME_ZONE_LABELS: Record<ThemeZone, { title: string; description: string }> = {
  window_bg: { title: "窗口背景", description: "整个设置窗口的最外层底色。" },
  surface_bg: { title: "面板底色", description: "内容区与侧栏的基础表面色。" },
  card_bg: { title: "卡片背景", description: "设置卡片与信息块的背景色。" },
  accent: { title: "主强调色", description: "按钮、选中态与关键高亮色。" },
  text_primary: { title: "主文字", description: "一级标题与主要正文颜色。" },
  text_secondary: { title: "次文字", description: "说明文字与辅助信息颜色。" },
  input_bg: { title: "输入框背景", description: "输入框、下拉框与可编辑区域底色。" },
};

export const WORD_FORMATTER_PAGE_LABELS: Record<WordFormatterPageKey, string> = {
  top_margin_cm: "上边距（cm）",
  bottom_margin_cm: "下边距（cm）",
  left_margin_cm: "左边距（cm）",
  right_margin_cm: "右边距（cm）",
  header_distance_cm: "页眉距离（cm）",
  footer_distance_cm: "页脚距离（cm）",
};

export const WORD_FORMATTER_FIELD_LABELS: Record<WordFormatterStyleField, string> = {
  font: "字体",
  size_pt: "字号（pt）",
  bold: "是否加粗",
  line_spacing: "行距",
  space_before_pt: "段前（pt）",
  space_after_pt: "段后（pt）",
  first_line_indent_cm: "首行缩进（cm）",
};

export type WordFormatterStyleDraft = Record<WordFormatterStyleField, string | boolean>;
export type WordFormatterDraft = {
  output_dir: string;
  page: Record<WordFormatterPageKey, string>;
  styles: Record<WordFormatterStyleKey, WordFormatterStyleDraft>;
};

export type ToolBehaviorDraft = {
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

export type DownloaderSettingsDraft = {
  webvideodownloader: {
    output_dir: string;
    proxy_host: string;
    proxy_port: string;
    proxy_url: string;
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
    proxy_url: string;
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

export type SettingsDraftState = {
  theme: ThemeName;
  customThemeEnabled: boolean;
  rememberPassword: boolean;
  autoLogin: boolean;
  themeColors: Record<ThemeName, ThemeColors>;
  toolOutputDirs: ToolOutputDirDraft;
  toolBehavior: ToolBehaviorDraft;
  downloader: DownloaderSettingsDraft;
  wordFormatter: WordFormatterDraft;
  disabledTools: Set<string>;
  disabledPlugins: Set<string>;
  sidebarOrder: string[];
};

export type SettingsUpdates = SettingsPatch["updates"];
export type ToolBehaviorSettingsId = "batchrename" | "filesorter" | "same" | "directdownloader";
export type DownloaderSettingsId = "webvideodownloader" | "tgdownloader";

export const DEFAULT_THEME_COLORS: Record<ThemeName, ThemeColors> = {
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

export const DEFAULT_TOOL_OUTPUT_DIR_DRAFT = Object.fromEntries(TOOL_OUTPUT_DIRS.map(({ id }) => [id, ""])) as ToolOutputDirDraft;

export const DEFAULT_TOOL_BEHAVIOR_DRAFT: ToolBehaviorDraft = {
  batchrename: {
    input_dir: "",
    prefix: "批量命名",
    group_mode: "按后缀",
    sort_mode: "按命名",
    sort_order: "从小到大",
  },
  filesorter: {
    input_dir: "",
    mode: "按大类分类",
    categories: Object.fromEntries(FILESORTER_CATEGORIES.map((category) => [category, true])),
  },
  same: {
    input_dir: "",
    recursive: true,
  },
  directdownloader: {
    connections: "16",
    overwrite: false,
    output_subdir_by_filename: false,
    proxy_url: "",
    referer: "",
  },
};

export const DEFAULT_DOWNLOADER_SETTINGS_DRAFT: DownloaderSettingsDraft = {
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

export const DEFAULT_WORD_FORMATTER_DRAFT: WordFormatterDraft = {
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

export const WORD_FORMATTER_PAGE_SETTING_KEYS: Record<WordFormatterPageKey, string> = {
  top_margin_cm: "wordformatter/page/top_margin_cm",
  bottom_margin_cm: "wordformatter/page/bottom_margin_cm",
  left_margin_cm: "wordformatter/page/left_margin_cm",
  right_margin_cm: "wordformatter/page/right_margin_cm",
  header_distance_cm: "wordformatter/page/header_distance_cm",
  footer_distance_cm: "wordformatter/page/footer_distance_cm",
};

export const WORD_FORMATTER_STYLE_SETTING_KEYS: Record<WordFormatterStyleKey, Record<WordFormatterStyleField, string>> = {
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

export function cloneWordFormatterDraft(source: WordFormatterDraft = DEFAULT_WORD_FORMATTER_DRAFT): WordFormatterDraft {
  return {
    output_dir: source.output_dir,
    page: { ...source.page },
    styles: Object.fromEntries(
      WORD_FORMATTER_STYLE_KEYS.map((styleKey) => [styleKey, { ...source.styles[styleKey] }]),
    ) as WordFormatterDraft["styles"],
  };
}

export function cloneThemeColors(source: Record<ThemeName, ThemeColors> = DEFAULT_THEME_COLORS): Record<ThemeName, ThemeColors> {
  return {
    dark: { ...source.dark },
    light: { ...source.light },
  };
}

export function cloneToolBehaviorDraft(source: ToolBehaviorDraft = DEFAULT_TOOL_BEHAVIOR_DRAFT): ToolBehaviorDraft {
  return {
    batchrename: { ...source.batchrename },
    filesorter: {
      ...source.filesorter,
      categories: { ...source.filesorter.categories },
    },
    same: { ...source.same },
    directdownloader: { ...source.directdownloader },
  };
}

export function cloneDownloaderSettingsDraft(source: DownloaderSettingsDraft = DEFAULT_DOWNLOADER_SETTINGS_DRAFT): DownloaderSettingsDraft {
  return {
    webvideodownloader: { ...source.webvideodownloader },
    tgdownloader: { ...source.tgdownloader },
  };
}

export function toolSettingsFromSnapshot(snapshot: SettingsSnapshot | null, toolId: string): ToolSettings {
  return snapshot?.tool_settings?.[toolId] ?? {};
}
